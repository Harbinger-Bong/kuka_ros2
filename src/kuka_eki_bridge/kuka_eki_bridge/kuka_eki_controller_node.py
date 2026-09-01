"""
kuka_eki_controller_node.py

The single authoritative interface between MoveIt and the real KRC4, given
this cell has no RSI technology package licensed (ruling out kuka_rsi_driver
entirely -- rsi_only/eki_rsi/mxa_rsi all require the RSI channel for cyclic
control, EKI alone only handles handshaking in that stack). This node stands
in for a ros2_control hardware interface: it is the FollowJointTrajectory
action server MoveGroup's trajectory execution manager talks to directly
(see eki_controllers.yaml), and it is the only thing that talks to the
KRC4, over the existing EKI motion + state sockets.

There is no ros2_control, no controller_manager, and no mock/fake hardware
in this path. /joint_states here is the REAL robot's state, not a loopback
simulation -- robot_state_publisher/RViz/TF downstream of this node reflect
the actual cell.

Replaces (deleted): bridge_node.py, gripper_bridge.py.

CHANGES (2026-07-30):
  goal_handle.succeed() used to fire purely off summed time.sleep(dt) from
  the PLANNED trajectory timing -- nothing here ever checked the real KRC4
  state before declaring a trajectory done. That let control_server fire
  gripper/retract commands while the real arm was still mid-move.
  Fix v1: block on real /joint_states-sourced arrival for the FINAL
  waypoint only, via _wait_until_arrived(), instead of trusting planned dt.

CHANGES (2026-07-30, later same day):
  Fix v1 above exposed a SEPARATE, pre-existing structural issue rather
  than causing a new one: MoveGroup's own trajectory_execution_manager
  watchdog (execution_duration_monitoring) independently cancels a goal
  if it runs past the PLANNED duration (scaled by a margin) -- it was
  written assuming the controller reports completion promptly and
  honestly. Real KRC4 execution is running well behind Pilz's planned
  timing (see 2026-07-30 field data), so MoveGroup's watchdog now fires
  and cancels the goal before our real-arrival wait can succeed, on
  nearly every non-trivial trajectory.

  _wait_until_arrived() was also blocking through that cancel signal --
  it never checked self._preempted while polling, so a client-side cancel
  was silently ignored for the full ARRIVAL_TIMEOUT_SEC, and this code
  then called goal_handle.abort() on a goal the client had already given
  up on. Fixed: the wait loop now checks self._preempted every iteration
  and returns 'preempted' immediately, so the goal is properly resolved
  with goal_handle.canceled() instead of a late, invalid abort().

  This does NOT fix MoveGroup's watchdog itself -- that is a separate,
  required change on the moveit_config / launch side (raise or disable
  trajectory_execution.execution_duration_monitoring /
  allowed_execution_duration_scaling / allowed_goal_duration_margin),
  since MoveGroup's timing assumption is fundamentally miscalibrated
  against this bridge's real (non-ros2_control) execution characteristics.
  See eki_moveit_planning.launch.py for where to add the override.

  At this point still holding off on checking EVERY kept waypoint against
  real state (not just the final one), reasoning that extending real-waits
  to every waypoint would only make MoveGroup's watchdog fire earlier and
  more often, not less.

CHANGES (2026-07-31):
  Replaced the flat ARRIVAL_TIMEOUT_SEC=120.0 with a kinematics-derived
  per-move estimate (estimate_arrival_time_sec, trapezoidal/triangular
  profile from the kr6_r900_2 joint limits, max across axes since KRL's
  PTP synchronizes axes to arrive together).

CHANGES (2026-07-31, later same day):
  Field data with the adaptive timeout above surfaced the REAL bug: the
  intermediate-waypoint loop was never checking real arrival at all --
  it advanced through kept waypoints on planned dt (time.sleep(dt) from
  the trajectory's time_from_start), exactly the same discredited
  assumption already fixed for the final waypoint back on 2026-07-30.
  Since execution_duration_monitoring is already disabled on the
  moveit_config/launch side (see 2026-07-30 entry), the watchdog-race
  concern that justified skipping intermediate real-waits no longer
  applies, so it's now safe to remove.

  Symptom before this fix: last_seen at the reported timeout was often
  20+ degrees off target on every axis -- not a slow-final-hop problem,
  but backlog: the loop kept firing new ptp() commands every planned dt
  regardless of whether the real arm had reached the PREVIOUS command,
  so by the last waypoint the arm was chasing a stale position several
  waypoints behind.

  Fix: every kept waypoint (not just the final one) now blocks on real
  arrival via _wait_until_arrived(), with its own kinematics-derived
  adaptive timeout. Intermediate waypoints use a looser
  INTERMEDIATE_TOLERANCE_DEG (goal precision only matters for the final
  waypoint, which downstream nodes act on) so this isn't as slow as the
  tight final check would be if applied throughout.

  This removes the old prev_t / planned-dt sleep from the intermediate
  branch entirely -- there is no more "trust the planner's timing" path
  left in this function.

  Caveats carried forward (do not remove until resolved):
    - ACCEL_SCALING_TODO: whether KSS scales acceleration by
      max_velocity_scaling the same way it scales velocity is NOT
      confirmed from documentation -- amax_scaled in
      estimate_arrival_time_sec() assumes 1:1 scaling. Logged
      (estimated, actual) pairs from the per-waypoint arrival-timing
      log line are the way to check this, not guessing.
    - ARRIVAL_TIME_MARGIN is an empirical fudge factor, not a physical
      constant. Tune it from logged data once enough real runs exist.
    - Still open, NOT yet investigated: whether EkiMotionClient.ptp()
      blocks until the KRC4 acknowledges the command or is fire-and-
      forget the instant the socket write returns. If fire-and-forget
      and the KRC4 itself queues multiple pending PTPs, there could be
      controller-side queue pileup independent of this node's own
      per-waypoint waiting. Needs a standalone test (single ptp() call
      + high-rate _state_loop logging) to confirm either way.

CHANGES (2026-08-03):
  Added a COMMANDED joint-target publisher (/commanded_joint_states) for
  dataset recording (episode_recorder.py). Every time this node actually
  sends a ptp() to the KRC4 for a kept waypoint, it now also publishes
  that same target as a JointState on /commanded_joint_states, so a
  recorder can log (real_state, commanded_target) pairs at each tick
  instead of having to infer "the action" purely by differencing
  consecutive observed states offline.

  IMPORTANT CAVEAT for anyone consuming this topic: this is NOT a
  continuous per-cycle command stream (there is no RSI channel on this
  cell -- see module docstring). It is a STEP signal that only changes
  when _execute_trajectory dispatches a new kept waypoint (every
  ~0.1-0.6s in practice, not fixed-rate). A recorder sampling this at a
  fixed rate will see the same commanded target repeated across several
  consecutive samples while the real arm is still catching up to it via
  _wait_until_arrived(). That's correct, not a bug -- do not mistake
  repeated values here for a stalled recorder; cross-check against
  /joint_states (which changes continuously) if in doubt.

  Published AFTER a successful ptp() send (not before), so a transmission
  failure never results in a phantom "commanded" value for a target that
  was never actually sent to the KRC4.
"""

import math
import sys
import threading
import time
import tty
import termios

import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from control_msgs.action import FollowJointTrajectory
from sensor_msgs.msg import JointState
from std_msgs.msg import Int8

from kuka_eki.eki import EkiMotionClient, EkiStateClient
from kuka_eki.krl import Axis

KUKA_IP = "192.168.1.147"

GRIPPER_CMD_TOPIC = '/gripper_cmd'          # Int8: 1 = ON, 0 = OFF
JOINT_STATE_TOPIC = '/joint_states'
COMMANDED_JOINT_TOPIC = '/commanded_joint_states'  # see CHANGES (2026-08-03)
ACTION_NAME = 'eki_arm_controller/follow_joint_trajectory'  # moveit_simple_controller_manager
                                                             # builds the full action name as
                                                             # <controller_name>/<action_ns> --
                                                             # must match eki_controllers.yaml's
                                                             # eki_arm_controller + action_ns pair.

JOINT_ORDER = [f'joint_{i}' for i in range(1, 7)]  # must match the URDF's joint names

MIN_STEP_DEG = 2.0    # skip a waypoint unless it's moved at least this far
                       # from the last one actually sent -- each ptp() is a
                       # discrete exact-stop move on the KRC4 (no blending),
                       # so forwarding every fine-grained interpolated point
                       # from AddTimeOptimalParameterization causes a visible
                       # stop-start stutter ("brr brr brr"). Raise this if it
                       # still stutters; lower it if path fidelity matters
                       # more than smoothness for a given move. The real fix
                       # is continuous-path blending (C_PTP/C_DIS) on the KRL
                       # side, if that program is ever open for editing.

MAX_VELOCITY_SCALING = 0.5   # passed to every ptp() below -- also fed into
                              # estimate_arrival_time_sec() so the adaptive
                              # timeout matches the speed actually commanded.
                              # Kept as one module constant since every
                              # ptp() call in this file uses the same value;
                              # if that ever changes, thread the value
                              # through explicitly instead of relying on
                              # this constant matching by convention.

ARRIVAL_TOLERANCE_DEG = 0.5        # per-axis max error vs commanded target
                                     # to call the FINAL waypoint "arrived".
                                     # This is goal precision -- downstream
                                     # nodes (vision, gripper) act on the
                                     # final waypoint specifically.
INTERMEDIATE_TOLERANCE_DEG = 3.0    # looser tolerance for non-final kept
                                     # waypoints -- these only need to be
                                     # "close enough to safely start the
                                     # next segment," not goal precision.
                                     # Tighten if intermediate waypoints
                                     # ever matter downstream (they don't
                                     # currently -- only vision/gripper
                                     # timing off the FINAL waypoint does).

ARRIVAL_TIME_MARGIN = 2.0      # multiplier applied to the kinematic estimate
                                # to get the actual timeout. NOT a physical
                                # constant -- see CHANGES (2026-07-31) above.
                                # Tune from logged (estimated, actual) pairs
                                # once enough real runs exist.
ARRIVAL_TIME_FLOOR_SEC = 2.0   # minimum timeout regardless of estimate, so a
                                # near-zero-distance waypoint doesn't get an
                                # unreasonably tight timeout from rounding.
ARRIVAL_TIME_CEILING_SEC = 120.0  # upper bound so a pathological estimate
                                    # (e.g. bad joint-limit data, or no real
                                    # state seen yet) can't wait forever.
                                    # This was the old flat timeout; now a
                                    # backstop rather than the default.
ARRIVAL_POLL_SEC = 0.02

# Per-axis (max_velocity rad/s, max_acceleration rad/s^2) at scaling=1.0,
# from kuka_agilus_support/config/kr6_r900_2_joint_limits.yaml. If you
# retarget this node to a different robot model, update this table --
# nothing here reads the yaml file directly.
JOINT_LIMITS_RAD = {
    1: (6.283185307179586, 22.79306584548506),
    2: (5.235987755982989, 6.620770071453642),
    3: (6.283185307179586, 24.422794286227496),
    4: (7.853981633974483, 122.63859993489172),
    5: (7.853981633974483, 118.98874683077257),
    6: (9.42477796076938, 237.15063943642176),
}


def estimate_arrival_time_sec(current_deg, target_deg, vel_scale):
    """Per-axis trapezoidal (or triangular, for short moves) velocity-profile
    time estimate, in seconds. Returns the MAX across the 6 axes, since KRL's
    PTP synchronizes all axes to arrive together (it scales the faster axes
    down to match whichever axis takes longest) -- the move as a whole can't
    finish before its slowest axis would, moving alone at the same scaling.

    ACCEL_SCALING_TODO: assumes max_acceleration scales by vel_scale the same
    way max_velocity does. Not confirmed against KSS documentation -- see
    module docstring. If logged actual arrivals run systematically later
    than this estimate at low vel_scale, try removing the vel_scale factor
    from amax_scaled first.
    """
    worst = 0.0
    for i in range(6):
        d = math.radians(abs(target_deg[i] - current_deg[i]))
        if d < 1e-6:
            continue
        vmax_full, amax_full = JOINT_LIMITS_RAD[i + 1]
        vmax = vmax_full * vel_scale
        amax_scaled = amax_full * vel_scale  # ACCEL_SCALING_TODO -- see above
        if vmax <= 0.0 or amax_scaled <= 0.0:
            continue
        t_accel = vmax / amax_scaled
        d_accel = vmax ** 2 / (2 * amax_scaled)
        if d >= 2 * d_accel:
            t = 2 * t_accel + (d - 2 * d_accel) / vmax
        else:
            t = 2 * math.sqrt(d / amax_scaled)
        worst = max(worst, t)
    return worst


def build_gripper_packet(state: int) -> bytes:
    """Type=0 -> no motion in the KRL switch, but $OUT[1] still gets set from Gripper."""
    return (
        b'<RobotCommand>'
        b'<Type>0</Type>'
        b'<Axis A1="0" A2="0" A3="0" A4="0" A5="0" A6="0"/>'
        b'<Cart X="0" Y="0" Z="0" A="0" B="0" C="0"/>'
        b'<Velocity>0.2</Velocity>'
        b'<Gripper>' + str(state).encode() + b'</Gripper>'
        b'</RobotCommand>'
    )


class KukaEkiControllerNode(Node):
    def __init__(self):
        super().__init__('kuka_eki_controller_node')

        self.get_logger().info(f"Connecting to KUKA at {KUKA_IP} (motion + state)...")
        self.motion_client = EkiMotionClient(KUKA_IP)
        self.motion_client.connect()
        self._eki_lock = threading.Lock()  # motion socket also carries gripper packets

        self.state_client = EkiStateClient(KUKA_IP)
        self.state_client.connect()
        self.get_logger().info("--- EKI CONTROLLER CONNECTED (motion + state) ---")

        # ---- Real joint state feedback ----
        # state_client.state() blocks on recv() -- it's paced by whatever
        # cycle the KRC4's state channel actually pushes on, not something to
        # poll on a ROS timer (a blocking recv() inside a timer callback is a
        # bad pattern regardless of executor threading). Runs as its own loop.
        self._joint_state_pub = self.create_publisher(JointState, JOINT_STATE_TOPIC, 10)

        # ---- Commanded joint-target feedback (dataset recording) ----
        # See CHANGES (2026-08-03) above -- STEP signal, not a continuous
        # per-cycle command stream. Published once per dispatched kept
        # waypoint, after a successful ptp() send.
        self._commanded_pub = self.create_publisher(JointState, COMMANDED_JOINT_TOPIC, 10)

        # Latest REAL joint angles in degrees, as reported by the KRC4 state
        # socket -- NOT the planned/commanded angles. _execute_trajectory
        # polls this to confirm physical arrival instead of trusting planned
        # segment timing. Written only by _state_loop, read only through
        # _get_latest_positions_deg().
        self._latest_state_lock = threading.Lock()
        self._latest_positions_deg = None

        self._state_thread = threading.Thread(target=self._state_loop, daemon=True)
        self._state_thread.start()

        # ---- Motion: FollowJointTrajectory action server (the "controller") ----
        self._cb_group = ReentrantCallbackGroup()
        self._preempted = False
        self._action_server = ActionServer(
            self,
            FollowJointTrajectory,
            ACTION_NAME,
            execute_callback=self._execute_trajectory,
            goal_callback=self._handle_goal,
            cancel_callback=self._handle_cancel,
            callback_group=self._cb_group,
        )
        self.get_logger().info(f"FollowJointTrajectory action server up on '{ACTION_NAME}'")

        # ---- Gripper ----
        self._gripper_state = 0
        self._gripper_lock = threading.Lock()
        self.create_subscription(Int8, GRIPPER_CMD_TOPIC, self._gripper_cmd_callback, 10)
        self.get_logger().info(f"Listening on {GRIPPER_CMD_TOPIC} for gripper commands ...")

        self._kb_thread = threading.Thread(target=self._keyboard_loop, daemon=True)
        self._kb_thread.start()
        self.get_logger().info("Gripper ready — SPACE to toggle manually, or via /gripper_cmd")

    # ── Real state feedback ──────────────────────────────────────────────────

    def _state_loop(self):
        while rclpy.ok():
            try:
                state = self.state_client.state()  # blocks until the KRC4 sends one
            except Exception as e:
                self.get_logger().warn(f"State read failed: {e}", throttle_duration_sec=2.0)
                time.sleep(0.5)  # avoid a hot loop if the socket is down
                continue

            # RobotState.from_xml (kuka_eki/krl.py) passes raw XML attribute
            # strings into Axis's constructor without casting -- Axis.a1..a6
            # are typed float but arrive as str at runtime (dataclasses don't
            # enforce their type hints). Cast explicitly here rather than
            # patching their library.
            try:
                axis = state.axis
                angles_deg = [float(getattr(axis, f'a{i}')) for i in range(1, 7)]
            except (AttributeError, ValueError) as e:
                self.get_logger().error(
                    f"RobotState field mismatch, update _state_loop: {e}", throttle_duration_sec=5.0)
                continue

            with self._latest_state_lock:
                self._latest_positions_deg = angles_deg

            positions_rad = [math.radians(a) for a in angles_deg]
            msg = JointState()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.name = JOINT_ORDER
            msg.position = positions_rad
            self._joint_state_pub.publish(msg)

    def _get_latest_positions_deg(self):
        with self._latest_state_lock:
            return None if self._latest_positions_deg is None else list(self._latest_positions_deg)

    def _publish_commanded_target(self, angles_deg):
        """Publish the joint-space target just dispatched to the KRC4 as a
        JointState on /commanded_joint_states. See CHANGES (2026-08-03) --
        call this only AFTER a successful ptp() send, never speculatively."""
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = JOINT_ORDER
        msg.position = [math.radians(a) for a in angles_deg]
        self._commanded_pub.publish(msg)

    def _wait_until_arrived(self, target_angles_deg,
                             tolerance_deg=ARRIVAL_TOLERANCE_DEG,
                             timeout_sec=None):
        """Block until the REAL robot (via the EKI state socket, not planned
        trajectory timing) is within tolerance_deg of target on every axis.
        Returns (status, elapsed_sec) where status is 'arrived', 'preempted'
        (client canceled), or 'timeout'.

        timeout_sec: caller-supplied adaptive timeout (see
        estimate_arrival_time_sec / _execute_trajectory). Falls back to
        ARRIVAL_TIME_CEILING_SEC if not given.

        MUST check self._preempted on every iteration -- without this, a
        cancel from the client (_handle_cancel sets _preempted) is silently
        ignored for the full timeout_sec, and the caller would then call
        goal_handle.abort() on a goal the client already gave up on."""
        if timeout_sec is None:
            timeout_sec = ARRIVAL_TIME_CEILING_SEC
        start = time.monotonic()
        deadline = start + timeout_sec
        while time.monotonic() < deadline:
            if self._preempted:
                return 'preempted', time.monotonic() - start
            current = self._get_latest_positions_deg()
            if current is not None:
                max_err = max(abs(c - t) for c, t in zip(current, target_angles_deg))
                if max_err <= tolerance_deg:
                    return 'arrived', time.monotonic() - start
            time.sleep(ARRIVAL_POLL_SEC)
        return 'timeout', time.monotonic() - start

    # ── Gripper ──────────────────────────────────────────────────────────────

    def _send_gripper(self, state: int, source: str = ''):
        try:
            with self._eki_lock:
                self.motion_client._tcp_client.sendall(build_gripper_packet(state))
            label = "ON  (pick)" if state else "OFF (place)"
            self.get_logger().info(f"Gripper {label}{f'  [{source}]' if source else ''}")
        except Exception as e:
            self.get_logger().error(f"Gripper send failed: {e}")

    def _set_gripper(self, state: int, source: str = ''):
        with self._gripper_lock:
            if self._gripper_state != state:
                self._gripper_state = state
                self._send_gripper(state, source)

    def _toggle_gripper(self):
        with self._gripper_lock:
            self._gripper_state ^= 1
            self._send_gripper(self._gripper_state, 'keyboard')

    def _gripper_cmd_callback(self, msg: Int8):
        state = int(msg.data)
        if state not in (0, 1):
            self.get_logger().warn(f"Invalid gripper_cmd value: {state} (expected 0 or 1)")
            return
        self._set_gripper(state, 'control_server')

    def _keyboard_loop(self):
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)
                if ch == ' ':
                    self._toggle_gripper()
                elif ch in ('q', 'Q', '\x03'):
                    break
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    # ── Trajectory execution (the actual "controller" behaviour) ────────────

    def _handle_goal(self, goal_request):
        if not goal_request.trajectory.points:
            self.get_logger().warn("Goal rejected: empty trajectory.")
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def _handle_cancel(self, goal_handle):
        self._preempted = True
        return CancelResponse.ACCEPT

    def _joint_index_map(self, joint_names):
        idx = {}
        for i, name in enumerate(joint_names):
            for axis_n, canonical in enumerate(JOINT_ORDER, start=1):
                if canonical in name:
                    idx[axis_n] = i
                    break
        return idx

    def _execute_trajectory(self, goal_handle):
        traj = goal_handle.request.trajectory
        idx = self._joint_index_map(traj.joint_names)
        if len(idx) != 6:
            self.get_logger().error(f"Could not map all 6 joints from {traj.joint_names}")
            goal_handle.abort()
            result = FollowJointTrajectory.Result()
            result.error_code = FollowJointTrajectory.Result.INVALID_JOINTS
            return result

        self._preempted = False
        points = traj.points
        self.get_logger().info(f"Trajectory has {len(points)} waypoints from the planner")

        # Thin: each ptp() below is a discrete exact-stop move on the KRC4,
        # so forwarding every finely-interpolated point causes a stop-start
        # stutter. Keep a point only if it's moved MIN_STEP_DEG from the last
        # one we're keeping -- except the last point, which is always kept
        # so the actual goal target is never dropped.
        kept = []
        last_kept_deg = None
        for i, point in enumerate(points):
            angles_deg = [math.degrees(point.positions[idx[a]]) for a in range(1, 7)]
            is_last = (i == len(points) - 1)
            if last_kept_deg is None or is_last:
                kept.append((i, point, angles_deg))
                last_kept_deg = angles_deg
                continue
            max_delta = max(abs(a - b) for a, b in zip(angles_deg, last_kept_deg))
            if max_delta >= MIN_STEP_DEG:
                kept.append((i, point, angles_deg))
                last_kept_deg = angles_deg

        self.get_logger().info(
            f"Executing {len(kept)}/{len(points)} waypoints after thinning "
            f"(MIN_STEP_DEG={MIN_STEP_DEG})")

        # Real position at the start of each segment, used to estimate that
        # segment's arrival time. Seeded from live state before the loop;
        # updated from live state again each iteration where available, so
        # this never silently reuses a stale commanded position.
        prev_angles_deg = self._get_latest_positions_deg()

        for k, (i, point, angles_deg) in enumerate(kept):
            if self._preempted:
                self.get_logger().info("Trajectory preempted.")
                goal_handle.canceled()
                return FollowJointTrajectory.Result()

            current_before = self._get_latest_positions_deg()
            if current_before is None:
                current_before = prev_angles_deg  # best available fallback

            target = Axis(
                a1=angles_deg[0], a2=angles_deg[1], a3=angles_deg[2],
                a4=angles_deg[3], a5=angles_deg[4], a6=angles_deg[5],
            )

            is_last = (k == len(kept) - 1)
            approx_flag = 0 if is_last else 1

            # NOTE: sent as a joint-space ptp() with approx_flag (1 for intermediate C_PTP blending, 0 for final exact target).
            try:
                with self._eki_lock:
                    self.motion_client.ptp(target, max_velocity_scaling=MAX_VELOCITY_SCALING, approx=approx_flag)
            except Exception as e:
                self.get_logger().error(f"Transmission failed at waypoint {i}: {e}")
                goal_handle.abort()
                result = FollowJointTrajectory.Result()
                result.error_code = FollowJointTrajectory.Result.PATH_TOLERANCE_VIOLATED
                return result

            # Only publish the commanded target once the send above actually succeeded.
            self._publish_commanded_target(angles_deg)

            tolerance = ARRIVAL_TOLERANCE_DEG if is_last else INTERMEDIATE_TOLERANCE_DEG

            # Intermediate waypoints use C_PTP continuous motion blending on KRC4 ($ADVANCE = 3).
            # For intermediate points, non-blocking check allows continuous fluid trajectory execution,
            # while the final waypoint blocks until verified exact arrival.
            if not is_last:
                # Brief check to ensure socket pipeline does not overflow while KRC4 processes buffer
                time.sleep(0.02)
                continue

            if current_before is not None:
                est = estimate_arrival_time_sec(current_before, angles_deg, MAX_VELOCITY_SCALING)
                adaptive_timeout = min(
                    ARRIVAL_TIME_CEILING_SEC,
                    max(ARRIVAL_TIME_FLOOR_SEC, est * ARRIVAL_TIME_MARGIN),
                )
            else:
                est = None
                adaptive_timeout = ARRIVAL_TIME_CEILING_SEC

            status, waited = self._wait_until_arrived(
                angles_deg, tolerance_deg=tolerance, timeout_sec=adaptive_timeout)

            # Logged regardless of outcome -- this is the data needed to
            # tune ARRIVAL_TIME_MARGIN and check the ACCEL_SCALING_TODO
            # assumption in estimate_arrival_time_sec(), instead of guessing.
            self.get_logger().info(
                f"Waypoint {i} ({'final' if is_last else 'intermediate'}, "
                f"tolerance={tolerance} deg): "
                f"estimated={('%.2f' % est) if est is not None else 'n/a'}s "
                f"margin={ARRIVAL_TIME_MARGIN} timeout={adaptive_timeout:.2f}s "
                f"actual={waited:.2f}s status={status}")

            if status == 'preempted':
                self.get_logger().info(
                    "Trajectory canceled by client while waiting for arrival "
                    "(likely MoveGroup's execution-duration watchdog, or an "
                    "explicit cancel -- see module docstring).")
                goal_handle.canceled()
                return FollowJointTrajectory.Result()
            if status == 'timeout':
                current = self._get_latest_positions_deg()
                self.get_logger().error(
                    f"Robot did not reach waypoint {i} "
                    f"({'final' if is_last else 'intermediate'}) within "
                    f"{adaptive_timeout:.2f}s (tolerance={tolerance} deg). "
                    f"target={['%.2f' % a for a in angles_deg]} "
                    f"last_seen={['%.2f' % a for a in current] if current else 'unknown'}. "
                    f"Aborting -- NOT safe for downstream (gripper/vision) to proceed.")
                goal_handle.abort()
                result = FollowJointTrajectory.Result()
                result.error_code = FollowJointTrajectory.Result.GOAL_TOLERANCE_VIOLATED
                return result
            # status == 'arrived' -> fall through to feedback and next segment

            prev_angles_deg = angles_deg

            fb = FollowJointTrajectory.Feedback()
            fb.desired = point
            goal_handle.publish_feedback(fb)

        goal_handle.succeed()
        result = FollowJointTrajectory.Result()
        result.error_code = FollowJointTrajectory.Result.SUCCESSFUL
        return result


def main(args=None):
    rclpy.init(args=args)
    node = KukaEkiControllerNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down controller.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
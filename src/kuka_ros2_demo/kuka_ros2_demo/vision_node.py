#!/usr/bin/env python3
"""
vision_node.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Trigger-based (NOT continuous-stream) object *detection* service, PLUS
a continuous low-rate image *publisher* on /camera/image_raw so other
nodes (e.g. episode_recorder.py) can consume the same physical camera
without opening a second cv2.VideoCapture on the same device index.

Why detection stays trigger-based, not livestreamed:
  This pipeline is designed to run on a Minisforum (no GPU). Continuous
  per-frame processing is fine for cheap HSV color thresholding, but the
  moment this gets swapped for a real trained detector (see TODO below),
  running that at video framerate on CPU-only hardware would be far too
  slow. Trigger-based (one frame, on demand, per voice command) stays
  cheap regardless of what runs inside detect_color(), so the swap to a
  real detector later doesn't require an architecture change -- only
  the internals of detect_color() change.

Why the image publisher was added:
  episode_recorder.py previously opened its own cv2.VideoCapture on the
  same camera index this node uses. Many UVC webcam drivers refuse a
  second simultaneous reader on one device, or silently starve one of
  the two consumers. Instead, this node now owns the single
  cv2.VideoCapture and publishes frames on /camera/image_raw at a fixed
  low rate; episode_recorder.py (and anything else that wants frames)
  subscribes to that topic instead of opening the device itself.

  Both the periodic publisher and the on-demand detection service read
  from the SAME cv2.VideoCapture object, so access is serialized with
  self._cap_lock to avoid the two paths racing on the device.

Exposes:
  /detect_object  (surgical_msgs/srv/DetectObject)
    request:  color_name (string)   e.g. "red", "blue", "yellow", "green"
    response: found (bool), x (float64, metres), y (float64, metres)
              -- in base_link frame, matching MoveIt/geometry_msgs convention.
              NOTE: internally this script works in millimetres (matching
              vision.py / the homography's native units) and converts to
              METRES only at the service response boundary. Keeping the
              ROS-facing contract in metres, consistent with every other
              node in this pipeline, is intentional -- this project has
              already been bitten once by a units mismatch (mm vs cm)
              that silently corrupted a calibration. Do not let internal
              mm-based math leak out of this boundary.

Publishes:
  /camera/image_raw  (sensor_msgs/Image, bgr8)
    Continuous frames at `publish_rate_hz` (default 10 Hz), straight
    from the same camera device this node already owns. Not undistorted
    -- consumers that need undistorted frames should apply
    CAMERA_MATRIX/DIST_COEFFS themselves, same as this node does
    internally before detection.

TODO (future upgrade path):
  Replace the body of detect_color() with a real object detector
  (.pt/.onnx model) call. Nothing else in this node, or in
  pick_place_coordinator.py, needs to change -- the service contract
  (color_name in, found/x/y out) stays the same regardless of what runs
  underneath. If the detector returns a class label instead of a color
  name, just adjust the request field's meaning accordingly.
"""

import threading
from collections import deque

import rclpy
from rclpy.node import Node

import numpy as np
import cv2

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

from surgical_msgs.srv import DetectObject

from kuka_ros2_demo.pick_place_constants import (
    WS_X_MIN, WS_X_MAX, WS_Y_MIN, WS_Y_MAX,
)


# --- Camera intrinsics (wrist camera, default_cam.yaml) ---
CAMERA_MATRIX = np.array([
    [865.3064988411312, 0.0,               257.05723081254752],
    [0.0,               861.37645533726345, 266.08102298248292],
    [0.0,               0.0,               1.0],
])
DIST_COEFFS = np.array([
    0.20180575610957421, -0.16658050726097001,
    0.005021470803111815, -0.022511455420610536, 0.0
])

# Default path -- override at launch with:
#   ros2 run kuka_ros2_demo vision_node --ros-args -p homography_path:=/some/other/path.npy
DEFAULT_HOMOGRAPHY_PATH = "/home/emil/kuka_ros2/src/kuka_ros2_demo/data/aruco_homography.npy"

CAMERA_DEVICE_INDEX = 2

# --- HSV color ranges -- same as vision.py, still needs tuning per lighting ---
COLOR_RANGES = {
    "red": [
        (np.array([0,   100, 80]),  np.array([10,  255, 255])),
        (np.array([170, 100, 80]),  np.array([179, 255, 255])),
    ],
    "yellow": [(np.array([20, 100, 80]), np.array([35, 255, 255]))],
    "green":  [(np.array([40, 80, 60]),  np.array([85, 255, 255]))],
    "blue":   [(np.array([95, 100, 60]), np.array([130, 255, 255]))],
}
MIN_CONTOUR_AREA_PX = 120   # Lowered from 200 -- a fully unoccluded 2x2cm cube
                            # at the observe-pose camera height/focal length
                            # works out to roughly 256px^2 (865px focal *
                            # 0.02m / 1.09m height, squared). A cube wedged
                            # against neighbours (touching cubes occlude each
                            # other in a top-down HSV+contour pipeline) can
                            # show far less than its full face -- 200px left
                            # almost no margin for that. Matches a value
                            # already validated once before via debug dumps;
                            # if false positives from noise start showing up
                            # at 120, check DEBUG_MASK_DIR dumps (below)
                            # before raising this back up blindly.
MAX_CONTOUR_AREA_PX = 20000

# Debug mask dumps -- same convention as updated_aruco.py's aruco_debug.png:
# written next to the homography file whenever a detection call comes back
# empty (or all-rejected), so you can open the actual thresholded mask and
# see real blob pixel counts instead of guessing at MIN_CONTOUR_AREA_PX.
DEBUG_MASK_ON_FAILURE = True
# commonly buffer several stale frames internally, so without this you can
# end up processing an image from a second or more ago (e.g. before the arm
# finished retracting to the parked observation pose).
BUFFER_FLUSH_FRAMES = 5

DEFAULT_PUBLISH_RATE_HZ = 10.0


class VisionNode(Node):
    def __init__(self):
        super().__init__('vision_node')

        self.declare_parameter('homography_path', DEFAULT_HOMOGRAPHY_PATH)
        homography_path = self.get_parameter('homography_path').value

        try:
            self.H = np.load(homography_path)
            self.get_logger().info(f"Loaded homography from {homography_path}")
        except FileNotFoundError:
            self.get_logger().error(
                f"Homography file not found at {homography_path}. "
                f"Run the calibration script first, or pass a different path via "
                f"--ros-args -p homography_path:=/your/path.npy"
            )
            raise

        # Debug mask dumps go next to the homography file -- same directory
        # updated_aruco.py already writes aruco_debug.png/preprocessed_debug.png
        # to, keeping all vision debug output in one place.
        import os
        self._debug_dir = os.path.dirname(os.path.abspath(homography_path))
        self._last_mask = None
        self._last_contour_areas = []

        self.cap = cv2.VideoCapture(CAMERA_DEVICE_INDEX, cv2.CAP_V4L2 if hasattr(cv2, 'CAP_V4L2') else cv2.CAP_ANY)
        if not self.cap.isOpened():
            self.get_logger().error(f"Could not open camera device index {CAMERA_DEVICE_INDEX}")
            raise RuntimeError("Camera open failed")

        # Set minimal V4L2 hardware driver buffer size to eliminate latency & stale frames
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Thread-safe RAM vector ring buffer (capped maxlen=2, <2 MB footprint)
        # Obsolete frame matrices pop automatically and get garbage-collected instantly
        self._frame_buffer = deque(maxlen=2)

        # Serializes access to self.cap
        self._cap_lock = threading.Lock()

        self.srv = self.create_service(DetectObject, 'detect_object', self._handle_request)

        # --- Continuous image publisher ---
        self.declare_parameter('publish_rate_hz', DEFAULT_PUBLISH_RATE_HZ)
        publish_rate = self.get_parameter('publish_rate_hz').value
        self.declare_parameter('camera_frame_id', 'camera_optical_frame')
        self._camera_frame_id = self.get_parameter('camera_frame_id').value

        self.bridge = CvBridge()
        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        self._publish_timer = self.create_timer(1.0 / publish_rate, self._publish_frame)

        self.get_logger().info(
            "vision_node ready -- serving /detect_object, "
            f"publishing /camera/image_raw at {publish_rate:.1f} Hz (RAM Ring Buffer maxlen=2)"
        )

    def _capture_fresh_frame(self):
        """Returns the most recent in-memory frame matrix from the RAM ring buffer."""
        with self._cap_lock:
            if self._frame_buffer:
                return self._frame_buffer[-1]
            ok, frame = self.cap.read()
        if not ok:
            return None
        return frame

    def _publish_frame(self):
        """Timer callback: capture 1 frame matrix directly into RAM ring buffer and publish."""
        with self._cap_lock:
            ok, frame = self.cap.read()
            if ok:
                self._frame_buffer.append(frame)
        if not ok:
            self.get_logger().warn(
                'Camera read failed during periodic publish -- skipping frame.',
                throttle_duration_sec=5.0,
            )
            return

        try:
            msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        except Exception as e:
            self.get_logger().warn(f'cv_bridge conversion failed: {e}', throttle_duration_sec=5.0)
            return

        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self._camera_frame_id
        self.image_pub.publish(msg)

    def _undistort(self, frame):
        h, w = frame.shape[:2]
        new_K, _ = cv2.getOptimalNewCameraMatrix(CAMERA_MATRIX, DIST_COEFFS, (w, h), 1, (w, h))
        return cv2.undistort(frame, CAMERA_MATRIX, DIST_COEFFS, None, new_K)

    def detect_color(self, hsv, color_name):
        """
        TODO: replace this method's body with a real object detector call
        when ready. Keep the same return contract: list of
        {"px":..., "py":..., "area":...} detections.
        """
        if color_name not in COLOR_RANGES:
            self._last_mask = None
            self._last_contour_areas = []
            return []

        ranges = COLOR_RANGES[color_name]
        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for lower, upper in ranges:
            mask |= cv2.inRange(hsv, lower, upper)

        kernel = np.ones((3, 3), np.uint8)   # was 5x5 -- large enough to erase
                                              # a thin occluded sliver entirely
                                              # before area filtering ever sees it
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < MIN_CONTOUR_AREA_PX or area > MAX_CONTOUR_AREA_PX:
                continue
            M = cv2.moments(cnt)
            if M["m00"] == 0:
                continue
            cx, cy = M["m10"] / M["m00"], M["m01"] / M["m00"]
            detections.append({"px": cx, "py": cy, "area": area})

        # Stashed (not part of the return contract -- detect_color() still
        # returns only the detections list, so a future real-detector swap-in
        # doesn't need to change) purely so _handle_request can dump it for
        # debugging on a failed/rejected call, per DEBUG_MASK_ON_FAILURE.
        self._last_mask = mask
        self._last_contour_areas = [cv2.contourArea(c) for c in contours]
        return detections

    def _dump_debug_mask(self, color_name, frame_bgr=None):
        if not DEBUG_MASK_ON_FAILURE or self._last_mask is None:
            return
        try:
            mask_path = f"{self._debug_dir}/vision_debug_mask_{color_name}.png"
            cv2.imwrite(mask_path, self._last_mask)
            areas = sorted(self._last_contour_areas, reverse=True)
            msg = (
                f"  Debug mask written to {mask_path} -- contour areas found: "
                f"{[round(a) for a in areas[:5]]}"
                f"{' (+more)' if len(areas) > 5 else ''} "
                f"(MIN_CONTOUR_AREA_PX={MIN_CONTOUR_AREA_PX})"
            )
            if frame_bgr is not None:
                # Save the LITERAL undistorted frame this call processed --
                # not a mask derived from it -- so `python3 vision.py
                # <this file>` reproduces exactly what the live node saw.
                # Comparing against a frame captured at a different moment
                # (different lighting/pose/cube arrangement) isn't a valid
                # apples-to-apples test of whether the code or the capture
                # is at fault.
                frame_path = f"{self._debug_dir}/vision_debug_frame_{color_name}.png"
                cv2.imwrite(frame_path, frame_bgr)
                msg += f"\n  Exact input frame written to {frame_path} -- run " \
                       f"`python3 vision.py {frame_path}` to compare directly."
            self.get_logger().info(msg)
        except Exception as e:
            self.get_logger().warn(f"Failed to write debug mask/frame: {e}")

    def _pixel_to_world_mm(self, px, py):
        p = np.array([px, py, 1.0])
        proj = self.H @ p
        world = proj[:2] / proj[2]
        return world[0], world[1]

    def _handle_request(self, request, response):
        color_name = request.color_name.strip().lower()
        self.get_logger().info(f"Detection request: color='{color_name}'")

        frame = self._capture_fresh_frame()
        if frame is None:
            self.get_logger().error("Frame capture failed")
            response.found = False
            return response

        undistorted = self._undistort(frame)
        hsv = cv2.cvtColor(undistorted, cv2.COLOR_BGR2HSV)

        detections = self.detect_color(hsv, color_name)
        if not detections:
            self.get_logger().warn(f"No '{color_name}' object detected")
            self._dump_debug_mask(color_name, undistorted)
            response.found = False
            return response

        # Resolve every candidate to world coords BEFORE picking "best by
        # area", and drop anything outside the real pick workspace. Without
        # this, a large false-positive blob near the robot's own base (e.g.
        # KUKA orange occasionally reading as "red" under some lighting) can
        # simply outmass the real object and win every single call, since it
        # sits at a fixed, always-large apparent size right under the wrist
        # camera. Using WS_X_MIN/MAX/WS_Y_MIN/MAX here is the same source of
        # truth control_server already rejects out-of-bounds picks against --
        # this just moves the rejection upstream, before a task is even
        # dispatched, instead of after a wasted park->detect->dispatch->fail
        # cycle.
        in_bounds = []
        rejected = 0
        for d in detections:
            x_mm, y_mm = self._pixel_to_world_mm(d["px"], d["py"])
            x_m, y_m = x_mm / 1000.0, y_mm / 1000.0
            if WS_X_MIN <= x_m <= WS_X_MAX and WS_Y_MIN <= y_m <= WS_Y_MAX:
                in_bounds.append({**d, "x_m": x_m, "y_m": y_m})
            else:
                rejected += 1

        if not in_bounds:
            if rejected:
                rejected_coords = [
                    (round(self._pixel_to_world_mm(d["px"], d["py"])[0] / 1000.0, 4),
                     round(self._pixel_to_world_mm(d["px"], d["py"])[1] / 1000.0, 4),
                     round(d["area"]))
                    for d in detections
                ]
                self.get_logger().warn(
                    f"'{color_name}': {rejected} detection(s) found but all fell "
                    f"outside the workspace bounds (likely a false positive near "
                    f"the robot base) -- treating as not found. "
                    f"Rejected candidates (x_m, y_m, area_px): {rejected_coords}")
            else:
                self.get_logger().warn(f"No '{color_name}' object detected")
            self._dump_debug_mask(color_name, undistorted)
            response.found = False
            return response

        best = max(in_bounds, key=lambda d: d["area"])

        # Convert at the boundary only -- everything ROS-facing is metres.
        response.found = True
        response.x = best["x_m"]
        response.y = best["y_m"]

        self.get_logger().info(
            f"Found '{color_name}' -> pixel=({best['px']:.1f},{best['py']:.1f})  "
            f"x={response.x:.4f}m  y={response.y:.4f}m  area={best['area']:.0f}px"
        )
        return response

    def destroy_node(self):
        if self.cap is not None:
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = VisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

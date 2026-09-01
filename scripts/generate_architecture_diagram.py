import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

WORKSPACE_ROOT = r"d:\~Ideas n Innovation\~~Taiwan\AU\11_Task_Robotic\kuka_ros2"

def draw_architecture_diagram(output_path):
    fig, ax = plt.subplots(figsize=(16, 11), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Color Palette (Publication Grade)
    c_bg_sub = '#F8FAFC'
    c_input = '#EBF5FB'
    c_input_b = '#2980B9'
    c_ros = '#E8F8F5'
    c_ros_b = '#16A085'
    c_plan = '#FEF9E7'
    c_plan_b = '#F39C12'
    c_bridge = '#F4ECF7'
    c_bridge_b = '#8E44AD'
    c_hw = '#FDEDEC'
    c_hw_b = '#C0392B'
    c_bench = '#EAEDED'
    c_bench_b = '#7F8C8D'

    # Helper: Rounded Box
    def draw_box(x, y, w, h, bg_col, b_col, title, subtitle="", fontsize_title=10, fontsize_sub=8, bold_title=True):
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.5,rounding_size=1.2",
            facecolor=bg_col, edgecolor=b_col, linewidth=1.8, zorder=2
        )
        ax.add_patch(rect)
        if subtitle:
            ax.text(x + w/2, y + h*0.62, title, ha='center', va='center', fontsize=fontsize_title, fontweight='bold' if bold_title else 'normal', color='#1A252C', zorder=3)
            ax.text(x + w/2, y + h*0.32, subtitle, ha='center', va='center', fontsize=fontsize_sub, color='#4A5568', zorder=3)
        else:
            ax.text(x + w/2, y + h*0.50, title, ha='center', va='center', fontsize=fontsize_title, fontweight='bold' if bold_title else 'normal', color='#1A252C', zorder=3)

    # Helper: Subgraph Group Box
    def draw_group(x, y, w, h, title, b_col='#CBD5E1'):
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.8,rounding_size=1.8",
            facecolor=c_bg_sub, edgecolor=b_col, linewidth=1.2, linestyle='--', zorder=1
        )
        ax.add_patch(rect)
        ax.text(x + 2, y + h - 2.8, title, ha='left', va='center', fontsize=11, fontweight='bold', color='#2D3748', zorder=3)

    # Helper: Arrow
    def draw_arrow(x1, y1, x2, y2, label="", color='#4B5563', style='->', lw=1.5, rad=0.0, label_pos=(0.5, 0.5), label_offset=(0, 1.2), fontsize=7.5, dashed=False):
        connectionstyle = f"arc3,rad={rad}" if rad != 0.0 else "arc3"
        arrow = patches.FancyArrowPatch(
            (x1, y1), (x2, y2),
            arrowstyle=style, connectionstyle=connectionstyle,
            color=color, linewidth=lw, linestyle='--' if dashed else '-',
            mutation_scale=14, zorder=4
        )
        ax.add_patch(arrow)
        if label:
            mid_x = x1 + (x2 - x1) * label_pos[0] + label_offset[0]
            mid_y = y1 + (y2 - y1) * label_pos[1] + label_offset[1]
            ax.text(mid_x, mid_y, label, ha='center', va='center', fontsize=fontsize, color=color,
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#E2E8F0', linewidth=0.8, alpha=0.92), zorder=5)

    # Title Header
    ax.text(50, 97.5, "KUKA ROS 2 MULTIMODAL SYSTEM ARCHITECTURE & COMMUNICATION PIPELINE",
            ha='center', va='center', fontsize=14, fontweight='bold', color='#1B365D')
    ax.text(50, 95.2, "Deterministic Voice-and-Vision Framework with MoveIt 2 Pilz Planner over Ethernet KRL (EKI Port 54600)",
            ha='center', va='center', fontsize=9.5, fontstyle='italic', color='#4A5568')

    # 1. LAYER 1: MULTIMODAL PERCEPTION (TOP LEFT)
    draw_group(3, 67, 30, 26, "1. Multimodal Perception Layer")
    draw_box(5, 80, 12, 8, c_input, c_input_b, "Microphone", "16 kHz Mono Audio", 9, 7.5)
    draw_box(19, 80, 12, 8, c_ros, c_ros_b, "voice_ai_node", "Vosk ASR + Alias Map", 9, 7.5)
    draw_arrow(17, 84, 19, 84, "Audio Stream", c_input_b)

    draw_box(5, 69.5, 12, 8, c_input, c_input_b, "RGB Camera", "Workspace Overhead", 9, 7.5)
    draw_box(19, 69.5, 12, 8, c_ros, c_ros_b, "vision_node", "12-ArUco Homography H\n+ HSV Color Segment", 8.5, 7)
    draw_arrow(17, 73.5, 19, 73.5, "Live Frame", c_input_b)

    # 2. LAYER 2: ORCHESTRATION & AUTOMATED BENCHMARKING (TOP RIGHT)
    draw_group(36, 67, 61, 26, "2. Task Orchestration & Automated Benchmarking")
    draw_box(38, 79.5, 23, 9.5, c_ros, c_ros_b, "pick_place_coordinator", "State Machine & Re-grasp Recovery", 9.5, 8)
    draw_arrow(31, 84, 38, 84, "Topic: /voice_command ('red', 'yellow')", c_ros_b)
    draw_arrow(31, 73.5, 38, 81, "Srv: /detect_object -> Point(X,Y,Z)", c_ros_b, rad=0.15)

    draw_box(65, 79.5, 20, 9.5, c_bench, c_bench_b, "auto_benchmark_runner", "Auto Test Orchestrator\n(Bounds Safety Check)", 9, 7.5)
    draw_box(65, 69, 13, 8.5, c_bench, c_bench_b, "benchmark_logger", "Passive Telemetry\n(/task_status, /joint_states)", 8.5, 7)
    draw_box(81, 69, 14, 8.5, c_bench, c_bench_b, "benchmark_results.csv", "Dummy_Changer Engine\n(Metrics Aggregation)", 8.5, 7)

    draw_arrow(65, 84.5, 61, 84.5, "Trigger Task", c_bench_b, dashed=True)
    draw_arrow(71.5, 79.5, 71.5, 77.5, "/benchmark_start /end", c_bench_b, dashed=True)
    draw_arrow(78, 73.2, 81, 73.2, "Log CSV", c_bench_b)

    # 3. LAYER 3: MOTION PLANNING (MIDDLE)
    draw_group(3, 36, 94, 28, "3. Motion Planning & Collision Management Layer")
    draw_box(6, 45, 24, 12, c_plan, c_plan_b, "control_server", "Task Sequence & Trajectory Dispatch\n- Pick: LIN descent + 500ms Vacuum Dwell\n- Place: PTP transit + 400ms Venting Dwell", 9.5, 7.5)
    draw_arrow(49.5, 79.5, 22, 57, "Service: /execute_task (TaskPickPlace.srv)", c_plan_b, rad=-0.12)

    draw_box(36, 45, 28, 12, c_plan, c_plan_b, "MoveIt 2 Motion Planning Core", "Pilz Industrial Motion Planner (LIN / PTP)\n- TCP Offset Compensation: Z_offset = 76 mm\n- Orientation Constraint: Tool pointing down", 9.5, 7.5)
    draw_arrow(30, 51, 36, 51, "Action: /move_action\n(MotionPlanRequest)", c_plan_b)

    draw_box(70, 45, 24, 12, c_plan, c_plan_b, "Planning Scene Monitor", "Dynamic Obstacle & Table Geometry\n(ApplyPlanningScene.srv)", 9, 7.5)
    draw_arrow(30, 47, 70, 47, "Srv: /apply_planning_scene", c_plan_b, rad=-0.2)

    draw_box(6, 38, 24, 5.5, c_bridge, c_bridge_b, "gripper_bridge", "Subscribes /gripper_cmd (1=ON, 0=OFF)", 8.5, 0)
    draw_arrow(18, 45, 18, 43.5, "/gripper_cmd", c_plan_b)

    # 4. LAYER 4: NETWORK BRIDGE (LOWER MIDDLE)
    draw_group(3, 20, 94, 14, "4. ROS 2 - KUKA EKI Communication Bridge Layer")
    draw_box(20, 22.5, 60, 9, c_bridge, c_bridge_b, "kuka_eki_bridge (TCP/IP Gigabit Socket Link)", "Port 54600 | IP: 192.168.1.147 | Protocol: Ethernet KRL XML Telegrams\n<RobotCommand><Type>0/1</Type><Cart X,Y,Z/><Gripper>1/0</Gripper></RobotCommand>", 9.5, 8)
    draw_arrow(50, 45, 50, 31.5, "Trajectory Display & Waypoints", c_bridge_b)
    draw_arrow(18, 38, 25, 31.5, "Gripper Packet Injection", c_bridge_b)

    # 5. LAYER 5: PHYSICAL HARDWARE (BOTTOM)
    draw_group(3, 2, 94, 16, "5. Industrial Hardware & Execution Layer")
    draw_box(6, 4.5, 26, 11, c_hw, c_hw_b, "KUKA KRC4 Controller", "KSS 8.3 | KRL Daemon: ros_eki.src\nCyclic 20 Hz State Feedback", 9.5, 8)
    draw_box(37, 4.5, 28, 11, c_hw, c_hw_b, "KUKA KR6 R900-2 (Agilus)", "6-DOF Rigid Industrial Manipulator\nPayload: 6 kg | Reach: 901 mm | Rep: ±0.03 mm", 9.5, 8)
    draw_box(70, 4.5, 24, 11, c_hw, c_hw_b, "Vacuum Gripper End-Effector", "Actuated via KUKA $OUT[1]\nr_cup = 8 mm | Suction + Venting Solenoid", 9.5, 7.5)

    draw_arrow(50, 22.5, 19, 15.5, "TCP/IP Socket Packet Transmission", c_hw_b)
    draw_arrow(32, 10, 37, 10, "Motor Drive Signals", c_hw_b)
    draw_arrow(32, 7, 70, 7, "Digital Output $OUT[1]", c_hw_b, rad=-0.15)
    draw_arrow(19, 15.5, 71.5, 69, "Telemetry: $AXIS_ACT / $POS_ACT -> /joint_states", c_hw_b, dashed=True, rad=0.45)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Successfully generated high-res system architecture diagram at: {output_path}")

if __name__ == "__main__":
    out = os.path.join(WORKSPACE_ROOT, "images", "system_architecture_diagram.png")
    draw_architecture_diagram(out)

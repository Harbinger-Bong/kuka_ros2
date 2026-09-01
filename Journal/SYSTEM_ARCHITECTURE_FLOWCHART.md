# 🤖 KUKA KR6 ROS 2 System Architecture & Communication Pipeline

Dokumen ini memuat diagram alur (*flowchart*), diagram arsitektur sistem, dan pemetaan komunikasi ROS 2 untuk sistem penanganan material berbasis suara dan visi pada robot industri **KUKA KR6 R900-2 (Agilus)** dengan pengontrol **KUKA KRC4**.

---

## 📊 1. Interactive Mermaid Flowchart (Strict Syntax Verified)

```mermaid
flowchart TD
    %% Styling Classes
    classDef inputStyle fill:#EBF5FB,stroke:#2980B9,stroke-width:2px,color:#1B4F72;
    classDef rosNode fill:#E8F8F5,stroke:#16A085,stroke-width:2px,color:#0E6251;
    classDef controlNode fill:#FEF9E7,stroke:#F39C12,stroke-width:2px,color:#7D6608;
    classDef bridgeNode fill:#F4ECF7,stroke:#8E44AD,stroke-width:2px,color:#512E5F;
    classDef kukaHW fill:#FDEDEC,stroke:#C0392B,stroke-width:2px,color:#78281F;
    classDef logNode fill:#EAEDED,stroke:#7F8C8D,stroke-width:2px,color:#2C3E50;

    subgraph Perception_Layer ["1. Multimodal Perception & Human Input"]
        MIC["🎤 Microphone (16 kHz)"] -->|"Audio Stream (PCM 16kHz)"| VOSK["voice_ai_node<br/>(Vosk Offline ASR + Alias Map)"]
        CAM["📷 Overhead RGB Camera"] -->|"Live Frame Stream"| VISION["vision_node<br/>(HSV + 12-ArUco Homography H)"]
    end

    subgraph Orchestration_Layer ["2. Orchestration & Automated Benchmarking"]
        VOSK -->|"Topic: /voice_command<br/>('red', 'yellow', 'blue')"| COORD["pick_place_coordinator<br/>(Task State Machine & Recovery)"]
        VISION <-->|"Service: /detect_object<br/>Returns Point XYZ in base_link"| COORD
        RUNNER["auto_benchmark_runner.py<br/>(Auto Test Orchestrator)"] -.->|"Trigger /voice_command"| COORD
        RUNNER -.->|"Topic: /benchmark_run_start"| LOGGER["benchmark_logger.py<br/>(Passive CSV Telemetry Logger)"]
        RUNNER -.->|"Topic: /benchmark_run_end"| LOGGER
        LOGGER -->|"Append Metrics"| CSV[("benchmark_results.csv<br/>& Dummy_Changer")]
    end

    subgraph Planning_Layer ["3. Motion Planning & Collision Management"]
        COORD -->|"Service: /execute_task<br/>(Pick & Place Request)"| CTRL["control_server<br/>(Task Sequence Controller)"]
        CTRL <-->|"Action: /move_action"| MOVEIT["MoveIt 2 Core<br/>(Pilz Industrial Planner: LIN / PTP)"]
        CTRL -->|"Service: /apply_planning_scene"| SCENE["Planning Scene<br/>(Dynamic Collision Objects)"]
        CTRL -->|"Topic: /gripper_cmd<br/>(1=ON / 0=OFF)"| GRP_BRDG["gripper_bridge / kuka_eki_bridge"]
    end

    subgraph Bridge_Layer ["4. ROS 2 - KUKA EKI Communication Bridge"]
        MOVEIT -->|"Trajectory: /display_planned_path"| GRP_BRDG
        GRP_BRDG -->|"XML Packet Serialization<br/>Port 54600 (Gigabit TCP/IP)"| SOCKET["TCP/IP Socket Link<br/>(kuka_eki_bridge)"]
    end

    subgraph Hardware_Layer ["5. Industrial Hardware & Execution Layer"]
        SOCKET <-->|"Bi-directional XML Telegrams<br/>(Cyclic 20 Hz)"| KRC4["KUKA KRC4 Controller<br/>(ros_eki.src KRL Daemon)"]
        KRC4 -->|"6-Axis Joint Drive Signals"| KR6["KUKA KR6 R900-2 Manipulator<br/>(6-DOF Agilus Arm)" ]
        KRC4 -->|"Digital Output: OUT1"| VAC["Vacuum Gripper End-Effector<br/>(T_buildup=500ms, T_vent=400ms)"]
        KRC4 -.->|"Actual Telemetry: AXIS_ACT / POS_ACT"| SOCKET
    end

    SOCKET -.->|"Topic: /joint_states & /task_status"| LOGGER

    class MIC,CAM inputStyle;
    class VOSK,VISION,COORD rosNode;
    class CTRL,MOVEIT,SCENE controlNode;
    class GRP_BRDG,SOCKET bridgeNode;
    class KRC4,KR6,VAC kukaHW;
    class RUNNER,LOGGER,CSV logNode;
```

---

## 🖼️ 2. High-Resolution Architecture Diagram (Publication Ready)

Diagram versi gambar beresolusi tinggi (300 DPI) telah disimpan di:
`images/system_architecture_diagram.png`

![System Architecture Diagram](../images/system_architecture_diagram.png)

---

## 📡 3. Rincian Antarmuka Komunikasi ROS 2 (Topics, Services, & Actions)

| Tipe | Nama Interface | Tipe Pesan | Deskripsi Fungsi |
| :--- | :--- | :--- | :--- |
| **Topic (Pub/Sub)** | `/voice_command` | `std_msgs/msg/String` | Pengiriman intent warna target (`red`, `yellow`, `blue`, `green`) hasil decoding Vosk ASR. |
| **Service** | `/detect_object` | `surgical_msgs/srv/DetectObject` | Pemanggilan estimasi koordinat dunia $(X, Y, Z)$ berbasis segmentasi HSV & homografi ArUco. |
| **Service** | `/execute_task` | `surgical_msgs/srv/TaskPickPlace` | Perintah sekuens eksekusi pick-and-place dari koordinator ke `control_server`. |
| **Action** | `/move_action` | `moveit_msgs/action/MoveGroup` | Perencanaan trajektori deterministik (LIN / PTP) MoveIt 2 Pilz Industrial Motion Planner. |
| **Service** | `/apply_planning_scene` | `moveit_msgs/srv/ApplyPlanningScene` | Pembaruan geometri meja dan rintangan collision secara dinamis di MoveIt 2. |
| **Topic (Pub/Sub)** | `/gripper_cmd` | `std_msgs/msg/Int8` | Perintah katup pneumatik pompa vakum (`1 = ON / Pick`, `0 = OFF / Place`). |
| **Topic (Pub/Sub)** | `/joint_states` | `sensor_msgs/msg/JointState` | Umpan balik telemetri posisi sendi aktual ($A1..A6$) dari KRC4 ($AXIS\_ACT$) pada frekuensi 20 Hz. |
| **Topic (Pub/Sub)** | `/benchmark_run_start` | `std_msgs/msg/String` | Metadata awal pengujian benchmark otomatis (`test`, `run`, `color`). |
| **Topic (Pub/Sub)** | `/benchmark_run_end` | `std_msgs/msg/String` | Ringkasan metrik pengujian fisik (`pos_error_mm`, `tracking_error_deg`, `pick_success`). |

---

## ⚙️ 4. Spesifikasi Parameter Teknis Sistem

*   **Manipulator**: KUKA KR6 R900-2 sixx Agilus (6-DOF, Payload 6 kg, Reach 901 mm, Repeatability $\pm 0.03\text{ mm}$).
*   **Controller**: KUKA KRC4 Compact running KUKA System Software (KSS) 8.3.
*   **Ethernet Protocol**: KUKA Ethernet KRL Interface (EKI), Port `54600`, IP Robot `192.168.1.147`.
*   **End-Effector**: Custom Vacuum Gripper dengan Tool Center Point (TCP) offset $Z_{\text{offset}} = 76\text{ mm}$ ($L_{\text{base}} = 60\text{ mm} + L_{\text{bellows}} = 16\text{ mm}$), radius *suction cup* $r = 8\text{ mm}$.
*   **Pneumatic Dwells**: *Vacuum buildup dwell* $T_{\text{vacuum}} = 500\text{ ms}$, *Venting release dwell* $T_{\text{release}} = 400\text{ ms}$.
*   **Kamera & Kalibrasi**: Kamera overhead pada pose observasi $(X=338.56\text{ mm}, Y=10.12\text{ mm}, Z=1091.51\text{ mm})$, 12 penanda ArUco resolusi sub-milimeter.
*   **Speech Recognition Engine**: Vosk offline ASR (`vosk-model-small-en-us`) dengan kamus alias fonetik pada frekuensi sampling 16 kHz.

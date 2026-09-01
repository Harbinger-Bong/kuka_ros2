#!/usr/bin/env python3
"""
vision_detect_node.py

Real object-detection service node for the KUKA surgical/hardware pick-and-place
demo, following the same split you described:

    YOLO (Ultralytics YOLO11-seg, best.pt)  -> WHAT the object is
    ArUco-derived homography (aruco_homography.npy) -> WHERE it is (robot base frame)

Exposes /detect_object as a ROS2 service, on-demand (inference only runs when a
request comes in), matching the pattern of the existing color-based
vision_node.py rather than the continuous webcam loop of the original scripts.

--------------------------------------------------------------------------
Uses a dedicated surgical_msgs/srv/DetectObjectYolo.srv (separate from the
existing DetectObject.srv, which stays untouched for the color-detection
path in vision_node.py):

    string target_class       # optional filter, "" = accept best hit
    ---
    bool found
    float64 x                 # metres, robot base frame (table plane)
    float64 y                 # metres, robot base frame (table plane)
    string object_class
    float32 confidence

Exposed on /detect_object_yolo, not /detect_object, so this node can run
alongside vision_node.py without either one fighting over the service name.

No z is returned -- same convention as DetectObject.srv. Z comes from
pick_place_constants.PICK_Z_M when pick_place_coordinator.py builds the pick
pose for /execute_task.
--------------------------------------------------------------------------
"""

import os

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from ultralytics import YOLO

from ament_index_python.packages import get_package_share_directory

from surgical_msgs.srv import DetectObjectYolo

from kuka_ros2_demo.hardware_database import SCREW_DATABASE, CONFUSED_GROUP, PIXELS_PER_MM, NEVER_PICK_CLASSES


def detect_if_silver(roi_image):
    """Analyzes the color properties of the object to isolate silver items."""
    if roi_image is None or roi_image.size == 0:
        return False
    hsv = cv2.cvtColor(roi_image, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1].mean()
    value = hsv[:, :, 2].mean()
    return saturation < 45 and value > 100


def smart_hardware_resolver(yolo_class, auto_len, auto_dia, roi_frame):
    """Same disambiguation logic as the original scripts, now covering all
    10 real classes and guarded against a zero-diameter measurement."""
    measured_ratio = auto_len / auto_dia if auto_dia > 0 else 0.0
    is_silver_detected = detect_if_silver(roi_frame)

    match_scores = {}
    for name, specs in SCREW_DATABASE.items():
        len_err = abs(auto_len - specs["length_mm"]) / 3.0
        dia_err = abs(auto_dia - specs["diameter_mm"]) / 1.0
        spec_ratio = specs["length_mm"] / specs["diameter_mm"]
        rat_err = abs(measured_ratio - spec_ratio) / 0.4
        base_score = (0.60 * len_err) + (0.30 * rat_err) + (0.10 * dia_err)
        if specs["is_silver"] and not is_silver_detected:
            base_score += 2.0
        match_scores[name] = base_score

    sorted_candidates = sorted(match_scores.items(), key=lambda x: x[1])
    best_match, _ = sorted_candidates[0]

    if yolo_class in CONFUSED_GROUP or best_match in CONFUSED_GROUP:
        if best_match in ["screw_2in", "screw_1_3_4in"]:
            final_class = "screw_2in" if auto_len > 46.5 else "screw_1_3_4in"
            explanation = f"Disambiguated to {final_class} via length threshold ({auto_len:.1f}mm)."
        elif best_match in ["screw_3_16_1_2in", "screw_5_32_3_8in"]:
            final_class = "screw_5_32_3_8in" if auto_len < 13.5 else "screw_3_16_1_2in"
            explanation = f"Disambiguated to {final_class} via size boundary gate ({auto_len:.1f}mm)."
        else:
            final_class = best_match
            explanation = f"Verified matching hardware specs for {final_class}."
    else:
        final_class = yolo_class
        explanation = "High-confidence YOLO classification, no disambiguation needed."

    return {"final_class": final_class, "explanation": explanation}


class VisionDetectNode(Node):
    def __init__(self):
        super().__init__('vision_detect_node')

        self.declare_parameter('weights_path', '')
        self.declare_parameter('homography_path', '')
        self.declare_parameter('camera_index', 2)
        self.declare_parameter('conf_threshold', 0.25)

        weights_path = self.get_parameter('weights_path').get_parameter_value().string_value
        homography_path = self.get_parameter('homography_path').get_parameter_value().string_value
        self.camera_index = self.get_parameter('camera_index').get_parameter_value().integer_value
        self.conf_threshold = self.get_parameter('conf_threshold').get_parameter_value().double_value

        # Default to files living alongside aruco_homography.npy in the
        # package's data/ dir, same convention vision_node.py already uses.
        pkg_share = get_package_share_directory('kuka_ros2_demo')
        if not weights_path:
            weights_path = os.path.join(pkg_share, 'data', 'best_v2.pt')
        if not homography_path:
            homography_path = os.path.join(pkg_share, 'data', 'aruco_homography.npy')

        if not os.path.exists(weights_path):
            self.get_logger().error(f"YOLO weights not found at: {weights_path}")
            raise FileNotFoundError(weights_path)
        if not os.path.exists(homography_path):
            self.get_logger().error(f"Homography file not found at: {homography_path}")
            raise FileNotFoundError(homography_path)

        self.get_logger().info(f"Loading YOLO model from {weights_path} ...")
        self.model = YOLO(weights_path)
        self.get_logger().info(f"Model loaded. Classes: {list(self.model.names.values())}")

        self.homography = np.load(homography_path)
        self.get_logger().info(f"Loaded homography from {homography_path}")

        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2 if hasattr(cv2, 'CAP_V4L2') else cv2.CAP_ANY)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not self.cap.isOpened():
            self.get_logger().error(f"Could not open camera index {self.camera_index}")
            raise RuntimeError("Camera open failed")

        self.srv = self.create_service(DetectObjectYolo, '/detect_object_yolo', self.handle_detect_object)
        self.get_logger().info("vision_detect_node ready: /detect_object_yolo service active.")

    def pixel_to_world(self, u, v):
        """Apply the ArUco-derived homography to map a pixel centroid to
        robot-base-frame metres. Mirrors what vision_node.py does for the
        color-detection path."""
        pt = np.array([u, v, 1.0], dtype=np.float64)
        world = self.homography @ pt
        world = world / world[2]
        x_mm, y_mm = world[0], world[1]
        return x_mm / 1000.0, y_mm / 1000.0

    def handle_detect_object(self, request, response):
        target_class = request.target_class.strip() if request.target_class else ""

        ret, frame = self.cap.read()
        if not ret or frame is None:
            response.found = False
            return response

        results = self.model(frame, conf=self.conf_threshold, verbose=False)

        if len(results[0].boxes) == 0:
            self.get_logger().info(
                f'Raw YOLO output: 0 detections above conf={self.conf_threshold} '
                f'(requested target_class="{target_class}"). '
                f'Camera saw nothing above threshold -- check the tray is in frame '
                f'and the camera_index parameter points at the right device.')
            response.found = False
            return response

        boxes = results[0].boxes
        masks = results[0].masks
        confs = boxes.conf.cpu().numpy()
        order = np.argsort(-confs)  # highest confidence first, not "first box in results"

        raw_detections = [
            (self.model.names[int(boxes.cls[i])], float(boxes.conf[i])) for i in order
        ]
        self.get_logger().info(f'Raw YOLO output ({len(raw_detections)} boxes): {raw_detections}')

        chosen_idx = None
        for idx in order:
            cls_name = self.model.names[int(boxes.cls[idx])]
            # Hard exclusion: never let a NEVER_PICK_CLASSES detection (e.g.
            # the ArUco marker) be selected as the pick target, even on an
            # unfiltered request. This is enforced here, not just by
            # omission from SCREW_DATABASE, so it can't be bypassed by
            # accident.
            if cls_name in NEVER_PICK_CLASSES:
                continue
            if target_class and cls_name != target_class:
                continue
            chosen_idx = int(idx)
            break

        if chosen_idx is None:
            self.get_logger().info(
                f'{len(raw_detections)} object(s) detected, but none matched '
                f'requested target_class="{target_class}". Raw classes seen: '
                f'{[c for c, _ in raw_detections]}')
            response.found = False
            return response

        box = boxes[chosen_idx]
        yolo_class = self.model.names[int(box.cls[0])]
        confidence = float(box.conf[0])

        xyxy = box.xyxy[0].cpu().numpy().astype(int)
        h, w, _ = frame.shape
        x1, y1, x2, y2 = max(0, xyxy[0]), max(0, xyxy[1]), min(w, xyxy[2]), min(h, xyxy[3])
        roi = frame[y1:y2, x1:x2]

        # Use the segmentation mask -- not the axis-aligned box -- for the
        # centroid and for rotation-invariant length/diameter. This is the
        # fix for the earlier bbox-based measurement, which overestimated
        # both dimensions whenever a screw wasn't perfectly axis-aligned.
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        calculated_length = (x2 - x1) / PIXELS_PER_MM
        calculated_diameter = (y2 - y1) / PIXELS_PER_MM

        if masks is not None and chosen_idx < len(masks.data):
            mask = masks.data[chosen_idx].cpu().numpy().astype(np.uint8)
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
            ys, xs = np.where(mask > 0)
            if len(xs) > 10:
                cx, cy = float(xs.mean()), float(ys.mean())
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                largest = max(contours, key=cv2.contourArea)
                (_, (rw, rh), _) = cv2.minAreaRect(largest)
                calculated_length = max(rw, rh) / PIXELS_PER_MM
                calculated_diameter = min(rw, rh) / PIXELS_PER_MM

        decision = smart_hardware_resolver(yolo_class, calculated_length, calculated_diameter, roi)
        final_class = decision["final_class"]
        self.get_logger().info(
            f"YOLO said '{yolo_class}' (conf={confidence:.2f}) -> resolved '{final_class}'. "
            f"{decision['explanation']}"
        )

        # WHERE: ArUco homography, not YOLO, decides position. No z here --
        # pick_place_coordinator.py adds Z from pick_place_constants.PICK_Z_M
        # when it builds the pick pose, same as it already does for the
        # color-detection path.
        x_m, y_m = self.pixel_to_world(cx, cy)

        response.found = True
        response.object_class = final_class
        response.x = x_m
        response.y = y_m
        response.confidence = confidence
        return response

    def destroy_node(self):
        if self.cap is not None:
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = VisionDetectNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
# Damage detection module
# Damage detection module

from ultralytics import YOLO
import cv2
import time
import os


# ============================================================
# LOAD YOLO MODEL
# ============================================================

MODEL_PATH = "model/weights.pt"

CONFIDENCE_THRESHOLD=0.50

model = YOLO(MODEL_PATH)


# ============================================================
# OLD PLACEHOLDER FUNCTION
# Keep temporarily so old main.py still works
# ============================================================

def detect_damage():

    return {
        "damage_found": True,
        "damage_type": "crush_dent",
        "confidence": 0.90,
        "image_path": "damage_001.jpg"
    }


# ============================================================
# PROCESS ONE FRAME FROM SHARED CAMERA
# ============================================================

def process_damage_frame(frame):
    """
    Run YOLO damage detection on one frame.

    Returns:
        damage_result:
            dictionary if detection >= confidence threshold
            None if no accepted damage

        annotated_frame:
            frame with YOLO bounding boxes,
            class names and confidence
    """

    # Run YOLO
    results = model(
        frame,
        verbose=False
    )

    boxes = results[0].boxes

    # Create the live YOLO view
    # This includes boxes, class names and confidence
    annotated_frame = results[0].plot()


    # ========================================================
    # NOTHING DETECTED
    # ========================================================

    if boxes is None or len(boxes) == 0:
        return None, annotated_frame


    # ========================================================
    # GET HIGHEST-CONFIDENCE DETECTION
    # ========================================================

    best_box = max(
        boxes,
        key=lambda box: float(box.conf[0])
    )

    class_id = int(best_box.cls[0])
    confidence = float(best_box.conf[0])

    damage_type = model.names[class_id]


    # ========================================================
    # IGNORE LOW-CONFIDENCE DETECTIONS
    # ========================================================

    if confidence < CONFIDENCE_THRESHOLD:
        return None, annotated_frame


    # ========================================================
    # SAVE DAMAGE EVIDENCE
    # ========================================================

    os.makedirs(
        "images",
        exist_ok=True
    )

    timestamp = time.strftime(
        "%Y%m%d_%H%M%S"
    )

    image_path = (
        f"images/damage_{timestamp}.jpg"
    )

    cv2.imwrite(
        image_path,
        annotated_frame
    )


    # ========================================================
    # RETURN DAMAGE RESULT
    # ========================================================

    damage_result = {
        "damage_found": True,
        "damage_type": damage_type,
        "confidence": confidence,
        "image_path": image_path
    }

    return damage_result, annotated_frame


    # ========================================================
    # GET THE HIGHEST-CONFIDENCE DETECTION
    # ========================================================

    best_box = max(
        boxes,
        key=lambda box: float(box.conf[0])
    )

    class_id = int(best_box.cls[0])
    confidence = float(best_box.conf[0])

    damage_type = model.names[class_id]
    
    # Ignore low-confidence detections
    if confidence < CONFIDENCE_THRESHOLD:
        return None

    # ========================================================
    # CREATE ANNOTATED IMAGE
    # ========================================================

    annotated_frame = results[0].plot()


    # ========================================================
    # SAVE DAMAGE EVIDENCE
    # ========================================================

    os.makedirs(
        "images",
        exist_ok=True
    )

    timestamp = time.strftime(
        "%Y%m%d_%H%M%S"
    )

    image_path = (
        f"images/damage_{timestamp}.jpg"
    )

    cv2.imwrite(
        image_path,
        annotated_frame
    )


    # ========================================================
    # RETURN DAMAGE RESULT
    # ========================================================

    damage_result = {
        "damage_found": True,
        "damage_type": damage_type,
        "confidence": confidence,
        "image_path": image_path
    }

    return damage_result

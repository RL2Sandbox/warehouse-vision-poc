from ultralytics import YOLO
from picamera2 import Picamera2
import cv2

model = YOLO("model/weights.pt")

picam2 = Picamera2()
picam2.configure(
    picam2.create_preview_configuration(
        main={"size": (1280, 720)}
    )
)
picam2.start()

while True:

    frame = picam2.capture_array()

    results = model(frame)

    annotated_frame = results[0].plot()

    cv2.imshow(
        "Warehouse Vision Damage Detection",
        annotated_frame
    )

    detections = results[0].boxes

    if len(detections) > 0:

        print("\n========== DETECTIONS ==========")

        for box in detections:

            cls = int(box.cls[0])
            conf = float(box.conf[0])

            damage_type = model.names[cls]

            print(
                f"Damage Type: {damage_type}"
            )

            print(
                f"Confidence: {conf*100:.1f}%"
            )

            print("------------------------")

    key = cv2.waitKey(1)

    if key == ord("q"):
        break

cv2.destroyAllWindows()

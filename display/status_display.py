import cv2
import time


STATUS_COLOURS = {
    "ready": (0, 215, 255),       # Yellow
    "success": (0, 255, 0),      # Green
    "working": (255, 200, 0),     # Blue-ish
    "error": (0, 0, 255),         # Red
}


def show_status(frame, message, status_type="ready"):
    """
    Draw an operator status message on the camera frame.
    """

    colour = STATUS_COLOURS.get(
        status_type,
        STATUS_COLOURS["ready"]
    )

    # Dark background behind status message
    cv2.rectangle(
        frame,
        (20, 20),
        (frame.shape[1] - 20, 90),
        (30, 30, 30),
        -1
    )

    cv2.putText(
        frame,
        message,
        (40, 67),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        colour,
        2,
        cv2.LINE_AA
    )

    return frame

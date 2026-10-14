# status/status_display.py

import cv2
import time


# ============================================================
# STATUS COLOURS
# OpenCV uses BGR, not RGB.
# ============================================================

COLOURS = {
    "ready": (0, 215, 255),       # Yellow
    "info": (255, 200, 0),        # Light blue
    "success": (0, 255, 0),       # Green
    "error": (0, 0, 255),         # Red
    "white": (255, 255, 255),
    "black": (0, 0, 0),
}


# ============================================================
# OPERATOR STATUS
# ============================================================

class StatusDisplay:
    """
    Keeps track of what message should currently be shown
    to the operator on the live camera feed.
    """

    def __init__(self):

        self.message = "READY - Scan label or show damage"
        self.submessage = ""

        self.status_type = "ready"

        self.message_time = time.time()
        self.display_duration = None

        self.ma_number = None
        self.damage_type = None
        self.confidence = None


    # ========================================================
    # INTERNAL STATUS UPDATE
    # ========================================================

    def set_status(
        self,
        message,
        submessage="",
        status_type="info",
        duration=None,
    ):

        self.message = message
        self.submessage = submessage
        self.status_type = status_type

        self.message_time = time.time()
        self.display_duration = duration


    # ========================================================
    # READY
    # ========================================================

    def show_ready(self):

        self.ma_number = None
        self.damage_type = None
        self.confidence = None

        self.set_status(
            message="READY",
            submessage="Scan label or show damage",
            status_type="ready",
        )


    # ========================================================
    # BARCODE CAPTURED
    # ========================================================

    def show_barcode_captured(self, barcode_data):

        self.ma_number = barcode_data.get("MA_Number", "Unknown")

        self.set_status(
            message="LABEL CAPTURED",
            submessage=f"MA: {self.ma_number} | Waiting for damage...",
            status_type="success",
        )


    # ========================================================
    # DAMAGE CAPTURED
    # ========================================================

    def show_damage_captured(
        self,
        damage_type,
        confidence,
    ):

        self.damage_type = damage_type
        self.confidence = confidence

        # Accept confidence as either:
        # 0.87
        # OR
        # 87

        if confidence is None:
            confidence_text = "N/A"

        elif confidence <= 1:
            confidence_text = f"{confidence * 100:.1f}%"

        else:
            confidence_text = f"{confidence:.1f}%"

        self.set_status(
            message="DAMAGE CAPTURED",
            submessage=(
                f"{damage_type} | "
                f"Confidence: {confidence_text}"
            ),
            status_type="success",
        )


    # ========================================================
    # WAITING FOR BARCODE
    # ========================================================

    def show_waiting_for_barcode(self):

        self.set_status(
            message="DAMAGE CAPTURED",
            submessage="Waiting for label...",
            status_type="ready",
        )


    # ========================================================
    # WAITING FOR DAMAGE
    # ========================================================

    def show_waiting_for_damage(self):

        ma_text = ""

        if self.ma_number:
            ma_text = f"MA: {self.ma_number} | "

        self.set_status(
            message="LABEL CAPTURED",
            submessage=ma_text + "Waiting for damage...",
            status_type="ready",
        )


    # ========================================================
    # UPLOADING
    # ========================================================

    def show_uploading(self):

        self.set_status(
            message="SAVING INSPECTION...",
            submessage="Uploading inspection record",
            status_type="info",
        )


    # ========================================================
    # INSPECTION SAVED
    # ========================================================

    def show_inspection_saved(
        self,
        ma_number=None,
        damage_type=None,
        confidence=None,
    ):

        if ma_number is not None:
            self.ma_number = ma_number

        if damage_type is not None:
            self.damage_type = damage_type

        if confidence is not None:
            self.confidence = confidence

        details = []

        if self.ma_number:
            details.append(f"MA: {self.ma_number}")

        if self.damage_type:
            details.append(f"Damage: {self.damage_type}")

        if self.confidence is not None:

            if self.confidence <= 1:
                confidence_text = (
                    f"{self.confidence * 100:.1f}%"
                )
            else:
                confidence_text = (
                    f"{self.confidence:.1f}%"
                )

            details.append(
                f"Confidence: {confidence_text}"
            )

        self.set_status(
            message="INSPECTION SAVED",
            submessage=" | ".join(details),
            status_type="success",
            duration=3,
        )


    # ========================================================
    # SAVE / UPLOAD FAILED
    # ========================================================

    def show_save_failed(self, error_message=None):

        if error_message:
            submessage = str(error_message)
        else:
            submessage = "Please retry inspection"

        self.set_status(
            message="SAVE FAILED",
            submessage=submessage,
            status_type="error",
        )


    # ========================================================
    # GENERIC ERROR
    # ========================================================

    def show_error(self, message):

        self.set_status(
            message="ERROR",
            submessage=str(message),
            status_type="error",
        )


    # ========================================================
    # CHECK IF TEMPORARY MESSAGE EXPIRED
    # ========================================================

    def update(self):

        if self.display_duration is None:
            return

        elapsed = time.time() - self.message_time

        if elapsed >= self.display_duration:
            self.show_ready()


    # ========================================================
    # DRAW STATUS ON CAMERA FRAME
    # ========================================================

    def draw(self, frame):

        self.update()

        height, width = frame.shape[:2]

        colour = COLOURS.get(
            self.status_type,
            COLOURS["white"],
        )

        # ----------------------------------------------------
        # Dark status panel
        # ----------------------------------------------------

        overlay = frame.copy()

        panel_height = 130

        cv2.rectangle(
            overlay,
            (0, 0),
            (width, panel_height),
            COLOURS["black"],
            -1,
        )

        # Make panel slightly transparent.
        frame = cv2.addWeighted(
            overlay,
            0.65,
            frame,
            0.35,
            0,
        )

        # ----------------------------------------------------
        # Main status message
        # ----------------------------------------------------

        cv2.putText(
            frame,
            self.message,
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            colour,
            3,
            cv2.LINE_AA,
        )

        # ----------------------------------------------------
        # Secondary information
        # ----------------------------------------------------

        if self.submessage:

            cv2.putText(
                frame,
                self.submessage,
                (30, 95),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                COLOURS["white"],
                2,
                cv2.LINE_AA,
            )

        return frame

import cv2
import time

from camera.camera_manager import CameraManager

from barcode.scan_trial import process_barcode_frame

from vision.damage_detector import process_damage_frame

from session.session_manager import (
    update_barcode,
    update_damage,
    ready,
    get_session,
    reset
)

from display.status_display import StatusDisplay


# ============================================================
# SETTINGS
# ============================================================

# Do not run expensive detection on every camera frame.
BARCODE_CHECK_EVERY = 3
DAMAGE_CHECK_EVERY = 3

# Prevent immediate detection of the next carton while the
# success message is being shown.
SUCCESS_DISPLAY_SECONDS = 3


# ============================================================
# INITIALISE SYSTEM
# ============================================================

camera = CameraManager(
    width=1280,
    height=720
)

status = StatusDisplay()

print("Warehouse Vision POC starting...")

camera.start()

status.show_ready()


# ============================================================
# SESSION STATE
# ============================================================

barcode_captured = False
damage_captured = False

frame_number = 0

success_time = None

yolo_display_frame= None

print("Warehouse Vision POC started.")
print("Press Q to quit.")


# ============================================================
# MAIN LIVE CAMERA LOOP
# ============================================================

try:

    while True:

        # ----------------------------------------------------
        # GET ONE FRAME FROM THE SHARED CAMERA
        # ----------------------------------------------------

        rgb_frame = camera.get_frame()

        # CameraManager supplies RGB888.
        # OpenCV normally displays BGR.
        frame = cv2.cvtColor(
            rgb_frame,
            cv2.COLOR_RGB2BGR
        )

        frame_number += 1


        # ====================================================
        # SUCCESS / RESET DELAY
        # ====================================================

        if success_time is not None:

            elapsed = time.time() - success_time

            if elapsed >= SUCCESS_DISPLAY_SECONDS:

                reset()

                barcode_captured = False
                damage_captured = False

                success_time = None

                status.show_ready()

                print("\nReady for next carton.")


        # ====================================================
        # BARCODE DETECTION
        # ====================================================

        if (
            success_time is None
            and not barcode_captured
            and frame_number % BARCODE_CHECK_EVERY == 0
        ):

            barcode_data = process_barcode_frame(
                frame
            )

            if barcode_data is not None:

                update_barcode(
                    barcode_data
                )

                barcode_captured = True

                print("\nBarcode stored.")
                print(barcode_data)

                status.show_barcode_captured(
                    barcode_data
                )

                if not damage_captured:

                    status.show_waiting_for_damage()


        # ====================================================
        # DAMAGE DETECTION
        # ====================================================

        if (
            success_time is None
            and not damage_captured
            and frame_number % DAMAGE_CHECK_EVERY == 0
        ):

            damage_result = process_damage_frame(
                frame
            )

            if damage_result is not None:

                update_damage(
                    damage_result
                )

                damage_captured = True

                print("\nDamage stored.")

                print(
                    "Damage Type:",
                    damage_result["damage_type"]
                )

                print(
                    "Confidence:",
                    f"{damage_result['confidence'] * 100:.1f}%"
                )

                status.show_damage_captured(
                    damage_result["damage_type"],
                    damage_result["confidence"]
                )

                if not barcode_captured:

                    status.show_waiting_for_barcode()


        # ====================================================
        # COMPLETE INSPECTION
        # ====================================================

        if (
            success_time is None
            and ready()
        ):

            record = get_session()

            print("\n" + "=" * 60)
            print("COMPLETE RECORD FOUND")
            print("=" * 60)

            print(record)


            # =================================================
            # GCP PLACEHOLDER
            # =================================================

            print("\nUploading to GCP...")
            print("(placeholder only)")


            # IMPORTANT:
            # This is NOT genuinely saved to GCP yet.
            #
            # Therefore we should NOT tell the operator
            # "INSPECTION SAVED" yet.
            #
            # For this integration test, show that the
            # inspection itself is complete.

            status.set_status(
                message="INSPECTION COMPLETE",
                submessage="GCP upload not connected yet",
                status_type="success"
            )

            success_time = time.time()


        # ====================================================
        # DRAW OPERATOR STATUS
        # ====================================================

        display_frame = status.draw(
            frame
        )


        # ====================================================
        # SHOW LIVE CAMERA
        # ====================================================

        cv2.imshow(
            "Warehouse Vision Inspection",
            display_frame
        )


        # ====================================================
        # KEYBOARD
        # ====================================================

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):

            print("\nExiting Warehouse Vision POC...")
            break


except KeyboardInterrupt:

    print("\nStopped using Ctrl+C.")


except Exception as error:

    print(
        f"\nSystem error: {error}"
    )

    status.show_error(
        str(error)
    )


finally:

    # ========================================================
    # CLEAN SHUTDOWN
    # ========================================================

    camera.stop()

    cv2.destroyAllWindows()

    print("System closed safely.")

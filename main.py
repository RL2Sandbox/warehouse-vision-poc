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

from cloud.gcp_upload import upload_record

# ============================================================
# SETTINGS
# ============================================================

# Do not run expensive detection on every camera frame.
BARCODE_CHECK_EVERY = 3
DAMAGE_CHECK_EVERY = 4

#damage must be detected consistently before capture
DAMAGE_CONFIRM_FRAMES = 3
DAMAGE_CONFIRM_WINDOW = 2.0


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

yolo_display_frame = None
damage_display_time = None

# Damage confirmation tracking
damage_candidate_type = None
damage_candidate_count = 0
damage_candidate_start = None
damage_candidate_result = None

upload_attempted = False

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

        #rgb_frame = camera.get_frame()

        # CameraManager supplies RGB888.
        # OpenCV normally displays BGR.
        
        #frame = cv2.cvtColor(
            #rgb_frame,
            #cv2.COLOR_RGB2BGR
        #)
        frame = camera.get_frame()
        
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

                # Clear the previous YOLO bounding-box frame
                yolo_display_frame = None
                upload_attempted = False

                damage_candidate_type = None
                damage_candidate_count = 0
                damage_candidate_start = None
                damage_candidate_result = None
                damage_display_time = None

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

            damage_result, yolo_display_frame = process_damage_frame(
                frame
            )
############
            if damage_result is not None:

                current_time = time.time()
                current_type = damage_result["damage_type"]

                # Has too much time passed since the candidate started?
                candidate_expired = (
                    damage_candidate_start is not None
                    and current_time - damage_candidate_start
                    > DAMAGE_CONFIRM_WINDOW
                )

                # Has YOLO changed its mind about the damage class?
                different_damage = (
                    damage_candidate_type is not None
                    and current_type != damage_candidate_type
                )


                # ========================================================
                # START / RESTART DAMAGE CONFIRMATION
                # ========================================================
            
                if (
                    damage_candidate_type is None
                    or candidate_expired
                    or different_damage
                ):
            
                    damage_candidate_type = current_type
                    damage_candidate_count = 1
                    damage_candidate_start = current_time
            
                else:
            
                    damage_candidate_count += 1
            
            
                # Keep most recent detection result
                damage_candidate_result = damage_result
            
            
                print(
                    f"Confirming {current_type}: "
                    f"{damage_candidate_count}/"
                    f"{DAMAGE_CONFIRM_FRAMES}"
                )
            
            
                # ========================================================
                # DAMAGE CONFIRMED
                # ========================================================
            
                if damage_candidate_count >= DAMAGE_CONFIRM_FRAMES:
            
                    update_damage(
                        damage_candidate_result
                    )
            
                    damage_captured = True
            
                    damage_display_time = current_time
            
                    print("\nDamage confirmed and stored.")
            
                    print(
                        "Damage Type:",
                        damage_candidate_result["damage_type"]
                    )
            
                    print(
                        "Confidence:",
                        f"{damage_candidate_result['confidence'] * 100:.1f}%"
                    )
            
                    status.show_damage_captured(
                        damage_candidate_result["damage_type"],
                        damage_candidate_result["confidence"]
                    )
            
                    if not barcode_captured:
            
                        status.show_waiting_for_barcode()
            #############
            


        # ====================================================
        # COMPLETE INSPECTION
        # ====================================================


        if (
            success_time is None
            and ready()
            and not upload_attempted
        ):
            record = get_session()

            print("\n" + "=" * 60)
            print("COMPLETE RECORD FOUND")
            print("=" * 60)
            print(record)

            # ================================================
            # UPLOAD TO GCP
            # ================================================

            print("\nUploading inspection to GCP...")

            status.show_uploading()

            upload_attempted = True

            upload_success = upload_record(record)

            # ================================================
            # UPLOAD SUCCESS
            # ================================================

            if upload_success:
                print("Inspection uploaded successfully.")

                barcode_data = record.get(
                    "barcode",
                    {}
                )

                damage_data = record.get(
                    "damage",
                    {}
                )

                status.show_inspection_saved(
                    ma_number=barcode_data.get(
                        "MA_Number"
                    ),
                    damage_type=damage_data.get(
                        "damage_type"
                    ),
                    confidence=damage_data.get(
                        "confidence"
                    )
                )

                success_time = time.time()

            # ================================================
            # UPLOAD FAILED
            # ================================================

            else:
                print("Inspection upload FAILED.")

                status.show_save_failed(
                    "GCP upload failed - inspection not reset"
                )
       
        # ====================================================
        # DRAW OPERATOR STATUS
        # ====================================================

        
        # Always start from current live camera
        display_frame = frame.copy()
        
        
        # Show current YOLO output while searching for damage
        if (
            not damage_captured
            and yolo_display_frame is not None
        ):
            display_frame = yolo_display_frame.copy()
        
        
        # After valid damage is captured,
        # keep the successful bounding box visible briefly
        elif (
            damage_captured
            and yolo_display_frame is not None
            and damage_display_time is not None
            and time.time() - damage_display_time < 1.5
        ):
            display_frame = yolo_display_frame.copy()
        
        
        # Draw status message on top
        display_frame = status.draw(
            display_frame
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

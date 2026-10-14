from barcode.scan_trial import scan_barcode
from vision.damage_detector import detect_damage
from session.session_manager import (
    update_barcode,
    update_damage,
    ready,
    get_session,
    reset
)

# from cloud.gcp_upload import upload_record

from status.status_display import StatusDisplay


# Create ONE status object for the application
status = StatusDisplay()


print("Warehouse Vision POC Started")

# Initial system state
status.show_ready()


while True:

    print("\nChoose an action:")
    print("1 = Scan Barcode")
    print("2 = Detect Damage")
    print("3 = Exit")

    choice = input("> ")


    # ========================================================
    # OPTION 1 - SCAN BARCODE
    # ========================================================

    if choice == "1":

        barcode_data = scan_barcode()

        if barcode_data is None:

            print("No barcode captured.")

            status.show_error(
                "No barcode captured"
            )

        else:

            update_barcode(barcode_data)

            print("Barcode stored.")
            print(barcode_data)

            # Tell status system that barcode was captured
            status.show_barcode_captured(
                barcode_data
            )

            # We now need the damage
            status.show_waiting_for_damage()


    # ========================================================
    # OPTION 2 - DETECT DAMAGE
    # ========================================================

    elif choice == "2":

        result = detect_damage()

        if result is None:

            print("No damage result returned.")

            status.show_error(
                "No damage captured"
            )

            continue


        print(
            f"Damage Type: "
            f"{result['damage_type']}"
        )

        print(
            f"Confidence: "
            f"{result['confidence']}"
        )


        update_damage(
            result["image_path"]
        )


        print("Damage stored.")


        # Tell status system what was captured
        status.show_damage_captured(
            result["damage_type"],
            result["confidence"]
        )


        # If barcode hasn't been captured yet,
        # the operator needs to scan it next.
        if not ready():

            status.show_waiting_for_barcode()


    # ========================================================
    # OPTION 3 - EXIT
    # ========================================================

    elif choice == "3":

        print("Exiting...")
        break


    # ========================================================
    # INVALID OPTION
    # ========================================================

    else:

        print("Invalid option.")

        status.show_error(
            "Invalid menu option"
        )

        continue


    # ========================================================
    # CHECK WHETHER INSPECTION IS COMPLETE
    # ========================================================

    if ready():

        print("\nCOMPLETE RECORD FOUND")

        record = get_session()

        print(record)


        # ----------------------------------------------------
        # FOR NOW GCP IS STILL PLACEHOLDER
        # ----------------------------------------------------

        print("\nUploading to GCP...")
        print("(placeholder only)")


        # IMPORTANT:
        #
        # Do NOT call:
        #
        # status.show_inspection_saved()
        #
        # yet.
        #
        # We should only show INSPECTION SAVED
        # after the REAL GCP upload succeeds.


        reset()

        print("Session reset.")

        status.show_ready()

# Main application entry point
# Main application entry point
from barcode.scan_trial import scan_barcode
from vision.damage_detector import detect_damage
from session.session_manager import (
    update_barcode,
    update_damage,
    ready,
    get_session,
    reset
)

#from cloud.gcp_upload import upload_record
from status.status_display import StatusDisplay
status= StatusDisplay()

print("Warehouse Vision POC Started")

while True:

    print("\nChoose an action:")
    print("1 = Scan Barcode")
    print("2 = Detect Damage")
    print("3 = Exit")

    choice = input("> ")

    if choice == "1":
        barcode_data = scan_barcode()
 
        if barcode_data is None:
 
            print("No barcode captured.")
 
        else:
 
            update_barcode(barcode_data)
 
            print("Barcode stored.")
            print(barcode_data)
        
    elif choice == "2":

        #damage_image = input("Enter damage image name: ")
        result = detect_damage()
        print(f"Damage Type: {result['damage_type']}")
        print(f"Confidence: {result['confidence']}")

        update_damage(result["image_path"])

        #update_damage(damage_image)

        print("Damage stored.")

    elif choice == "3":

        print("Exiting...")
        break

    else:

        print("Invalid option.")
        continue

    if ready():

        print("\nCOMPLETE RECORD FOUND")

        print(get_session())

        print("\nUploading to GCP...")
        print("(placeholder only)")

        reset()

        print("Session reset.")

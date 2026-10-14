#copy code into here
import time
import cv2
import numpy as np

from picamera2 import Picamera2
from pylibdmtx.pylibdmtx import decode

try:
    from libcamera import controls
    LIBCAMERA_CONTROLS_AVAILABLE = True
except ImportError:
    LIBCAMERA_CONTROLS_AVAILABLE = False


# ============================================================
# DATA MATRIX FIELD CONFIGURATION
# ============================================================

# These meanings are confirmed from your current requirement.
# Fields whose meanings are not confirmed retain their prefixes
# as their output names so that the program does not guess.
PREFIX_MAPPING = {
    "50P": "50P",
    "13D": "13D",
    "3P": "MA_Number",
    "1T": "Vendor_Lot",
    "9D": "9D",
    "1P": "1P",
    "7Q": "7Q",
    "Q": "Quantity",
    "S": "S"
}

GROUP_SEPARATOR = "\x1d"
RECORD_SEPARATOR = "\x1e"
END_OF_TRANSMISSION = "\x04"

DECODE_EVERY_N_FRAMES = 3
DUPLICATE_DELAY_SECONDS = 3.0


# ============================================================
# DATA MATRIX PARSING
# ============================================================

def make_control_characters_visible(text):
    """Display invisible barcode separators visibly in terminal."""

    return (
        text.replace(RECORD_SEPARATOR, "␞")
        .replace(GROUP_SEPARATOR, "␝")
        .replace(END_OF_TRANSMISSION, "␄")
    )


def parse_datamatrix(raw_data):
    """
    Split the Data Matrix using ASCII Group Separator.

    The values can have different lengths because the Group
    Separator marks where each field ends.
    """

    header = "[)>" + RECORD_SEPARATOR + "06" + GROUP_SEPARATOR

    if raw_data.startswith(header):
        cleaned_data = raw_data[len(header):]
    else:
        cleaned_data = raw_data

    cleaned_data = cleaned_data.rstrip(
        RECORD_SEPARATOR + END_OF_TRANSMISSION
    )

    fields = cleaned_data.split(GROUP_SEPARATOR)

    parsed_data = {}
    unrecognised_fields = []

    # Longer prefixes must be checked first.
    # For example, check 50P before shorter prefixes.
    sorted_prefixes = sorted(
        PREFIX_MAPPING.keys(),
        key=len,
        reverse=True
    )

    for field in fields:
        field = field.strip()

        if not field:
            continue

        matched = False

        for prefix in sorted_prefixes:
            if field.startswith(prefix):
                output_name = PREFIX_MAPPING[prefix]
                output_value = field[len(prefix):]

                parsed_data[output_name] = output_value
                matched = True
                break

        if not matched:
            unrecognised_fields.append(field)

    if unrecognised_fields:
        parsed_data["Unrecognised_Fields"] = unrecognised_fields

    return parsed_data


def print_result(raw_data, parsed_data, method):
    """Print the decoded and parsed Data Matrix content."""

    print("\n" + "=" * 65)
    print("DATA MATRIX DETECTED")
    print("=" * 65)

    print(f"\nDetection method: {method}")

    print("\nRaw decoded data:")
    print(make_control_characters_visible(raw_data))

    print("\nParsed output:")

    if not parsed_data:
        print("No recognised fields were found.")
    else:
        for field_name, field_value in parsed_data.items():
            print(f"{field_name}: {field_value}")

    print("=" * 65 + "\n")


# ============================================================
# IMAGE PROCESSING
# ============================================================

def create_scan_versions(scan_area):
    """
    Create several image versions.

    Small industrial Data Matrix codes may decode better after
    enlargement, sharpening or thresholding.
    """

    grayscale = cv2.cvtColor(scan_area, cv2.COLOR_BGR2GRAY)

    enlarged = cv2.resize(
        grayscale,
        None,
        fx=2.0,
        fy=2.0,
        interpolation=cv2.INTER_CUBIC
    )

    # Increase local contrast.
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    contrast_enhanced = clahe.apply(enlarged)

    # Sharpen the enlarged image.
    blurred = cv2.GaussianBlur(
        contrast_enhanced,
        (0, 0),
        1.2
    )

    sharpened = cv2.addWeighted(
        contrast_enhanced,
        1.8,
        blurred,
        -0.8,
        0
    )

    # Create a strong black-and-white version.
    adaptive_threshold = cv2.adaptiveThreshold(
        sharpened,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        5
    )

    return [
        ("Original colour", scan_area),
        ("Grayscale", grayscale),
        ("Enlarged grayscale", enlarged),
        ("Contrast enhanced", contrast_enhanced),
        ("Sharpened", sharpened),
        ("Adaptive threshold", adaptive_threshold)
    ]


def decode_scan_area(scan_area):
    """
    Try to decode the scan area using several processed versions.

    pylibdmtx searches for Data Matrix codes rather than the
    surrounding 1D barcodes.
    """

    image_versions = create_scan_versions(scan_area)

    for method_name, image in image_versions:
        try:
            results = decode(
                image,
                timeout=120,
                max_count=1
            )

            if results:
                return results[0], method_name

        except Exception as error:
            print(f"Decode warning for {method_name}: {error}")

    return None, None

# ============================================================
# PROCESS ONE FRAME FROM SHARED CAMERA
# ============================================================

def process_barcode_frame(frame):
    """
    Check one frame supplied by the shared camera for a
    Data Matrix code.

    Returns:
        parsed barcode dictionary if detected
        None if no Data Matrix is detected
    """

    frame_height, frame_width = frame.shape[:2]

    # Central scan region
    scan_width = int(frame_width * 0.70)
    scan_height = int(frame_height * 0.72)

    scan_x1 = (frame_width - scan_width) // 2
    scan_y1 = (frame_height - scan_height) // 2

    scan_x2 = scan_x1 + scan_width
    scan_y2 = scan_y1 + scan_height

    scan_area = frame[
        scan_y1:scan_y2,
        scan_x1:scan_x2
    ].copy()

    # Try to decode Data Matrix
    detected_item, detection_method = decode_scan_area(
        scan_area
    )

    if detected_item is None:
        return None

    # Decode raw barcode data
    raw_data = detected_item.data.decode(
        "utf-8",
        errors="replace"
    )

    # Convert raw barcode into your dictionary
    parsed_data = parse_datamatrix(raw_data)

    print_result(
        raw_data,
        parsed_data,
        detection_method
    )

    return parsed_data

def scan_barcode():
    # ============================================================
    # CAMERA SETUP
    # ============================================================
    
    picam2 = Picamera2()
    
    camera_configuration = picam2.create_preview_configuration(
        main={
            "size": (1920, 1080),
            "format": "RGB888"
        },
        buffer_count=4
    )
    
    picam2.configure(camera_configuration)
    picam2.start()
    
    # Allow exposure and white balance to settle.
    time.sleep(2)
    
    
    # ============================================================
    # CAMERA MODULE 3 AUTOFOCUS
    # ============================================================
    
    if LIBCAMERA_CONTROLS_AVAILABLE:
        try:
            picam2.set_controls({
                "AfMode": controls.AfModeEnum.Continuous,
                "AfRange": controls.AfRangeEnum.Macro,
                "AfSpeed": controls.AfSpeedEnum.Fast
            })
    
            print("Continuous close-range autofocus enabled.")
    
        except Exception as error:
            print(f"Macro autofocus could not be enabled: {error}")
            print("Trying normal continuous autofocus.")
    
            try:
                picam2.set_controls({
                    "AfMode": controls.AfModeEnum.Continuous
                })
            except Exception as autofocus_error:
                print(f"Autofocus warning: {autofocus_error}")
    
    else:
        # Numeric fallback:
        # AfMode 2 represents continuous autofocus.
        try:
            picam2.set_controls({
                "AfMode": 2
            })
    
            print("Continuous autofocus enabled.")
    
        except Exception as error:
            print(f"Autofocus warning: {error}")
    
    
    print("\nData Matrix scanner started.")
    print("Place the Data Matrix inside the green rectangle.")
    print("Hold the label still until the image becomes sharp.")
    print("Press F to trigger autofocus.")
    print("Press S to save the scanning area.")
    print("Press Q to quit.\n")
    
    
    # ============================================================
    # MAIN LIVE SCANNING LOOP
    # ============================================================
    
    frame_number = 0
    last_scanned_data = None
    last_scan_time = 0
    status_message = "Place Data Matrix inside green box"
    status_colour = (0, 215, 255)
    status_message_time = 0
    
    try:
        while True:
            rgb_frame = picam2.capture_array()
    
            frame = cv2.cvtColor(
                rgb_frame,
                cv2.COLOR_RGB2BGR
            )
    
            frame_height, frame_width = frame.shape[:2]
    
            # Central scan region.
            # Keeping the code inside this area helps the decoder work
            # on a smaller image instead of the entire label.
            scan_width = int(frame_width * 0.70)
            scan_height = int(frame_height * 0.72)
    
            scan_x1 = (frame_width - scan_width) // 2
            scan_y1 = (frame_height - scan_height) // 2
            scan_x2 = scan_x1 + scan_width
            scan_y2 = scan_y1 + scan_height
    
            scan_area = frame[
                scan_y1:scan_y2,
                scan_x1:scan_x2
            ].copy()
    
            frame_number += 1
    
            detected_item = None
            detection_method = None
    
            if frame_number % DECODE_EVERY_N_FRAMES == 0:
                detected_item, detection_method = decode_scan_area(
                    scan_area
                )
    
            if detected_item is not None:
                raw_data = detected_item.data.decode(
                    "utf-8",
                    errors="replace"
                )
    
                current_time = time.time()
    
                new_barcode = raw_data != last_scanned_data
                duplicate_delay_complete = (
                    current_time - last_scan_time
                    >= DUPLICATE_DELAY_SECONDS
                )
    
                if new_barcode or duplicate_delay_complete:
                    parsed_data = parse_datamatrix(raw_data)
    
                    print_result(
                        raw_data,
                        parsed_data,
                        detection_method
                    )
    
                    last_scanned_data = raw_data
                    last_scan_time = current_time
                    return parsed_data
    
                status_message = "DATA MATRIX DETECTED"
                status_colour = (0, 255, 0)
                status_message_time = current_time
    
            elif time.time() - status_message_time > 1:
                status_message = "Hold label still and let camera focus"
                status_colour = (0, 215, 255)
    
            # Draw the scanning rectangle.
            cv2.rectangle(
                frame,
                (scan_x1, scan_y1),
                (scan_x2, scan_y2),
                status_colour,
                3
            )
    
            cv2.putText(
                frame,
                status_message,
                (scan_x1, max(scan_y1 - 18, 35)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                status_colour,
                2
            )
    
            cv2.putText(
                frame,
                "Put the small Data Matrix inside the green box",
                (25, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 255, 255),
                2
            )
    
            cv2.putText(
                frame,
                "F: Focus   S: Save scan area   Q: Quit",
                (25, frame_height - 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )
    
            # Resize only the display window.
            # Decoding still uses the higher-resolution image.
            display_width = 1280
            display_height = int(
                frame_height * display_width / frame_width
            )
    
            display_frame = cv2.resize(
                frame,
                (display_width, display_height)
            )
    
            cv2.imshow(
                "Camera Module 3 - Data Matrix Scanner",
                display_frame
            )
    
            key = cv2.waitKey(1) & 0xFF
    
            if key == ord("q"):
                return None
    
            elif key == ord("s"):
                filename = time.strftime(
                    "datamatrix_scan_%Y%m%d_%H%M%S.jpg"
                )
    
                cv2.imwrite(filename, scan_area)
                print(f"Saved scanning area: {filename}")
    
                status_message = "SCAN AREA SAVED"
                status_colour = (255, 200, 0)
                status_message_time = time.time()
    
            elif key == ord("f"):
                print("Autofocus requested.")
    
                try:
                    if LIBCAMERA_CONTROLS_AVAILABLE:
                        picam2.set_controls({
                            "AfMode": controls.AfModeEnum.Auto,
                            "AfTrigger": controls.AfTriggerEnum.Start
                        })
    
                        time.sleep(1)
    
                        picam2.set_controls({
                            "AfMode": controls.AfModeEnum.Continuous,
                            "AfRange": controls.AfRangeEnum.Macro
                        })
    
                    else:
                        picam2.set_controls({
                            "AfMode": 1,
                            "AfTrigger": 0
                        })
    
                except Exception as error:
                    print(f"Autofocus trigger warning: {error}")
    
    
    except KeyboardInterrupt:
        print("\nScanner stopped with Ctrl+C.")
        return None
    
    
    finally:
        picam2.stop()
        cv2.destroyAllWindows()
        print("Camera closed safely.")
      
    #Added Data matrix scanner code
# ============================================================
# STANDALONE TESTING
# ============================================================
if __name__ == "__main__":
    scan_result = scan_barcode()

    if scan_result is not None:
        print("Scan completed successfully.")
    else:
        print("No Data Matrix was captured.")

# cloud/gcp_upload.py

from google.cloud import storage

import json
import os
import time


# ============================================================
# GCP CONFIGURATION
# ============================================================

BUCKET_NAME = "vision_rpi_camera"


# ============================================================
# UPLOAD COMPLETE INSPECTION
# ============================================================

def upload_record(record):
    """
    Upload a completed inspection to Google Cloud Storage.

    Uploads:
        1. Damage image
        2. Inspection JSON record

    Returns:
        True if both uploads succeed
        False if anything fails
    """

    try:
        # ====================================================
        # CONNECT TO GCP
        # ====================================================

        client = storage.Client()

        bucket = client.bucket(
            BUCKET_NAME
        )


        # ====================================================
        # CREATE TIMESTAMP
        # ====================================================

        timestamp = time.strftime(
            "%Y%m%d_%H%M%S"
        )


        # ====================================================
        # GET SESSION DATA
        # ====================================================

        barcode_data = record.get(
            "barcode",
            {}
        )

        damage_data = record.get(
            "damage",
            {}
        )


        ma_number = barcode_data.get(
            "MA_Number",
            "unknown"
        )

        serial_number = barcode_data.get(
            "S",
            "unknown"
        )

        damage_type = damage_data.get(
            "damage_type",
            "unknown"
        )

        confidence = damage_data.get(
            "confidence"
        )

        local_image_path = damage_data.get(
            "image_path"
        )


        # ====================================================
        # CREATE CLOUD STORAGE FOLDER
        # ====================================================

        inspection_folder = (
            f"inspections/"
            f"{serial_number}/"
            f"{timestamp}"
        )


        # ====================================================
        # CHECK DAMAGE IMAGE
        # ====================================================

        if not local_image_path:
            print(
                "GCP upload failed: "
                "No damage image path."
            )
            return False

        if not os.path.exists(local_image_path):
            print(
                "GCP upload failed: "
                f"Image not found: {local_image_path}"
            )
            return False


        # ====================================================
        # UPLOAD DAMAGE IMAGE
        # ====================================================

        cloud_image_path = (
            f"{inspection_folder}/damage.jpg"
        )

        image_blob = bucket.blob(
            cloud_image_path
        )

        image_blob.upload_from_filename(
            local_image_path
        )

        print(
            "Damage image uploaded:",
            cloud_image_path
        )


        # ====================================================
        # CREATE JSON RECORD
        # ====================================================

        inspection_record = {
            "timestamp": timestamp,
            "serial_number": serial_number,
            "ma_number": ma_number,
            
            "barcode": barcode_data,

            "damage": {
                "damage_found": damage_data.get(
                    "damage_found",
                    False
                ),

                "damage_type": damage_type,

                "confidence": confidence,

                "image_path": cloud_image_path
            }
        }


        # ====================================================
        # UPLOAD JSON RECORD
        # ====================================================

        json_cloud_path = (
            f"{inspection_folder}/"
            f"inspection.json"
        )

        json_blob = bucket.blob(
            json_cloud_path
        )

        json_blob.upload_from_string(
            json.dumps(
                inspection_record,
                indent=4
            ),
            content_type="application/json"
        )

        print(
            "Inspection record uploaded:",
            json_cloud_path
        )


        # ====================================================
        # SUCCESS
        # ====================================================

        print(
            "GCP upload completed successfully."
        )

        return True


    except Exception as error:

        print(
            f"GCP upload failed: {error}"
        )

        return False

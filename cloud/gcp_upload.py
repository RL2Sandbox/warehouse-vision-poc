
# GCP upload module
# cloud/gcp_upload.py

from google.cloud import storage

import json
import os
import time


# ============================================================
# GCP CONFIGURATION
# ============================================================

# Change this to your actual GCP bucket name
BUCKET_NAME = "vision_rpi_camera"


# ============================================================
# UPLOAD COMPLETE INSPECTION
# ============================================================

def upload_record(record):
    """
    Upload the completed warehouse inspection to GCP.

    Uploads:
        1. Damage image
        2. JSON inspection record

    Returns:
        True if everything uploads successfully
        False if upload fails
    """

    try:

        # ----------------------------------------------------
        # CONNECT TO GCP
        # ----------------------------------------------------

        client = storage.Client()

        bucket = client.bucket(
            BUCKET_NAME
        )


        # ----------------------------------------------------
        # CREATE INSPECTION TIMESTAMP
        # ----------------------------------------------------

        timestamp = time.strftime(
            "%Y%m%d_%H%M%S"
        )


        # ----------------------------------------------------
        # GET DATA FROM SESSION RECORD
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # CREATE GCP FOLDER FOR THIS INSPECTION
        # ----------------------------------------------------

        inspection_folder = (
            f"inspections/"
            f"{ma_number}/"
            f"{timestamp}"
        )


        # ----------------------------------------------------
        # UPLOAD DAMAGE IMAGE
        # ----------------------------------------------------

        cloud_image_path = None

        if (
            local_image_path
            and os.path.exists(local_image_path)
        ):

            cloud_image_path = (
                f"{inspection_folder}/"
                f"damage.jpg"
            )

            image_blob = bucket.blob(
                cloud_image_path
            )

            image_blob.upload_from_filename(
                local_image_path
            )

            print(
                f"Damage image uploaded: "
                f"{cloud_image_path}"
            )

        else:

            print(
                "Damage image was not found."
            )

            return False


        # ----------------------------------------------------
        # CREATE JSON 

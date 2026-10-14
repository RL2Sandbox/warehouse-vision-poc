
# Session management
# Session management
# session/session_manager.py


# ============================================================
# CURRENT CARTON SESSION
# ============================================================

session = {
    "barcode": None,
    "damage": None
}


# ============================================================
# STORE BARCODE DATA
# ============================================================

def update_barcode(barcode_data):
    """
    Store the parsed Data Matrix dictionary.
    """

    session["barcode"] = barcode_data


# ============================================================
# STORE DAMAGE RESULT
# ============================================================

def update_damage(damage_result):
    """
    Store the complete damage detection result.

    Expected format:

    {
        "damage_found": True,
        "damage_type": "crush_dent",
        "confidence": 0.90,
        "image_path": "damage_001.jpg"
    }
    """

    session["damage"] = damage_result


# ============================================================
# CHECK IF SESSION IS COMPLETE
# ============================================================

def ready():
    """
    Inspection is ready when both barcode data
    and damage data have been captured.
    """

    return (
        session["barcode"] is not None
        and session["damage"] is not None
    )


# ============================================================
# GET COMPLETE SESSION
# ============================================================

def get_session():
    return session


# ============================================================
# RESET SESSION
# ============================================================

def reset():
    """
    Clear the current carton after the inspection
    has been successfully completed.
    """

    session["barcode"] = None
    session["damage"] = None

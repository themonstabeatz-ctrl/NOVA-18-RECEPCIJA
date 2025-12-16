"""
🔒 LOCKDOWN MODULE - Massage/Couples Backend Protection
========================================================
This module protects the massage and couples booking logic from modifications.

LOCKED ENDPOINTS:
- POST /api/appointments/couple
- POST /api/appointments/couple/v2
- POST /api/book-couple-appointment
- All massage pricing/discount logic

TO UNLOCK (emergency only):
Set environment variable: LOCK_TOKEN=BL_LOCK_2025_12_16
"""

import os

LOCKED = True
EXPECTED = "BL_LOCK_2025_12_16"

def assert_not_locked():
    """
    Call this at the top of any locked endpoint handler.
    Raises RuntimeError if lockdown is active and token not provided.
    """
    token = os.getenv("LOCK_TOKEN", "")
    if LOCKED and token != EXPECTED:
        raise RuntimeError("LOCKDOWN VIOLATION: Massage/Couples backend is locked.")

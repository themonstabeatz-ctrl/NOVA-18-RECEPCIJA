"""
🔒 LOCKDOWN MODULE - Massage/Couples Backend Protection (Feature Flag)
======================================================================
This module protects the massage and couples booking logic from modifications.

DEFAULT: Booking works normally (LOCKDOWN_ENFORCE=0 or unset)
LOCKED:  Only when LOCKDOWN_ENFORCE=1, requires LOCK_TOKEN

LOCKED ENDPOINTS:
- POST /api/appointments/couple
- POST /api/appointments/couple/v2
- POST /api/book-couple-appointment

TO ENABLE LOCK (for agent work):
  LOCKDOWN_ENFORCE=1
  LOCK_TOKEN_EXPECTED=BL_LOCK_2025_12_16
  LOCK_TOKEN=BL_LOCK_2025_12_16
"""

import os

def lockdown_enabled() -> bool:
    """Check if lockdown enforcement is active"""
    return os.getenv("LOCKDOWN_ENFORCE", "0") == "1"

def require_lock_token():
    """
    Call this at the top of any protected endpoint handler.
    Only blocks when LOCKDOWN_ENFORCE=1 and token doesn't match.
    Default (production): does NOT block.
    """
    if not lockdown_enabled():
        return  # DO NOT BLOCK PRODUCTION
    
    token = os.getenv("LOCK_TOKEN", "")
    expected = os.getenv("LOCK_TOKEN_EXPECTED", "")
    
    if token != expected:
        raise RuntimeError("LOCKDOWN VIOLATION: Couples backend is locked.")

# Backward compatibility alias
def assert_not_locked():
    require_lock_token()

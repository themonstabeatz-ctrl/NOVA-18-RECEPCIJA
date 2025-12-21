"""
💰 PRICING UTILS - Bulletproof pricing resolution
Single source of truth for extracting and displaying pricing data.

STANDARDIZED FIELD NAMES:
- original_total: Original price BEFORE discount (int)
- final_total: Price AFTER discount (int) 
- discount_percent: Discount percentage (int, 0-15)
- has_discount: Boolean flag
- card_id: Card ID for tracking

RULES:
❌ NEVER use appointment.total as "orig"
❌ NEVER use original_price if original_total exists  
❌ NEVER strikethrough final_total
"""

import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


def resolve_pricing(appt: Dict) -> Dict:
    """
    🔒 BULLETPROOF pricing resolver - ONE helper for ALL displays.
    
    Use this for:
    - Notifications
    - Listing
    - Termini (Appointments)
    - Email templates
    
    Args:
        appt: Appointment dict with optional 'pricing' nested object
        
    Returns:
        {
            "orig": int | None,      # Original price (before discount)
            "final": int | None,     # Final price (after discount)
            "discount": int,         # Discount percentage
            "has": bool,             # Has discount flag
            "card_id": str | None    # Card ID for tracking
        }
        
    Raises:
        ValueError: If has_discount=True but orig <= final (invalid state)
    """
    p = appt.get("pricing") or {}
    
    # Get discount percentage
    discount = int(p.get("discount_percent") or 0)
    
    # Get has_discount flag
    has = bool(p.get("has_discount")) and discount > 0
    
    # Get card_id
    card_id = p.get("card_id")
    
    # 🔒 PREFER NEW KEYS (original_total, final_total)
    orig = p.get("original_total")
    final = p.get("final_total") or appt.get("total")
    
    # 🔄 LEGACY FALLBACK: Map old keys to new
    if orig is None:
        orig = p.get("original_price")
    if final is None:
        final = p.get("final_price")
    
    # 🧮 REVERSE CALCULATION: Only if orig is missing but we have discount
    if orig is None and has and final is not None and discount > 0:
        # orig = final / (1 - discount/100)
        orig = round(final / (1 - discount / 100))
    
    # Convert to int if present
    if orig is not None:
        orig = int(orig)
    if final is not None:
        final = int(final)
    
    # 🛡️ FINAL GUARD: Prevent invalid pricing state
    if has and orig is not None and final is not None:
        if orig <= final:
            logger.error(f"🚨 INVALID_PRICING: orig({orig}) <= final({final}) with discount {discount}%")
            raise ValueError(f"Invalid pricing: orig({orig}) <= final({final}) with discount {discount}%")
    
    return {
        "orig": orig,
        "final": final,
        "discount": discount,
        "has": has,
        "card_id": card_id
    }


def create_standardized_snapshot(
    original_total: int,
    discount_percent: int = 0,
    card_id: str = None,
    reason: str = None
) -> Dict:
    """
    🔒 Create STANDARDIZED pricing snapshot for DB storage.
    
    Uses ONLY the standard field names:
    - original_total (not original_price)
    - final_total (not final_price)
    - discount_percent
    - has_discount
    - card_id
    
    Args:
        original_total: Original price before discount
        discount_percent: Discount percentage (0, 5, 10, or 15)
        card_id: Card ID for tracking
        reason: Reason for snapshot (e.g., "SPA_RITUAL_BOOKING")
        
    Returns:
        Standardized pricing snapshot dict
    """
    # Validate discount
    valid_discounts = [0, 5, 10, 15]
    if discount_percent not in valid_discounts:
        discount_percent = max([d for d in valid_discounts if d <= discount_percent], default=0)
    
    # Calculate
    discount_amount = int(round(original_total * discount_percent / 100))
    final_total = int(original_total - discount_amount)
    has_discount = discount_percent > 0 and final_total < original_total
    
    return {
        # 🔒 STANDARD FIELD NAMES ONLY
        "original_total": int(original_total),
        "final_total": int(final_total),
        "discount_percent": int(discount_percent),
        "discount_amount": int(discount_amount),
        "has_discount": has_discount,
        "card_id": card_id,
        "reason": reason,
        "snapshot_at": None  # Will be set to ISO timestamp when saved
    }


def format_pricing_for_display(pricing: Dict) -> str:
    """
    Format pricing dict for display in logs/debug.
    """
    orig = pricing.get("orig") or pricing.get("original_total")
    final = pricing.get("final") or pricing.get("final_total")
    discount = pricing.get("discount") or pricing.get("discount_percent") or 0
    has = pricing.get("has") or pricing.get("has_discount")
    
    if has:
        return f"<s>{orig:,}</s> RSD → {final:,} RSD (-{discount}%)"
    else:
        return f"{final or orig:,} RSD"

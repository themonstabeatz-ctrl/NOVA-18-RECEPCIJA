"""
💰 PRICING UTILS - Bulletproof pricing resolution
Single source of truth for extracting and displaying pricing data.

STANDARDIZED FIELD NAMES:
- original_total: Original price BEFORE discount (int)
- final_total: Price AFTER discount (int) 
- discount_percent: Discount percentage (int, 0-15)
- has_discount: Boolean flag (true/false)
- card_id: Card ID for tracking

RULES:
❌ NEVER use appointment.total as "orig"
❌ NEVER use original_price if original_total exists  
❌ NEVER strikethrough final_total
✅ IF has_discount == true, original_total MUST be > final_total
"""

import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


def compute_pricing(original_total: int, discount_percent: int) -> dict:
    """
    🔒 BULLETPROOF pricing calculator - USE THIS EVERYWHERE.
    
    This is THE ONE function that computes pricing. No other logic allowed.
    
    Args:
        original_total: Original price before discount (must be int)
        discount_percent: Discount percentage (0, 5, 10, or 15)
        
    Returns:
        {
            "original_total": int,
            "final_total": int,
            "discount_percent": int,
            "has_discount": bool
        }
        
    Raises:
        ValueError: If has_discount=True but original_total <= final_total
    """
    # Ensure integers
    original_total = int(original_total or 0)
    discount_percent = int(discount_percent or 0)
    
    # Clamp discount to valid range
    if discount_percent < 0:
        discount_percent = 0
    if discount_percent > 15:
        discount_percent = 15
    
    # Calculate final
    has_discount = discount_percent > 0
    final_total = int(round(original_total * (100 - discount_percent) / 100.0))
    
    # 🛡️ GUARD: If has_discount, original MUST be > final
    if has_discount and not (original_total > final_total):
        raise ValueError(f"Invalid discount: original={original_total}, final={final_total}, pct={discount_percent}")
    
    # Recalculate has_discount based on actual values
    has_discount = discount_percent > 0 and original_total > final_total
    
    return {
        "original_total": original_total,
        "final_total": final_total,
        "discount_percent": discount_percent,
        "has_discount": has_discount,
    }


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
            "original_total": int,      # Original price (before discount)
            "final_total": int,         # Final price (after discount)
            "discount_percent": int,    # Discount percentage
            "has_discount": bool,       # Has discount flag
            "card_id": str | None       # Card ID for tracking
        }
        
    Raises:
        ValueError: If has_discount=True but original_total <= final_total (invalid state)
    """
    p = appt.get("pricing") or {}
    
    # Get discount percentage
    discount_percent = int(p.get("discount_percent") or appt.get("discount_percentage") or 0)
    
    # Get has_discount flag
    has_discount = bool(p.get("has_discount") or appt.get("has_discount")) and discount_percent > 0
    
    # Get card_id
    card_id = p.get("card_id") or appt.get("card_id")
    
    # 🔒 PREFER PRICING OBJECT KEYS (original_total, final_total)
    original_total = p.get("original_total")
    final_total = p.get("final_total")
    
    # Fallback to top-level fields if pricing object doesn't have them
    if original_total is None:
        original_total = appt.get("original_total") or appt.get("original_price")
    if final_total is None:
        final_total = appt.get("final_total") or appt.get("total") or appt.get("total_price")
    
    # 🧮 REVERSE CALCULATION: Only if original is missing but we have discount
    if original_total is None and has_discount and final_total is not None and discount_percent > 0:
        # original = final / (1 - discount/100)
        original_total = int(round(final_total / (1 - discount_percent / 100)))
    
    # Convert to int if present
    if original_total is not None:
        original_total = int(original_total)
    if final_total is not None:
        final_total = int(final_total)
    
    # If no original, use final as fallback
    if original_total is None and final_total is not None:
        original_total = final_total
    
    # If no final, use original as fallback
    if final_total is None and original_total is not None:
        final_total = original_total
    
    # Default to 0 if still None
    original_total = original_total or 0
    final_total = final_total or 0
    
    # Recalculate has_discount based on actual values
    has_discount = discount_percent > 0 and original_total > final_total
    
    # 🛡️ FINAL GUARD: Prevent invalid pricing state
    if has_discount and original_total <= final_total:
        logger.error(f"🚨 INVALID_PRICING: original({original_total}) <= final({final_total}) with discount {discount_percent}%")
        # Instead of raising, fix the state
        has_discount = False
    
    return {
        "original_total": original_total,
        "final_total": final_total,
        "discount_percent": discount_percent,
        "has_discount": has_discount,
        "card_id": card_id
    }


def create_pricing_snapshot(
    original_total: int,
    discount_percent: int = 0,
    card_id: str = None,
    reason: str = None
) -> Dict:
    """
    🔒 Create STANDARDIZED pricing snapshot for DB storage.
    
    Uses compute_pricing as the single source of truth.
    
    Args:
        original_total: Original price before discount
        discount_percent: Discount percentage (0, 5, 10, or 15)
        card_id: Card ID for tracking
        reason: Reason for snapshot (e.g., "SPA_RITUAL_BOOKING")
        
    Returns:
        Standardized pricing snapshot dict with:
        - original_total
        - final_total
        - discount_percent
        - has_discount
        - card_id
        - reason
    """
    # Use compute_pricing as single source of truth
    pricing = compute_pricing(original_total, discount_percent)
    
    # Add metadata
    pricing["card_id"] = card_id
    pricing["reason"] = reason
    pricing["snapshot_at"] = None  # Will be set to ISO timestamp when saved
    
    return pricing


def format_pricing_for_display(pricing: Dict) -> str:
    """
    Format pricing dict for display in logs/debug.
    """
    original = pricing.get("original_total") or pricing.get("original_price") or 0
    final = pricing.get("final_total") or pricing.get("final_price") or 0
    discount = pricing.get("discount_percent") or pricing.get("discount_percentage") or 0
    has = pricing.get("has_discount") or False
    
    if has:
        return f"<s>{original:,}</s> RSD → {final:,} RSD (-{discount}%)"
    else:
        return f"{final or original:,} RSD"

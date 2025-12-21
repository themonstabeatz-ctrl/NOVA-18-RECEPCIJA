"""
💰 DISCOUNT ENGINE - Unified discount handling for SPA and MASSAGE
Single source of truth for all discount calculations.

USES pricing_utils.compute_pricing as THE SINGLE SOURCE OF TRUTH.
"""

import logging
from typing import List, Dict, Optional, Any
from pricing_utils import compute_pricing

logger = logging.getLogger(__name__)


def apply_best_discount(original_price: int, discounts: List[Dict]) -> Dict:
    """
    Apply the BEST (highest) discount from a list.
    NEVER call this twice on the same object!
    
    Args:
        original_price: Original price in RSD (must be integer)
        discounts: List of discount dicts: [{"id": "SPA10", "percent": 10, "active": True}, ...]
    
    Returns:
        {
            "discount_percent": int,
            "discount_amount": int,
            "final_price": int,
            "discount_id": str | None,
            "has_discount": bool
        }
    """
    # Filter active discounts only
    active = [d for d in discounts if d.get("active", True)]
    
    if not active:
        return {
            "discount_percent": 0,
            "discount_amount": 0,
            "final_price": int(original_price),
            "discount_id": None,
            "has_discount": False
        }
    
    # Get the BEST (highest percent) discount
    best = max(active, key=lambda d: int(d.get("percent", 0)))
    pct = int(best.get("percent", 0))
    
    if pct <= 0:
        return {
            "discount_percent": 0,
            "discount_amount": 0,
            "final_price": int(original_price),
            "discount_id": None,
            "has_discount": False
        }
    
    # Use compute_pricing as single source of truth
    pricing = compute_pricing(int(original_price), pct)
    
    return {
        "discount_percent": pricing["discount_percent"],
        "discount_amount": pricing["original_total"] - pricing["final_total"],
        "final_price": pricing["final_total"],
        "discount_id": best.get("id"),
        "has_discount": pricing["has_discount"]
    }


def apply_spa_discount_v2(
    original_total: int, 
    discount_percent: float = 0,
    discount_id: str = None
) -> Dict:
    """
    Apply SPA discount with validation.
    Valid discounts: 0%, 5%, 10%, 15%
    
    Returns pricing dict with STANDARDIZED field names:
    - original_total
    - final_total
    - discount_percent
    - has_discount
    """
    # Validate discount percentage
    valid_discounts = [0, 5, 10, 15]
    if int(discount_percent) not in valid_discounts:
        # Use highest valid discount <= requested
        discount_percent = max([d for d in valid_discounts if d <= int(discount_percent)], default=0)
    
    # Use compute_pricing as single source of truth
    pricing = compute_pricing(int(original_total), int(discount_percent))
    
    discount_amount = pricing["original_total"] - pricing["final_total"]
    
    # Log discount application
    if pricing["has_discount"]:
        logger.info(f"💰 DISCOUNT_APPLIED type=SPA original={pricing['original_total']} pct={pricing['discount_percent']} final={pricing['final_total']}")
    
    return {
        # 🔒 STANDARDIZED FIELD NAMES (PRIMARY)
        "original_total": pricing["original_total"],
        "final_total": pricing["final_total"],
        "discount_percent": pricing["discount_percent"],
        "discount_amount": discount_amount,
        "discount_id": discount_id,
        "has_discount": pricing["has_discount"],
        # 🔄 LEGACY ALIASES (for backward compatibility)
        "original_price": pricing["original_total"],
        "final_price": pricing["final_total"]
    }


def create_pricing_snapshot(
    original_total: int,
    discount_percent: float = 0,
    discount_id: str = None,
    reason: str = None
) -> Dict:
    """
    Create a pricing snapshot for storing in appointment.
    This snapshot is immutable - represents the price at booking time.
    
    Uses STANDARDIZED field names:
    - original_total
    - final_total
    - discount_percent
    - has_discount
    """
    pricing = apply_spa_discount_v2(original_total, discount_percent, discount_id)
    
    return {
        # 🔒 STANDARDIZED FIELD NAMES (PRIMARY)
        "original_total": pricing["original_total"],
        "final_total": pricing["final_total"],
        "discount_percent": pricing["discount_percent"],
        "discount_amount": pricing["discount_amount"],
        "has_discount": pricing["has_discount"],
        "discount_id": pricing["discount_id"],
        "discount_reason": reason,
        "snapshot_at": None,  # Will be set to ISO timestamp when saved
        # 🔄 LEGACY ALIASES (for backward compatibility)
        "original_price": pricing["original_total"],
        "final_price": pricing["final_total"]
    }


def enrich_service_with_discount(service: Dict, active_discount_percent: float = 0) -> Dict:
    """
    Add pricing fields to a service/package for listing endpoints.
    
    Input: service dict with 'price' field
    Output: service dict with added pricing fields
    """
    original_price = int(service.get("price", 0))
    
    pricing = apply_spa_discount_v2(
        original_total=original_price,
        discount_percent=active_discount_percent
    )
    
    return {
        **service,
        "original_price": pricing["original_total"],
        "discount_percent": pricing["discount_percent"],
        "discount_amount": pricing["discount_amount"],
        "final_price": pricing["final_total"],
        "has_discount": pricing["has_discount"]
    }


def format_price_for_display(amount: int) -> str:
    """Format price for display: 9200 -> '9.200 RSD'"""
    return f"{amount:,}".replace(",", ".") + " RSD"

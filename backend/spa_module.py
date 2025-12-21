"""
🧖 SPA MODULE - Completely separate from Massage/Couples
=========================================================
This module handles SPA services, quotes, and appointments.
DOES NOT interact with massage/couples logic.

Endpoints:
- GET /api/spa/services
- GET /api/spa/cards
- PATCH /api/spa/cards/{card_id}/discount
- POST /api/spa/quote
- POST /api/spa/card-quote
- POST /api/spa/appointments
- GET /api/spa/analytics
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import logging
import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import re

# Import discount engine
from discount_engine import apply_spa_discount_v2, create_pricing_snapshot, enrich_service_with_discount

logger = logging.getLogger(__name__)

# ============================================
# 🎴 SPA CARDS - Source of Truth for Card Discounts
# ============================================
# This is the ONLY place where card discounts are defined.
# Admin can update via PATCH /api/spa/cards/{card_id}/discount
# Quote and booking endpoints READ from here.

ALLOWED_CARD_DISCOUNTS = {0, 5, 10, 15}

SPA_CARDS = {
    "silky_body_ritual": {
        "title_sr": "Silky Body Ritual",
        "title_en": "Silky Body Ritual",
        "discount_percent": 0,
    },
    "gentle_touch_ritual": {
        "title_sr": "Gentle Touch Ritual",
        "title_en": "Gentle Touch Ritual",
        "discount_percent": 0,
    },
    "deep_renewal_ritual": {
        "title_sr": "Deep Renewal Ritual",
        "title_en": "Deep Renewal Ritual",
        "discount_percent": 0,
    },

    "silky_herbal_compress_ritual": {
        "title_sr": "Silky Herbal Compress Ritual",
        "title_en": "Silky Herbal Compress Ritual",
        "discount_percent": 0,
    },
    "thai_herbal_compress_ritual": {
        "title_sr": "Thai Herbal Compress Ritual",
        "title_en": "Thai Herbal Compress Ritual",
        "discount_percent": 0,
    },
    "aroma_stone_harmony_ritual": {
        "title_sr": "Aroma Stone Harmony Ritual",
        "title_en": "Aroma Stone Harmony Ritual",
        "discount_percent": 0,
    },

    "spa_zone": {
        "title_sr": "SPA Zone",
        "title_en": "SPA Zone",
        "discount_percent": 0,
    },

    "romantic_couple_package": {
        "title_sr": "Romantični paket za parove",
        "title_en": "Romantic Couple Package",
        "discount_percent": 0,
    },
    "romantic_peeling_couple_package": {
        "title_sr": "Romantični piling paket za parove",
        "title_en": "Romantic Peeling Couple Package",
        "discount_percent": 0,
    },
}

# ============================================
# SPA NOTES PARSER & NORMALIZER
# ============================================
def parse_spa_notes(notes: str) -> dict:
    """Parse SPA notes to extract structured data as fallback"""
    notes = notes or ""
    out = {
        "service_name": None,
        "service_description": "",
        "duration_min": None,
        "spa_zone": ""
    }
    
    # "SPA paket: Thai Herbal Compress Ritual"
    m = re.search(r"SPA paket:\s*([^\n\r]+?)(?:\s+Varijanta:|\s+SPA zona:|\s+Ukupno|\s+$)", notes)
    if m:
        out["service_name"] = m.group(1).strip()
    
    # "Varijanta: Sa masažom lica (+3.000 RSD)"
    m = re.search(r"Varijanta:\s*([^\n\r]+?)(?:\s+SPA zona:|\s+Ukupno|\s+$)", notes)
    if m:
        out["service_description"] = m.group(1).strip()
    
    # "Ukupno trajanje: 180 min"
    m = re.search(r"Ukupno trajanje:\s*(\d+)\s*min", notes)
    if m:
        out["duration_min"] = int(m.group(1))
    
    # "SPA zona: Sauna: 30 min - Parno kupatilo: 30 min - Jacuzzi: 60 min"
    m = re.search(r"SPA zona:\s*([^\n\r]+?)(?:\s+Ukupno|\s+$)", notes)
    if m:
        out["spa_zone"] = m.group(1).strip()
    
    return out


def normalize_spa_appt(appt: dict) -> dict:
    """
    Normalize SPA appointment - ensures ALL required fields are set.
    MUST be called before saving to DB and before returning response.
    """
    appt = appt or {}
    notes = appt.get("notes", "") or ""
    parsed = parse_spa_notes(notes)
    snap = appt.get("services_snapshot") or []
    snap0 = snap[0] if snap else {}
    
    # 1) service_name - NEVER null/empty
    if not appt.get("service_name") or appt.get("service_name") == "SPA":
        appt["service_name"] = (
            snap0.get("name")
            or parsed["service_name"]
            or "SPA Tretman"
        )
    
    # 2) service_description - can be empty string
    if not appt.get("service_description"):
        appt["service_description"] = (
            snap0.get("description")
            or parsed["service_description"]
            or ""
        )
    
    # 3) duration_min - NEVER null
    if not appt.get("duration_min"):
        appt["duration_min"] = (
            snap0.get("duration_min")
            or snap0.get("duration")
            or parsed["duration_min"]
        )
        # fallback: calculate from start/end
        if not appt["duration_min"]:
            try:
                st = appt.get("start_time")
                en = appt.get("end_time")
                if st and en:
                    if isinstance(st, str):
                        st = datetime.fromisoformat(st.replace("Z", ""))
                    if isinstance(en, str):
                        en = datetime.fromisoformat(en.replace("Z", ""))
                    appt["duration_min"] = int((en - st).total_seconds() / 60)
            except Exception:
                pass
        # ultimate fallback - NEVER N/A
        if not appt["duration_min"]:
            appt["duration_min"] = 120
    
    # 4) spa_zone - can be empty string
    if not appt.get("spa_zone"):
        appt["spa_zone"] = parsed["spa_zone"] or ""
    
    # 5) services_snapshot - ensure at least one entry
    if not snap:
        snap = [{
            "name": appt["service_name"],
            "description": appt["service_description"],
            "duration_min": appt["duration_min"],
            "duration": appt["duration_min"],
            "price": appt.get("final_total") or appt.get("price") or 0
        }]
        appt["services_snapshot"] = snap
    
    return appt


async def create_in_app_notification(db, appt: dict):
    """Create in-app notification for new SPA booking"""
    try:
        # Get pricing info
        pricing = appt.get('pricing', {})
        original_price = pricing.get('original_price') or appt.get('original_total', 0)
        discount_percent = pricing.get('discount_percent') or appt.get('discount_percentage', 0)
        final_price = pricing.get('final_price') or appt.get('final_total', 0)
        
        notification = {
            "id": str(uuid.uuid4()),
            "type": "spa_booking",
            "appointment_id": appt.get("id"),
            "title": f"Nova SPA rezervacija: {appt.get('service_name', 'SPA')}",
            "message": f"{appt.get('client_first_name', '')} {appt.get('client_last_name', '')} - {appt.get('service_name', 'SPA')}",
            "details": {
                "service_name": appt.get("service_name"),
                "duration_min": appt.get("duration_min"),
                "price": final_price,
                "original_price": original_price,
                "discount_percent": discount_percent,
                "has_discount": discount_percent > 0,
                "client_phone": appt.get("client_phone", ""),
                "start_time": appt.get("start_time")
            },
            "is_read": False,
            "created_at": datetime.now().isoformat()
        }
        await db.notifications.insert_one(notification)
        logger.info(f"📢 SPA IN-APP NOTIFICATION created for {appt.get('id')}")
        return True
    except Exception as e:
        logger.error(f"❌ SPA IN-APP NOTIFICATION failed: {e}")
        return False


# ============================================
# SPECIAL COUPLE PACKAGES (Romantični paketi)
# ============================================
SPECIAL_PACKAGES = {
    "ROMANTIC_COUPLE_1": {
        "name": "Romantični paket za parove",
        "duration": 210,
        "price": 25000,
        "description": "Savršen romantični doživljaj za dvoje"
    },
    "ROMANTIC_COUPLE_2": {
        "name": "Romantični piling paket za parove",
        "duration": 210,
        "price": 25000,
        "description": "Piling tretman za parove"
    }
}

# ============================================
# SPA Router
# ============================================
spa_router = APIRouter(prefix="/spa", tags=["SPA"])

# ============================================
# SPA Models
# ============================================
class SpaService(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str  # "spa_zone", "spa_ritual", "spa_special", "spa_addon"
    duration: int  # minutes
    price: int  # RSD - must end in 00
    description: Optional[str] = None
    booking_type: str = "ZAKAZITE"  # "ZAKAZITE" or "POZOVITE"
    created_at: datetime = Field(default_factory=datetime.now)
    # ADD-ON specific fields
    addon_group: Optional[str] = None  # "sauna", "steam", "jacuzzi", "face"
    applicable_to: Optional[List[str]] = None  # ["spa_ritual"]

class SpaQuoteRequest(BaseModel):
    service_ids: List[str] = []  # Legacy support
    discount_percentage: Optional[float] = 0  # DEPRECATED - use card_id instead
    # 🎴 CARD-LEVEL DISCOUNT - Source of truth
    card_id: Optional[str] = None  # e.g., "silky_body_ritual", "spa_zone"
    # Support for package + addons (SPA_RITUAL)
    spa_package_id: Optional[str] = None  # Main ritual/package ID
    spa_category: Optional[str] = None  # "spa_ritual", "spa_zone", etc.
    selected_addons: Optional[List[str]] = []  # List of addon IDs
    # Support for SPA_ZONE booking
    selected_zones: Optional[List[str]] = []  # List of zone service IDs
    # Support for HERBAL included zone
    included_spa_zone: Optional[str] = None  # "none", "SAUNA_15", "STEAM_15"

class SpaQuoteResponse(BaseModel):
    services: List[dict]
    original_total: int
    discount_percent: int  # Standardized name (was discount_percentage)
    discount_amount: int
    final_total: int
    has_discount: bool = False  # NEW
    card_id: Optional[str] = None  # NEW
    breakdown: str
    # NEW: Addon details
    base_price: Optional[int] = 0
    addon_price: Optional[int] = 0
    total_duration: Optional[int] = 0
    addons: Optional[List[dict]] = []

class SpaAppointmentCreate(BaseModel):
    client_first_name: str
    client_last_name: str
    client_phone: str
    client_email: Optional[str] = None
    service_ids: List[str] = []  # Legacy
    start_time: Optional[datetime] = None  # ISO format
    # Alternative date/time format from frontend
    appointment_date: Optional[str] = None  # "2025-12-31"
    appointment_time: Optional[str] = None  # "10:00"
    discount_percentage: Optional[float] = 0
    notes: Optional[str] = None
    # Package + addons support (SPA_RITUAL)
    spa_package_id: Optional[str] = None
    spa_category: Optional[str] = None
    spa_name: Optional[str] = None
    base_duration: Optional[int] = None
    base_price: Optional[int] = None
    selected_addons: Optional[List[str]] = []
    total_duration: Optional[int] = None
    total_original: Optional[int] = None
    final_price: Optional[int] = None
    # SPA_ZONE booking support
    selected_zones: Optional[List[str]] = []
    # SPA_SPECIAL_COUPLE support
    guests: Optional[int] = 2  # Number of guests for couple packages
    # HERBAL included zone
    included_spa_zone: Optional[str] = None
    # Auto-generated message
    message: Optional[str] = None
    total_original: Optional[int] = None
    final_price: Optional[int] = None

class SpaAppointment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_first_name: str
    client_last_name: str
    client_phone: str
    client_email: Optional[str] = None
    service_ids: List[str]
    services_snapshot: List[dict]
    start_time: datetime
    end_time: datetime
    original_total: int
    discount_percentage: float
    discount_amount: int
    final_total: int
    notes: Optional[str] = None
    status: str = "scheduled"
    created_at: datetime = Field(default_factory=datetime.now)
    # ADD-ONS tracking
    addons: List[dict] = []  # [{code, name, price}]
    addons_total: int = 0
    # SPA category for analytics
    spa_category: Optional[str] = None  # "spa_zone", "spa_ritual", "spa_special_couple"
    # Service name for display
    service_name: Optional[str] = None  # Primary service name for listing


# ============================================
# Card Discount Models (NEW)
# ============================================
class CardDiscountUpdate(BaseModel):
    """Update card discount for a SPA ritual/card"""
    card_discount_percent: int = Field(..., description="Card discount: 0, 5, 10, or 15%")


def apply_percent(amount: int, percent: int) -> int:
    """Apply percentage discount and return rounded integer (RSD)"""
    if percent <= 0:
        return int(amount)
    return int(round(amount * (100 - percent) / 100))


def get_card_discount(card_id: str) -> int:
    """Get card discount percent from SPA_CARDS source of truth"""
    if not card_id:
        return 0
    card = SPA_CARDS.get(card_id)
    if card:
        return int(card.get("discount_percent", 0))
    return 0


class CardQuoteRequest(BaseModel):
    """Request for card-level quote calculation"""
    card_id: str = Field(..., description="Card/ritual ID (e.g., 'silky_body_ritual')")
    base_service_id: str = Field(..., description="Base ritual service ID")
    variant_service_id: Optional[str] = Field(None, description="Variant service ID (e.g., Face Massage)")
    spa_zone: Optional[dict] = Field(default={}, description="SPA zone selections: {sauna_id, steam_id, jacuzzi_id}")


class CardQuoteResponse(BaseModel):
    """Response with card-level pricing"""
    card_id: str
    original_total: int
    discount_percent: int
    final_total: int
    has_discount: bool
    breakdown: dict  # {base, variant, spa_zone}


# ============================================
# SPA Price Lock (separate from massage)
# ============================================
def spa_price_lock_check(price: int, service_name: str) -> None:
    """SPA PRICE LOCK: All prices must end in 00"""
    if price % 100 != 0:
        raise HTTPException(
            status_code=400,
            detail=f"SPA PRICE LOCK: Price {price} RSD for '{service_name}' must end in 00."
        )

# ============================================
# SPA Discount Logic (separate from massage)
# ============================================
def apply_spa_discount(original_total: int, discount_pct: float) -> tuple:
    """
    Apply SPA discount. Supports 0%, 5%, 10%, 15%.
    Returns (discount_amount, final_total)
    """
    # Validate discount
    valid_discounts = [0, 5, 10, 15]
    if discount_pct not in valid_discounts:
        # Use highest valid discount <= requested
        discount_pct = max([d for d in valid_discounts if d <= discount_pct], default=0)
    
    discount_amount = int(round(original_total * discount_pct / 100))
    final_total = original_total - discount_amount
    
    return discount_amount, final_total, discount_pct

# ============================================
# Database reference (will be set from main server)
# ============================================
db = None
_dispatch_notifications = None  # Central dispatcher function

def set_db(database):
    global db
    db = database

def set_dispatcher(dispatcher_func):
    """Set the central notification dispatcher function from server.py"""
    global _dispatch_notifications
    _dispatch_notifications = dispatcher_func
    logger.info("✅ SPA module connected to central notification dispatcher")

# ============================================
# SPA Default Services Data
# ============================================
SPA_DEFAULT_SERVICES = [
    # ============================================
    # SPA ZONE (standalone) - tačne cene
    # ============================================
    {"name": "Sauna 15 min", "category": "spa_zone", "duration": 15, "price": 1400, "booking_type": "ZAKAZITE"},
    {"name": "Sauna 30 min", "category": "spa_zone", "duration": 30, "price": 2400, "booking_type": "ZAKAZITE"},
    {"name": "Parno kupatilo 15 min", "category": "spa_zone", "duration": 15, "price": 1400, "booking_type": "ZAKAZITE"},
    {"name": "Parno kupatilo 30 min", "category": "spa_zone", "duration": 30, "price": 2400, "booking_type": "ZAKAZITE"},
    {"name": "Jacuzzi 30 min", "category": "spa_zone", "duration": 30, "price": 2200, "booking_type": "ZAKAZITE"},
    {"name": "Jacuzzi 60 min", "category": "spa_zone", "duration": 60, "price": 3400, "booking_type": "ZAKAZITE"},
    
    # ============================================
    # SPA Rituali - tačni nazivi i cene sa websajta
    # ============================================
    {"name": "Silky Body Ritual", "category": "spa_ritual", "duration": 150, "price": 9200, "booking_type": "ZAKAZITE", "description": "Svilenkasto meko telo ritual"},
    {"name": "Gentle Touch Ritual", "category": "spa_ritual", "duration": 180, "price": 10400, "booking_type": "ZAKAZITE", "description": "Nežni dodir ritual"},
    {"name": "Deep Renewal Ritual", "category": "spa_ritual", "duration": 210, "price": 11600, "booking_type": "ZAKAZITE", "description": "Duboka obnova ritual"},
    {"name": "Silky Herbal Compress Ritual", "category": "spa_ritual", "duration": 120, "price": 7600, "booking_type": "ZAKAZITE", "description": "Svilenkasti biljni kompres ritual"},
    {"name": "Thai Herbal Compress Ritual", "category": "spa_ritual", "duration": 120, "price": 7600, "booking_type": "ZAKAZITE", "description": "Tajlandski biljni kompres ritual"},
    {"name": "Aroma Stone Harmony Ritual", "category": "spa_ritual", "duration": 120, "price": 7600, "booking_type": "ZAKAZITE", "description": "Aroma kamen harmonija ritual"},
    
    # ============================================
    # SPA Special - paketi za posebne prilike
    # ============================================
    {"name": "Romantični paket za parove", "category": "spa_special", "duration": 180, "price": 22000, "booking_type": "ZAKAZITE", "description": "Savršen romantični doživljaj za dvoje"},
    {"name": "Romantični piling paket za parove", "category": "spa_special", "duration": 150, "price": 19000, "booking_type": "ZAKAZITE", "description": "Piling tretman za parove"},
    {"name": "Devojačko veče & Lady Party", "category": "spa_special", "duration": 240, "price": 0, "booking_type": "POZOVITE", "description": "Za grupne rezervacije pozovite nas direktno"},
    
    # ============================================
    # SPA ADD-ONS (doplate uz ritual) - NOVE STAVKE
    # ============================================
    {"name": "Face Massage (ADD-ON)", "category": "spa_addon", "duration": 0, "price": 3000, "booking_type": "ZAKAZITE", "addon_group": "face", "applicable_to": ["spa_ritual"]},
    {"name": "Sauna +15 min (ADD-ON)", "category": "spa_addon", "duration": 15, "price": 800, "booking_type": "ZAKAZITE", "addon_group": "sauna", "applicable_to": ["spa_ritual"]},
    {"name": "Sauna +30 min (ADD-ON)", "category": "spa_addon", "duration": 30, "price": 1400, "booking_type": "ZAKAZITE", "addon_group": "sauna", "applicable_to": ["spa_ritual"]},
    {"name": "Parno kupatilo +15 min (ADD-ON)", "category": "spa_addon", "duration": 15, "price": 800, "booking_type": "ZAKAZITE", "addon_group": "steam", "applicable_to": ["spa_ritual"]},
    {"name": "Parno kupatilo +30 min (ADD-ON)", "category": "spa_addon", "duration": 30, "price": 1400, "booking_type": "ZAKAZITE", "addon_group": "steam", "applicable_to": ["spa_ritual"]},
    {"name": "Jacuzzi +30 min (ADD-ON)", "category": "spa_addon", "duration": 30, "price": 1400, "booking_type": "ZAKAZITE", "addon_group": "jacuzzi", "applicable_to": ["spa_ritual"]},
    {"name": "Jacuzzi +60 min (ADD-ON)", "category": "spa_addon", "duration": 60, "price": 2800, "booking_type": "ZAKAZITE", "addon_group": "jacuzzi", "applicable_to": ["spa_ritual"]},
]

# ============================================
# SPA Endpoints
# ============================================
@spa_router.get("/services")
async def get_spa_services(category: Optional[str] = None):
    """Get all SPA services, optionally filtered by category.
    
    Returns services with pricing fields:
    - original_price: Base price (never changes)
    - discount_percent: Active discount per service (0, 5, 10, 15)
    - final_price: Price after discount
    - has_discount: Boolean
    
    BACKEND IS SOURCE OF TRUTH - frontend never calculates prices.
    """
    query = {}
    if category:
        query["category"] = category
    
    services = await db.spa_services.find(query, {"_id": 0}).to_list(100)
    
    # If no services, initialize with defaults
    if not services:
        logger.info("SPA services empty, initializing with defaults...")
        for svc_data in SPA_DEFAULT_SERVICES:
            svc = SpaService(**svc_data)
            # Initialize with original_price = price, no discount
            svc_doc = svc.model_dump()
            svc_doc["original_price"] = svc_doc["price"]
            svc_doc["discount_percent"] = 0
            svc_doc["final_price"] = svc_doc["price"]
            svc_doc["has_discount"] = False
            await db.spa_services.insert_one(svc_doc)
        services = await db.spa_services.find(query, {"_id": 0}).to_list(100)
    
    # Enrich each service with pricing fields (from individual service discount)
    enriched_services = []
    for svc in services:
        # Get original price (first time? use price field)
        original_price = svc.get("original_price") or svc.get("price", 0)
        original_price = int(original_price)
        
        # Get discount from THIS service (not global)
        service_discount = svc.get("discount_percent", 0)
        
        # Calculate pricing using discount engine
        pricing = apply_spa_discount_v2(original_price, service_discount)
        
        enriched_services.append({
            **svc,
            "original_price": pricing["original_price"],
            "discount_percent": pricing["discount_percent"],
            "discount_amount": pricing["discount_amount"],
            "final_price": pricing["final_price"],
            "has_discount": pricing["has_discount"]
        })
    
    return enriched_services


@spa_router.patch("/services/{service_id}")
async def update_spa_service(service_id: str, payload: dict):
    """
    🔐 ADMIN ENDPOINT: Update SPA service fields (name, category, etc.)
    
    Used for:
    - Migrating services between categories
    - Renaming services
    - Updating any service field
    
    Preserves ID - no duplication!
    """
    existing = await db.spa_services.find_one({"id": service_id})
    if not existing:
        raise HTTPException(status_code=404, detail="SPA_SERVICE_NOT_FOUND")
    
    # Build update dict from allowed fields
    allowed_fields = ["name", "category", "price", "duration", "description", "booking_type"]
    updates = {}
    
    for field in allowed_fields:
        if field in payload and payload[field] is not None:
            value = payload[field]
            if isinstance(value, str):
                value = value.strip()
            updates[field] = value
    
    if not updates:
        raise HTTPException(status_code=400, detail="NO_VALID_FIELDS_TO_UPDATE")
    
    logger.info(f"🔄 SPA_SERVICE_UPDATE id={service_id} updates={updates}")
    
    await db.spa_services.update_one(
        {"id": service_id},
        {"$set": updates}
    )
    
    updated = await db.spa_services.find_one({"id": service_id}, {"_id": 0})
    
    # Return with pricing fields
    original_price = updated.get("original_price") or updated.get("price", 0)
    discount_pct = updated.get("discount_percent", 0)
    pricing = apply_spa_discount_v2(int(original_price), int(discount_pct))
    
    return {
        **updated,
        "original_price": pricing["original_price"],
        "discount_percent": pricing["discount_percent"],
        "final_price": pricing["final_price"],
        "has_discount": pricing["has_discount"]
    }


@spa_router.patch("/services/{service_id}/discount")
async def update_spa_service_discount(service_id: str, discount: int = Query(...)):
    """
    🔐 ADMIN ENDPOINT: Update discount for a SPA service.
    
    Allowed values: 0, 5, 10, 15
    Returns computed pricing fields: original_price, discount_percent, has_discount, final_price
    
    Usage: PATCH /api/spa/services/{service_id}/discount?discount=15
    """
    ALLOWED_DISCOUNTS = {0, 5, 10, 15}
    if discount not in ALLOWED_DISCOUNTS:
        raise HTTPException(status_code=400, detail=f"INVALID_DISCOUNT_PERCENT. Allowed: {ALLOWED_DISCOUNTS}")
    
    # Find service in spa_services collection
    existing = await db.spa_services.find_one({"id": service_id})
    if not existing:
        raise HTTPException(status_code=404, detail="SPA_SERVICE_NOT_FOUND")
    
    # Get original price - never loses the original
    original_price = existing.get("original_price") or existing.get("price", 0)
    original_price = int(original_price)
    
    # Calculate final price using discount engine
    pricing = apply_spa_discount_v2(original_price, discount)
    
    # Update service with discount
    update_data = {
        "original_price": original_price,
        "discount_percent": discount,
        "final_price": pricing["final_price"],
        "has_discount": discount > 0
    }
    
    logger.info(f"💸 SPA_DISCOUNT_APPLIED service_id={service_id} original={original_price} pct={discount} final={pricing['final_price']}")
    
    await db.spa_services.update_one(
        {"id": service_id},
        {"$set": update_data}
    )
    
    updated = await db.spa_services.find_one({"id": service_id}, {"_id": 0})
    
    # Return with computed pricing fields (admin UI expects these)
    return {
        "id": updated.get("id"),
        "name": updated.get("name"),
        "category": updated.get("category"),
        "duration": updated.get("duration"),
        "booking_type": updated.get("booking_type"),
        # Pricing fields (required by admin UI and frontend)
        "original_price": original_price,
        "discount_percent": discount,
        "has_discount": discount > 0,
        "final_price": pricing["final_price"],
        # Legacy field
        "price": pricing["final_price"]
    }


# ============================================
# 🎴 SPA Cards Admin API
# ============================================

@spa_router.get("/cards")
async def get_spa_cards():
    """
    📋 Get all SPA cards with their discount settings.
    
    Returns list of all cards from SPA_CARDS configuration.
    This is the source of truth for card-level discounts.
    """
    return [
        {
            "card_id": card_id,
            "title_sr": card_data["title_sr"],
            "title_en": card_data["title_en"],
            "discount_percent": card_data["discount_percent"],
            "has_discount": card_data["discount_percent"] > 0
        }
        for card_id, card_data in SPA_CARDS.items()
    ]


@spa_router.patch("/cards/{card_id}/discount")
async def update_card_discount(card_id: str, discount: int = Query(...)):
    """
    🔐 ADMIN ENDPOINT: Set card-level discount for a SPA card.
    
    This discount applies to the ENTIRE card total:
    - Base ritual price
    - Variant add-ons (e.g., Face Massage +3000)
    - SPA ZONE selections (sauna/steam/jacuzzi)
    
    Allowed values: 0, 5, 10, 15
    
    Usage: PATCH /api/spa/cards/silky_body_ritual/discount?discount=10
    """
    if card_id not in SPA_CARDS:
        raise HTTPException(status_code=404, detail="CARD_NOT_FOUND")
    
    if discount not in ALLOWED_CARD_DISCOUNTS:
        raise HTTPException(status_code=400, detail="INVALID_DISCOUNT_PERCENT")
    
    # Update the in-memory config (source of truth)
    SPA_CARDS[card_id]["discount_percent"] = discount
    
    logger.info(f"💳 CARD_DISCOUNT_SET card_id={card_id} title={SPA_CARDS[card_id]['title_sr']} discount={discount}%")
    
    return {
        "card_id": card_id,
        "discount_percent": discount,
        "has_discount": discount > 0
    }


@spa_router.post("/card-quote")
async def get_card_quote(request: CardQuoteRequest):
    """
    🧮 Calculate quote for a SPA CARD with all selections.
    
    Card discount comes from SPA_CARDS configuration (source of truth).
    Applied to the ENTIRE total:
    original_total = base + variant + spa_zone_sum
    final_total = original_total * (1 - card_discount_percent/100)
    
    Frontend sends service IDs, backend calculates everything.
    """
    
    # 1) Get card discount from SPA_CARDS (SOURCE OF TRUTH)
    card_config = SPA_CARDS.get(request.card_id)
    if not card_config:
        # Try to find by partial match
        for cid, cdata in SPA_CARDS.items():
            if cid in request.card_id or request.card_id in cid:
                card_config = cdata
                break
    
    card_discount = card_config["discount_percent"] if card_config else 0
    if card_discount not in ALLOWED_CARD_DISCOUNTS:
        card_discount = 0
    
    # 2) Get base service price
    base_service = await db.spa_services.find_one({"id": request.base_service_id}, {"_id": 0})
    if not base_service:
        raise HTTPException(status_code=404, detail="BASE_SERVICE_NOT_FOUND")
    
    base_price = int(base_service.get("original_price") or base_service.get("price", 0))
    base_name = base_service.get("name", "")
    
    # 3) Get variant price (if selected)
    variant_price = 0
    variant_name = None
    if request.variant_service_id:
        variant_service = await db.spa_services.find_one({"id": request.variant_service_id}, {"_id": 0})
        if variant_service:
            variant_price = int(variant_service.get("original_price") or variant_service.get("price", 0))
            variant_name = variant_service.get("name", "")
    
    # 4) Get SPA ZONE prices
    spa_zone_total = 0
    spa_zone_details = {}
    spa_zone = request.spa_zone or {}
    
    for zone_key in ["sauna_id", "sauna_service_id", "steam_id", "steam_service_id", "jacuzzi_id", "jacuzzi_service_id"]:
        zone_id = spa_zone.get(zone_key)
        if zone_id:
            zone_service = await db.spa_services.find_one({"id": zone_id}, {"_id": 0})
            if zone_service:
                zone_price = int(zone_service.get("original_price") or zone_service.get("price", 0))
                spa_zone_total += zone_price
                # Normalize key name
                normalized_key = zone_key.replace("_service_id", "").replace("_id", "")
                spa_zone_details[normalized_key] = {
                    "id": zone_id,
                    "name": zone_service.get("name"),
                    "price": zone_price
                }
    
    # 5) Calculate totals
    original_total = base_price + variant_price + spa_zone_total
    
    # 6) Apply card discount to ENTIRE total
    if card_discount > 0:
        final_total = int(round(original_total * (100 - card_discount) / 100))
    else:
        final_total = original_total
    
    discount_amount = original_total - final_total
    has_discount = card_discount > 0 and final_total < original_total
    
    logger.info(f"💳 CARD_QUOTE card_id={request.card_id} base={base_price} variant={variant_price} spa_zone={spa_zone_total} original={original_total} discount={card_discount}% final={final_total}")
    
    return {
        "card_id": request.card_id,
        "original_total": original_total,
        "discount_percent": card_discount,
        "discount_amount": discount_amount,
        "final_total": final_total,
        "has_discount": has_discount,
        "breakdown": {
            "base": {
                "name": base_name,
                "price": base_price
            },
            "variant": {
                "name": variant_name,
                "price": variant_price
            } if variant_name else None,
            "spa_zone": spa_zone_details if spa_zone_details else None,
            "spa_zone_total": spa_zone_total
        }
    }


@spa_router.post("/quote", response_model=SpaQuoteResponse)
async def get_spa_quote(request: SpaQuoteRequest):
    """Calculate SPA quote with optional discount and add-ons"""
    
    # ============================================
    # SPA_ZONE MODE: Standalone zone booking
    # ============================================
    if request.spa_category == "spa_zone" and request.selected_zones:
        # Fetch selected zones
        zones = await db.spa_services.find(
            {"id": {"$in": request.selected_zones}, "category": "spa_zone"},
            {"_id": 0}
        ).to_list(100)
        
        if not zones:
            raise HTTPException(status_code=404, detail="No SPA zones found")
        
        # Validate: max 1 per type (sauna, steam, jacuzzi)
        zone_types_used = {}
        for zone in zones:
            zone_name = zone["name"].lower()
            if "sauna" in zone_name:
                zone_type = "sauna"
            elif "parno" in zone_name:
                zone_type = "steam"
            elif "jacuzzi" in zone_name:
                zone_type = "jacuzzi"
            else:
                zone_type = "other"
            
            if zone_type != "other" and zone_type in zone_types_used:
                raise HTTPException(status_code=400, detail={
                    "error": "DUPLICATE_ZONE_TYPE",
                    "zone_type": zone_type,
                    "existing": zone_types_used[zone_type],
                    "duplicate": zone["name"],
                    "message": f"Možete izabrati samo jednu opciju za '{zone_type}'."
                })
            zone_types_used[zone_type] = zone["name"]
        
        # Calculate totals
        original_total = sum(z["price"] for z in zones)
        total_duration = sum(z["duration"] for z in zones)
        
        # 🎴 Apply CARD-LEVEL discount from SPA_CARDS
        card_id = request.card_id or "spa_zone"
        discount_pct = get_card_discount(card_id)
        final_total = apply_percent(original_total, discount_pct)
        discount_amount = original_total - final_total
        has_discount = discount_pct > 0 and final_total < original_total
        
        # Build breakdown
        zone_names = [f"{z['name']} ({z['price']} RSD)" for z in zones]
        breakdown = " + ".join(zone_names) + f" = {original_total} RSD"
        if discount_pct > 0:
            breakdown += f" - {discount_pct}% = {final_total} RSD"
        
        # Build message
        message = "SPA ZONA: " + ", ".join([z["name"] for z in zones])
        
        logger.info(f"💰 SPA_QUOTE (ZONE): card_id={card_id} zones={[z['name'] for z in zones]}, total={original_total}, discount={discount_pct}%, final={final_total}")
        
        return SpaQuoteResponse(
            services=[{"id": z["id"], "name": z["name"], "price": z["price"], "duration": z["duration"]} for z in zones],
            original_total=original_total,
            discount_percent=discount_pct,
            discount_amount=discount_amount,
            final_total=final_total,
            has_discount=has_discount,
            card_id=card_id,
            breakdown=breakdown,
            total_duration=total_duration,
            base_price=original_total,
            addon_price=0,
            addons=[]
        )
    
    # ============================================
    # HERBAL MODE: Included SPA zone (no extra charge)
    # ============================================
    if request.spa_package_id and request.included_spa_zone and request.included_spa_zone != "none":
        # Fetch main package (herbal)
        package = await db.spa_services.find_one({"id": request.spa_package_id}, {"_id": 0})
        if not package:
            raise HTTPException(status_code=404, detail=f"SPA package {request.spa_package_id} not found")
        
        # Determine included zone name
        included_zone_name = ""
        if request.included_spa_zone == "SAUNA_15":
            included_zone_name = "Sauna 15 min"
        elif request.included_spa_zone == "STEAM_15":
            included_zone_name = "Parno kupatilo 15 min"
        
        base_price = package["price"]
        base_duration = package["duration"]
        
        # No extra charge for included zone
        original_total = base_price
        total_duration = base_duration  # Duration stays same for herbal
        
        # 🎴 Apply CARD-LEVEL discount from SPA_CARDS
        card_id = request.card_id
        discount_pct = get_card_discount(card_id)
        final_total = apply_percent(original_total, discount_pct)
        discount_amount = original_total - final_total
        has_discount = discount_pct > 0 and final_total < original_total
        
        # Build breakdown with included zone note
        breakdown = f"{package['name']} ({base_price} RSD) + SPA zona (uključeno: {included_zone_name}) = {original_total} RSD"
        if discount_pct > 0:
            breakdown += f" - {discount_pct}% = {final_total} RSD"
        
        logger.info(f"💰 SPA_QUOTE (HERBAL+ZONE): card_id={card_id} package={package['name']}, included_zone={included_zone_name}, total={original_total}, discount={discount_pct}%")
        
        return SpaQuoteResponse(
            services=[{"id": package["id"], "name": package["name"], "price": package["price"], "duration": package["duration"]}],
            original_total=original_total,
            discount_percent=discount_pct,
            discount_amount=discount_amount,
            final_total=final_total,
            has_discount=has_discount,
            card_id=card_id,
            breakdown=breakdown,
            total_duration=total_duration,
            base_price=base_price,
            addon_price=0,
            addons=[{"name": f"SPA zona (uključeno): {included_zone_name}", "price": 0, "duration": 0}] if included_zone_name else []
        )
    
    # ============================================
    # RITUAL + Addons mode
    # ============================================
    if request.spa_package_id:
        # Fetch main package
        package = await db.spa_services.find_one({"id": request.spa_package_id}, {"_id": 0})
        if not package:
            raise HTTPException(status_code=404, detail=f"SPA package {request.spa_package_id} not found")
        
        # Check POZOVITE
        if package.get("booking_type") == "POZOVITE":
            raise HTTPException(status_code=400, detail={
                "error": "POZOVITE_SERVICE",
                "service_name": package["name"],
                "message": f"Usluga '{package['name']}' nije dostupna za online rezervaciju. Molimo pozovite nas direktno."
            })
        
        base_price = package["price"]
        base_duration = package["duration"]
        package_category = package.get("category", "")
        
        # Fetch addons
        addons = []
        addon_price = 0
        addon_duration = 0
        addon_groups_used = {}  # Track which groups are used
        
        if request.selected_addons:
            addon_services = await db.spa_services.find(
                {"id": {"$in": request.selected_addons}, "category": "spa_addon"},
                {"_id": 0}
            ).to_list(100)
            
            for addon in addon_services:
                # Validate addon is applicable to this category
                applicable_to = addon.get("applicable_to", [])
                if applicable_to and package_category not in applicable_to:
                    raise HTTPException(status_code=400, detail={
                        "error": "ADDON_NOT_APPLICABLE",
                        "addon_name": addon["name"],
                        "package_category": package_category,
                        "message": f"Add-on '{addon['name']}' nije primenjiv na kategoriju '{package_category}'"
                    })
                
                # Validate no duplicate groups (sauna, steam, jacuzzi)
                addon_group = addon.get("addon_group", "")
                if addon_group and addon_group != "face":  # Face can be only 0 or 1
                    if addon_group in addon_groups_used:
                        raise HTTPException(status_code=400, detail={
                            "error": "DUPLICATE_ADDON_GROUP",
                            "addon_group": addon_group,
                            "existing": addon_groups_used[addon_group],
                            "duplicate": addon["name"],
                            "message": f"Ne možete odabrati više od jednog add-on-a iz grupe '{addon_group}'. Već ste izabrali '{addon_groups_used[addon_group]}'."
                        })
                    addon_groups_used[addon_group] = addon["name"]
                
                addons.append(addon)
                addon_price += addon["price"]
                addon_duration += addon["duration"]
        
        # Calculate totals
        original_total = base_price + addon_price
        total_duration = base_duration + addon_duration
        
        # 🎴 Apply CARD-LEVEL discount from SPA_CARDS
        card_id = request.card_id
        discount_pct = get_card_discount(card_id)
        final_total = apply_percent(original_total, discount_pct)
        discount_amount = original_total - final_total
        has_discount = discount_pct > 0 and final_total < original_total
        
        # Build breakdown
        breakdown_parts = [f"{package['name']} ({base_price} RSD)"]
        for addon in addons:
            breakdown_parts.append(f"+{addon['name']} ({addon['price']} RSD)")
        breakdown = " ".join(breakdown_parts) + f" = {original_total} RSD"
        if discount_pct > 0:
            breakdown += f" - {discount_pct}% = {final_total} RSD"
        
        logger.info(f"💰 SPA_QUOTE (PACKAGE+ADDONS): card_id={card_id} base={base_price}, addon={addon_price}, total={original_total}, discount={discount_pct}%, final={final_total}, duration={total_duration}")
        
        return SpaQuoteResponse(
            services=[{"id": package["id"], "name": package["name"], "price": package["price"], "duration": package["duration"]}],
            original_total=original_total,
            discount_percent=discount_pct,
            discount_amount=discount_amount,
            final_total=final_total,
            has_discount=has_discount,
            card_id=card_id,
            breakdown=breakdown,
            base_price=base_price,
            addon_price=addon_price,
            total_duration=total_duration,
            addons=[{"id": a["id"], "name": a["name"], "price": a["price"], "duration": a["duration"]} for a in addons]
        )
    
    # ============================================
    # LEGACY: Simple service_ids mode
    # ============================================
    services = await db.spa_services.find(
        {"id": {"$in": request.service_ids}}, 
        {"_id": 0}
    ).to_list(100)
    
    if not services:
        raise HTTPException(status_code=404, detail="No SPA services found")
    
    # Check for POZOVITE services
    for svc in services:
        if svc.get("booking_type") == "POZOVITE":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "POZOVITE_SERVICE",
                    "service_name": svc["name"],
                    "message": f"Usluga '{svc['name']}' nije dostupna za online rezervaciju. Molimo pozovite nas direktno."
                }
            )
    
    # Calculate original total
    original_total = sum(svc["price"] for svc in services)
    total_duration = sum(svc["duration"] for svc in services)
    
    # SPA PRICE LOCK check
    if original_total % 100 != 0:
        logger.error(f"SPA PRICE LOCK FAILED: original_total={original_total}")
        raise HTTPException(
            status_code=400,
            detail=f"SPA PRICE LOCK: Total {original_total} RSD must end in 00."
        )
    
    # 🎴 Apply CARD-LEVEL discount from SPA_CARDS
    card_id = request.card_id
    discount_pct = get_card_discount(card_id)
    final_total = apply_percent(original_total, discount_pct)
    discount_amount = original_total - final_total
    has_discount = discount_pct > 0 and final_total < original_total
    
    # Build breakdown
    service_names = [f"{svc['name']} ({svc['price']} RSD)" for svc in services]
    breakdown = " + ".join(service_names) + f" = {original_total} RSD"
    if discount_pct > 0:
        breakdown += f" - {discount_pct}% = {final_total} RSD"
    
    logger.info(f"💰 SPA_QUOTE: card_id={card_id} original={original_total}, discount={discount_pct}%, final={final_total}")
    
    return SpaQuoteResponse(
        services=[{"id": s["id"], "name": s["name"], "price": s["price"], "duration": s["duration"]} for s in services],
        original_total=original_total,
        discount_percentage=applied_discount,
        discount_amount=discount_amount,
        final_total=final_total,
        total_duration=total_duration,
        breakdown=breakdown
    )

@spa_router.post("/appointments")
async def create_spa_appointment(appointment: SpaAppointmentCreate):
    """Create a SPA appointment - supports multiple formats including special couple packages"""
    
    # 🔒 VALIDATION: client_email is REQUIRED for SPA booking
    if not appointment.client_email or not appointment.client_email.strip():
        raise HTTPException(
            status_code=422, 
            detail="client_email is required for SPA booking. Please provide a valid email address."
        )
    
    # Parse start_time from various formats
    def get_start_time():
        if appointment.start_time:
            return appointment.start_time.replace(tzinfo=None) if appointment.start_time.tzinfo else appointment.start_time
        elif appointment.appointment_date and appointment.appointment_time:
            date_str = f"{appointment.appointment_date}T{appointment.appointment_time}:00"
            return datetime.fromisoformat(date_str)
        else:
            return datetime.now() + timedelta(days=1)
    
    # ============================================
    # SPECIAL COUPLE PACKAGES (Romantični paketi)
    # ============================================
    if appointment.spa_category == "spa_special_couple" and appointment.spa_package_id:
        if appointment.spa_package_id not in SPECIAL_PACKAGES:
            raise HTTPException(status_code=400, detail=f"Unknown special package: {appointment.spa_package_id}")
        
        pkg = SPECIAL_PACKAGES[appointment.spa_package_id]
        start_time = get_start_time()
        end_time = start_time + timedelta(minutes=pkg["duration"])
        
        # Apply discount using discount engine (SINGLE SOURCE OF TRUTH)
        original_total = pkg["price"]
        discount_pct = min(appointment.discount_percentage or 0, 15)
        pricing = apply_spa_discount_v2(original_total, discount_pct)
        
        # Create pricing snapshot for immutable record
        pricing_snapshot = create_pricing_snapshot(
            original_price=original_total,
            discount_percent=discount_pct,
            reason="SPA_SPECIAL_COUPLE_BOOKING"
        )
        pricing_snapshot["snapshot_at"] = datetime.now().isoformat()
        
        spa_apt = SpaAppointment(
            client_first_name=appointment.client_first_name,
            client_last_name=appointment.client_last_name,
            client_phone=appointment.client_phone,
            client_email=appointment.client_email,
            service_ids=[appointment.spa_package_id],
            services_snapshot=[{
                "id": appointment.spa_package_id,
                "name": pkg["name"],
                "price": pkg["price"],
                "duration": pkg["duration"],
                "duration_min": pkg["duration"],  # Explicit duration_min
                "description": pkg.get("description", f"Romantični paket za {appointment.guests or 2} osobe"),
                "category": "spa_special_couple"
            }],
            start_time=start_time,
            end_time=end_time,
            original_total=pricing["original_price"],
            discount_percentage=pricing["discount_percent"],
            discount_amount=pricing["discount_amount"],
            final_total=pricing["final_price"],
            notes=appointment.message or appointment.notes
        )
        
        # Save to database with spa_category
        doc = spa_apt.model_dump()
        doc['start_time'] = doc['start_time'].isoformat()
        doc['end_time'] = doc['end_time'].isoformat()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['spa_category'] = "spa_special_couple"
        doc['guests'] = appointment.guests or 2
        
        # 🔐 PRICING SNAPSHOT - immutable record of prices at booking time
        doc['pricing'] = pricing_snapshot
        
        # Add COMPLETE service data for listing (NO N/A allowed)
        doc['service_name'] = pkg['name']
        doc['service_description'] = pkg.get('description', f"Romantični paket za {appointment.guests or 2} osobe")
        doc['duration_min'] = pkg['duration']  # MUST have duration
        doc['addons'] = []
        doc['addons_total'] = 0
        doc['is_viewed'] = False  # For notification badge on dashboard
        
        # 1) INSERT into DB first
        await db.spa_appointments.insert_one(doc)
        
        # 2) NORMALIZE - ensure all fields are set
        doc = normalize_spa_appt(doc)
        
        # 3) UPDATE DB with normalized fields
        await db.spa_appointments.update_one(
            {"id": doc["id"]},
            {"$set": {
                "service_name": doc["service_name"],
                "service_description": doc["service_description"],
                "duration_min": doc["duration_min"],
                "spa_zone": doc.get("spa_zone", ""),
                "services_snapshot": doc["services_snapshot"]
            }}
        )
        
        # LOG: Appointment created with pricing snapshot
        logger.info(f"✅ SPA BOOKED id={doc['id']} name={doc['service_name']} email={appointment.client_email} pricing={pricing_snapshot}")
        
        # 4) SEND NOTIFICATIONS via CENTRAL DISPATCHER (same as massage)
        notify_result = {"email_sent": False, "notify_status": "pending", "notify_error": None}
        
        if _dispatch_notifications:
            notification_payload = {
                "type": "spa",
                "appointment_id": doc["id"],
                "service_name": doc["service_name"],
                "service_description": doc.get("service_description", ""),
                "duration_min": doc["duration_min"],
                "spa_zone": doc.get("spa_zone", ""),
                "start_time": doc.get("start_time"),
                "end_time": doc.get("end_time"),
                "price": doc.get("final_total", 0),
                "final_total": doc.get("final_total", 0),
                "client_first_name": doc.get("client_first_name", ""),
                "client_last_name": doc.get("client_last_name", ""),
                "client_email": doc.get("client_email", ""),
                "client_phone": doc.get("client_phone", "")
            }
            notify_result = await _dispatch_notifications(notification_payload)
        else:
            logger.warning("⚠️ Central dispatcher not available, using local email")
            try:
                email_sent = await send_spa_booking_email({**doc, "spa_category": "spa_special_couple"})
                await create_in_app_notification(db, doc)
                notify_result = {"email_sent": email_sent, "notify_status": "sent" if email_sent else "partial"}
            except Exception as e:
                notify_result = {"email_sent": False, "notify_status": "failed", "notify_error": str(e)[:200]}
        
        # 5) BUILD RESPONSE
        response = spa_apt.model_dump()
        response['email_sent'] = notify_result.get("email_sent", False)
        response['email_sent_admin'] = notify_result.get("email_sent_admin", False)
        response['email_sent_client'] = notify_result.get("email_sent_client", False)
        response['notification_created'] = notify_result.get("notification_created", False)
        response['email_error'] = notify_result.get("notify_error")
        response['notify_status'] = notify_result.get("notify_status", "unknown")
        response['warnings'] = [] if notify_result.get("notify_status") == "sent" else ["EMAIL_FAILED"]
        response['service_name'] = doc['service_name']
        response['service_description'] = doc['service_description']
        response['duration_min'] = doc['duration_min']
        response['spa_zone'] = doc.get('spa_zone', '')
        response['services_snapshot'] = doc['services_snapshot']
        
        return response
    
    # ============================================
    # REGULAR SPA BOOKINGS (Zone, Ritual, etc.)
    # ============================================
    
    # Determine which IDs to use based on what was provided
    service_ids_to_use = []
    
    # Priority 1: selected_zones for SPA_ZONE bookings
    if appointment.selected_zones:
        service_ids_to_use = appointment.selected_zones
    # Priority 2: spa_package_id for ritual bookings
    elif appointment.spa_package_id:
        service_ids_to_use = [appointment.spa_package_id]
        if appointment.selected_addons:
            service_ids_to_use.extend(appointment.selected_addons)
    
    # If still no IDs, try to create minimal appointment (for testing)
    if not service_ids_to_use:
        logger.warning("SPA appointment created without services - creating placeholder")
        # Create a minimal appointment without services
        start_time = get_start_time()
        
        spa_apt = SpaAppointment(
            client_first_name=appointment.client_first_name,
            client_last_name=appointment.client_last_name,
            client_phone=appointment.client_phone,
            client_email=appointment.client_email,
            service_ids=[],
            services_snapshot=[],
            start_time=start_time,
            end_time=start_time + timedelta(minutes=60),
            original_total=appointment.total_original or 0,
            discount_percentage=appointment.discount_percentage or 0,
            discount_amount=0,
            final_total=appointment.final_price or 0,
            notes=appointment.message or appointment.notes
        )
        
        doc = spa_apt.model_dump()
        doc['start_time'] = doc['start_time'].isoformat()
        doc['end_time'] = doc['end_time'].isoformat()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['spa_category'] = appointment.spa_category or 'spa_zone'
        doc['is_viewed'] = False  # For notification badge on dashboard
        
        # 1) INSERT into DB
        await db.spa_appointments.insert_one(doc)
        
        # 2) NORMALIZE - parse notes to get proper fields
        doc = normalize_spa_appt(doc)
        
        # 3) UPDATE DB with normalized fields
        await db.spa_appointments.update_one(
            {"id": doc["id"]},
            {"$set": {
                "service_name": doc["service_name"],
                "service_description": doc["service_description"],
                "duration_min": doc["duration_min"],
                "spa_zone": doc.get("spa_zone", ""),
                "services_snapshot": doc["services_snapshot"]
            }}
        )
        
        logger.info(f"✅ SPA BOOKED id={doc['id']} name={doc['service_name']} email={appointment.client_email} price={doc.get('final_total', 0)}")
        
        # 4) NOTIFICATIONS via CENTRAL DISPATCHER
        notify_result = {"email_sent": False, "notify_status": "pending"}
        if _dispatch_notifications:
            notification_payload = {
                "type": "spa",
                "appointment_id": doc["id"],
                "service_name": doc["service_name"],
                "service_description": doc.get("service_description", ""),
                "duration_min": doc["duration_min"],
                "spa_zone": doc.get("spa_zone", ""),
                "start_time": doc.get("start_time"),
                "end_time": doc.get("end_time"),
                "price": doc.get("final_total", 0),
                "final_total": doc.get("final_total", 0),
                "client_first_name": doc.get("client_first_name", ""),
                "client_last_name": doc.get("client_last_name", ""),
                "client_email": doc.get("client_email", ""),
                "client_phone": doc.get("client_phone", "")
            }
            notify_result = await _dispatch_notifications(notification_payload)
        else:
            try:
                email_sent = await send_spa_booking_email(doc)
                await create_in_app_notification(db, doc)
                notify_result = {"email_sent": email_sent, "notify_status": "sent" if email_sent else "partial"}
            except Exception as e:
                notify_result = {"email_sent": False, "notify_status": "failed"}
        
        # 5) RESPONSE
        response = spa_apt.model_dump()
        response['service_name'] = doc['service_name']
        response['service_description'] = doc['service_description']
        response['duration_min'] = doc['duration_min']
        response['spa_zone'] = doc.get('spa_zone', '')
        response['services_snapshot'] = doc['services_snapshot']
        response['notify_status'] = notify_result.get("notify_status", "unknown")
        response['email_sent'] = notify_result.get("email_sent", False)
        response['email_sent_admin'] = notify_result.get("email_sent_admin", False)
        response['email_sent_client'] = notify_result.get("email_sent_client", False)
        response['notification_created'] = notify_result.get("notification_created", False)
        
        return response
    
    # Fetch services
    services = await db.spa_services.find(
        {"id": {"$in": service_ids_to_use}}, 
        {"_id": 0}
    ).to_list(100)
    
    if not services:
        raise HTTPException(status_code=404, detail=f"No SPA services found for IDs: {service_ids_to_use}")
    
    # Check for POZOVITE services
    for svc in services:
        if svc.get("booking_type") == "POZOVITE":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "POZOVITE_SERVICE",
                    "service_name": svc["name"],
                    "message": f"Usluga '{svc['name']}' nije dostupna za online rezervaciju. Molimo pozovite nas direktno."
                }
            )
    
    # Calculate totals
    original_total = sum(svc["price"] for svc in services)
    total_duration = sum(svc["duration"] for svc in services)
    
    # Apply discount using discount engine (SINGLE SOURCE OF TRUTH)
    discount_pct = min(appointment.discount_percentage or 0, 15)
    pricing = apply_spa_discount_v2(original_total, discount_pct)
    
    # Create pricing snapshot for immutable record
    pricing_snapshot = create_pricing_snapshot(
        original_price=original_total,
        discount_percent=discount_pct,
        reason="SPA_ZONE_RITUAL_BOOKING"
    )
    pricing_snapshot["snapshot_at"] = datetime.now().isoformat()
    
    # Create COMPLETE snapshot with all required fields
    services_snapshot = [
        {
            "id": s["id"], 
            "name": s["name"], 
            "price": s["price"], 
            "duration": s["duration"],
            "duration_min": s["duration"],  # Explicit duration_min
            "description": s.get("description", ""),
            "category": s.get("category", "spa_zone")
        }
        for s in services
    ]
    
    # Calculate end time
    start_time = get_start_time()
    end_time = start_time + timedelta(minutes=total_duration)
    
    # Create appointment
    spa_apt = SpaAppointment(
        client_first_name=appointment.client_first_name,
        client_last_name=appointment.client_last_name,
        client_phone=appointment.client_phone,
        client_email=appointment.client_email,
        service_ids=appointment.service_ids,
        services_snapshot=services_snapshot,
        start_time=start_time,
        end_time=end_time,
        original_total=pricing["original_price"],
        discount_percentage=pricing["discount_percent"],
        discount_amount=pricing["discount_amount"],
        final_total=pricing["final_price"],
        notes=appointment.notes
    )
    
    # Save to database
    doc = spa_apt.model_dump()
    doc['start_time'] = doc['start_time'].isoformat()
    doc['end_time'] = doc['end_time'].isoformat()
    doc['created_at'] = doc['created_at'].isoformat()
    
    # Separate base services from addons
    base_services = [s for s in services if s.get('category') != 'spa_addon']
    addon_services = [s for s in services if s.get('category') == 'spa_addon']
    addons_list = [{"code": s.get('id'), "name": s.get('name'), "price": s.get('price', 0)} for s in addon_services]
    addons_total = sum(s.get('price', 0) for s in addon_services)
    
    # Add COMPLETE snapshot data to doc (NO N/A allowed)
    doc['addons'] = addons_list
    doc['addons_total'] = addons_total
    doc['spa_category'] = appointment.spa_category or 'spa_zone'
    
    # Service name - MUST be set (NO generic "SPA")
    primary_service = base_services[0] if base_services else (services[0] if services else None)
    doc['service_name'] = primary_service.get('name') if primary_service else 'SPA Tretman'
    
    # Service description - MUST be set
    doc['service_description'] = primary_service.get('description', '') if primary_service else ''
    if not doc['service_description'] and services_snapshot:
        # Build description from service names
        doc['service_description'] = ', '.join([s.get('name', '') for s in services_snapshot])
    
    # Duration in minutes - MUST be set (NO N/A)
    doc['duration_min'] = total_duration if total_duration > 0 else 120  # Default 120 min if not calculated
    doc['is_viewed'] = False  # For notification badge on dashboard
    
    # 💰 PRICING SNAPSHOT - Immutable record of price at booking time
    doc['pricing'] = pricing_snapshot
    
    # Log discount if applied
    if pricing["discount_percent"] > 0:
        logger.info(f"💰 DISCOUNT_APPLIED type=SPA item={doc['service_name']} pricing={pricing_snapshot}")
    
    # 1) INSERT into DB first
    await db.spa_appointments.insert_one(doc)
    
    # 2) NORMALIZE - ensure all fields are set (uses notes parsing as fallback)
    doc = normalize_spa_appt(doc)
    
    # 3) UPDATE DB with normalized fields (so they persist, not just in response!)
    await db.spa_appointments.update_one(
        {"id": doc["id"]},
        {"$set": {
            "service_name": doc["service_name"],
            "service_description": doc["service_description"],
            "duration_min": doc["duration_min"],
            "spa_zone": doc.get("spa_zone", ""),
            "services_snapshot": doc["services_snapshot"]
        }}
    )
    
    # LOG: Appointment created with normalized fields
    logger.info(f"✅ SPA BOOKED id={doc['id']} name={doc['service_name']} email={appointment.client_email} pricing={pricing_snapshot}")
    
    # 4) SEND NOTIFICATIONS via CENTRAL DISPATCHER (same as massage)
    notify_result = {"email_sent": False, "notify_status": "pending", "notify_error": None}
    
    if _dispatch_notifications:
        # Use SAME dispatcher as massage bookings
        notification_payload = {
            "type": "spa",
            "appointment_id": doc["id"],
            "service_name": doc["service_name"],
            "service_description": doc.get("service_description", ""),
            "duration_min": doc["duration_min"],
            "spa_zone": doc.get("spa_zone", ""),
            "start_time": doc.get("start_time"),
            "end_time": doc.get("end_time"),
            "price": doc.get("final_total", 0),
            "final_total": doc.get("final_total", 0),
            "client_first_name": doc.get("client_first_name", ""),
            "client_last_name": doc.get("client_last_name", ""),
            "client_email": doc.get("client_email", ""),
            "client_phone": doc.get("client_phone", "")
        }
        notify_result = await _dispatch_notifications(notification_payload)
    else:
        # Fallback: use local email function
        logger.warning("⚠️ Central dispatcher not available, using local email")
        try:
            email_sent = await send_spa_booking_email(doc)
            await create_in_app_notification(db, doc)
            notify_result = {"email_sent": email_sent, "notify_status": "sent" if email_sent else "partial"}
        except Exception as e:
            notify_result = {"email_sent": False, "notify_status": "failed", "notify_error": str(e)[:200]}
    
    # 5) BUILD RESPONSE with all normalized fields
    response = spa_apt.model_dump()
    response['email_sent'] = notify_result.get("email_sent", False)
    response['email_sent_admin'] = notify_result.get("email_sent_admin", False)
    response['email_sent_client'] = notify_result.get("email_sent_client", False)
    response['notification_created'] = notify_result.get("notification_created", False)
    response['email_error'] = notify_result.get("notify_error")
    response['notify_status'] = notify_result.get("notify_status", "unknown")
    response['warnings'] = [] if notify_result.get("notify_status") == "sent" else ["EMAIL_FAILED"]
    response['addons'] = addons_list
    response['addons_total'] = addons_total
    # Include normalized fields in response
    response['service_name'] = doc['service_name']
    response['service_description'] = doc['service_description']
    response['duration_min'] = doc['duration_min']
    response['spa_zone'] = doc.get('spa_zone', '')
    response['services_snapshot'] = doc['services_snapshot']
    
    return response

@spa_router.get("/appointments")
async def get_spa_appointments():
    """Get all SPA appointments"""
    appointments = await db.spa_appointments.find({}, {"_id": 0}).to_list(1000)
    return appointments

# ============================================
# SPA DELETE ENDPOINTS
# ============================================
@spa_router.delete("/appointments/{appointment_id}")
async def delete_spa_appointment(appointment_id: str):
    """Delete a single SPA appointment by ID"""
    result = await db.spa_appointments.delete_one({"id": appointment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"SPA appointment {appointment_id} not found")
    logger.info(f"🗑️ SPA appointment deleted: {appointment_id}")
    return {"message": "SPA appointment deleted", "id": appointment_id}

@spa_router.delete("/appointments/bulk")
async def delete_spa_appointments_bulk(
    from_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    to_date: Optional[str] = Query(None, description="End date YYYY-MM-DD")
):
    """Delete multiple SPA appointments within a date range"""
    query = {}
    if from_date:
        query["start_time"] = {"$gte": from_date}
    if to_date:
        if "start_time" in query:
            query["start_time"]["$lte"] = to_date + "T23:59:59"
        else:
            query["start_time"] = {"$lte": to_date + "T23:59:59"}
    
    result = await db.spa_appointments.delete_many(query)
    logger.info(f"🗑️ Bulk SPA delete: {result.deleted_count} appointments deleted")
    return {"message": f"Deleted {result.deleted_count} SPA appointments", "count": result.deleted_count}

# ============================================
# EMAIL SENDING FOR SPA BOOKINGS
# ============================================
async def send_spa_booking_email(appointment_data: dict):
    """Send email notification for SPA booking"""
    try:
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        owner_email = os.getenv("SMTP_TO_OWNER", os.getenv("OWNER_EMAIL", ""))
        
        if not all([smtp_user, smtp_password, owner_email]):
            logger.warning(f"Email credentials not configured (user={smtp_user}, owner={owner_email}), skipping SPA email")
            return False
        
        # Build email content
        client_name = f"{appointment_data.get('client_first_name', '')} {appointment_data.get('client_last_name', '')}"
        client_phone = appointment_data.get('client_phone', 'N/A')
        client_email = appointment_data.get('client_email', 'N/A')
        start_time = appointment_data.get('start_time', 'N/A')
        total = appointment_data.get('final_total', 0)
        services = appointment_data.get('services_snapshot', [])
        spa_category = appointment_data.get('spa_category', 'SPA')
        
        service_names = ", ".join([s.get('name', '') for s in services]) if services else spa_category
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
                <h2 style="color: #8B4513; text-align: center;">🧖 Nova SPA Rezervacija</h2>
                <hr style="border: 1px solid #ddd;">
                <p><strong>Klijent:</strong> {client_name}</p>
                <p><strong>Telefon:</strong> {client_phone}</p>
                <p><strong>Email:</strong> {client_email}</p>
                <p><strong>Datum/Vreme:</strong> {start_time}</p>
                <p><strong>Usluge:</strong> {service_names}</p>
                <p><strong>Ukupno:</strong> {total} RSD</p>
                <hr style="border: 1px solid #ddd;">
                <p style="text-align: center; color: #888;">Bu Aluang Thai Spa</p>
            </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🧖 Nova SPA rezervacija - {client_name}"
        msg["From"] = smtp_user
        msg["To"] = owner_email
        msg.attach(MIMEText(html_content, "html"))
        
        await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=smtp_port,
            start_tls=True,
            username=smtp_user,
            password=smtp_password
        )
        
        logger.info(f"📧 SPA booking email sent to {owner_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send SPA email: {e}")
        return False

# ============================================
# SPA ANALYTICS ENDPOINT
# ============================================
@spa_router.get("/analytics")
async def get_spa_analytics(
    from_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    to_date: Optional[str] = Query(None, description="End date YYYY-MM-DD")
):
    """Get SPA analytics including all categories.
    
    Returns:
        - totals.revenue_gross: sum(original_price) - Bruto zarada
        - totals.revenue_net: sum(final_price) - Neto zarada
        - totals.discount_total: sum(discount_amount) - Ukupni popusti
    """
    
    # Build date filter
    date_filter = {}
    if from_date:
        date_filter["$gte"] = from_date
    if to_date:
        date_filter["$lte"] = to_date + "T23:59:59"
    
    query = {}
    if date_filter:
        query["start_time"] = date_filter
    
    # Fetch all SPA appointments
    appointments = await db.spa_appointments.find(query, {"_id": 0}).to_list(10000)
    
    # Initialize counters
    totals = {
        "revenue": 0,           # legacy - same as revenue_net
        "revenue_net": 0,       # sum(final_price) - Za naplatu
        "revenue_gross": 0,     # sum(original_price) - Bruto
        "count": 0,
        "discount_total": 0     # sum(discount_amount)
    }
    
    breakdown = {
        "spa_zone": {"count": 0, "revenue": 0, "revenue_gross": 0},
        "spa_ritual": {"count": 0, "revenue": 0, "revenue_gross": 0},
        "spa_special_couple": {"count": 0, "revenue": 0, "revenue_gross": 0},
        "spa_addons": {"count": 0, "revenue": 0}
    }
    
    for apt in appointments:
        # Get pricing from snapshot or legacy fields
        pricing = apt.get("pricing", {})
        final_total = pricing.get("final_price") or apt.get("final_total", 0)
        original_total = pricing.get("original_price") or apt.get("original_total", final_total)
        discount_amount = pricing.get("discount_amount") or apt.get("discount_amount", 0)
        spa_category = apt.get("spa_category", "spa_zone")
        addons_total = apt.get("addons_total", 0)
        
        totals["revenue"] += final_total
        totals["revenue_net"] += final_total
        totals["revenue_gross"] += original_total
        totals["count"] += 1
        totals["discount_total"] += discount_amount
        
        # Track add-ons separately (from new addons field OR from services_snapshot)
        if addons_total > 0:
            breakdown["spa_addons"]["count"] += 1
            breakdown["spa_addons"]["revenue"] += addons_total
        else:
            # Legacy: Check services_snapshot for ADD-ON
            services = apt.get("services_snapshot", [])
            for svc in services:
                svc_name = svc.get("name", "")
                svc_category = svc.get("category", "")
                if "ADD-ON" in svc_name.upper() or svc_category == "spa_addon":
                    breakdown["spa_addons"]["count"] += 1
                    breakdown["spa_addons"]["revenue"] += svc.get("price", 0)
        
        # Categorize main appointment
        if spa_category == "spa_special_couple":
            breakdown["spa_special_couple"]["count"] += 1
            breakdown["spa_special_couple"]["revenue"] += final_total
            breakdown["spa_special_couple"]["revenue_gross"] += original_total
        elif spa_category == "spa_ritual":
            breakdown["spa_ritual"]["count"] += 1
            breakdown["spa_ritual"]["revenue"] += final_total
            breakdown["spa_ritual"]["revenue_gross"] += original_total
        else:
            breakdown["spa_zone"]["count"] += 1
            breakdown["spa_zone"]["revenue"] += final_total
            breakdown["spa_zone"]["revenue_gross"] += original_total
    
    logger.info(f"📊 SPA Analytics: {totals['count']} appointments, gross={totals['revenue_gross']}, net={totals['revenue_net']}, discounts={totals['discount_total']}")
    
    return {
        "totals": totals,
        "breakdown": breakdown,
        "appointments_count": len(appointments)
    }

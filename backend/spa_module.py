"""
🧖 SPA MODULE - Completely separate from Massage/Couples
=========================================================
This module handles SPA services, quotes, and appointments.
DOES NOT interact with massage/couples logic.

Endpoints:
- GET /api/spa/services
- POST /api/spa/quote
- POST /api/spa/appointments
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

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
    category: str  # "spa_zone", "spa_ritual", "spa_special"
    duration: int  # minutes
    price: int  # RSD - must end in 00
    description: Optional[str] = None
    booking_type: str = "ZAKAZITE"  # "ZAKAZITE" or "POZOVITE"
    created_at: datetime = Field(default_factory=datetime.now)

class SpaQuoteRequest(BaseModel):
    service_ids: List[str]  # Legacy support
    discount_percentage: Optional[float] = 0  # 0, 5, 10, or 15
    # NEW: Support for package + addons
    spa_package_id: Optional[str] = None  # Main ritual/package ID
    spa_category: Optional[str] = None  # "spa_ritual", "spa_zone", etc.
    selected_addons: Optional[List[str]] = []  # List of addon IDs

class SpaQuoteResponse(BaseModel):
    services: List[dict]
    original_total: int
    discount_percentage: float
    discount_amount: int
    final_total: int
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
    service_ids: List[str]  # Legacy
    start_time: datetime
    discount_percentage: Optional[float] = 0
    notes: Optional[str] = None
    # NEW: Package + addons support
    spa_package_id: Optional[str] = None
    spa_category: Optional[str] = None
    spa_name: Optional[str] = None
    base_duration: Optional[int] = None
    base_price: Optional[int] = None
    selected_addons: Optional[List[str]] = []
    total_duration: Optional[int] = None
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

def set_db(database):
    global db
    db = database

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
    """Get all SPA services, optionally filtered by category"""
    query = {}
    if category:
        query["category"] = category
    
    services = await db.spa_services.find(query, {"_id": 0}).to_list(100)
    
    # If no services, initialize with defaults
    if not services:
        logger.info("SPA services empty, initializing with defaults...")
        for svc_data in SPA_DEFAULT_SERVICES:
            svc = SpaService(**svc_data)
            await db.spa_services.insert_one(svc.model_dump())
        services = await db.spa_services.find(query, {"_id": 0}).to_list(100)
    
    return services

@spa_router.post("/quote", response_model=SpaQuoteResponse)
async def get_spa_quote(request: SpaQuoteRequest):
    """Calculate SPA quote with optional discount"""
    # Fetch requested services
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
    
    # SPA PRICE LOCK check
    if original_total % 100 != 0:
        logger.error(f"SPA PRICE LOCK FAILED: original_total={original_total}")
        raise HTTPException(
            status_code=400,
            detail=f"SPA PRICE LOCK: Total {original_total} RSD must end in 00."
        )
    
    # Apply discount (max 15%, only highest applies)
    discount_pct = min(request.discount_percentage or 0, 15)
    discount_amount, final_total, applied_discount = apply_spa_discount(original_total, discount_pct)
    
    # Build breakdown
    service_names = [f"{svc['name']} ({svc['price']} RSD)" for svc in services]
    breakdown = " + ".join(service_names) + f" = {original_total} RSD"
    if applied_discount > 0:
        breakdown += f" - {applied_discount}% = {final_total} RSD"
    
    logger.info(f"💰 SPA_QUOTE: original={original_total}, discount={applied_discount}%, final={final_total}")
    
    return SpaQuoteResponse(
        services=[{"id": s["id"], "name": s["name"], "price": s["price"], "duration": s["duration"]} for s in services],
        original_total=original_total,
        discount_percentage=applied_discount,
        discount_amount=discount_amount,
        final_total=final_total,
        breakdown=breakdown
    )

@spa_router.post("/appointments", response_model=SpaAppointment)
async def create_spa_appointment(appointment: SpaAppointmentCreate):
    """Create a SPA appointment"""
    # Fetch services
    services = await db.spa_services.find(
        {"id": {"$in": appointment.service_ids}}, 
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
    
    # Calculate totals
    original_total = sum(svc["price"] for svc in services)
    total_duration = sum(svc["duration"] for svc in services)
    
    # Apply discount
    discount_pct = min(appointment.discount_percentage or 0, 15)
    discount_amount, final_total, applied_discount = apply_spa_discount(original_total, discount_pct)
    
    # Create snapshot
    services_snapshot = [
        {"id": s["id"], "name": s["name"], "price": s["price"], "duration": s["duration"]}
        for s in services
    ]
    
    # Calculate end time
    start_time = appointment.start_time.replace(tzinfo=None) if appointment.start_time.tzinfo else appointment.start_time
    from datetime import timedelta
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
        original_total=original_total,
        discount_percentage=applied_discount,
        discount_amount=discount_amount,
        final_total=final_total,
        notes=appointment.notes
    )
    
    # Save to database
    doc = spa_apt.model_dump()
    doc['start_time'] = doc['start_time'].isoformat()
    doc['end_time'] = doc['end_time'].isoformat()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.spa_appointments.insert_one(doc)
    
    logger.info(f"✅ SPA Appointment created: {spa_apt.id}, total={final_total} RSD")
    
    return spa_apt

@spa_router.get("/appointments")
async def get_spa_appointments():
    """Get all SPA appointments"""
    appointments = await db.spa_appointments.find({}, {"_id": 0}).to_list(1000)
    return appointments

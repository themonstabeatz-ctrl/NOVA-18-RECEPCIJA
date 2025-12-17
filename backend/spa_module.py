"""
🧖 SPA MODULE - Completely separate from Massage/Couples
=========================================================
This module handles SPA services, quotes, and appointments.
DOES NOT interact with massage/couples logic.

Endpoints:
- GET /api/spa/services
- POST /api/spa/quote
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

logger = logging.getLogger(__name__)

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
    discount_percentage: Optional[float] = 0  # 0, 5, 10, or 15
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
        
        # Apply discount
        discount_pct = min(request.discount_percentage or 0, 15)
        discount_amount, final_total, applied_discount = apply_spa_discount(original_total, discount_pct)
        
        # Build breakdown
        zone_names = [f"{z['name']} ({z['price']} RSD)" for z in zones]
        breakdown = " + ".join(zone_names) + f" = {original_total} RSD"
        if applied_discount > 0:
            breakdown += f" - {applied_discount}% = {final_total} RSD"
        
        # Build message
        message = "SPA ZONA: " + ", ".join([z["name"] for z in zones])
        
        logger.info(f"💰 SPA_QUOTE (ZONE): zones={[z['name'] for z in zones]}, total={original_total}, duration={total_duration}")
        
        return SpaQuoteResponse(
            services=[{"id": z["id"], "name": z["name"], "price": z["price"], "duration": z["duration"]} for z in zones],
            original_total=original_total,
            discount_percentage=applied_discount,
            discount_amount=discount_amount,
            final_total=final_total,
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
        
        # Apply discount
        discount_pct = min(request.discount_percentage or 0, 15)
        discount_amount, final_total, applied_discount = apply_spa_discount(original_total, discount_pct)
        
        # Build breakdown with included zone note
        breakdown = f"{package['name']} ({base_price} RSD) + SPA zona (uključeno: {included_zone_name}) = {original_total} RSD"
        if applied_discount > 0:
            breakdown += f" - {applied_discount}% = {final_total} RSD"
        
        logger.info(f"💰 SPA_QUOTE (HERBAL+ZONE): package={package['name']}, included_zone={included_zone_name}, total={original_total}")
        
        return SpaQuoteResponse(
            services=[{"id": package["id"], "name": package["name"], "price": package["price"], "duration": package["duration"]}],
            original_total=original_total,
            discount_percentage=applied_discount,
            discount_amount=discount_amount,
            final_total=final_total,
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
        
        # Apply discount
        discount_pct = min(request.discount_percentage or 0, 15)
        discount_amount, final_total, applied_discount = apply_spa_discount(original_total, discount_pct)
        
        # Build breakdown
        breakdown_parts = [f"{package['name']} ({base_price} RSD)"]
        for addon in addons:
            breakdown_parts.append(f"+{addon['name']} ({addon['price']} RSD)")
        breakdown = " ".join(breakdown_parts) + f" = {original_total} RSD"
        if applied_discount > 0:
            breakdown += f" - {applied_discount}% = {final_total} RSD"
        
        logger.info(f"💰 SPA_QUOTE (PACKAGE+ADDONS): base={base_price}, addon={addon_price}, total={original_total}, discount={applied_discount}%, final={final_total}, duration={total_duration}")
        
        return SpaQuoteResponse(
            services=[{"id": package["id"], "name": package["name"], "price": package["price"], "duration": package["duration"]}],
            original_total=original_total,
            discount_percentage=applied_discount,
            discount_amount=discount_amount,
            final_total=final_total,
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
        total_duration=total_duration,
        breakdown=breakdown
    )

@spa_router.post("/appointments", response_model=SpaAppointment)
async def create_spa_appointment(appointment: SpaAppointmentCreate):
    """Create a SPA appointment - supports multiple formats"""
    
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
    # Priority 3: Legacy service_ids
    elif appointment.service_ids:
        service_ids_to_use = appointment.service_ids
    
    # Parse start_time from various formats
    from datetime import timedelta
    
    def get_start_time():
        if appointment.start_time:
            return appointment.start_time.replace(tzinfo=None) if appointment.start_time.tzinfo else appointment.start_time
        elif appointment.appointment_date and appointment.appointment_time:
            # Parse from separate date and time fields
            date_str = f"{appointment.appointment_date}T{appointment.appointment_time}:00"
            return datetime.fromisoformat(date_str)
        else:
            # Default to now + 1 day
            return datetime.now() + timedelta(days=1)
    
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
        
        await db.spa_appointments.insert_one(doc)
        logger.info(f"✅ SPA Appointment created (no services): {spa_apt.id}")
        return spa_apt
    
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
    
    # Apply discount
    discount_pct = min(appointment.discount_percentage or 0, 15)
    discount_amount, final_total, applied_discount = apply_spa_discount(original_total, discount_pct)
    
    # Create snapshot
    services_snapshot = [
        {"id": s["id"], "name": s["name"], "price": s["price"], "duration": s["duration"]}
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

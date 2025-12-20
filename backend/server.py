from fastapi import FastAPI, APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any, Union
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 🔒 LOCKDOWN IMPORT
from lockdown import assert_not_locked


# ============================================
# 🛡️ API ONLY MIDDLEWARE - BLOCKS STATIC FILES
# This ensures backend NEVER serves frontend assets
# ============================================
class ApiOnlyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 1) BLOCK STATIC FILES (critical for preventing frontend serving)
        if path.startswith("/static/") or path.startswith("/assets/"):
            return JSONResponse(
                {"ok": False, "error": "STATIC_DISABLED_ON_API_DOMAIN", "path": path},
                status_code=404
            )

        # 2) ALLOW only /api/* + / (root) + docs (optional)
        if path == "/" or path.startswith("/api/") or path.startswith("/docs") or path.startswith("/openapi"):
            return await call_next(request)

        # 3) BLOCK EVERYTHING ELSE (prevent SPA fallback)
        return JSONResponse(
            {"ok": False, "error": "API_ONLY_DOMAIN", "path": path},
            status_code=404
        )

# 🧖 SPA MODULE IMPORT (separate from massage)
from spa_module import spa_router, set_db as set_spa_db, set_dispatcher as set_spa_dispatcher


import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ============================================
# 🧖 SPA APPOINTMENT NORMALIZER
# Ensures ALL SPA appointments have ready-to-render fields
# ============================================
def _parse_notes_spa(notes: str) -> dict:
    """Parse SPA notes to extract structured data"""
    if not notes:
        return {"title": None, "variant": None, "total_min": None, "spa_zone": None}
    
    # Title: "SPA paket: Deep Renewal Ritual" (stop at Varijanta/SPA zona/Ukupno/newline)
    title = None
    m = re.search(r"SPA paket:\s*([^\n]+?)(?:\s+Varijanta:|\s+SPA zona:|\s+Ukupno trajanje:|\s+Ukupna cena:|$)", notes)
    if m:
        title = m.group(1).strip()
    
    # Variant: "Varijanta: Sa masažom lica (+3.000 RSD)" (stop at SPA zona/Ukupno/Ukupna/newline)
    variant = None
    m = re.search(r"Varijanta:\s*([^\n]+?)(?:\s+SPA zona:|\s+Ukupno trajanje:|\s+Ukupna cena:|$)", notes)
    if m:
        variant = m.group(1).strip()
    
    # Duration: "Ukupno trajanje: 210 min"
    total_min = None
    m = re.search(r"Ukupno trajanje:\s*(\d+)\s*min", notes)
    if m:
        total_min = int(m.group(1))
    
    # SPA Zone: "SPA zona: Sauna: 30 min - Parno: 30 min..." (stop at Ukupno)
    spa_zone = None
    m = re.search(r"SPA zona:\s*([^\n]+?)(?:\s+Ukupno trajanje:|\s+Ukupna cena:|$)", notes)
    if m:
        spa_zone = m.group(1).strip()
    
    return {"title": title, "variant": variant, "total_min": total_min, "spa_zone": spa_zone}


def normalize_spa_appt(appt: dict) -> dict:
    """
    Returns SPA appointment in unified frontend-friendly shape.
    MUST include: service_name, service_description, duration_min, type
    Backend delivers "ready-to-render" - frontend should NOT parse notes.
    """
    notes = appt.get("notes") or ""
    snap = appt.get("services_snapshot") or []
    snap0 = snap[0] if len(snap) else {}
    
    parsed = _parse_notes_spa(notes)
    
    # ============================================
    # SERVICE NAME - Priority order
    # ============================================
    service_name = (
        appt.get("service_name")
        or snap0.get("name")
        or parsed["title"]
    )
    # Fallback to category-based name if still empty or generic
    if not service_name or service_name == "SPA":
        category = appt.get("spa_category", "spa_zone")
        category_names = {
            "spa_zone": "SPA Zona Tretman",
            "spa_ritual": "SPA Ritual Tretman", 
            "spa_special_couple": "SPA Romantični Paket"
        }
        service_name = category_names.get(category, "SPA Tretman")
    
    # ============================================
    # SERVICE DESCRIPTION - Priority order
    # ============================================
    service_description = (
        appt.get("service_description")
        or snap0.get("description")
        or parsed["variant"]
        or ""
    )
    # Build description from services if still empty
    if not service_description and snap:
        service_description = ", ".join([s.get("name", "") for s in snap if s.get("name")])
    # Fallback: use service_name, NOT raw notes
    if not service_description:
        service_description = service_name
    
    # ============================================
    # DURATION - Priority order (NEVER N/A)
    # ============================================
    duration_min = (
        appt.get("duration_min")
        or snap0.get("duration_min")
        or snap0.get("duration")
        or parsed["total_min"]
    )
    # Sum from snapshot if available
    if not duration_min and snap:
        duration_min = sum(s.get("duration_min", s.get("duration", 0)) for s in snap)
    # Calculate from start/end times
    if not duration_min:
        try:
            start = appt.get("start_time")
            end = appt.get("end_time")
            if start and end:
                if isinstance(start, str):
                    start = datetime.fromisoformat(start.replace("Z", "+00:00"))
                if isinstance(end, str):
                    end = datetime.fromisoformat(end.replace("Z", "+00:00"))
                duration_min = int((end - start).total_seconds() / 60)
        except:
            pass
    # Ultimate fallback - NEVER return N/A
    if not duration_min or duration_min <= 0:
        duration_min = 120
    
    # ============================================
    # SPA ZONE breakdown
    # ============================================
    spa_zone = parsed["spa_zone"] or appt.get("spa_zone") or ""
    
    # Build unified output
    out = dict(appt)
    out["type"] = "spa"
    out["service_name"] = service_name
    out["service_description"] = service_description
    out["duration_min"] = int(duration_min)
    out["service_duration"] = int(duration_min)  # Alias for compatibility
    out["spa_zone"] = spa_zone
    
    # Add aliases for frontend compatibility
    out["service_title"] = service_name
    out["service_desc"] = service_description
    
    return out


# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize SPA module with database
set_spa_db(db)

# Create the main app without a prefix
app = FastAPI()

# 🛡️ ADD API ONLY MIDDLEWARE FIRST (before CORS)
app.add_middleware(ApiOnlyMiddleware)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# ============================================
# Enums
# ============================================
class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============================================
# Models - Therapists
# ============================================
class TherapistBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: bool = True

class TherapistCreate(TherapistBase):
    pass

class Therapist(TherapistBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now())


# ============================================
# Models - Services
# ============================================
class ServiceBase(BaseModel):
    name: str
    duration: int = Field(..., description="Duration in minutes: 15, 30, 45, 60, 90, 120, 150, 165, 180, 195, 210, 225, 240, 255, 270, 285, 300, 315, 330, 360, 420")
    price: float = Field(..., description="Price in RSD")
    description: Optional[str] = None
    category: Optional[str] = Field(default="regular", description="Service category: regular, couple")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata for couple appointments")
    discount_percentage: float = Field(default=0.0, ge=0, le=100, description="Active discount percentage (0-100%)")
    discount_amount: Optional[float] = Field(default=None, description="Discount amount in RSD")
    has_discount: Optional[bool] = Field(default=None, description="Flag for easier filtering")
    service_code: Optional[str] = Field(default=None, description="Unique service code for matching across categories")
    is_couple: bool = Field(default=False, description="True if this is a couple/[PAROVI] service")

class ServiceCreate(ServiceBase):
    pass

class Service(ServiceBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    final_price: Optional[float] = Field(default=None, description="Calculated price after discount")


# ============================================
# Models - Couple Settings
# ============================================
class CoupleSettings(BaseModel):
    discount_percentage: float = Field(default=15.0, ge=0, le=100, description="Discount for couple massages (0-100%)")

class CoupleSettingsUpdate(BaseModel):
    discount_percentage: float = Field(..., ge=0, le=100)


# ============================================
# Models - Appointments
# ============================================
class AppointmentBase(BaseModel):
    client_first_name: str
    client_last_name: str
    client_phone: str
    client_email: Optional[EmailStr] = None
    therapist_id: Optional[str] = None  # CHANGED: Optional - assigned manually by receptionist
    service_id: str
    start_time: datetime
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    body_map_gender: Optional[str] = None  # "male" or "female"
    body_map_points: Optional[List[Dict[str, Any]]] = []  # List of marked points

class AppointmentCreate(AppointmentBase):
    # Optional snapshot fields - if provided by websajt, use them directly
    # This prevents double calculation of discount (once in GET /api/services, once in POST)
    service_code: Optional[str] = None
    original_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    final_price: Optional[float] = None

class Appointment(AppointmentBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    end_time: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    is_viewed: bool = False  # Flag for notifications
    is_couples_booking: bool = False  # Flag for couples multi-service bookings
    # Snapshot fields for price history (prevents retroactive price changes)
    snapshot_price: Optional[float] = None
    snapshot_original_price: Optional[float] = None
    snapshot_discount_percentage: Optional[float] = None
    snapshot_discount_amount: Optional[float] = None
    # Couples multi-service snapshot (for listing display)
    person1_services_snapshot: Optional[List[Dict[str, Any]]] = None
    person2_services_snapshot: Optional[List[Dict[str, Any]]] = None
    pricing_breakdown: Optional[str] = None
    # Alias fields for frontend compatibility (duplicated from snapshot_ fields for JSON response)
    final_total: Optional[float] = None
    original_total: Optional[float] = None
    discount_percentage: Optional[float] = None  # Same as snapshot_discount_percentage
    discount_amount: Optional[float] = None  # Same as snapshot_discount_amount


# ============================================
# Models - Couple Appointments
# ============================================
class PersonMassage(BaseModel):
    massage_name: str
    massage_id: str
    duration: int
    price: float

class CoupleAppointmentCreate(BaseModel):
    client_first_name: str
    client_last_name: str
    client_phone: str
    client_email: Optional[EmailStr] = None
    therapist_id: Optional[str] = None  # CHANGED: Optional - assigned manually by receptionist
    start_time: datetime
    person1_massage: PersonMassage
    person2_massage: PersonMassage
    total_price_before_discount: float
    discount_couples_massage: float  # percentage
    total_price_after_discount: float
    status: AppointmentStatus = AppointmentStatus.SCHEDULED


# Old model for backward compatibility
class CoupleAppointmentCreateOld(BaseModel):
    client_first_name: str
    client_last_name: str
    client_phone: str
    client_email: Optional[EmailStr] = None
    therapist_id: Optional[str] = None  # CHANGED: Optional - assigned manually by receptionist
    start_time: datetime
    duration_type: int  # 60, 90, or 120 (base duration per person)
    person1_services: List[str]  # List of service IDs for person 1
    person2_services: List[str]  # List of service IDs for person 2
    discount_couples_massage: float = 0.0  # Added: percentage discount (default 0)
    status: AppointmentStatus = AppointmentStatus.SCHEDULED


# Service item for person1/person2 arrays in couple booking
class CoupleServiceItem(BaseModel):
    service_id: str
    name: str
    duration: int
    original_price: Optional[float] = None  # Optional - backend can fetch from DB
    final_price: Optional[float] = None  # Optional - backend can calculate

# Website compatible model - therapist_id is optional, assigned manually by receptionist later
class CoupleAppointmentWebsite(BaseModel):
    client_first_name: str
    client_last_name: str
    client_phone: str
    client_email: Optional[EmailStr] = None
    appointment_date: Optional[str] = None  # "2025-12-31" format
    start_time: datetime
    notes: Optional[str] = None
    
    # NEW FORMAT: person1/person2_services are now arrays of objects (not just IDs)
    # Support BOTH old format (List[str]) and new format (List[CoupleServiceItem])
    person1_services: Union[List[str], List[CoupleServiceItem]]
    person2_services: Union[List[str], List[CoupleServiceItem]]
    
    # Category and pricing snapshot (optional - backend can calculate from components)
    category: str = "Kartica masaza za parove"
    original_price: Optional[float] = None  # If not provided, backend calculates from components
    final_price: Optional[float] = None  # If not provided, backend calculates from components
    discount_percentage: Optional[float] = 0  # Default 0 if not provided
    discount_amount: Optional[float] = 0  # Default 0 if not provided
    is_couples_booking: bool = True
    
    # Old fields for backward compatibility (optional)
    duration_type: Optional[int] = None
    discount_couples_massage: Optional[float] = None


# ============================================
# Helper Functions - Service Type Detection
# ============================================
def is_couple_service(service_name: str) -> bool:
    """
    Check if service is a couple service based on [PAROVI] prefix
    This is the OFFICIAL identifier for couple services
    """
    return service_name.startswith("[PAROVI]") if service_name else False

def get_service_category_display(service_name: str, category: str = None) -> str:
    """
    Get display category for service based on name prefix
    [PAROVI] services → "Kartica Masaza za parove"
    All others → use provided category or default to "Obicne masaze"
    """
    if is_couple_service(service_name):
        return "Kartica Masaza za parove"
    return category if category else "Obicne masaze"


# ============================================
# Models - Business Hours
# ============================================
class BusinessHours(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    start_time: str = "10:00"  # HH:MM format
    end_time: str = "22:00"    # HH:MM format
    slot_duration: int = 30    # minutes

class BusinessHoursUpdate(BaseModel):
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    slot_duration: Optional[int] = None



# ============================================
# Helper Functions - Service Code & Discount Logic
# ============================================
def generate_service_code(name: str, duration: int, is_couple: bool = False) -> str:
    """
    Generate a unique service code from service name and duration.
    
    IMPORTANT: Single and Couple services have DIFFERENT service codes!
    This ensures they are treated as SEPARATE products.
    
    Example:
        "Aroma terapija - 60 min" (single) -> "AROMA_TERAPIJA_60"
        "[PAROVI] Aroma terapija - 60 min" (couple) -> "AROMA_TERAPIJA_60_COUPLE"
    
    Args:
        name: Service name
        duration: Duration in minutes
        is_couple: True if this is a couple/[PAROVI] service
    """
    import re
    import unicodedata
    
    # Check if this is a couple service from name
    is_couple_from_name = name.startswith('[PAROVI]')
    is_couple_service = is_couple or is_couple_from_name
    
    # Remove [PAROVI] prefix and other category prefixes
    clean_name = re.sub(r'^\[.*?\]\s*', '', name)
    
    # Remove duration suffix if present (e.g., "- 60 min", "- 90 min")
    clean_name = re.sub(r'\s*-?\s*\d+\s*min\s*$', '', clean_name, flags=re.IGNORECASE)
    
    # Normalize unicode characters (ć -> c, š -> s, etc.)
    clean_name = unicodedata.normalize('NFKD', clean_name)
    clean_name = clean_name.encode('ascii', 'ignore').decode('ascii')
    
    # Convert to uppercase and replace spaces/special chars with underscore
    clean_name = re.sub(r'[^a-zA-Z0-9]+', '_', clean_name.upper())
    
    # Remove leading/trailing underscores
    clean_name = clean_name.strip('_')
    
    # Add duration to make it unique
    service_code = f"{clean_name}_{duration}"
    
    # CRITICAL: Add _COUPLE suffix for couple services to separate them from single services
    if is_couple_service:
        service_code = f"{service_code}_COUPLE"
    
    return service_code


async def get_best_discount_for_service_code(service_code: str) -> dict:
    """
    Find all services with the same service_code and return the one with the highest discount.
    
    Returns:
        dict with keys: 
            - best_discount_percentage (float)
            - original_price (float)
            - service_id (str) - ID of the service with best discount
    """
    # Find all services with this service_code
    services = await db.services.find({"service_code": service_code}, {"_id": 0}).to_list(100)
    
    if not services or len(services) == 0:
        return {
            "best_discount_percentage": 0.0,
            "original_price": 0.0,
            "service_id": None
        }
    
    # Find the service with the highest discount
    try:
        best_service = max(services, key=lambda s: s.get('discount_percentage', 0.0) if s else 0.0)
    except (ValueError, TypeError) as e:
        # Handle empty list or None values in list
        logger.warning(f"Error finding max discount for service_code={service_code}: {e}")
        return {
            "best_discount_percentage": 0.0,
            "original_price": 0.0,
            "service_id": None
        }
    
    # Safety check - should never be None but just in case
    if best_service is None:
        logger.error(f"best_service is None for service_code={service_code}, services_count={len(services)}")
        return {
            "best_discount_percentage": 0.0,
            "original_price": 0.0,
            "service_id": None
        }
    
    if not isinstance(best_service, dict):
        logger.error(f"best_service is not dict: {type(best_service)} for service_code={service_code}")
        return {
            "best_discount_percentage": 0.0,
            "original_price": 0.0,
            "service_id": None
        }
    
    # IMPORTANT: service['price'] IS the original price (no need to check metadata)
    original_price = best_service.get('price', 0.0)
    
    return {
        "best_discount_percentage": best_service.get('discount_percentage', 0.0),
        "original_price": original_price,
        "service_id": best_service.get('id')
    }


async def calculate_discounted_price(service_code: str, base_price: float) -> dict:
    """
    Calculate the final price after applying the best available discount for a service_code.
    
    Returns:
        dict with keys:
            - final_price (float)
            - discount_percentage (float)
            - original_price (float)
    """
    discount_info = await get_best_discount_for_service_code(service_code)
    
    best_discount = discount_info['best_discount_percentage']
    original_price = discount_info['original_price'] if discount_info['original_price'] > 0 else base_price
    
    # Calculate final price with discount
    final_price = original_price * (1 - best_discount / 100.0)
    
    return {
        "final_price": round(final_price, 2),
        "discount_percentage": best_discount,
        "original_price": original_price
    }


# ============================================
# Routes - Health Check
# ============================================
@api_router.get("/health")
async def health_check():
    """Health check endpoint - always returns 200"""
    return {"status": "healthy"}

# ============================================
# Routes - Therapists
# ============================================
@api_router.post("/therapists", response_model=Therapist)
async def create_therapist(therapist: TherapistCreate):
    """Create a new therapist"""
    therapist_obj = Therapist(**therapist.model_dump())
    doc = therapist_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.therapists.insert_one(doc)
    return therapist_obj

@api_router.get("/therapists", response_model=List[Therapist])
async def get_therapists(active_only: bool = Query(False)):
    """Get all therapists"""
    query = {"is_active": True} if active_only else {}
    therapists = await db.therapists.find(query, {"_id": 0}).to_list(1000)
    
    for therapist in therapists:
        if isinstance(therapist['created_at'], str):
            therapist['created_at'] = datetime.fromisoformat(therapist['created_at'])
    
    return therapists

@api_router.get("/therapists/{therapist_id}", response_model=Therapist)
async def get_therapist(therapist_id: str):
    """Get a specific therapist"""
    therapist = await db.therapists.find_one({"id": therapist_id}, {"_id": 0})
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    if isinstance(therapist['created_at'], str):
        therapist['created_at'] = datetime.fromisoformat(therapist['created_at'])
    
    return therapist

@api_router.put("/therapists/{therapist_id}", response_model=Therapist)
async def update_therapist(therapist_id: str, therapist: TherapistCreate):
    """Update a therapist"""
    existing = await db.therapists.find_one({"id": therapist_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    update_data = therapist.model_dump()
    await db.therapists.update_one({"id": therapist_id}, {"$set": update_data})
    
    updated = await db.therapists.find_one({"id": therapist_id}, {"_id": 0})
    if isinstance(updated['created_at'], str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    
    return updated

@api_router.delete("/therapists/{therapist_id}")
async def delete_therapist(therapist_id: str):
    """Delete a therapist"""
    result = await db.therapists.delete_one({"id": therapist_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Therapist not found")
    return {"message": "Therapist deleted successfully"}

@api_router.get("/therapists/availability/status")
async def get_therapists_availability(date: Optional[str] = Query(None)):
    """Get therapist availability status for a specific date"""
    if date:
        try:
            target_date = datetime.fromisoformat(date)
        except:
            raise HTTPException(status_code=400, detail="Invalid date format")
    else:
        target_date = datetime.now(timezone.utc)
    
    # Get all active therapists
    therapists = await db.therapists.find({"is_active": True}, {"_id": 0}).to_list(1000)
    
    # Get appointments for the date
    start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    
    appointments = await db.appointments.find({
        "start_time": {
            "$gte": start_of_day.isoformat(),
            "$lt": end_of_day.isoformat()
        },
        "status": AppointmentStatus.SCHEDULED
    }, {"_id": 0}).to_list(1000)
    
    # Calculate availability
    availability = []
    for therapist in therapists:
        therapist_appointments = [apt for apt in appointments if apt['therapist_id'] == therapist['id']]
        availability.append({
            "therapist_id": therapist['id'],
            "therapist_name": therapist['name'],
            "is_busy": len(therapist_appointments) > 0,
            "appointments_count": len(therapist_appointments)
        })
    
    return availability


# ============================================
# Routes - Services
# ============================================
@api_router.post("/services", response_model=Service)
async def create_service(service: ServiceCreate):
    """Create a new service"""
    if service.duration not in [30, 45, 60, 90, 120, 180, 240]:
        raise HTTPException(status_code=400, detail="Duration must be 30, 45, 60, 90, 120, 180, or 240 minutes")
    
    service_obj = Service(**service.model_dump())
    
    # Auto-generate service_code if not provided
    if not service_obj.service_code:
        service_obj.service_code = generate_service_code(service_obj.name, service_obj.duration)
    
    # Ensure metadata has original_price
    if not service_obj.metadata:
        service_obj.metadata = {}
    if 'original_price' not in service_obj.metadata:
        service_obj.metadata['original_price'] = service_obj.price
    
    doc = service_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.services.insert_one(doc)
    return service_obj

@api_router.get("/services", response_model=List[Service])
async def get_services(service_type: Optional[str] = Query(None, description="Filter by type: 'single' or 'couple'")):
    """
    🔒 DO NOT MODIFY — STABLE SERVICE CALCULATION LOGIC (Bua Luang - BuaLuang-BACKEND-STABLE-01)
    
    Get all services with calculated final_price based on best available discount.
    For each service, the system finds all services with the same service_code
    and applies the highest discount percentage.
    
    Query parameters:
    - service_type: Filter services by type
      - 'single': Returns only single services (is_couple=False) - for "Obične masaže"
      - 'couple': Returns only couple services (is_couple=True) - for "Kartica Masaza za parove"
      - None: Returns all services
    
    🔒 STABLE ZONE: Ne menjati metadata.original_price/final_price logiku bez dozvole!
    """
    # Build query based on filter
    query = {}
    if service_type == "single":
        query["is_couple"] = False
    elif service_type == "couple":
        query["is_couple"] = True
    
    services = await db.services.find(query, {"_id": 0}).to_list(1000)
    
    # DEBUG: Log Aroma sa toplim biljnim kompresama services
    for svc in services:
        if svc and "Aroma sa toplim biljnim kompresama" in svc.get("name", ""):
            logger.info(f"[DEBUG] Aroma backend service BEFORE processing: {svc.get('name')} | duration={svc.get('duration')} | price={svc.get('price')} | discount={svc.get('discount_percentage')} | service_code={svc.get('service_code')} | metadata={svc.get('metadata')}")
    
    for service in services:
        # Safety check - skip None or invalid services
        if service is None or not isinstance(service, dict):
            logger.warning(f"Skipping invalid service: {service}")
            continue
            
        if isinstance(service.get('created_at'), str):
            service['created_at'] = datetime.fromisoformat(service['created_at'])
        
        # 🔒 DO NOT MODIFY — STABLE DISCOUNT CALCULATION LOGIC (Bua Luang)
        # Calculate final_price using ORIGINAL price (not current price which may be discounted)
        service_code = service.get('service_code')
        metadata = service.get('metadata') or {}
        
        # CRITICAL: Get ORIGINAL price, not current (potentially discounted) price
        # metadata.original_price is set when discount is first applied
        original_price = metadata.get('original_price') or service.get('price', 0)
        original_price = float(original_price)
        
        # Get discount from service record (set by PATCH /api/services/{id}/discount)
        discount_pct = service.get('discount_percentage', 0)
        
        # Calculate final price (NO service_code lookup - we use per-service discount)
        if discount_pct > 0:
            final_price = original_price * (1 - discount_pct / 100.0)
        else:
            final_price = original_price
        
        service['final_price'] = round(final_price, 2)
        service['discount_percentage'] = discount_pct
        # 🔒 END STABLE ZONE
    
    # DEBUG: Log Aroma sa toplim biljnim kompresama services AFTER processing
    for svc in services:
        if svc and "Aroma sa toplim biljnim kompresama" in svc.get("name", ""):
            logger.info(f"[DEBUG] Aroma backend service AFTER processing: {svc.get('name')} | duration={svc.get('duration')} | price={svc.get('price')} | final_price={svc.get('final_price')} | discount={svc.get('discount_percentage')} | service_code={svc.get('service_code')}")
    
    return services

@api_router.get("/services/couples/list", response_model=List[Service])
async def get_couple_services():
    """
    Get ONLY couple services ([PAROVI] from "Kartica Masaza za parove").
    This endpoint is specifically for the website's "Masaža za parove" card.
    
    Returns services where is_couple=True.
    """
    return await get_services(service_type="couple")

@api_router.get("/services/single/list", response_model=List[Service])
async def get_single_services():
    """
    Get ONLY single services (from "Obične masaže").
    This endpoint is specifically for the website's individual massage cards.
    
    Returns services where is_couple=False.
    """
    return await get_services(service_type="single")

@api_router.get("/services/{service_id}", response_model=Service)
async def get_service(service_id: str):
    """Get a specific service with calculated final_price"""
    service = await db.services.find_one({"id": service_id}, {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if isinstance(service['created_at'], str):
        service['created_at'] = datetime.fromisoformat(service['created_at'])
    
    # Calculate final_price using best discount logic
    service_code = service.get('service_code')
    metadata = service.get('metadata') or {}  # Handle None metadata
    if service_code:
        discount_info = await get_best_discount_for_service_code(service_code)
        original_price = metadata.get('original_price', service.get('price', 0))
        
        # Apply best discount
        best_discount = discount_info['best_discount_percentage']
        final_price = original_price * (1 - best_discount / 100.0)
        
        service['final_price'] = round(final_price, 2)
        service['discount_percentage'] = best_discount
    else:
        original_price = metadata.get('original_price', service.get('price', 0))
        discount = service.get('discount_percentage', 0)
        service['final_price'] = round(original_price * (1 - discount / 100.0), 2)
    
    return service

@api_router.put("/services/{service_id}", response_model=Service)
async def update_service(service_id: str, service: ServiceCreate):
    """Update a service"""
    if service.duration not in [30, 45, 60, 90, 120, 180, 240]:
        raise HTTPException(status_code=400, detail="Duration must be 30, 45, 60, 90, 120, 180, or 240 minutes")
    
    existing = await db.services.find_one({"id": service_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Service not found")
    
    update_data = service.model_dump()
    await db.services.update_one({"id": service_id}, {"$set": update_data})
    
    updated = await db.services.find_one({"id": service_id}, {"_id": 0})
    if isinstance(updated['created_at'], str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    
    return updated

@api_router.patch("/services/{service_id}/discount")
async def update_service_discount(service_id: str, discount: float):
    """Update discount percentage and automatically adjust price.
    
    Allowed values: 0, 5, 10, 15
    Returns computed pricing fields: original_price, discount_percent, has_discount, final_price
    """
    # Validate allowed discount percentages
    ALLOWED_DISCOUNTS = {0, 5, 10, 15}
    if int(discount) not in ALLOWED_DISCOUNTS:
        raise HTTPException(status_code=400, detail=f"INVALID_DISCOUNT_PERCENT. Allowed: {ALLOWED_DISCOUNTS}")
    
    existing = await db.services.find_one({"id": service_id})
    if not existing:
        raise HTTPException(status_code=404, detail="SERVICE_NOT_FOUND")
    
    # Get original price from metadata if it exists, otherwise use current price
    metadata = existing.get('metadata')
    if metadata and isinstance(metadata, dict) and 'original_price' in metadata:
        original_price = int(metadata['original_price'])
    else:
        # First time setting discount, save current price as original
        original_price = int(existing.get('price', 0))
    
    # Calculate new discounted price using centralized function
    discount_int = int(discount)
    if discount_int > 0:
        discount_amount = int(round(original_price * discount_int / 100))
        final_price = max(0, original_price - discount_amount)
        update_data = {
            "price": final_price,
            "discount_percentage": discount_int,
            "metadata": {
                "original_price": original_price,
                "discount_applied": discount_int,
                "final_price": final_price
            }
        }
    else:
        # No discount - restore original price
        final_price = original_price
        update_data = {
            "price": original_price,
            "discount_percentage": 0,
            "metadata": {
                "original_price": original_price,
                "discount_applied": 0,
                "final_price": original_price
            }
        }
    
    logger.info(f"💸 DISCOUNT_APPLIED type=SERVICE id={service_id} original={original_price} pct={discount_int} final={final_price}")
    
    await db.services.update_one(
        {"id": service_id}, 
        {"$set": update_data}
    )
    
    updated = await db.services.find_one({"id": service_id}, {"_id": 0})
    
    # Return with computed pricing fields (admin UI expects these)
    return {
        "id": updated.get("id"),
        "name": updated.get("name"),
        "duration": updated.get("duration"),
        "category": updated.get("category"),
        "description": updated.get("description"),
        "service_code": updated.get("service_code"),
        "is_couple": updated.get("is_couple", False),
        # Pricing fields (required by admin UI and frontend)
        "original_price": original_price,
        "discount_percent": discount_int,
        "has_discount": discount_int > 0,
        "final_price": final_price,
        # Legacy fields
        "price": final_price,
        "discount_percentage": discount_int,
        "metadata": updated.get("metadata")
    }

@api_router.delete("/services/{service_id}")
async def delete_service(service_id: str):
    """Delete a service"""
    result = await db.services.delete_one({"id": service_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"message": "Service deleted successfully"}


# ============================================
# Routes - Appointments
# ============================================

# 🔒🔒🔒 LOCKED ZONE START - SINGLE APPOINTMENT BOOKING 🔒🔒🔒
# DO NOT MODIFY WITHOUT EXPLICIT OWNER APPROVAL
# See: /app/LOCKDOWN_RULES.md
# Backend is the ONLY source of truth for prices and discounts
@api_router.post("/appointments", response_model=Appointment)
async def create_appointment(appointment: AppointmentCreate):
    """
    🔒 DO NOT MODIFY — STABLE BOOKING LOGIC (Bua Luang - BuaLuang-BACKEND-STABLE-01)
    
    Create a new appointment for single/couple massages
    
    🔒 STABLE PAYLOAD FIELDS - Do not remove or rename:
    - client_first_name
    - client_last_name
    - client_phone
    - client_email
    - start_time
    - service_id
    - therapist_id (optional - assigned by receptionist)
    - body_map_gender (optional)
    - body_map_points (optional)
    """
    # 🛡️ COUPLES PROTECTION: Block couples bookings on this endpoint
    # Couples MUST use /api/appointments/couple to get proper snapshot data
    raw_data = appointment.model_dump()
    
    # Check for couples indicators in payload
    is_couples_attempt = False
    couples_indicators = []
    
    if raw_data.get('booking_type') == 'COUPLES':
        is_couples_attempt = True
        couples_indicators.append('booking_type=COUPLES')
    
    if raw_data.get('person1_services') or raw_data.get('person2_services'):
        is_couples_attempt = True
        couples_indicators.append('person1/person2_services present')
    
    if raw_data.get('is_couples_booking') == True:
        is_couples_attempt = True
        couples_indicators.append('is_couples_booking=True')
    
    # Also check if selected service is a couples service
    service_check = await db.services.find_one({"id": appointment.service_id})
    if service_check:
        service_name = service_check.get('name', '').lower()
        service_category = service_check.get('category', '').lower()
        if 'parovi' in service_name or 'couple' in service_category or service_check.get('is_couple') == True:
            is_couples_attempt = True
            couples_indicators.append(f'service is couples: {service_check.get("name")}')
    
    if is_couples_attempt:
        logger.warning(f"🛡️ BLOCKED: Couples booking attempted on /api/appointments. Indicators: {couples_indicators}")
        raise HTTPException(
            status_code=400,
            detail="COUPLES bookings must use /api/appointments/couple endpoint to ensure proper snapshot data (person1_services_snapshot, person2_services_snapshot, pricing_breakdown)"
        )
    
    # Verify therapist exists (only if provided)
    if appointment.therapist_id:
        therapist = await db.therapists.find_one({"id": appointment.therapist_id})
        if not therapist:
            raise HTTPException(status_code=404, detail="Therapist not found")
    
    # Verify service exists and get duration
    service = await db.services.find_one({"id": appointment.service_id})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Remove timezone info if present to use naive datetime (local time)
    start_time = appointment.start_time.replace(tzinfo=None) if appointment.start_time.tzinfo else appointment.start_time
    
    # Calculate end time based on service duration
    end_time = start_time + timedelta(minutes=service['duration'])
    
    # Note: Overlap validation removed - multiple appointments can be scheduled at the same time
    # This allows multiple therapists and rooms to be utilized simultaneously
    
    # PRIORITY 1: Check if websajt sent snapshot data (Varijanta 1)
    # This prevents double calculation - discount is calculated only once in GET /api/services
    if appointment.final_price is not None and appointment.original_price is not None:
        # Websajt sent complete pricing snapshot - use it directly
        logger.info(f"📸 Using snapshot from websajt: original={appointment.original_price}, final={appointment.final_price}, discount={appointment.discount_percentage}%")
        final_price = appointment.final_price
        original_price = appointment.original_price
        best_discount = appointment.discount_percentage if appointment.discount_percentage is not None else 0.0
    else:
        # PRIORITY 2: Websajt sent only service_id (backward compatibility)
        # Calculate discount here (this is the "double calculation" scenario we want to avoid)
        logger.info(f"⚙️ Websajt didn't send snapshot - calculating discount from service_code")
        
        service_code = service.get('service_code')
        
        if service_code:
            # Find best discount for this service_code
            discount_info = await get_best_discount_for_service_code(service_code)
            best_discount = discount_info['best_discount_percentage']
            
            # Get original price from metadata
            service_metadata = service.get('metadata')
            if service_metadata and isinstance(service_metadata, dict) and 'original_price' in service_metadata:
                original_price = service_metadata['original_price']
            else:
                original_price = service.get('price', 0)
            
            # Calculate final price with best discount
            final_price = original_price * (1 - best_discount / 100.0)
        else:
            # Fallback to old logic if service_code doesn't exist
            service_price = service.get('price', 0)
            service_discount = service.get('discount_percentage', 0)
            
            service_metadata = service.get('metadata')
            if service_metadata and isinstance(service_metadata, dict) and 'original_price' in service_metadata:
                original_price = service_metadata['original_price']
            else:
                original_price = service_price
            
            best_discount = service_discount
            final_price = service_price
    
    # Create appointment object with corrected start_time and snapshot data
    appointment_dict = appointment.model_dump()
    appointment_dict['start_time'] = start_time
    appointment_dict['end_time'] = end_time
    # CRITICAL: Add snapshot fields to appointment object
    appointment_dict['snapshot_price'] = round(final_price, 2)
    appointment_dict['snapshot_original_price'] = original_price
    appointment_dict['snapshot_discount_percentage'] = best_discount
    appointment_obj = Appointment(**appointment_dict)
    
    doc = appointment_obj.model_dump()
    doc['start_time'] = doc['start_time'].isoformat()
    doc['end_time'] = doc['end_time'].isoformat()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.appointments.insert_one(doc)
    
    # Send email notifications (non-blocking)
    try:
        email_data = {
            'id': appointment_obj.id,  # Add appointment ID for logging
            'client_first_name': appointment_obj.client_first_name,
            'client_last_name': appointment_obj.client_last_name,
            'client_phone': appointment_obj.client_phone,
            'client_email': appointment_obj.client_email,
            'start_time': appointment_obj.start_time,
            'service_name': service.get('name', 'Unknown Service') if service else 'Unknown Service',
            'notes': ''
        }
        await send_booking_emails(email_data)
    except Exception as e:
        logger.error(f"Email notification failed (non-blocking): {e}")
    
    return appointment_obj
# 🔒🔒🔒 LOCKED ZONE END - SINGLE APPOINTMENT BOOKING 🔒🔒🔒


# ============================================
# Couple Settings Endpoints
# ============================================
@api_router.get("/settings/couple-discount")
async def get_couple_discount():
    """Get current couple massage discount percentage"""
    settings = await db.couple_settings.find_one({"_id": "default"})
    if not settings:
        # Return default 15%
        return {"discount_percentage": 15.0}
    return {"discount_percentage": settings.get("discount_percentage", 15.0)}

@api_router.put("/settings/couple-discount")
async def update_couple_discount(settings: CoupleSettingsUpdate):
    """Update couple massage discount percentage"""
    await db.couple_settings.update_one(
        {"_id": "default"},
        {"$set": {"discount_percentage": settings.discount_percentage}},
        upsert=True
    )
    return {"discount_percentage": settings.discount_percentage, "message": "Discount updated successfully"}

# ============================================
# Couple Appointments Endpoints
# ============================================
@api_router.post("/appointments/couple/v2", response_model=Appointment)
async def create_couple_appointment_v2(couple: CoupleAppointmentCreate):
    """Create a couple appointment with detailed person data and custom discount"""
    # 🔒 LOCKDOWN GUARD
    assert_not_locked()
    
    # Verify therapist exists ONLY if provided (therapist_id is OPTIONAL for online booking)
    therapist = None
    if couple.therapist_id:
        therapist = await db.therapists.find_one({"id": couple.therapist_id})
        if not therapist:
            raise HTTPException(status_code=404, detail="Therapist not found")
    
    # Remove timezone info if present
    start_time = couple.start_time.replace(tzinfo=None) if couple.start_time.tzinfo else couple.start_time
    
    # Calculate total duration - both persons are serviced simultaneously (parallel)
    # Duration is the MAX of the two (they finish when the longer one ends)
    total_duration = max(couple.person1_massage.duration, couple.person2_massage.duration)
    end_time = start_time + timedelta(minutes=total_duration)
    
    # Create service name description - total_duration IS the appointment duration
    service_name = f"Masaža za parove - {total_duration} min"
    service_description = f"Osoba 1: {couple.person1_massage.massage_name} ({couple.person1_massage.duration} min) | Osoba 2: {couple.person2_massage.massage_name} ({couple.person2_massage.duration} min)"
    
    if couple.discount_couples_massage > 0:
        service_name += f" - {couple.discount_couples_massage}% popust"
    
    # Create couple service
    couple_service_id = str(uuid.uuid4())
    couple_service = {
        "id": couple_service_id,
        "name": service_name,
        "duration": total_duration,
        "price": couple.total_price_after_discount,
        "description": service_description,
        "category": "couple",
        "created_at": datetime.now().isoformat(),
        "metadata": {
            "person1_massage_id": couple.person1_massage.massage_id,
            "person1_massage_name": couple.person1_massage.massage_name,
            "person1_duration": couple.person1_massage.duration,
            "person1_price": couple.person1_massage.price,
            "person2_massage_id": couple.person2_massage.massage_id,
            "person2_massage_name": couple.person2_massage.massage_name,
            "person2_duration": couple.person2_massage.duration,
            "person2_price": couple.person2_massage.price,
            "total_before_discount": couple.total_price_before_discount,
            "discount_percentage": couple.discount_couples_massage,
            "total_after_discount": couple.total_price_after_discount
        }
    }
    
    # Store couple service
    await db.services.insert_one(couple_service)
    
    # Create appointment with snapshot data
    appointment_dict = {
        "client_first_name": couple.client_first_name,
        "client_last_name": couple.client_last_name,
        "client_phone": couple.client_phone,
        "client_email": couple.client_email,
        "therapist_id": couple.therapist_id,
        "service_id": couple_service_id,
        "start_time": start_time,
        "end_time": end_time,
        "status": couple.status,
        "body_map_gender": None,
        "body_map_points": [],
        # CRITICAL: Add snapshot fields to appointment object
        "snapshot_price": couple.total_price_after_discount,
        "snapshot_original_price": couple.total_price_before_discount,
        "snapshot_discount_percentage": couple.discount_couples_massage
    }
    
    appointment_obj = Appointment(**appointment_dict)
    
    doc = appointment_obj.model_dump()
    doc['start_time'] = doc['start_time'].isoformat()
    doc['end_time'] = doc['end_time'].isoformat()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.appointments.insert_one(doc)
    return appointment_obj

@api_router.post("/appointments/couple", response_model=Appointment)
async def create_couple_appointment(couple: CoupleAppointmentCreateOld):
    """Create a couple appointment (OLD VERSION - backward compatibility, NOW WITH DISCOUNT SUPPORT)"""
    # 🔒 LOCKDOWN GUARD
    assert_not_locked()
    
    # Log incoming request for debugging
    logger.info(f"Couple appointment request - duration_type: {couple.duration_type}, person1_services: {couple.person1_services}, person2_services: {couple.person2_services}")
    logger.info(f"🔍 OLD ENDPOINT - DISCOUNT FROM WEBSITE: {couple.discount_couples_massage}%")
    
    # Verify therapist exists ONLY if provided (therapist_id is OPTIONAL for online booking)
    therapist = None
    if couple.therapist_id:
        therapist = await db.therapists.find_one({"id": couple.therapist_id})
        if not therapist:
            raise HTTPException(status_code=404, detail="Therapist not found")
    
    # Fetch all services for both persons
    all_service_ids = couple.person1_services + couple.person2_services
    services = await db.services.find({"id": {"$in": all_service_ids}}).to_list(100)
    service_map = {s['id']: s for s in services}
    
    # Verify all services exist
    for service_id in all_service_ids:
        if service_id not in service_map:
            raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
    
    # ============================================
    # 🔒 COUPLES VALIDATION - START
    # ============================================
    
    # A) Validate ALL services are [PAROVI] couples services
    for service_id in all_service_ids:
        svc = service_map[service_id]
        svc_name = svc.get('name', '')
        if not is_couple_service(svc_name):
            logger.error(f"🔒 INVALID_COUPLES_SERVICE: service_id={service_id}, name={svc_name}, is_parovi=False")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "INVALID_COUPLES_SERVICE",
                    "service_id": service_id,
                    "service_name": svc_name,
                    "message": f"Service '{svc_name}' is not a [PAROVI] couples service"
                }
            )
    
    # B) Normalize duration_type to int
    duration_type_int = int(couple.duration_type)
    if duration_type_int not in [60, 90, 120]:
        logger.error(f"🔒 INVALID_DURATION_TYPE: {duration_type_int}, must be 60/90/120")
        raise HTTPException(status_code=400, detail=f"Invalid duration_type: {duration_type_int}. Must be 60, 90, or 120.")
    
    # C) Calculate total duration per person
    p1_total_duration = sum(service_map[sid].get('duration', 0) for sid in couple.person1_services)
    p2_total_duration = sum(service_map[sid].get('duration', 0) for sid in couple.person2_services)
    
    # D) Debug log before validation
    p1_service_info = [(sid, service_map[sid].get('name'), service_map[sid].get('duration')) for sid in couple.person1_services]
    p2_service_info = [(sid, service_map[sid].get('name'), service_map[sid].get('duration')) for sid in couple.person2_services]
    logger.info(f"🔍 COUPLES DURATION VALIDATION:")
    logger.info(f"   duration_type={duration_type_int}")
    logger.info(f"   person1_services={p1_service_info}, total={p1_total_duration}")
    logger.info(f"   person2_services={p2_service_info}, total={p2_total_duration}")
    
    # E) Validate duration per person matches duration_type
    # Special rule for 120: allow [120] or [60,60]
    def is_valid_duration(total: int, services_count: int, durations: list) -> bool:
        if duration_type_int == 120:
            # Allow: single 120, or two 60s
            if total == 120:
                return True
            if len(durations) == 2 and all(d == 60 for d in durations):
                return True
            return False
        else:
            # For 60 and 90: must match exactly
            return total == duration_type_int
    
    p1_durations = [service_map[sid].get('duration', 0) for sid in couple.person1_services]
    p2_durations = [service_map[sid].get('duration', 0) for sid in couple.person2_services]
    
    if not is_valid_duration(p1_total_duration, len(couple.person1_services), p1_durations):
        logger.error(f"🔒 DURATION_MISMATCH person1: total={p1_total_duration}, expected={duration_type_int}, durations={p1_durations}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "DURATION_MISMATCH",
                "person": 1,
                "total_duration": p1_total_duration,
                "expected_duration": duration_type_int,
                "services": p1_service_info,
                "message": f"Person 1 services total {p1_total_duration} min, but duration_type is {duration_type_int} min"
            }
        )
    
    if not is_valid_duration(p2_total_duration, len(couple.person2_services), p2_durations):
        logger.error(f"🔒 DURATION_MISMATCH person2: total={p2_total_duration}, expected={duration_type_int}, durations={p2_durations}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "DURATION_MISMATCH",
                "person": 2,
                "total_duration": p2_total_duration,
                "expected_duration": duration_type_int,
                "services": p2_service_info,
                "message": f"Person 2 services total {p2_total_duration} min, but duration_type is {duration_type_int} min"
            }
        )
    
    logger.info(f"✅ COUPLES VALIDATION PASSED: duration_type={duration_type_int}, p1={p1_total_duration}, p2={p2_total_duration}")
    
    # ============================================
    # 🔒 COUPLES VALIDATION - END
    # ============================================
    
    # Calculate total price - use ORIGINAL prices from metadata if available
    # [PAROVI] services may have pre-discounted prices stored, so we need to get original_price from metadata
    original_total = 0
    person1_service_names = []
    person2_service_names = []
    
    for service_id in couple.person1_services:
        service = service_map[service_id]
        # Try to get original_price from metadata, otherwise use price field
        metadata = service.get('metadata') or {}
        svc_original_price = metadata.get('original_price', service['price'])
        original_total += svc_original_price
        person1_service_names.append(service['name'])
    
    for service_id in couple.person2_services:
        service = service_map[service_id]
        # Try to get original_price from metadata, otherwise use price field
        metadata = service.get('metadata') or {}
        svc_original_price = metadata.get('original_price', service['price'])
        original_total += svc_original_price
        person2_service_names.append(service['name'])
    
    # Round to integer RSD
    original_total = int(round(original_total))
    
    # Apply couple discount if provided (from request, not from service)
    discount_pct = couple.discount_couples_massage if couple.discount_couples_massage else 0.0
    
    # 🔒 PRICE LOCK: Validate ONLY original_total (before discount) ends in 00
    # Final price after discount does NOT need to end in 00
    if original_total % 100 != 0:
        logger.error(f"🔒 PRICE LOCK FAILED: original_total={original_total}, discount_pct={discount_pct}")
        raise HTTPException(
            status_code=400,
            detail=f"PRICE LOCK: Original total {original_total} RSD must end in 00. Check service prices."
        )
    
    # Calculate final price after discount
    final_total = int(round(original_total * (100 - discount_pct) / 100))
    
    # Debug log for price calculation
    logger.info(f"💰 COUPLES_PRICE_DEBUG: original_total={original_total}, discount_pct={discount_pct}, final_total={final_total}")
    
    # Note: final_total may not end in 00 (e.g., 11600 * 0.85 = 9860)
    # This is acceptable - only original_total must end in 00
    
    # Calculate total duration (both persons are serviced simultaneously - together at the same time)
    total_duration = couple.duration_type  # 60, 90, or 120 minutes (they go together, not one after another)
    
    # Remove timezone info if present
    start_time = couple.start_time.replace(tzinfo=None) if couple.start_time.tzinfo else couple.start_time
    end_time = start_time + timedelta(minutes=total_duration)
    
    # Create service name description - duration_type IS the total appointment duration
    service_name = f"Masaža za parove - {couple.duration_type} min"
    
    # Create a dummy service entry for couple package
    couple_service_id = str(uuid.uuid4())
    couple_service = {
        "id": couple_service_id,
        "name": service_name,
        "duration": total_duration,
        "price": final_total,  # STORE FINAL PRICE (after discount)
        "description": f"Osoba 1: {', '.join(person1_service_names)} | Osoba 2: {', '.join(person2_service_names)}",
        "created_at": datetime.now().isoformat(),
        "category": "couple",
        "discount_percentage": discount_pct,
        "metadata": {
            "original_price": original_total,
            "discount_applied": discount_pct,
            "final_price": final_total
        } if discount_pct > 0 else None
    }
    
    # Store couple service details
    await db.services.insert_one(couple_service)
    
    # Build person services snapshot
    person1_services_snapshot = []
    for service_id in couple.person1_services:
        svc = service_map[service_id]
        person1_services_snapshot.append({
            "id": service_id,
            "name": svc['name'],
            "duration": svc.get('duration', couple.duration_type),
            "price": svc['price']
        })
    
    person2_services_snapshot = []
    for service_id in couple.person2_services:
        svc = service_map[service_id]
        person2_services_snapshot.append({
            "id": service_id,
            "name": svc['name'],
            "duration": svc.get('duration', couple.duration_type),
            "price": svc['price']
        })
    
    # Calculate person totals for breakdown
    person1_total = sum(service_map[sid]['price'] for sid in couple.person1_services)
    person2_total = sum(service_map[sid]['price'] for sid in couple.person2_services)
    
    # Create appointment with couple service and snapshot data
    appointment_dict = {
        "client_first_name": couple.client_first_name,
        "client_last_name": couple.client_last_name,
        "client_phone": couple.client_phone,
        "client_email": couple.client_email,
        "therapist_id": couple.therapist_id,
        "service_id": couple_service_id,
        "start_time": start_time,
        "end_time": end_time,
        "status": couple.status,
        "body_map_gender": None,
        "body_map_points": [],
        "is_couples_booking": True,  # CRITICAL: Flag for couples booking
        # CRITICAL: Add snapshot fields to appointment object
        "snapshot_price": final_total,
        "snapshot_original_price": original_total,
        "snapshot_discount_percentage": discount_pct,
        "snapshot_discount_amount": original_total - final_total if discount_pct > 0 else 0,
        # ALIAS FIELDS for frontend compatibility
        "final_total": final_total,
        "original_total": original_total,
        "discount_percentage": discount_pct,
        "discount_amount": original_total - final_total if discount_pct > 0 else 0,
        # COUPLES MULTI-SERVICE SNAPSHOT: Store ALL selected services
        "person1_services_snapshot": person1_services_snapshot,
        "person2_services_snapshot": person2_services_snapshot,
        "pricing_breakdown": f"{person1_total} + {person2_total} = {original_total}"
    }
    
    appointment_obj = Appointment(**appointment_dict)
    
    doc = appointment_obj.model_dump()
    doc['start_time'] = doc['start_time'].isoformat()
    doc['end_time'] = doc['end_time'].isoformat()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.appointments.insert_one(doc)
    
    # Send email notification (non-blocking)
    try:
        notes_text = f"Osoba 1: {', '.join(person1_service_names)} | Osoba 2: {', '.join(person2_service_names)}"
        email_data = {
            'client_first_name': couple.client_first_name,
            'client_last_name': couple.client_last_name,
            'client_phone': couple.client_phone,
            'client_email': couple.client_email,
            'start_time': appointment_obj.start_time,
            'service_name': service_name,
            'notes': notes_text
        }
        await send_booking_emails(email_data)
    except Exception as e:
        logger.error(f"Email notification failed for couples booking (non-blocking): {e}")
    
    return appointment_obj


# 🔒🔒🔒 LOCKED ZONE START - COUPLES APPOINTMENT BOOKING 🔒🔒🔒
# DO NOT MODIFY WITHOUT EXPLICIT OWNER APPROVAL
# See: /app/LOCKDOWN_RULES.md
# Backend is the ONLY source of truth for prices and discounts
# Couples booking WITHOUT discount MUST have: discount_percentage = 0, final_price = original_price
@api_router.post("/book-couple-appointment", response_model=Appointment)
async def book_couple_appointment_website(couple: CoupleAppointmentWebsite):
    """
    🔒 LOCKED - Website-compatible couple appointment endpoint
    Therapist is NOT assigned here - receptionist assigns manually later
    
    ACCEPTS NEW FORMAT:
    - person1_services: [{ service_id, name, duration, original_price, final_price }]
    - person2_services: [{ service_id, name, duration, original_price, final_price }]
    - category, original_price, final_price, discount_percentage, discount_amount
    - NO recalculation - uses snapshot values from payload
    """
    # 🔒 LOCKDOWN GUARD
    assert_not_locked()
    
    # DEBUG LOGGING - Log complete payload for troubleshooting
    try:
        logger.info(f"📥 COUPLE BOOKING REQUEST RECEIVED")
        logger.info(f"   Client: {couple.client_first_name} {couple.client_last_name}")
        logger.info(f"   Phone: {couple.client_phone}")
        logger.info(f"   Category: {couple.category}")
        logger.info(f"   Original Price: {couple.original_price} RSD")
        logger.info(f"   Final Price: {couple.final_price} RSD")
        logger.info(f"   Discount: {couple.discount_percentage}%")
        logger.info(f"   Discount Amount: {couple.discount_amount} RSD")
        logger.info(f"   Person1 Services Count: {len(couple.person1_services) if couple.person1_services else 0}")
        logger.info(f"   Person2 Services Count: {len(couple.person2_services) if couple.person2_services else 0}")
    except Exception as e:
        logger.error(f"❌ Error logging request: {e}")
    
    # Wrap entire endpoint in try-except for detailed error reporting
    try:
        # Therapist will be assigned manually by receptionist later
        therapist_id = None
    
        # Extract service IDs (handle both old format List[str] and new format List[CoupleServiceItem])
        person1_service_ids = []
        person2_service_ids = []
        person1_service_names = []
        person2_service_names = []
        
        # Check if services are objects (new format) or just IDs (old format)
        if couple.person1_services and isinstance(couple.person1_services[0], CoupleServiceItem):
            # NEW FORMAT: Extract from objects
            person1_service_ids = [s.service_id for s in couple.person1_services]
            person1_service_names = [s.name for s in couple.person1_services]
        elif couple.person1_services and isinstance(couple.person1_services[0], str):
            # OLD FORMAT: Just IDs
            person1_service_ids = couple.person1_services
        
        if couple.person2_services and isinstance(couple.person2_services[0], CoupleServiceItem):
            # NEW FORMAT
            person2_service_ids = [s.service_id for s in couple.person2_services]
            person2_service_names = [s.name for s in couple.person2_services]
        elif couple.person2_services and isinstance(couple.person2_services[0], str):
            # OLD FORMAT
            person2_service_ids = couple.person2_services
        
        all_service_ids = person1_service_ids + person2_service_ids
        
        # Fetch services from DB (for validation and fallback)
        services = await db.services.find({"id": {"$in": all_service_ids}}, {"_id": 0}).to_list(100)
        service_map = {s['id']: s for s in services}
        
        # Verify all services exist
        for service_id in all_service_ids:
            if service_id not in service_map:
                error_msg = f"Service {service_id} not found in database"
                logger.error(f"❌ {error_msg}")
                raise HTTPException(status_code=404, detail=error_msg)
        
        # 🔒🔒🔒 CRITICAL LOCKED SECTION - STRICT PRICING RULES 🔒🔒🔒
        
        # --- STRICT VALIDATION: [PAROVI] PREFIX REQUIRED ---
        # All couples services MUST have [PAROVI] prefix
        # If not, this is a DATA ERROR and booking must fail
        
        logger.info(f"🔍 STRICT VALIDATION - Checking [PAROVI] prefix:")
        
        validation_errors = []
        
        # Validate Person1 services
        for sid in person1_service_ids:
            if sid in service_map:
                service_name = service_map[sid]['name']
                if not service_name.startswith('[PAROVI]'):
                    error_msg = f"Person1 service '{service_name}' does NOT have [PAROVI] prefix"
                    validation_errors.append(error_msg)
                    logger.error(f"❌ VALIDATION FAILED: {error_msg}")
                else:
                    logger.info(f"   ✅ Person1: {service_name} - [PAROVI] prefix OK")
        
        # Validate Person2 services
        for sid in person2_service_ids:
            if sid in service_map:
                service_name = service_map[sid]['name']
                if not service_name.startswith('[PAROVI]'):
                    error_msg = f"Person2 service '{service_name}' does NOT have [PAROVI] prefix"
                    validation_errors.append(error_msg)
                    logger.error(f"❌ VALIDATION FAILED: {error_msg}")
                else:
                    logger.info(f"   ✅ Person2: {service_name} - [PAROVI] prefix OK")
        
        # HARD FAIL if validation errors
        if validation_errors:
            error_detail = f"COUPLES BOOKING VALIDATION FAILED: {'; '.join(validation_errors)}"
            logger.error(f"🚨 {error_detail}")
            logger.error(f"🚨 REFUSING TO CREATE APPOINTMENT - Data integrity violation")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "COUPLES_BOOKING_VALIDATION_FAILED",
                    "message": "All services for couples booking must have [PAROVI] prefix",
                    "validation_errors": validation_errors
                }
            )
        
        logger.info(f"✅ PREFIX VALIDATION PASSED - All services have [PAROVI] prefix")
        
        # ============================================
        # 🔒 DURATION VALIDATION - For couples booking
        # ============================================
        
        # Calculate total duration per person
        p1_total_duration = sum(service_map[sid].get('duration', 0) for sid in person1_service_ids if sid in service_map)
        p2_total_duration = sum(service_map[sid].get('duration', 0) for sid in person2_service_ids if sid in service_map)
        
        # Debug log durations
        p1_duration_info = [(sid, service_map[sid].get('name'), service_map[sid].get('duration')) for sid in person1_service_ids if sid in service_map]
        p2_duration_info = [(sid, service_map[sid].get('name'), service_map[sid].get('duration')) for sid in person2_service_ids if sid in service_map]
        
        logger.info(f"🔍 DURATION VALIDATION:")
        logger.info(f"   duration_type from request: {couple.duration_type}")
        logger.info(f"   person1_services: {p1_duration_info}, total={p1_total_duration} min")
        logger.info(f"   person2_services: {p2_duration_info}, total={p2_total_duration} min")
        
        # If duration_type is provided, validate it
        if couple.duration_type is not None:
            duration_type_int = int(couple.duration_type)
            if duration_type_int not in [60, 90, 120]:
                logger.error(f"🔒 INVALID_DURATION_TYPE: {duration_type_int}, must be 60/90/120")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "INVALID_DURATION_TYPE",
                        "duration_type": duration_type_int,
                        "message": f"Invalid duration_type: {duration_type_int}. Must be 60, 90, or 120."
                    }
                )
            
            # Validate duration per person matches duration_type
            # Special rule for 120: allow [120] or [60,60]
            def is_valid_duration_website(total: int, durations: list, expected: int) -> bool:
                if expected == 120:
                    # Allow: single 120, or two 60s
                    if total == 120:
                        return True
                    if len(durations) == 2 and all(d == 60 for d in durations):
                        return True
                    return False
                else:
                    # For 60 and 90: must match exactly
                    return total == expected
            
            p1_durations = [service_map[sid].get('duration', 0) for sid in person1_service_ids if sid in service_map]
            p2_durations = [service_map[sid].get('duration', 0) for sid in person2_service_ids if sid in service_map]
            
            if not is_valid_duration_website(p1_total_duration, p1_durations, duration_type_int):
                logger.error(f"🔒 DURATION_MISMATCH person1: total={p1_total_duration}, expected={duration_type_int}, durations={p1_durations}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "DURATION_MISMATCH",
                        "person": 1,
                        "total_duration": p1_total_duration,
                        "expected_duration": duration_type_int,
                        "services": p1_duration_info,
                        "message": f"Person 1 services total {p1_total_duration} min, but duration_type is {duration_type_int} min"
                    }
                )
            
            if not is_valid_duration_website(p2_total_duration, p2_durations, duration_type_int):
                logger.error(f"🔒 DURATION_MISMATCH person2: total={p2_total_duration}, expected={duration_type_int}, durations={p2_durations}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "DURATION_MISMATCH",
                        "person": 2,
                        "total_duration": p2_total_duration,
                        "expected_duration": duration_type_int,
                        "services": p2_duration_info,
                        "message": f"Person 2 services total {p2_total_duration} min, but duration_type is {duration_type_int} min"
                    }
                )
            
            logger.info(f"✅ DURATION VALIDATION PASSED: duration_type={duration_type_int}, p1={p1_total_duration} min, p2={p2_total_duration} min")
        else:
            # If duration_type not provided, just log the calculated durations
            logger.info(f"⚠️ duration_type not provided - skipping duration validation")
            logger.info(f"   Calculated: p1={p1_total_duration} min, p2={p2_total_duration} min")
        
        # ============================================
        # 🔒 DURATION VALIDATION - END
        # ============================================
        
        # --- CALCULATE PRICE FROM [PAROVI] COMPONENTS ---
        # COUPLES SERVICE MUST NOT HAVE HARDCODED PRICE
        # Price is ALWAYS sum of [PAROVI] services for each person
        
        logger.info(f"💰 CALCULATING COUPLES PRICE FROM [PAROVI] COMPONENTS:")
        
        # Calculate from Person1 services
        person1_total = 0.0
        for sid in person1_service_ids:
            if sid in service_map:
                service_price = float(service_map[sid].get('price', 0))
                person1_total += service_price
                logger.info(f"   Person1: {service_map[sid]['name']} = {service_price} RSD")
        
        # Calculate from Person2 services
        person2_total = 0.0
        for sid in person2_service_ids:
            if sid in service_map:
                service_price = float(service_map[sid].get('price', 0))
                person2_total += service_price
                logger.info(f"   Person2: {service_map[sid]['name']} = {service_price} RSD")
        
        # TOTAL = Person1 + Person2 (NO addons, NO fees, NO magic)
        calculated_total = person1_total + person2_total
        logger.info(f"   CALCULATED TOTAL: {person1_total} + {person2_total} = {calculated_total} RSD")
        
        # --- STRICT VALIDATION: ROUND PRICES (must end with 0) ---
        # Our prices are round numbers: 4400, 5600, 6800, 3960, 6120, etc.
        # They must end with 0 (divisible by 10)
        # If price has decimals other than .0, it's a data error
        
        logger.info(f"🔍 STRICT VALIDATION - Checking round prices:")
        
        price_validation_errors = []
        
        # Check Person1 prices
        for sid in person1_service_ids:
            if sid in service_map:
                price = float(service_map[sid].get('price', 0))
                if price % 10 != 0:
                    error_msg = f"Person1 service '{service_map[sid]['name']}' has non-round price: {price} RSD (must end with 0)"
                    price_validation_errors.append(error_msg)
                    logger.error(f"❌ PRICE VALIDATION FAILED: {error_msg}")
                else:
                    logger.info(f"   ✅ Person1: {price} RSD - Round price OK")
        
        # Check Person2 prices
        for sid in person2_service_ids:
            if sid in service_map:
                price = float(service_map[sid].get('price', 0))
                if price % 10 != 0:
                    error_msg = f"Person2 service '{service_map[sid]['name']}' has non-round price: {price} RSD (must end with 0)"
                    price_validation_errors.append(error_msg)
                    logger.error(f"❌ PRICE VALIDATION FAILED: {error_msg}")
                else:
                    logger.info(f"   ✅ Person2: {price} RSD - Round price OK")
        
        # Check calculated total
        if calculated_total % 10 != 0:
            error_msg = f"Calculated total {calculated_total} RSD does NOT end with 0 - Data mixing or error!"
            price_validation_errors.append(error_msg)
            logger.error(f"❌ TOTAL PRICE VALIDATION FAILED: {error_msg}")
        else:
            logger.info(f"   ✅ Total: {calculated_total} RSD - Round price OK")
        
        # HARD FAIL if price validation errors
        if price_validation_errors:
            error_detail = f"COUPLES PRICING VALIDATION FAILED: {'; '.join(price_validation_errors)}"
            logger.error(f"🚨 {error_detail}")
            logger.error(f"🚨 REFUSING TO CREATE APPOINTMENT - Price integrity violation")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "COUPLES_PRICING_VALIDATION_FAILED",
                    "message": "All prices must be round (ending with 0). Non-round prices indicate data mixing or errors.",
                    "validation_errors": price_validation_errors
                }
            )
        
        logger.info(f"✅ PRICE VALIDATION PASSED - All prices are round (end with 0)")
        
        # --- DETERMINE PRICE SOURCE ---
        # Priority 1: If website sends original_price, verify it matches calculation
        if couple.original_price and float(couple.original_price) > 0:
            website_price = float(couple.original_price)
            if abs(website_price - calculated_total) > 1:  # Allow 1 RSD rounding difference
                logger.warning(f"⚠️ PRICE MISMATCH: Website={website_price}, Calculated={calculated_total}")
                logger.warning(f"⚠️ Using CALCULATED price (components) as source of truth")
                snap_original = calculated_total
            else:
                snap_original = website_price
                logger.info(f"✅ Website price matches calculation: {website_price} RSD")
        else:
            # Priority 2: Use calculated price if website doesn't send
            snap_original = calculated_total
            logger.info(f"✅ Using calculated price (website didn't send): {snap_original} RSD")
        
        # --- DETERMINE DISCOUNT INTENT FROM WEBSITE PAYLOAD ---
        discount_intent = couple.discount_percentage
        
        logger.info(f"🔍 COUPLES DISCOUNT OVERRIDE: request_discount={discount_intent}")
        
        # If website explicitly says 0 => FORCE NO DISCOUNT
        if discount_intent is not None and float(discount_intent) == 0:
            applied_discount = 0.0
            snap_final = snap_original  # FORCE equal - NO DISCOUNT
            snap_discount_amount = 0.0
            logger.info(f"🔒 EXPLICIT NO DISCOUNT: applied={applied_discount}, original={snap_original}, final={snap_final}")
        
        # If website explicitly sends discount > 0 => apply that discount
        elif discount_intent is not None and float(discount_intent) > 0:
            applied_discount = float(discount_intent)
            snap_final = float(couple.final_price or snap_original * (1 - applied_discount / 100))
            snap_discount_amount = snap_original - snap_final
            logger.info(f"💰 EXPLICIT DISCOUNT: applied={applied_discount}%, original={snap_original}, final={snap_final}")
        
        # If website doesn't specify discount => DEFAULT IS NO DISCOUNT
        else:
            applied_discount = 0.0
            snap_final = snap_original  # FORCE equal - NO DISCOUNT
            snap_discount_amount = 0.0
            logger.info(f"🔒 DEFAULT NO DISCOUNT: applied={applied_discount}, original={snap_original}, final={snap_final}")
        
        # Assign final values
        original_total = snap_original
        discounted_price = snap_final
        discount_percentage = applied_discount
        discount_amount = snap_discount_amount
        
        # --- DISCOUNT VALIDATION FOR TESTING ---
        # Allow discounts for testing/campaigns (0 or positive percentage)
        
        if discount_percentage < 0:
            error_msg = f"Discount percentage cannot be negative: {discount_percentage}%"
            logger.error(f"❌ DISCOUNT VALIDATION FAILED: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "INVALID_DISCOUNT",
                    "message": "Discount percentage cannot be negative",
                    "received_discount": discount_percentage
                }
            )
        
        if discount_percentage == 0:
            logger.info(f"✅ NO DISCOUNT: discount = 0%")
        else:
            logger.info(f"💰 DISCOUNT APPLIED: discount = {discount_percentage}%")
        
        # --- DEBUG LOG: COMPLETE BOOKING BREAKDOWN ---
        logger.info(f"")
        logger.info(f"📋 ===== COUPLES BOOKING COMPLETE BREAKDOWN =====")
        logger.info(f"   Appointment Type: COUPLES / MASAŽA ZA PAROVE")
        logger.info(f"   ")
        logger.info(f"   Person1 Services:")
        for sid in person1_service_ids:
            if sid in service_map:
                svc = service_map[sid]
                logger.info(f"     - ID: {sid}")
                logger.info(f"       Name: {svc['name']}")
                logger.info(f"       Price: {svc['price']} RSD")
                logger.info(f"       [PAROVI] prefix: ✅")
        logger.info(f"   Person1 Subtotal: {person1_total} RSD")
        logger.info(f"   ")
        logger.info(f"   Person2 Services:")
        for sid in person2_service_ids:
            if sid in service_map:
                svc = service_map[sid]
                logger.info(f"     - ID: {sid}")
                logger.info(f"       Name: {svc['name']}")
                logger.info(f"       Price: {svc['price']} RSD")
                logger.info(f"       [PAROVI] prefix: ✅")
        logger.info(f"   Person2 Subtotal: {person2_total} RSD")
        logger.info(f"   ")
        logger.info(f"   FINAL FORMULA: {person1_total} + {person2_total} = {original_total} RSD")
        logger.info(f"   Discount: {discount_percentage}% (0 - NO DISCOUNT)")
        logger.info(f"   Final Price: {discounted_price} RSD")
        logger.info(f"   ")
        logger.info(f"   ✅ All validations passed:")
        logger.info(f"      ✅ [PAROVI] prefix on all services")
        logger.info(f"      ✅ Round prices (ending with 00)")
        logger.info(f"      ✅ No discount applied")
        logger.info(f"      ✅ Price calculated from components")
        logger.info(f"📋 ===============================================")
        logger.info(f"")
        
        # 🔒🔒🔒 END CRITICAL LOCKED SECTION - STRICT PRICING RULES 🔒🔒🔒
        
        # If service names weren't extracted yet (old format), get them from DB
        if not person1_service_names:
            person1_service_names = [service_map[sid]['name'] for sid in person1_service_ids if sid in service_map]
        if not person2_service_names:
            person2_service_names = [service_map[sid]['name'] for sid in person2_service_ids if sid in service_map]
        
        # Calculate total duration from person1_services (NEW FORMAT has duration in each service)
        if couple.person1_services and isinstance(couple.person1_services[0], CoupleServiceItem):
            # Sum durations from service objects
            total_duration = sum(s.duration for s in couple.person1_services)
            logger.info(f"⏱️ Total duration calculated from services: {total_duration} min")
        elif couple.duration_type:
            # Fallback to old format duration_type
            total_duration = couple.duration_type
            logger.info(f"⏱️ Total duration from duration_type: {total_duration} min")
        else:
            # Default to 60 minutes if nothing provided
            total_duration = 60
            logger.warning(f"⚠️ No duration info - defaulting to 60 min")
        
        # Remove timezone info if present
        start_time = couple.start_time.replace(tzinfo=None) if couple.start_time.tzinfo else couple.start_time
        end_time = start_time + timedelta(minutes=total_duration)
        
        # Create service name description - total_duration IS the appointment duration
        service_name = f"Masaža za parove - {total_duration} min"
        
        # Create a dummy service entry for couple package
        # Store DISCOUNTED price in price field, and discount percentage in metadata
        couple_service_id = str(uuid.uuid4())
        
        # Use category from website payload if provided, otherwise default to "couple"
        category = couple.category if couple.category else "couple"
        
        # --- BUILD DETAILED DESCRIPTION WITH ALL SERVICES ---
        # Format: "Service1 - XXmin (YYY RSD) + Service2 - XXmin (YYY RSD)"
        person1_desc_parts = []
        for sid in person1_service_ids:
            if sid in service_map:
                svc = service_map[sid]
                person1_desc_parts.append(f"{svc['name']} - {svc['duration']}min ({svc['price']} RSD)")
        
        person2_desc_parts = []
        for sid in person2_service_ids:
            if sid in service_map:
                svc = service_map[sid]
                person2_desc_parts.append(f"{svc['name']} - {svc['duration']}min ({svc['price']} RSD)")
        
        detailed_description = f"Osoba 1: {' + '.join(person1_desc_parts)} | Osoba 2: {' + '.join(person2_desc_parts)}"
        logger.info(f"📝 DESCRIPTION: {detailed_description}")
        
        # --- PREPARE DETAILED SERVICES SNAPSHOT FOR LISTING ---
        # Store ALL services with details so listing can display everything
        person1_services_snapshot = []
        for sid in person1_service_ids:
            if sid in service_map:
                svc = service_map[sid]
                person1_services_snapshot.append({
                    "service_id": sid,
                    "name": svc['name'],
                    "duration": svc['duration'],
                    "price": svc['price']
                })
        
        person2_services_snapshot = []
        for sid in person2_service_ids:
            if sid in service_map:
                svc = service_map[sid]
                person2_services_snapshot.append({
                    "service_id": sid,
                    "name": svc['name'],
                    "duration": svc['duration'],
                    "price": svc['price']
                })
        
        logger.info(f"📸 SNAPSHOT: Stored {len(person1_services_snapshot)} services for Person1")
        logger.info(f"📸 SNAPSHOT: Stored {len(person2_services_snapshot)} services for Person2")
        
        couple_service = {
            "id": couple_service_id,
            "name": service_name,
            "duration": total_duration,
            "price": discounted_price,  # STORE DISCOUNTED PRICE (what customer pays)
            "description": detailed_description,
            "created_at": datetime.now().isoformat(),
            "category": category,  # Use category from website or default "couple"
            "discount_percentage": discount_percentage,
            "discount_amount": discount_amount,
            "has_discount": discount_percentage > 0,  # Flag for easier filtering
            "metadata": {
                "original_price": original_total,
                "discount_applied": discount_percentage,
                "final_price": discounted_price,
                "person1_services": person1_services_snapshot,
                "person2_services": person2_services_snapshot
            }
        }
        
        # Store couple service details
        await db.services.insert_one(couple_service)
        
        # Create appointment with couple service and snapshot data
        appointment_dict = {
            "client_first_name": couple.client_first_name,
            "client_last_name": couple.client_last_name,
            "client_phone": couple.client_phone,
            "client_email": couple.client_email,
            "therapist_id": therapist_id,
            "service_id": couple_service_id,
            "start_time": start_time,
            "end_time": end_time,
            "status": AppointmentStatus.SCHEDULED,
            "body_map_gender": None,
            "body_map_points": [],
            "is_couples_booking": True,  # CRITICAL: Flag for couples booking
            # CRITICAL: Add snapshot fields to appointment object
            "snapshot_price": discounted_price,
            "snapshot_original_price": original_total,
            "snapshot_discount_percentage": discount_percentage,
            "snapshot_discount_amount": discount_amount,
            # ALIAS FIELDS for frontend compatibility
            "final_total": discounted_price,
            "original_total": original_total,
            "discount_percentage": discount_percentage,
            "discount_amount": discount_amount,
            # COUPLES MULTI-SERVICE SNAPSHOT: Store ALL selected services
            "person1_services_snapshot": person1_services_snapshot,
            "person2_services_snapshot": person2_services_snapshot,
            "pricing_breakdown": f"{person1_total} + {person2_total} = {original_total}"
        }
        
        appointment_obj = Appointment(**appointment_dict)
        
        doc = appointment_obj.model_dump()
        doc['start_time'] = doc['start_time'].isoformat()
        doc['end_time'] = doc['end_time'].isoformat()
        doc['created_at'] = doc['created_at'].isoformat()
        
        await db.appointments.insert_one(doc)
        
        # Send email notifications (non-blocking)
        try:
            # Get service name from the couple service
            couple_service_name = couple_service.get('name', 'Masaža za parove') if couple_service else 'Masaža za parove'
            
            # Include notes with person selections
            notes_text = couple.notes or ''
            
            email_data = {
                'client_first_name': couple.client_first_name,
                'client_last_name': couple.client_last_name,
                'client_phone': couple.client_phone,
                'client_email': couple.client_email,
                'start_time': appointment_obj.start_time,
                'service_name': couple_service_name,
                'notes': notes_text
            }
            await send_booking_emails(email_data)
        except Exception as e:
            logger.error(f"Email notification failed for couples booking (non-blocking): {e}")
        
        logger.info(f"✅ Couple appointment created successfully: {appointment_obj.id}")
        logger.info(f"   Service ID: {couple_service_id}")
        logger.info(f"   Category: {category}")
        logger.info(f"   Snapshot: original={original_total}, final={discounted_price}, discount={discount_percentage}%")
        return appointment_obj
            
    except HTTPException as http_ex:
        # Re-raise HTTP exceptions (404, etc.)
        logger.error(f"❌ HTTP Exception in couple booking: {http_ex.status_code} - {http_ex.detail}")
        raise
    except Exception as e:
        # Catch all other exceptions and log detailed info
        logger.error(f"❌ COUPLE BOOKING FAILED - Unexpected Error")
        logger.error(f"   Error Type: {type(e).__name__}")
        logger.error(f"   Error Message: {str(e)}")
        logger.error(f"   Client: {couple.client_first_name} {couple.client_last_name}")
        logger.error(f"   Phone: {couple.client_phone}")
        
        # Log full payload for debugging
        try:
            payload_dict = couple.model_dump()
            logger.error(f"   Full Payload: {payload_dict}")
        except:
            logger.error(f"   Could not serialize payload")
        
        # Return user-friendly error
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create couple booking: {str(e)}"
        )
# 🔒🔒🔒 LOCKED ZONE END - COUPLES APPOINTMENT BOOKING 🔒🔒🔒


@api_router.get("/appointments")
async def get_appointments(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    therapist_id: Optional[str] = Query(None),
    status: Optional[AppointmentStatus] = Query(None),
    include_spa: bool = Query(True, description="Include SPA appointments in results")
):
    """
    Get appointments with optional filters.
    Now includes SPA appointments by default for unified calendar view.
    """
    query = {}
    
    if start_date and end_date:
        query["start_time"] = {
            "$gte": start_date,
            "$lte": end_date
        }
    
    if therapist_id:
        query["therapist_id"] = therapist_id
    
    if status:
        query["status"] = status
    
    # Fetch MASSAGE appointments
    appointments = await db.appointments.find(query, {"_id": 0}).to_list(1000)
    
    for apt in appointments:
        apt['type'] = 'massage'  # Add type field
        if isinstance(apt['start_time'], str):
            apt['start_time'] = datetime.fromisoformat(apt['start_time'])
        if isinstance(apt['end_time'], str):
            apt['end_time'] = datetime.fromisoformat(apt['end_time'])
        if isinstance(apt['created_at'], str):
            apt['created_at'] = datetime.fromisoformat(apt['created_at'])
    
    # Fetch SPA appointments if requested
    if include_spa and start_date and end_date:
        spa_query = {
            "start_time": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        spa_appointments = await db.spa_appointments.find(spa_query, {"_id": 0}).to_list(1000)
        
        # Get service info map for massage appointments
        service_ids = list(set(apt.get('service_id') for apt in appointments if apt.get('service_id')))
        if service_ids:
            services = await db.services.find({"id": {"$in": service_ids}}, {"_id": 0}).to_list(1000)
            service_map = {s['id']: s for s in services}
        else:
            service_map = {}
        
        # Normalize SPA appointments using the unified normalizer
        for spa in spa_appointments:
            # Use normalize_spa_appt for consistent data across ALL endpoints
            normalized = normalize_spa_appt(spa)
            
            # Parse datetime fields
            start_time = normalized.get('start_time')
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            
            end_time = normalized.get('end_time')
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            elif not end_time and start_time:
                end_time = start_time + timedelta(minutes=normalized.get('duration_min', 120))
            
            # Create calendar-compatible object
            normalized_spa = {
                'id': normalized.get('id'),
                'type': 'spa',
                'client_first_name': normalized.get('client_first_name', ''),
                'client_last_name': normalized.get('client_last_name', ''),
                'client_phone': normalized.get('client_phone', ''),
                'client_email': normalized.get('client_email', ''),
                'service_id': spa.get('spa_package_id') or spa.get('id'),
                # NORMALIZED SERVICE DATA (from normalize_spa_appt)
                'service_name': normalized['service_name'],
                'service_title': normalized['service_title'],  # Alias
                'service_description': normalized['service_description'],
                'service_desc': normalized['service_desc'],  # Alias
                'service_duration': normalized['duration_min'],
                'duration_min': normalized['duration_min'],
                'service_category': normalized.get('spa_category') or spa.get('spa_category', 'spa_zone'),
                'spa_zone': normalized.get('spa_zone', ''),
                'start_time': start_time,
                'end_time': end_time,
                'created_at': datetime.fromisoformat(spa.get('created_at')) if spa.get('created_at') else datetime.now(),
                'status': spa.get('status', 'scheduled'),
                'notes': spa.get('notes', ''),
                'is_viewed': spa.get('is_viewed', False),
                'is_couples_booking': spa.get('spa_category') == 'spa_special_couple',
                # Pricing fields
                'snapshot_price': spa.get('final_total', 0),
                'snapshot_original_price': spa.get('original_total', 0),
                'snapshot_discount_percentage': spa.get('discount_percentage', 0),
                'snapshot_discount_amount': spa.get('discount_amount', 0),
                'final_total': spa.get('final_total', 0),
                'original_total': spa.get('original_total', 0),
                'discount_percentage': spa.get('discount_percentage', 0),
                'discount_amount': spa.get('discount_amount', 0),
                # Services snapshot for detail view
                'services_snapshot': spa.get('services_snapshot', []),
                'addons': spa.get('addons', []),
                'addons_total': spa.get('addons_total', 0)
            }
            
            appointments.append(normalized_spa)
        
        logger.info(f"📅 Calendar feed: {len(appointments) - len(spa_appointments)} massage + {len(spa_appointments)} SPA appointments")
    
    # Sort by start_time
    appointments.sort(key=lambda x: x.get('start_time') if x.get('start_time') else datetime.min)
    
    return appointments

# ============================================
# UNIFIED LISTING ENDPOINT (Massage + SPA)
# ============================================
@api_router.get("/appointments/list")
async def get_unified_appointments_list(
    period: Optional[str] = Query("week", description="Period: day, week, month, year"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD")
):
    """
    UNIFIED LISTING: Returns both massage and SPA appointments in a single list.
    Used by CEO Dashboard "Listing Rezervacija" feature.
    """
    from datetime import datetime, timedelta
    
    # Calculate date range based on period if not provided
    now = datetime.now()
    if not start_date or not end_date:
        if period == "day":
            start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = start_dt + timedelta(days=1)
        elif period == "week":
            start_dt = now - timedelta(days=now.weekday())
            start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = start_dt + timedelta(days=7)
        elif period == "month":
            start_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end_dt = start_dt.replace(year=now.year + 1, month=1)
            else:
                end_dt = start_dt.replace(month=now.month + 1)
        elif period == "year":
            start_dt = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_dt = start_dt.replace(year=now.year + 1)
        else:
            start_dt = now - timedelta(days=7)
            end_dt = now + timedelta(days=1)
        
        start_date = start_dt.isoformat()
        end_date = end_dt.isoformat()
    
    items = []
    
    # 1. Fetch MASSAGE appointments
    massage_query = {
        "start_time": {
            "$gte": start_date,
            "$lte": end_date
        }
    }
    massage_appointments = await db.appointments.find(massage_query, {"_id": 0}).to_list(10000)
    
    # Get services for massage appointments
    service_ids = list(set(apt.get('service_id') for apt in massage_appointments if apt.get('service_id')))
    services = await db.services.find({"id": {"$in": service_ids}}, {"_id": 0}).to_list(1000)
    service_map = {s['id']: s for s in services}
    
    for apt in massage_appointments:
        service = service_map.get(apt.get('service_id'), {})
        service_name = service.get('name', 'Nepoznata usluga')
        
        # Handle couples booking - use description for service details
        if apt.get('is_couples_booking'):
            service_name = service.get('description', service_name)
        
        items.append({
            "id": apt.get('id'),
            "type": "massage",
            "start_time": apt.get('start_time'),
            "end_time": apt.get('end_time'),
            "client_first_name": apt.get('client_first_name', ''),
            "client_last_name": apt.get('client_last_name', ''),
            "client_name": f"{apt.get('client_first_name', '')} {apt.get('client_last_name', '')}",
            "client_phone": apt.get('client_phone', ''),
            "service_name": service_name,
            "service_duration": service.get('duration', 0),
            "service_description": service.get('description', ''),
            "original_price": apt.get('snapshot_original_price') or service.get('price', 0),
            "final_total": apt.get('snapshot_price') or service.get('price', 0),
            "total_price": apt.get('snapshot_price') or service.get('price', 0),
            "discount_percentage": apt.get('snapshot_discount_percentage', 0) or 0,
            "discount_amount": apt.get('snapshot_discount_amount', 0) or 0,
            "is_couples_booking": apt.get('is_couples_booking', False),
            "status": apt.get('status', 'scheduled')
        })
    
    # 2. Fetch SPA appointments
    spa_query = {
        "start_time": {
            "$gte": start_date,
            "$lte": end_date
        }
    }
    spa_appointments = await db.spa_appointments.find(spa_query, {"_id": 0}).to_list(10000)
    
    for apt in spa_appointments:
        # Use normalize_spa_appt for consistent data across ALL endpoints
        normalized = normalize_spa_appt(apt)
        
        # Add addon info to description if present
        addons = apt.get('addons', [])
        addons_total = apt.get('addons_total', 0)
        addon_names = ', '.join([a.get('name', '') for a in addons]) if addons else ''
        service_description = normalized['service_description']
        if addon_names and addon_names not in service_description:
            service_description = f"{service_description} + {addon_names}"
        
        items.append({
            "id": apt.get('id'),
            "type": "spa",
            "start_time": apt.get('start_time'),
            "end_time": apt.get('end_time'),
            "client_first_name": apt.get('client_first_name', ''),
            "client_last_name": apt.get('client_last_name', ''),
            "client_name": f"{apt.get('client_first_name', '')} {apt.get('client_last_name', '')}",
            "client_phone": apt.get('client_phone', ''),
            # NORMALIZED SERVICE DATA (from normalize_spa_appt)
            "service_name": normalized['service_name'],
            "service_title": normalized['service_title'],  # Alias
            "service_description": service_description,
            "service_desc": normalized['service_desc'],  # Alias
            "service_duration": normalized['duration_min'],
            "duration_min": normalized['duration_min'],
            "spa_zone": normalized.get('spa_zone', ''),
            "original_price": apt.get('original_total', 0),
            "final_total": apt.get('final_total', 0),
            "total_price": apt.get('final_total', 0),
            "discount_percentage": apt.get('discount_percentage', 0) or 0,
            "discount_amount": apt.get('discount_amount', 0) or 0,
            "is_couples_booking": apt.get('spa_category') == 'spa_special_couple',
            "status": apt.get('status', 'scheduled'),
            "addons": addons,
            "addons_total": addons_total
        })
    
    # Sort by start_time
    items.sort(key=lambda x: x.get('start_time', ''))
    
    logger.info(f"📋 UNIFIED LISTING: {len(massage_appointments)} massage + {len(spa_appointments)} SPA = {len(items)} total")
    
    return {
        "items": items,
        "total_count": len(items),
        "massage_count": len(massage_appointments),
        "spa_count": len(spa_appointments),
        "period": period,
        "start_date": start_date,
        "end_date": end_date
    }

# ============================================
# DELETE ALL APPOINTMENTS (Unified)
# ============================================
@api_router.delete("/appointments/all")
async def delete_all_appointments_unified(
    period: Optional[str] = Query("week", description="Period: day, week, month, year"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    include_spa: bool = Query(True, description="Also delete SPA appointments")
):
    """
    Delete ALL appointments (massage + optionally SPA) within a date range.
    Used by CEO Dashboard "Obriši Sve" feature.
    """
    from datetime import datetime, timedelta
    
    # Calculate date range based on period if not provided
    now = datetime.now()
    if not start_date or not end_date:
        if period == "day":
            start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = start_dt + timedelta(days=1)
        elif period == "week":
            start_dt = now - timedelta(days=now.weekday())
            start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = start_dt + timedelta(days=7)
        elif period == "month":
            start_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end_dt = start_dt.replace(year=now.year + 1, month=1)
            else:
                end_dt = start_dt.replace(month=now.month + 1)
        elif period == "year":
            start_dt = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_dt = start_dt.replace(year=now.year + 1)
        else:
            start_dt = now - timedelta(days=7)
            end_dt = now + timedelta(days=1)
        
        start_date = start_dt.isoformat()
        end_date = end_dt.isoformat()
    
    query = {
        "start_time": {
            "$gte": start_date,
            "$lte": end_date
        }
    }
    
    # Delete massage appointments
    massage_result = await db.appointments.delete_many(query)
    massage_deleted = massage_result.deleted_count
    
    # Delete SPA appointments if requested
    spa_deleted = 0
    if include_spa:
        spa_result = await db.spa_appointments.delete_many(query)
        spa_deleted = spa_result.deleted_count
    
    total_deleted = massage_deleted + spa_deleted
    logger.info(f"🗑️ BULK DELETE: {massage_deleted} massage + {spa_deleted} SPA = {total_deleted} total")
    
    return {
        "message": f"Deleted {total_deleted} appointments",
        "massage_deleted": massage_deleted,
        "spa_deleted": spa_deleted,
        "total_deleted": total_deleted
    }

@api_router.get("/appointments/{appointment_id}", response_model=Appointment)
async def get_appointment(appointment_id: str):
    """Get a specific appointment"""
    appointment = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if isinstance(appointment['start_time'], str):
        appointment['start_time'] = datetime.fromisoformat(appointment['start_time'])
    if isinstance(appointment['end_time'], str):
        appointment['end_time'] = datetime.fromisoformat(appointment['end_time'])
    if isinstance(appointment['created_at'], str):
        appointment['created_at'] = datetime.fromisoformat(appointment['created_at'])
    
    return appointment

@api_router.put("/appointments/{appointment_id}", response_model=Appointment)
async def update_appointment(appointment_id: str, appointment: AppointmentCreate):
    """Update an appointment"""
    existing = await db.appointments.find_one({"id": appointment_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Verify therapist exists (only if provided)
    if appointment.therapist_id:
        therapist = await db.therapists.find_one({"id": appointment.therapist_id})
        if not therapist:
            raise HTTPException(status_code=404, detail="Therapist not found")
    
    # Verify service exists and get duration
    service = await db.services.find_one({"id": appointment.service_id})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Remove timezone info if present to use naive datetime (local time)
    start_time = appointment.start_time.replace(tzinfo=None) if appointment.start_time.tzinfo else appointment.start_time
    
    # Calculate end time based on service duration
    end_time = start_time + timedelta(minutes=service['duration'])
    
    # Check for overlapping appointments (only if therapist is assigned)
    if appointment.therapist_id:
        overlapping = await db.appointments.find({
            "id": {"$ne": appointment_id},
            "therapist_id": appointment.therapist_id,
            "status": AppointmentStatus.SCHEDULED,
            "$or": [
                {
                    "start_time": {"$lt": end_time.isoformat()},
                    "end_time": {"$gt": start_time.isoformat()}
                }
            ]
        }).to_list(1)
        
        if overlapping:
            raise HTTPException(status_code=400, detail="Therapist is not available at this time")
    
    update_data = appointment.model_dump()
    update_data['end_time'] = end_time.isoformat()
    update_data['start_time'] = start_time.isoformat()
    
    await db.appointments.update_one({"id": appointment_id}, {"$set": update_data})
    
    updated = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    if isinstance(updated['start_time'], str):
        updated['start_time'] = datetime.fromisoformat(updated['start_time'])
    if isinstance(updated['end_time'], str):
        updated['end_time'] = datetime.fromisoformat(updated['end_time'])
    if isinstance(updated['created_at'], str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    
    return updated

@api_router.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str):
    """Delete an appointment"""
    result = await db.appointments.delete_one({"id": appointment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Appointment deleted successfully"}

@api_router.patch("/appointments/{appointment_id}/assign-therapist")
async def assign_therapist_to_appointment(appointment_id: str, therapist_id: str):
    """
    Assign therapist to appointment (used by receptionist)
    This endpoint allows receptionist to manually assign a therapist to a booking
    """
    # Check if appointment exists
    appointment = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Verify therapist exists
    therapist = await db.therapists.find_one({"id": therapist_id}, {"_id": 0})
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    # Parse times for overlap check
    start_time = appointment['start_time']
    end_time = appointment['end_time']
    
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time)
    if isinstance(end_time, str):
        end_time = datetime.fromisoformat(end_time)
    
    # Check for overlapping appointments with this therapist
    overlapping = await db.appointments.find({
        "id": {"$ne": appointment_id},
        "therapist_id": therapist_id,
        "status": AppointmentStatus.SCHEDULED,
        "$or": [
            {
                "start_time": {"$lt": end_time.isoformat()},
                "end_time": {"$gt": start_time.isoformat()}
            }
        ]
    }).to_list(1)
    
    if overlapping:
        raise HTTPException(
            status_code=400, 
            detail=f"Therapist {therapist['name']} is not available at this time"
        )
    
    # Assign therapist
    result = await db.appointments.update_one(
        {"id": appointment_id},
        {"$set": {"therapist_id": therapist_id}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to assign therapist")
    
    # Return updated appointment
    updated = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    if isinstance(updated['start_time'], str):
        updated['start_time'] = datetime.fromisoformat(updated['start_time'])
    if isinstance(updated['end_time'], str):
        updated['end_time'] = datetime.fromisoformat(updated['end_time'])
    if isinstance(updated['created_at'], str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    
    return updated

@api_router.patch("/appointments/{appointment_id}/status")
async def update_appointment_status(appointment_id: str, status: AppointmentStatus):
    """Update appointment status"""
    result = await db.appointments.update_one(
        {"id": appointment_id},
        {"$set": {"status": status}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Status updated successfully"}


@api_router.get("/appointments/unviewed/count")
async def get_unviewed_appointments_count():
    """Get count of unviewed appointments (massage + SPA)"""
    massage_count = await db.appointments.count_documents({"is_viewed": False})
    spa_count = await db.spa_appointments.count_documents({"is_viewed": False})
    return {"count": massage_count + spa_count}

@api_router.get("/appointments/unviewed/list")
async def get_unviewed_appointments():
    """Get list of unviewed appointments with service details (massage + SPA)"""
    # Get massage appointments
    massage_appointments = await db.appointments.find(
        {"is_viewed": False}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Get SPA appointments
    spa_appointments = await db.spa_appointments.find(
        {"is_viewed": False}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Combine and sort by created_at
    appointments = massage_appointments + spa_appointments
    appointments.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # Get all services for lookup
    services = await db.services.find({}, {"_id": 0}).to_list(1000)
    service_map = {s['id']: s for s in services}
    
    # Get all therapists for lookup
    therapists = await db.therapists.find({}, {"_id": 0}).to_list(1000)
    therapist_map = {t['id']: t for t in therapists}
    
    # Enrich appointments with service and therapist details
    result = []
    for apt in appointments:
        # Parse datetime strings to datetime objects first
        start_time = apt.get('start_time')
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
        
        end_time = apt.get('end_time')
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time)
        
        created_at = apt.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        # Detect if this is SPA or massage appointment
        is_spa = apt.get('spa_category') is not None or apt.get('final_total') is not None
        
        if is_spa:
            # SPA appointment - use direct fields
            service_name = apt.get('service_name') or 'SPA Tretman'
            service_duration = apt.get('duration_min') or 120
            service_category = apt.get('spa_category') or 'spa'
            service_price = apt.get('final_total') or 0
            original_price = apt.get('original_total') or service_price
            discount_percentage = apt.get('discount_percentage') or 0
            therapist_name = None  # SPA usually doesn't have assigned therapist
        else:
            # Massage appointment - use service lookup
            service = service_map.get(apt.get('service_id'))
            service_name = service.get('name') if service else None
            service_duration = service.get('duration') if service else None
            service_category = service.get('category', 'regular') if service else None
            
            # PRIORITY: Use snapshot price from appointment if available (prevents retroactive price changes)
            if 'snapshot_price' in apt:
                service_price = apt['snapshot_price']
                original_price = apt.get('snapshot_original_price', service_price)
                discount_percentage = apt.get('snapshot_discount_percentage', 0)
            else:
                # Fallback: Get price from service (for old appointments without snapshot)
                service_price = service.get('price') if service else None
                discount_percentage = service.get('discount_percentage', 0) if service else 0
                
                # Get original price from metadata if discount was applied
                original_price = service_price
                if service and discount_percentage > 0:
                    metadata = service.get('metadata')
                    if metadata and isinstance(metadata, dict):
                        original_price = metadata.get('original_price', service_price)
            
            # Add therapist name
            therapist = therapist_map.get(apt.get('therapist_id'))
            therapist_name = therapist.get('name') if therapist else None
        
        # Build clean response object with couples snapshot data
        result.append({
            'id': apt.get('id'),
            'client_first_name': apt.get('client_first_name'),
            'client_last_name': apt.get('client_last_name'),
            'client_phone': apt.get('client_phone'),
            'client_email': apt.get('client_email'),
            'therapist_id': apt.get('therapist_id'),
            'therapist_name': therapist_name,
            'service_id': apt.get('service_id'),
            'service_name': service_name,
            'service_price': service_price,
            'original_price': original_price,
            'discount_percentage': discount_percentage,
            'service_duration': service_duration,
            'service_category': service_category,
            'start_time': start_time.isoformat() if start_time else None,
            'end_time': end_time.isoformat() if end_time else None,
            'created_at': created_at.isoformat() if created_at else None,
            'status': apt.get('status'),
            'is_viewed': apt.get('is_viewed', False),
            'is_spa': is_spa,  # Flag to identify SPA appointments
            # Couples booking snapshot data - CRITICAL for multi-service display
            'is_couples_booking': apt.get('is_couples_booking', False),
            'person1_services_snapshot': apt.get('person1_services_snapshot'),
            'person2_services_snapshot': apt.get('person2_services_snapshot'),
            'pricing_breakdown': apt.get('pricing_breakdown'),
            'snapshot_discount_amount': apt.get('snapshot_discount_amount', 0)
        })
    
    return result

@api_router.patch("/appointments/{appointment_id}/mark-viewed")
async def mark_appointment_viewed(appointment_id: str):
    """Mark appointment as viewed"""
    result = await db.appointments.update_one(
        {"id": appointment_id},
        {"$set": {"is_viewed": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Appointment marked as viewed"}

@api_router.patch("/appointments/mark-all-viewed")
async def mark_all_appointments_viewed():
    """Mark all appointments as viewed (massage + SPA)"""
    massage_result = await db.appointments.update_many(
        {"is_viewed": False},
        {"$set": {"is_viewed": True}}
    )
    spa_result = await db.spa_appointments.update_many(
        {"is_viewed": False},
        {"$set": {"is_viewed": True}}
    )
    total_marked = massage_result.modified_count + spa_result.modified_count
    return {"message": f"Marked {total_marked} appointments as viewed"}



# ============================================
# Routes - Business Hours
# ============================================
@api_router.get("/business-hours", response_model=BusinessHours)
async def get_business_hours():
    """Get business hours configuration"""
    hours = await db.business_hours.find_one({}, {"_id": 0})
    if not hours:
        # Return default if not set
        default_hours = BusinessHours()
        doc = default_hours.model_dump()
        await db.business_hours.insert_one(doc)
        return default_hours
    return hours

@api_router.put("/business-hours", response_model=BusinessHours)
async def update_business_hours(hours: BusinessHoursUpdate):
    """Update business hours configuration"""
    existing = await db.business_hours.find_one({})
    
    if not existing:
        # Create new if doesn't exist
        new_hours = BusinessHours(**(hours.model_dump(exclude_none=True)))
        doc = new_hours.model_dump()
        await db.business_hours.insert_one(doc)
        return new_hours
    
    update_data = hours.model_dump(exclude_none=True)
    await db.business_hours.update_one({"id": existing['id']}, {"$set": update_data})
    
    updated = await db.business_hours.find_one({"id": existing['id']}, {"_id": 0})
    return updated


# ============================================
# Routes - Analytics / Dashboard
# ============================================
@api_router.get("/analytics/therapist-stats")
async def get_therapist_statistics(
    therapist_id: Optional[str] = Query(None),
    period: str = Query("week", regex="^(day|week|month|year)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get therapist statistics (hours worked, revenue, client count)"""
    
    # Calculate date range based on period
    now = datetime.now(timezone.utc)
    
    if start_date and end_date:
        date_start = datetime.fromisoformat(start_date)
        date_end = datetime.fromisoformat(end_date)
    else:
        if period == "day":
            date_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=1)
        elif period == "week":
            date_start = now - timedelta(days=now.weekday())
            date_start = date_start.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=7)
        elif period == "month":
            date_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                date_end = date_start.replace(year=now.year + 1, month=1)
            else:
                date_end = date_start.replace(month=now.month + 1)
        else:  # year
            date_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start.replace(year=now.year + 1)
    
    # Build query
    query = {
        "start_time": {
            "$gte": date_start.isoformat(),
            "$lt": date_end.isoformat()
        },
        "status": {"$in": [AppointmentStatus.SCHEDULED, AppointmentStatus.COMPLETED]}
    }
    
    if therapist_id:
        query["therapist_id"] = therapist_id
    
    # Get appointments
    appointments = await db.appointments.find(query, {"_id": 0}).to_list(10000)
    
    # Get all therapists
    therapists = await db.therapists.find({}, {"_id": 0}).to_list(1000)
    therapist_map = {t['id']: t['name'] for t in therapists}
    
    # Get all services for pricing
    services = await db.services.find({}, {"_id": 0}).to_list(1000)
    service_map = {s['id']: s for s in services}
    
    # Calculate statistics per therapist
    stats_by_therapist = {}
    
    for apt in appointments:
        tid = apt['therapist_id']
        
        if tid not in stats_by_therapist:
            stats_by_therapist[tid] = {
                "therapist_id": tid,
                "therapist_name": therapist_map.get(tid, "Unknown"),
                "total_hours": 0,
                "total_revenue": 0,
                "client_count": 0,
                "appointments": []
            }
        
        # Calculate duration in hours
        start = datetime.fromisoformat(apt['start_time']) if isinstance(apt['start_time'], str) else apt['start_time']
        end = datetime.fromisoformat(apt['end_time']) if isinstance(apt['end_time'], str) else apt['end_time']
        duration_hours = (end - start).total_seconds() / 3600
        
        # Get service price with discount applied
        service = service_map.get(apt['service_id'], {})
        original_price = service.get('price', 0)
        discount_percentage = service.get('discount_percentage', 0)
        # Calculate discounted price
        discounted_price = original_price * (1 - discount_percentage / 100)
        
        stats_by_therapist[tid]["total_hours"] += duration_hours
        stats_by_therapist[tid]["total_revenue"] += discounted_price
        stats_by_therapist[tid]["client_count"] += 1
        stats_by_therapist[tid]["appointments"].append(apt['id'])
    
    result = list(stats_by_therapist.values())
    
    return {
        "period": period,
        "start_date": date_start.isoformat(),
        "end_date": date_end.isoformat(),
        "statistics": result
    }

@api_router.get("/analytics/revenue")
async def get_revenue_statistics(
    period: str = Query("week", regex="^(day|week|month|year)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get total revenue statistics"""
    
    # Calculate date range
    now = datetime.now(timezone.utc)
    
    if start_date and end_date:
        date_start = datetime.fromisoformat(start_date)
        date_end = datetime.fromisoformat(end_date)
    else:
        if period == "day":
            date_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=1)
        elif period == "week":
            date_start = now - timedelta(days=now.weekday())
            date_start = date_start.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=7)
        elif period == "month":
            date_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                date_end = date_start.replace(year=now.year + 1, month=1)
            else:
                date_end = date_start.replace(month=now.month + 1)
        else:  # year
            date_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start.replace(year=now.year + 1)
    
    query = {
        "start_time": {
            "$gte": date_start.isoformat(),
            "$lt": date_end.isoformat()
        },
        "status": {"$in": [AppointmentStatus.SCHEDULED, AppointmentStatus.COMPLETED]}
    }
    
    appointments = await db.appointments.find(query, {"_id": 0}).to_list(10000)
    
    # Get services for pricing
    services = await db.services.find({}, {"_id": 0}).to_list(1000)
    service_map = {s['id']: s for s in services}
    
    total_revenue = 0
    for apt in appointments:
        service = service_map.get(apt['service_id'], {})
        original_price = service.get('price', 0)
        discount_percentage = service.get('discount_percentage', 0)
        # Calculate discounted price
        discounted_price = original_price * (1 - discount_percentage / 100)
        total_revenue += discounted_price
    
    return {
        "period": period,
        "start_date": date_start.isoformat(),
        "end_date": date_end.isoformat(),
        "total_revenue": total_revenue,
        "currency": "RSD",
        "appointments_count": len(appointments)
    }

@api_router.get("/analytics/clients")
async def get_client_statistics(
    period: str = Query("week", regex="^(day|week|month|year)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get client count statistics"""
    
    # Calculate date range
    now = datetime.now(timezone.utc)
    
    if start_date and end_date:
        date_start = datetime.fromisoformat(start_date)
        date_end = datetime.fromisoformat(end_date)
    else:
        if period == "day":
            date_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=1)
        elif period == "week":
            date_start = now - timedelta(days=now.weekday())
            date_start = date_start.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=7)
        elif period == "month":
            date_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                date_end = date_start.replace(year=now.year + 1, month=1)
            else:
                date_end = date_start.replace(month=now.month + 1)
        else:  # year
            date_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start.replace(year=now.year + 1)
    
    query = {
        "start_time": {
            "$gte": date_start.isoformat(),
            "$lt": date_end.isoformat()
        },
        "status": {"$in": [AppointmentStatus.SCHEDULED, AppointmentStatus.COMPLETED]}
    }
    
    appointments = await db.appointments.find(query, {"_id": 0}).to_list(10000)
    
    # Count unique clients
    unique_clients = set()
    for apt in appointments:
        client_key = f"{apt['client_first_name']}_{apt['client_last_name']}_{apt['client_phone']}"
        unique_clients.add(client_key)
    
    return {
        "period": period,
        "start_date": date_start.isoformat(),
        "end_date": date_end.isoformat(),
        "total_clients": len(unique_clients),
        "total_appointments": len(appointments)
    }

@api_router.get("/analytics/couple-appointments")
async def get_couple_appointments_analytics(
    period: str = Query("week", regex="^(day|week|month|year)$")
):
    """Get analytics specifically for couple appointments"""
    # Calculate date range
    now = datetime.now(timezone.utc)
    
    if period == "day":
        date_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)
    elif period == "week":
        date_start = now - timedelta(days=now.weekday())
        date_start = date_start.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=7)
    elif period == "month":
        date_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            date_end = date_start.replace(year=now.year + 1, month=1)
        else:
            date_end = date_start.replace(month=now.month + 1)
    else:  # year
        date_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start.replace(year=now.year + 1)
    
    # Get all couple appointments
    query = {
        "start_time": {
            "$gte": date_start.isoformat(),
            "$lte": date_end.isoformat()
        },
        "status": {"$in": [AppointmentStatus.SCHEDULED, AppointmentStatus.COMPLETED]}
    }
    
    appointments = await db.appointments.find(query).to_list(10000)
    
    # Filter couple appointments
    couple_appointments = []
    couple_revenue = 0
    couple_count = 0
    
    for apt in appointments:
        service = await db.services.find_one({"id": apt['service_id']})
        if service and service.get('category') == 'couple':
            couple_appointments.append({
                "id": apt['id'],
                "client_name": f"{apt['client_first_name']} {apt['client_last_name']}",
                "start_time": apt['start_time'],
                "service_name": service['name'],
                "price": service['price'],
                "duration": service['duration'],
                "metadata": service.get('metadata', {})
            })
            couple_revenue += service['price']
            couple_count += 1
    
    return {
        "period": period,
        "start_date": date_start.isoformat(),
        "end_date": date_end.isoformat(),
        "couple_appointments_count": couple_count,
        "couple_revenue": couple_revenue,
        "appointments": couple_appointments
    }


@api_router.get("/analytics/detailed")
async def get_detailed_analytics(
    period: str = Query("week", regex="^(day|week|month|year)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    Get detailed analytics with:
    - Revenue by category
    - Original vs discounted prices
    - Discount statistics
    - Individual appointments with discounts
    """
    
    # Calculate date range
    now = datetime.now(timezone.utc)
    
    if start_date and end_date:
        date_start = datetime.fromisoformat(start_date)
        date_end = datetime.fromisoformat(end_date)
    else:
        if period == "day":
            date_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=1)
        elif period == "week":
            date_start = now - timedelta(days=now.weekday())
            date_start = date_start.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=7)
        elif period == "month":
            date_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                date_end = date_start.replace(year=now.year + 1, month=1)
            else:
                date_end = date_start.replace(month=now.month + 1)
        else:  # year
            date_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start.replace(year=now.year + 1)
    
    # Get appointments
    query = {
        "start_time": {
            "$gte": date_start.isoformat(),
            "$lt": date_end.isoformat()
        },
        "status": {"$in": [AppointmentStatus.SCHEDULED, AppointmentStatus.COMPLETED]}
    }
    
    appointments = await db.appointments.find(query, {"_id": 0}).to_list(10000)
    
    # Get all services
    services = await db.services.find({}, {"_id": 0}).to_list(1000)
    service_map = {s['id']: s for s in services}
    
    # Initialize category stats (without "Kartica Masaza za parove" - will be added dynamically from "couple")
    # NOTE: SPA categories removed - SPA analytics is handled by /api/spa/analytics endpoint
    categories = {
        "Obicne masaze": {
            "appointments_count": 0,
            "revenue": 0,
            "original_revenue": 0,
            "discount_given": 0,
            "with_discount": 0,
            "without_discount": 0
        }
    }
    
    # Discount statistics
    discount_stats = {
        "0": {"count": 0, "revenue": 0},
        "5": {"count": 0, "revenue": 0},
        "10": {"count": 0, "revenue": 0},
        "15": {"count": 0, "revenue": 0}
    }
    
    # Individual appointments with discounts
    appointments_with_discount = []
    
    # Process each appointment
    for apt in appointments:
        service = service_map.get(apt['service_id'])
        if not service:
            continue
        
        # Determine category using official [PAROVI] prefix logic
        service_name = service.get('name', '')
        category = get_service_category_display(service_name, service.get('category'))
        
        # PRIORITY: Use snapshot price from appointment if available (prevents retroactive price changes)
        if 'snapshot_price' in apt:
            service_price = apt['snapshot_price']
            original_price = apt.get('snapshot_original_price', service_price)
            discount_percentage = apt.get('snapshot_discount_percentage', 0)
        else:
            # Fallback: Get price from service (for old appointments without snapshot)
            service_price = service.get('price', 0)
            discount_percentage = service.get('discount_percentage', 0)
            
            # Get original price from metadata if available
            metadata = service.get('metadata')
            if metadata and isinstance(metadata, dict):
                original_price = metadata.get('original_price', service_price)
            else:
                original_price = service_price
        
        # Calculate actual discount amount
        discount_amount = original_price - service_price
        
        # Get or create category (if not in predefined list)
        if category not in categories:
            categories[category] = {
                "appointments_count": 0,
                "revenue": 0,
                "original_revenue": 0,
                "discount_given": 0,
                "with_discount": 0,
                "without_discount": 0
            }
        
        # Update category stats
        categories[category]["appointments_count"] += 1
        categories[category]["revenue"] += service_price  # This is the discounted price (what customer pays)
        categories[category]["original_revenue"] += original_price
        categories[category]["discount_given"] += discount_amount
        
        # Check if appointment has discount (either by percentage or amount)
        has_discount = discount_percentage > 0 or discount_amount > 0
        
        if has_discount:
            categories[category]["with_discount"] += 1
            
            # Add to appointments with discount list
            appointments_with_discount.append({
                "id": apt['id'],
                "client_name": f"{apt['client_first_name']} {apt['client_last_name']}",
                "client_phone": apt['client_phone'],
                "start_time": apt['start_time'],
                "service_name": service['name'],
                "category": category,
                "original_price": original_price,
                "discounted_price": service_price,
                "discount_percentage": discount_percentage,
                "discount_amount": discount_amount
            })
        else:
            categories[category]["without_discount"] += 1
        
        # Update discount stats
        discount_key = str(int(discount_percentage))
        if discount_key not in discount_stats:
            discount_stats[discount_key] = {"count": 0, "revenue": 0}
        discount_stats[discount_key]["count"] += 1
        discount_stats[discount_key]["revenue"] += service_price
    
    # Calculate totals
    total_revenue = sum(cat["revenue"] for cat in categories.values())
    total_original_revenue = sum(cat["original_revenue"] for cat in categories.values())
    total_discount_given = sum(cat["discount_given"] for cat in categories.values())
    total_appointments = sum(cat["appointments_count"] for cat in categories.values())
    
    # Group appointments by service for detailed listing
    appointments_by_service = {}
    for apt in appointments:
        service = service_map.get(apt['service_id'])
        if not service:
            continue
        
        service_id = service['id']
        if service_id not in appointments_by_service:
            appointments_by_service[service_id] = {
                "service_id": service_id,
                "service_name": service['name'],
                "service_duration": service.get('duration'),
                "service_category": service.get('category', 'Obicne masaze'),
                "service_description": service.get('description'),  # For couple appointments - shows massage names
                "appointments": []
            }
        
        # PRIORITY: Use snapshot price from appointment if available (prevents retroactive price changes)
        if 'snapshot_price' in apt:
            final_price = apt['snapshot_price']
            original_price = apt.get('snapshot_original_price', final_price)
            discount_percentage = apt.get('snapshot_discount_percentage', 0)
        else:
            # Fallback: Get price from service (for old appointments without snapshot)
            final_price = service.get('price', 0)
            discount_percentage = service.get('discount_percentage', 0)
            
            # Get original price from metadata if available
            metadata = service.get('metadata')
            if metadata and isinstance(metadata, dict):
                original_price = metadata.get('original_price', final_price)
            else:
                original_price = final_price
        
        appointments_by_service[service_id]["appointments"].append({
            "id": apt['id'],
            "client_first_name": apt.get('client_first_name'),
            "client_last_name": apt.get('client_last_name'),
            "client_phone": apt.get('client_phone'),
            "client_email": apt.get('client_email'),
            "start_time": apt['start_time'],
            "end_time": apt.get('end_time'),
            "status": apt['status'],
            "total_price": final_price,  # This is the discounted price (what customer pays)
            "original_price": original_price,
            "discount_percentage": discount_percentage
        })
    
    # Convert to list and sort appointments within each service
    appointments_by_service_list = list(appointments_by_service.values())
    for service_data in appointments_by_service_list:
        service_data["appointments"].sort(key=lambda x: x["start_time"])
    
    return {
        "period": period,
        "start_date": date_start.isoformat(),
        "end_date": date_end.isoformat(),
        "total_revenue": total_revenue,
        "total_appointments": total_appointments,
        "summary": {
            "total_revenue": total_revenue,
            "total_original_revenue": total_original_revenue,
            "total_discount_given": total_discount_given,
            "total_appointments": total_appointments,
            "discount_percentage": (total_discount_given / total_original_revenue * 100) if total_original_revenue > 0 else 0
        },
        "by_category": categories,
        "by_discount": discount_stats,
        "appointments_with_discount": appointments_with_discount,
        "appointments_by_service": appointments_by_service_list
    }



# ============================================
# 🚫 BLOCKER ENDPOINTS - Prevent frontend from updating SPA discounts
# SPA Discounts are BACKEND-ONLY (admin panel via /api/spa/settings)
# Note: /api/services/{id}/discount is a legitimate admin endpoint for massage discounts
# ============================================
# NOTE: SPA service discount endpoint is now in spa_module.py
# Admin UI uses PATCH /api/spa/services/{service_id}/discount?discount=X
# This allows per-service discount management (0, 5, 10, 15%)


# ============================================
# Root route
# ============================================
@api_router.get("/")
async def api_root():
    return {"message": "Spa & Massage Booking System API", "version": "1.0"}


# ============================================
# 🔐 HARD-LOCKED URLs - ONLY THESE ARE VALID
# ============================================
BACKEND_PUBLIC_URL = "https://spa-integration.preview.emergentagent.com"
FRONTEND_PUBLIC_URL = "https://relax-reserve-5.preview.emergentagent.com"

# Root endpoint - returns JSON to confirm this is API server
@app.get("/")
async def root():
    return JSONResponse({"ok": True, "service": "spa-integration", "mode": "api-only", "hint": "Use /api/health"})


# Include the router in the main app
app.include_router(api_router)

# 🧖 Include SPA router (separate module)
app.include_router(spa_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', FRONTEND_PUBLIC_URL).split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔒 Security Headers Middleware (BaseHTTPMiddleware already imported at top)
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        # Prevent clickjacking
        response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# 🔐 HARD-LOCK: Log locked URLs on startup
print(f"🔐 LOCKED BACKEND_PUBLIC_URL = {BACKEND_PUBLIC_URL}")
print(f"🔐 LOCKED FRONTEND_PUBLIC_URL = {FRONTEND_PUBLIC_URL}")

# Log allowed CORS origins on startup
cors_origins = os.environ.get('CORS_ORIGINS', FRONTEND_PUBLIC_URL).split(',')
print(f"🔒 CORS LOCK: Allowed origins = {cors_origins}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================
# CENTRAL NOTIFICATION DISPATCHER
# Used by BOTH massage AND SPA bookings
# ============================================
async def dispatch_booking_notifications(payload: dict) -> dict:
    """
    🔔 CENTRAL DISPATCHER - Send all booking notifications.
    Used by BOTH massage AND SPA bookings.
    
    Args:
        payload: Dict with booking details (type, appointment_id, service_name, etc.)
    
    Returns:
        Dict with detailed status for frontend:
        {
            "notify_status": "sent" | "partial" | "failed",
            "email_sent": bool,
            "email_sent_admin": bool,
            "email_sent_client": bool,
            "notification_created": bool,
            "notify_error": str | None
        }
    """
    booking_type = payload.get("type", "massage")
    appointment_id = payload.get("appointment_id", "unknown")
    client_email = payload.get("client_email", "")
    service_name = payload.get("service_name", "Usluga")
    
    # 🔥 BRUTALNI LOG - početak
    logger.info(f"✅ SPA_BOOKED id={appointment_id} service={service_name} client_email={client_email}")
    
    result = {
        "email_sent": False,
        "email_sent_admin": False,
        "email_sent_client": False,
        "notification_created": False,
        "notify_status": "pending",
        "notify_error": None
    }
    
    try:
        # 1) Send admin + client emails (uses existing send_booking_emails with tracking)
        email_result = await send_booking_emails_tracked(payload)
        result["email_sent_admin"] = email_result.get("admin_sent", False)
        result["email_sent_client"] = email_result.get("client_sent", False)
        result["email_sent"] = result["email_sent_admin"] or result["email_sent_client"]
        
        # 🔥 BRUTALNI LOG - email status sa appt_id
        if result["email_sent_admin"]:
            logger.info(f"📧 ADMIN_EMAIL_SENT to=bualuangthailandspa@gmail.com appt_id={appointment_id}")
        else:
            logger.warning(f"❌ ADMIN_EMAIL_FAILED type={booking_type} appt_id={appointment_id}")
        
        if client_email:
            if result["email_sent_client"]:
                logger.info(f"📧 CLIENT_EMAIL_SENT to={client_email} appt_id={appointment_id}")
            else:
                logger.warning(f"❌ CLIENT_EMAIL_FAILED to={client_email} appt_id={appointment_id}")
        else:
            logger.info(f"ℹ️ CLIENT_EMAIL_SKIPPED - no email provided appt_id={appointment_id}")
        
        # 2) Create dashboard notification (in-app)
        notification_id = None
        try:
            notification_id = str(uuid.uuid4())
            notification = {
                "id": notification_id,
                "type": f"{booking_type}_booking",
                "appointment_id": appointment_id,
                "title": f"Nova {booking_type.upper()} rezervacija",
                "message": f"{payload.get('client_first_name', '')} {payload.get('client_last_name', '')} - {service_name}",
                "details": {
                    "service_name": service_name,
                    "duration_min": payload.get("duration_min"),
                    "price": payload.get("price") or payload.get("final_total", 0),
                    "start_time": payload.get("start_time"),
                    "client_phone": payload.get("client_phone", "")
                },
                "is_read": False,
                "created_at": datetime.now().isoformat()
            }
            await db.notifications.insert_one(notification)
            result["notification_created"] = True
            
            # 🔥 BRUTALNI LOG - notification created
            logger.info(f"🔔 NOTIFICATION_CREATED appt_id={appointment_id}")
        except Exception as e:
            logger.error(f"❌ NOTIFICATION_FAILED id={notification_id} error={e}")
        
        # Determine final status
        if result["email_sent_admin"] and result["notification_created"]:
            result["notify_status"] = "sent"
        elif result["email_sent_admin"] or result["notification_created"]:
            result["notify_status"] = "partial"
        else:
            result["notify_status"] = "failed"
        
    except Exception as e:
        logger.error(f"❌ NOTIFICATION_DISPATCH_FAILED type={booking_type} id={appointment_id} error={e}")
        result["notify_status"] = "failed"
        result["notify_error"] = str(e)[:200]
    
    return result


async def send_booking_emails_tracked(appointment_data: dict) -> dict:
    """
    Send booking confirmation emails with tracking.
    - ADMIN: Separate internal template
    - CLIENT: SHARED template (same for SPA and MASSAGE!)
    Returns: {"admin_sent": bool, "client_sent": bool}
    """
    import hashlib
    from email_templates import render_admin_email, BookingEmailData
    from email_templates.adapters import build_client_email_for_spa, build_client_email_for_massage
    
    def _hash(s: str) -> str:
        return hashlib.md5(s.encode("utf-8")).hexdigest()[:8]
    
    result = {"admin_sent": False, "client_sent": False}
    
    try:
        # Get SMTP settings from environment
        smtp_host = os.environ.get('SMTP_HOST')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_user = os.environ.get('SMTP_USER')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        smtp_from = os.environ.get('SMTP_FROM', smtp_user)
        smtp_to_owner = os.environ.get('SMTP_TO_OWNER', 'bualuangthailandspa@gmail.com')
        
        # Check if SMTP is configured
        if not smtp_host or not smtp_user or smtp_password == 'PLACEHOLDER_APP_PASSWORD':
            logger.warning("⚠️ Email not sent - SMTP not configured")
            return result
        
        # Extract appointment details
        client_name = f"{appointment_data.get('client_first_name', '')} {appointment_data.get('client_last_name', '')}".strip()
        client_phone = appointment_data.get('client_phone', 'N/A')
        client_email = appointment_data.get('client_email', '')
        start_time = appointment_data.get('start_time')
        service_name = appointment_data.get('service_name', 'Rezervacija')
        booking_type = appointment_data.get('type', 'spa')
        duration_min = appointment_data.get('duration_min')
        price = appointment_data.get('price') or appointment_data.get('final_total')
        
        # Build service details (spa_zone, variants, etc.)
        service_details_parts = []
        if appointment_data.get('service_description'):
            service_details_parts.append(appointment_data['service_description'])
        if appointment_data.get('spa_zone'):
            service_details_parts.append(f"SPA zona: {appointment_data['spa_zone']}")
        service_details = " | ".join(service_details_parts) if service_details_parts else None
        
        # Format datetime
        if isinstance(start_time, str):
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                formatted_date = start_dt.strftime('%d.%m.%Y')
                formatted_time_only = start_dt.strftime('%H:%M')
            except:
                formatted_date = start_time
                formatted_time_only = ""
        else:
            formatted_date = start_time.strftime('%d.%m.%Y') if start_time else 'N/A'
            formatted_time_only = start_time.strftime('%H:%M') if start_time else ''
        
        # Get pricing info from appointment
        pricing = appointment_data.get('pricing', {})
        original_price = pricing.get('original_price') or appointment_data.get('original_total')
        discount_percent = pricing.get('discount_percent') or appointment_data.get('discount_percentage', 0)
        
        # Build email data object
        email_data = BookingEmailData(
            salon_name="Bua Luang Thai Spa",
            client_full_name=client_name,
            client_phone=client_phone,
            client_email=client_email,
            service_title=service_name,
            service_details=service_details,
            date_str=formatted_date,
            time_str=formatted_time_only,
            duration_min=duration_min,
            price=price,
            address_line="Abebe Bikile 10A, Beograd",
            contact_email="bualuangthailandspa@gmail.com",
            contact_phone="+381 62 625 500",
            booking_type=booking_type,
            # Pricing fields for discount display
            original_price=original_price,
            discount_percent=discount_percent
        )
        
        # Render ADMIN template (internal, plain)
        admin_subject, admin_html = render_admin_email(email_data)
        
        # Render CLIENT template using SHARED template (same for SPA and MASSAGE!)
        if booking_type == "spa":
            client_subject, client_html = build_client_email_for_spa(appointment_data)
        else:
            client_subject, client_html = build_client_email_for_massage(appointment_data)
        
        # 1) Send to ADMIN (internal notification)
        try:
            admin_msg = MIMEMultipart()
            admin_msg['From'] = smtp_from
            admin_msg['To'] = smtp_to_owner
            admin_msg['Subject'] = admin_subject
            admin_msg.attach(MIMEText(admin_html, 'html', 'utf-8'))
            
            await aiosmtplib.send(
                admin_msg,
                hostname=smtp_host,
                port=smtp_port,
                username=smtp_user,
                password=smtp_password,
                start_tls=True
            )
            result["admin_sent"] = True
            logger.info(f"📧 ADMIN_EMAIL_SENT to={smtp_to_owner} subj=\"{admin_subject}\" body_hash={_hash(admin_html)}")
        except Exception as e:
            logger.error(f"❌ ADMIN_EMAIL_EXCEPTION: {e}")
        
        # 2) Send to CLIENT (SHARED template - same design for SPA and MASSAGE!)
        if client_email and client_email.strip():
            try:
                client_msg = MIMEMultipart()
                client_msg['From'] = smtp_from
                client_msg['To'] = client_email
                client_msg['Subject'] = client_subject
                client_msg.attach(MIMEText(client_html, 'html', 'utf-8'))
                
                await aiosmtplib.send(
                    client_msg,
                    hostname=smtp_host,
                    port=smtp_port,
                    username=smtp_user,
                    password=smtp_password,
                    start_tls=True
                )
                result["client_sent"] = True
                logger.info(f"📧 CLIENT_EMAIL_SENT to={client_email} subj=\"{client_subject}\" body_hash={_hash(client_html)}")
            except Exception as e:
                logger.error(f"❌ CLIENT_EMAIL_EXCEPTION to={client_email}: {e}")
    
    except Exception as e:
        logger.error(f"❌ EMAIL_GENERAL_EXCEPTION: {e}")
    
    return result

# Connect SPA module to central dispatcher
set_spa_dispatcher(dispatch_booking_notifications)

# ============================================
# Email Notification Helper
# ============================================
# 🔒🔒🔒 LOCKED ZONE START - EMAIL NOTIFICATION 🔒🔒🔒
# DO NOT MODIFY WITHOUT EXPLICIT OWNER APPROVAL
# See: /app/LOCKDOWN_RULES.md
async def send_booking_emails(appointment_data: dict):
    """
    🔒 LOCKED - Send booking confirmation emails to client and owner.
    
    IMPORTANT: Admin gets ADMIN template, Client gets CLIENT template!
    Template choice does NOT depend on booking type (massage/spa).
    
    Args:
        appointment_data: Dictionary containing appointment details
        
    Note: This function will NOT raise exceptions to prevent blocking booking creation.
    """
    from email_templates import BookingEmailData, render_admin_email
    from email_templates.adapters import build_client_email_for_massage
    
    logger.info(f"📧 EMAIL FUNCTION CALLED for: {appointment_data.get('client_email')}")
    try:
        # Get SMTP settings from environment
        smtp_host = os.environ.get('SMTP_HOST')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_user = os.environ.get('SMTP_USER')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        smtp_from = os.environ.get('SMTP_FROM', smtp_user)
        smtp_to_owner = os.environ.get('SMTP_TO_OWNER')
        
        logger.info(f"📧 SMTP Config: host={smtp_host}, port={smtp_port}, user={smtp_user}, password={'SET' if smtp_password else 'EMPTY'}")
        
        # Check if SMTP is configured
        if not smtp_host or not smtp_user or smtp_password == 'PLACEHOLDER_APP_PASSWORD':
            logger.warning("⚠️ Email not sent - SMTP not configured (PLACEHOLDER password detected)")
            return
        
        # Extract appointment details
        client_name = f"{appointment_data.get('client_first_name', '')} {appointment_data.get('client_last_name', '')}".strip()
        client_phone = appointment_data.get('client_phone', 'N/A')
        client_email = appointment_data.get('client_email')
        start_time = appointment_data.get('start_time')
        service_name = appointment_data.get('service_name', 'N/A')
        appt_id = appointment_data.get('id', 'unknown')
        
        # Format datetime
        if isinstance(start_time, str):
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                formatted_date = start_dt.strftime('%d.%m.%Y')
                formatted_time_only = start_dt.strftime('%H:%M')
            except:
                formatted_date = start_time
                formatted_time_only = ""
        else:
            formatted_date = start_time.strftime('%d.%m.%Y') if start_time else 'N/A'
            formatted_time_only = start_time.strftime('%H:%M') if start_time else ''
        
        # ============================================
        # ADMIN EMAIL - Uses ADMIN template (plain, internal)
        # ============================================
        admin_data = BookingEmailData(
            salon_name="Bua Luang Thai Spa",
            client_full_name=client_name,
            client_phone=client_phone,
            client_email=client_email or '',
            service_title=service_name,
            service_details=None,
            date_str=formatted_date,
            time_str=formatted_time_only,
            duration_min=None,
            price=appointment_data.get('price') or appointment_data.get('final_total'),
            address_line="Abebe Bikile 10A, Beograd",
            contact_email="bualuangthailandspa@gmail.com",
            contact_phone="+381 62 625 500",
            booking_type="massage"
        )
        admin_subject, admin_html = render_admin_email(admin_data)
        
        # Send to owner (ADMIN template)
        try:
            owner_msg = MIMEMultipart()
            owner_msg['From'] = smtp_from
            owner_msg['To'] = smtp_to_owner
            owner_msg['Subject'] = admin_subject
            owner_msg.attach(MIMEText(admin_html, 'html', 'utf-8'))
            
            await aiosmtplib.send(
                owner_msg,
                hostname=smtp_host,
                port=smtp_port,
                username=smtp_user,
                password=smtp_password,
                start_tls=True
            )
            logger.info(f"📧 ADMIN_EMAIL_SENT to={smtp_to_owner} template=ADMIN appt_id={appt_id}")
        except Exception as e:
            logger.error(f"❌ Failed to send email to owner: {str(e)}")
        
        # ============================================
        # CLIENT EMAIL - Uses CLIENT template (branded, beautiful)
        # ============================================
        if client_email:
            client_subject, client_html = build_client_email_for_massage(appointment_data)
            
            client_msg = MIMEMultipart()
            client_msg['From'] = smtp_from
            client_msg['To'] = client_email
            client_msg['Subject'] = client_subject
            client_msg.attach(MIMEText(client_html, 'html', 'utf-8'))
            
            try:
                await aiosmtplib.send(
                    client_msg,
                    hostname=smtp_host,
                    port=smtp_port,
                    username=smtp_user,
                    password=smtp_password,
                    start_tls=True
                )
                logger.info(f"📧 CLIENT_EMAIL_SENT to={client_email} template=CLIENT appt_id={appt_id}")
            except Exception as e:
                logger.error(f"❌ Failed to send email to client: {str(e)}")
        else:
            logger.info(f"ℹ️ CLIENT_EMAIL_SKIPPED - no email provided appt_id={appt_id}")
            
    except Exception as e:
        # Catch all errors to prevent blocking booking
        logger.error(f"❌ Email sending failed (non-blocking): {str(e)}")
# 🔒🔒🔒 LOCKED ZONE END - EMAIL NOTIFICATION 🔒🔒🔒


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

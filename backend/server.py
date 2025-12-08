from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any, Union
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

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
    duration: int = Field(..., description="Duration in minutes: 15, 30, 45, 60, 90, 120, 150, 165, 180, 195, 210, 225, 240, 255, 300, 360, 420")
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
    # Snapshot fields for price history (prevents retroactive price changes)
    snapshot_price: Optional[float] = None
    snapshot_original_price: Optional[float] = None
    snapshot_discount_percentage: Optional[float] = None
    snapshot_discount_amount: Optional[float] = None


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
    original_price: float
    final_price: float

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
    
    # Category and pricing snapshot (provided by website)
    category: str = "Kartica masaza za parove"
    original_price: float
    final_price: float
    discount_percentage: float
    discount_amount: float
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
        # Calculate final_price using best discount logic
        service_code = service.get('service_code')
        if service_code:
            discount_info = await get_best_discount_for_service_code(service_code)
            # IMPORTANT: service['price'] IS the original price
            original_price = service.get('price', 0)
            
            # Apply best discount
            best_discount = discount_info['best_discount_percentage']
            final_price = original_price * (1 - best_discount / 100.0)
            
            service['final_price'] = round(final_price, 2)
            service['discount_percentage'] = best_discount
        # 🔒 END STABLE ZONE
        else:
            # Fallback if service_code doesn't exist (shouldn't happen after migration)
            try:
                original_price = service.get('price', 0)
                discount = service.get('discount_percentage', 0)
                service['final_price'] = round(original_price * (1 - discount / 100.0), 2)
            except (AttributeError, TypeError) as e:
                logger.warning(f"Error calculating fallback price for service {service.get('name', 'unknown')}: {e}")
                service['final_price'] = service.get('price', 0)
    
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
    if service_code:
        discount_info = await get_best_discount_for_service_code(service_code)
        original_price = service.get('metadata', {}).get('original_price', service.get('price', 0))
        
        # Apply best discount
        best_discount = discount_info['best_discount_percentage']
        final_price = original_price * (1 - best_discount / 100.0)
        
        service['final_price'] = round(final_price, 2)
        service['discount_percentage'] = best_discount
    else:
        original_price = service.get('metadata', {}).get('original_price', service.get('price', 0))
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
    """Update discount percentage and automatically adjust price"""
    if discount < 0 or discount > 100:
        raise HTTPException(status_code=400, detail="Discount must be between 0 and 100")
    
    existing = await db.services.find_one({"id": service_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Get original price from metadata if it exists, otherwise use current price
    metadata = existing.get('metadata')
    if metadata and isinstance(metadata, dict) and 'original_price' in metadata:
        original_price = metadata['original_price']
    else:
        # First time setting discount, save current price as original
        original_price = existing.get('price', 0)
    
    # Calculate new discounted price
    if discount > 0:
        discounted_price = original_price * (1 - discount / 100)
        update_data = {
            "price": discounted_price,
            "discount_percentage": discount,
            "metadata": {
                "original_price": original_price,
                "discount_applied": discount,
                "final_price": discounted_price
            }
        }
    else:
        # No discount - restore original price
        update_data = {
            "price": original_price,
            "discount_percentage": 0,
            "metadata": None
        }
    
    logger.info(f"💸 Service {service_id}: Discount {discount}% - Price {existing.get('price')} → {update_data['price']}")
    
    await db.services.update_one(
        {"id": service_id}, 
        {"$set": update_data}
    )
    
    updated = await db.services.find_one({"id": service_id}, {"_id": 0})
    if isinstance(updated['created_at'], str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    
    return updated

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
    return appointment_obj

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
    # Verify therapist exists
    therapist = await db.therapists.find_one({"id": couple.therapist_id})
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    # Remove timezone info if present
    start_time = couple.start_time.replace(tzinfo=None) if couple.start_time.tzinfo else couple.start_time
    
    # Calculate total duration
    total_duration = couple.person1_massage.duration + couple.person2_massage.duration
    end_time = start_time + timedelta(minutes=total_duration)
    
    # Create service name description
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
    # Log incoming request for debugging
    logger.info(f"Couple appointment request - duration_type: {couple.duration_type}, person1_services: {couple.person1_services}, person2_services: {couple.person2_services}")
    logger.info(f"🔍 OLD ENDPOINT - DISCOUNT FROM WEBSITE: {couple.discount_couples_massage}%")
    
    # Verify therapist exists
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
    
    # Calculate total price
    total_price = 0
    person1_service_names = []
    person2_service_names = []
    
    for service_id in couple.person1_services:
        service = service_map[service_id]
        total_price += service['price']
        person1_service_names.append(service['name'])
    
    for service_id in couple.person2_services:
        service = service_map[service_id]
        total_price += service['price']
        person2_service_names.append(service['name'])
    
    # Apply couple discount if provided
    discount_percentage = couple.discount_couples_massage if couple.discount_couples_massage else 0.0
    original_price = total_price
    
    # Calculate discounted price
    if discount_percentage > 0:
        discounted_price = total_price * (1 - discount_percentage / 100)
    else:
        discounted_price = total_price
    
    # Calculate total duration (both persons are serviced simultaneously - together at the same time)
    total_duration = couple.duration_type  # 60, 90, or 120 minutes (they go together, not one after another)
    
    # Remove timezone info if present
    start_time = couple.start_time.replace(tzinfo=None) if couple.start_time.tzinfo else couple.start_time
    end_time = start_time + timedelta(minutes=total_duration)
    
    # Create service name description
    if couple.duration_type == 60:
        service_name = f"Masaža za parove - 120 min (2x60 min)"
    elif couple.duration_type == 90:
        service_name = f"Masaža za parove - 180 min (2x90 min)"
    else:  # 120
        service_name = f"Masaža za parove - 240 min (2x120 min)"
    
    # Create a dummy service entry for couple package
    couple_service_id = str(uuid.uuid4())
    couple_service = {
        "id": couple_service_id,
        "name": service_name,
        "duration": total_duration,
        "price": discounted_price,  # STORE DISCOUNTED PRICE
        "description": f"Osoba 1: {', '.join(person1_service_names)} | Osoba 2: {', '.join(person2_service_names)}",
        "created_at": datetime.now().isoformat(),
        "category": "couple",
        "discount_percentage": discount_percentage,
        "metadata": {
            "original_price": original_price,
            "discount_applied": discount_percentage,
            "final_price": discounted_price
        } if discount_percentage > 0 else None
    }
    
    # Store couple service details
    await db.services.insert_one(couple_service)
    
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
        # CRITICAL: Add snapshot fields to appointment object
        "snapshot_price": discounted_price,
        "snapshot_original_price": original_price,
        "snapshot_discount_percentage": discount_percentage
    }
    
    appointment_obj = Appointment(**appointment_dict)
    
    doc = appointment_obj.model_dump()
    doc['start_time'] = doc['start_time'].isoformat()
    doc['end_time'] = doc['end_time'].isoformat()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.appointments.insert_one(doc)
    return appointment_obj


@api_router.post("/book-couple-appointment", response_model=Appointment)
async def book_couple_appointment_website(couple: CoupleAppointmentWebsite):
    """
    Website-compatible couple appointment endpoint
    Therapist is NOT assigned here - receptionist assigns manually later
    
    ACCEPTS NEW FORMAT:
    - person1_services: [{ service_id, name, duration, original_price, final_price }]
    - person2_services: [{ service_id, name, duration, original_price, final_price }]
    - category, original_price, final_price, discount_percentage, discount_amount
    - NO recalculation - uses snapshot values from payload
    """
    
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
        
        # Use snapshot values from website payload (NO recalculation)
        logger.info(f"📸 COUPLE: Using snapshot from website payload")
        original_price = couple.original_price
        discounted_price = couple.final_price
        discount_percentage = couple.discount_percentage
        discount_amount = couple.discount_amount
        
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
        
        # Create service name description based on total duration
        service_name = f"Masaža za parove - {total_duration*2} min (2x{total_duration} min)"
        
        # Create a dummy service entry for couple package
        # Store DISCOUNTED price in price field, and discount percentage in metadata
        couple_service_id = str(uuid.uuid4())
        
        # Use category from website payload if provided, otherwise default to "couple"
        category = couple.category if couple.category else "couple"
        
        couple_service = {
            "id": couple_service_id,
            "name": service_name,
            "duration": total_duration,
            "price": discounted_price,  # STORE DISCOUNTED PRICE (what customer pays)
            "description": f"Osoba 1: {', '.join(person1_service_names)} | Osoba 2: {', '.join(person2_service_names)}",
            "created_at": datetime.now().isoformat(),
            "category": category,  # Use category from website or default "couple"
            "discount_percentage": discount_percentage,
            "discount_amount": discount_amount,
            "has_discount": discount_percentage > 0,  # Flag for easier filtering
            "metadata": {
                "original_price": original_price,
                "discount_applied": discount_percentage,
                "final_price": discounted_price
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
            # CRITICAL: Add snapshot fields to appointment object (from website payload)
            "snapshot_price": discounted_price,
            "snapshot_original_price": original_price,
            "snapshot_discount_percentage": discount_percentage,
            "snapshot_discount_amount": discount_amount
        }
        
        appointment_obj = Appointment(**appointment_dict)
        
        doc = appointment_obj.model_dump()
        doc['start_time'] = doc['start_time'].isoformat()
        doc['end_time'] = doc['end_time'].isoformat()
        doc['created_at'] = doc['created_at'].isoformat()
        
        await db.appointments.insert_one(doc)
        
        logger.info(f"✅ Couple appointment created successfully: {appointment_obj.id}")
        logger.info(f"   Service ID: {couple_service_id}")
        logger.info(f"   Category: {category}")
        logger.info(f"   Snapshot: original={original_price}, final={discounted_price}, discount={discount_percentage}%")
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


@api_router.get("/appointments", response_model=List[Appointment])
async def get_appointments(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    therapist_id: Optional[str] = Query(None),
    status: Optional[AppointmentStatus] = Query(None)
):
    """Get appointments with optional filters"""
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
    
    appointments = await db.appointments.find(query, {"_id": 0}).to_list(1000)
    
    for apt in appointments:
        if isinstance(apt['start_time'], str):
            apt['start_time'] = datetime.fromisoformat(apt['start_time'])
        if isinstance(apt['end_time'], str):
            apt['end_time'] = datetime.fromisoformat(apt['end_time'])
        if isinstance(apt['created_at'], str):
            apt['created_at'] = datetime.fromisoformat(apt['created_at'])
    
    return appointments

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
    """Get count of unviewed appointments"""
    count = await db.appointments.count_documents({"is_viewed": False})
    return {"count": count}

@api_router.get("/appointments/unviewed/list")
async def get_unviewed_appointments():
    """Get list of unviewed appointments with service details"""
    appointments = await db.appointments.find(
        {"is_viewed": False}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
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
        
        # Add service details
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
        
        # Build clean response object
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
            'is_viewed': apt.get('is_viewed', False)
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
    """Mark all appointments as viewed"""
    result = await db.appointments.update_many(
        {"is_viewed": False},
        {"$set": {"is_viewed": True}}
    )
    return {"message": f"Marked {result.modified_count} appointments as viewed"}



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
    categories = {
        "Obicne masaze": {
            "appointments_count": 0,
            "revenue": 0,
            "original_revenue": 0,
            "discount_given": 0,
            "with_discount": 0,
            "without_discount": 0
        },
        "SPA": {
            "appointments_count": 0,
            "revenue": 0,
            "original_revenue": 0,
            "discount_given": 0,
            "with_discount": 0,
            "without_discount": 0
        },
        "SPA Special kartica": {
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
# Root route
# ============================================
@api_router.get("/")
async def root():
    return {"message": "Spa & Massage Booking System API", "version": "1.0"}


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

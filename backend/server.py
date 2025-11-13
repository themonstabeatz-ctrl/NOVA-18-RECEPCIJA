from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
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
    duration: int = Field(..., description="Duration in minutes: 30, 45, 60, 90, 120, 180, or 240")
    price: float = Field(..., description="Price in RSD")
    description: Optional[str] = None
    category: Optional[str] = Field(default="regular", description="Service category: regular, couple")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata for couple appointments")
    discount_percentage: float = Field(default=0.0, ge=0, le=100, description="Active discount percentage (0-100%)")

class ServiceCreate(ServiceBase):
    pass

class Service(ServiceBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now())


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
    therapist_id: str
    service_id: str
    start_time: datetime
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    body_map_gender: Optional[str] = None  # "male" or "female"
    body_map_points: Optional[List[Dict[str, Any]]] = []  # List of marked points

class AppointmentCreate(AppointmentBase):
    pass

class Appointment(AppointmentBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    end_time: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    is_viewed: bool = False  # Flag for notifications


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
    therapist_id: str
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
    therapist_id: str
    start_time: datetime
    duration_type: int  # 60, 90, or 120 (base duration per person)
    person1_services: List[str]  # List of service IDs for person 1
    person2_services: List[str]  # List of service IDs for person 2
    status: AppointmentStatus = AppointmentStatus.SCHEDULED


# Website compatible model - therapist_id is optional, will be auto-assigned
class CoupleAppointmentWebsite(BaseModel):
    client_first_name: str
    client_last_name: str
    client_phone: str
    client_email: Optional[EmailStr] = None
    start_time: datetime
    duration_type: int  # 60, 90, or 120 (base duration per person)
    person1_services: List[str]  # List of service IDs for person 1
    person2_services: List[str]  # List of service IDs for person 2
    discount_couples_massage: float = 0.0  # No default discount - only if explicitly set


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
    doc = service_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.services.insert_one(doc)
    return service_obj

@api_router.get("/services", response_model=List[Service])
async def get_services():
    """Get all services"""
    services = await db.services.find({}, {"_id": 0}).to_list(1000)
    
    for service in services:
        if isinstance(service['created_at'], str):
            service['created_at'] = datetime.fromisoformat(service['created_at'])
    
    return services

@api_router.get("/services/{service_id}", response_model=Service)
async def get_service(service_id: str):
    """Get a specific service"""
    service = await db.services.find_one({"id": service_id}, {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if isinstance(service['created_at'], str):
        service['created_at'] = datetime.fromisoformat(service['created_at'])
    
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
    """Update only the discount percentage for a service"""
    if discount < 0 or discount > 100:
        raise HTTPException(status_code=400, detail="Discount must be between 0 and 100")
    
    existing = await db.services.find_one({"id": service_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Service not found")
    
    await db.services.update_one(
        {"id": service_id}, 
        {"$set": {"discount_percentage": discount}}
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
    """Create a new appointment"""
    # Verify therapist exists
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
    
    # Create appointment object with corrected start_time
    appointment_dict = appointment.model_dump()
    appointment_dict['start_time'] = start_time
    appointment_dict['end_time'] = end_time
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
    
    # Create appointment
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
        "body_map_points": []
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
    """Create a couple appointment with 15% discount (OLD VERSION - backward compatibility)"""
    # Log incoming request for debugging
    logger.info(f"Couple appointment request - duration_type: {couple.duration_type}, person1_services: {couple.person1_services}, person2_services: {couple.person2_services}")
    
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
    
    # Calculate total price WITHOUT any discount
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
    
    # NO DISCOUNT APPLIED - use original price
    
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
        "price": total_price,  # ORIGINAL PRICE - NO DISCOUNT
        "description": f"Osoba 1: {', '.join(person1_service_names)} | Osoba 2: {', '.join(person2_service_names)}",
        "created_at": datetime.now().isoformat(),
        "category": "couple",
        "discount_percentage": 0.0
    }
    
    # Store couple service details
    await db.services.insert_one(couple_service)
    
    # Create appointment with couple service
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
        "body_map_points": []
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
    Automatically assigns first available therapist if not provided
    """
    logger.info(f"Website couple booking - duration_type: {couple.duration_type}, person1: {couple.person1_services}, person2: {couple.person2_services}")
    
    # Get first available therapist
    therapists = await db.therapists.find({"is_active": True}, {"_id": 0}).to_list(10)
    if not therapists:
        raise HTTPException(status_code=500, detail="No therapists available")
    
    therapist_id = therapists[0]['id']
    logger.info(f"Auto-assigned therapist: {therapist_id}")
    
    # Fetch all services for both persons
    all_service_ids = couple.person1_services + couple.person2_services
    services = await db.services.find({"id": {"$in": all_service_ids}}).to_list(100)
    service_map = {s['id']: s for s in services}
    
    # Verify all services exist
    for service_id in all_service_ids:
        if service_id not in service_map:
            raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
    
    # Calculate total price with discount
    total_price = 0
    person1_service_names = []
    person2_service_names = []
    
    for service_id in couple.person1_services:
        service = service_map[service_id]
        original_price = service['price']
        discount_pct = service.get('discount_percentage', 0)
        discounted_price = original_price * (1 - discount_pct / 100)
        total_price += discounted_price
        person1_service_names.append(service['name'])
    
    for service_id in couple.person2_services:
        service = service_map[service_id]
        original_price = service['price']
        discount_pct = service.get('discount_percentage', 0)
        discounted_price = original_price * (1 - discount_pct / 100)
        total_price += discounted_price
        person2_service_names.append(service['name'])
    
    # NO DISCOUNT APPLIED - use original total price
    
    # Calculate total duration (both persons are serviced simultaneously - together at the same time)
    total_duration = couple.duration_type  # 60, 90, or 120 minutes (they go together, not one after another)
    
    # Remove timezone info if present
    start_time = couple.start_time.replace(tzinfo=None) if couple.start_time.tzinfo else couple.start_time
    end_time = start_time + timedelta(minutes=total_duration)
    
    # Create service name description (WITHOUT discount in name)
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
        "price": total_price,  # ORIGINAL PRICE - NO DISCOUNT
        "description": f"Osoba 1: {', '.join(person1_service_names)} | Osoba 2: {', '.join(person2_service_names)}",
        "created_at": datetime.now().isoformat(),
        "category": "couple",
        "discount_percentage": 0.0
    }
    
    # Store couple service details
    await db.services.insert_one(couple_service)
    
    # Create appointment with couple service
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
        "body_map_points": []
    }
    
    appointment_obj = Appointment(**appointment_dict)
    
    doc = appointment_obj.model_dump()
    doc['start_time'] = doc['start_time'].isoformat()
    doc['end_time'] = doc['end_time'].isoformat()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.appointments.insert_one(doc)
    
    logger.info(f"✅ Couple appointment created successfully: {appointment_obj.id}")
    return appointment_obj


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
    
    # Verify therapist exists
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
    
    # Check for overlapping appointments (excluding current appointment)
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
        service_price = service.get('price') if service else None
        service_duration = service.get('duration') if service else None
        service_category = service.get('category', 'regular') if service else None
        
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
    
    # Initialize category stats
    categories = {
        "Obicne masaze": {
            "appointments_count": 0,
            "revenue": 0,
            "original_revenue": 0,
            "discount_given": 0,
            "with_discount": 0,
            "without_discount": 0
        },
        "Kartica Masaza za parove": {
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
        
        category = service.get('category', 'Obicne masaze')
        original_price = service.get('price', 0)
        discount_percentage = service.get('discount_percentage', 0)
        discounted_price = original_price * (1 - discount_percentage / 100)
        discount_amount = original_price - discounted_price
        
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
        categories[category]["revenue"] += discounted_price
        categories[category]["original_revenue"] += original_price
        categories[category]["discount_given"] += discount_amount
        
        if discount_percentage > 0:
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
                "discounted_price": discounted_price,
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
        discount_stats[discount_key]["revenue"] += discounted_price
    
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
                "appointments": []
            }
        
        # Calculate price for this appointment
        original_price = service.get('price', 0)
        discount_percentage = service.get('discount_percentage', 0)
        total_price = original_price * (1 - discount_percentage / 100)
        
        appointments_by_service[service_id]["appointments"].append({
            "id": apt['id'],
            "client_first_name": apt.get('client_first_name'),
            "client_last_name": apt.get('client_last_name'),
            "client_phone": apt.get('client_phone'),
            "client_email": apt.get('client_email'),
            "start_time": apt['start_time'],
            "end_time": apt.get('end_time'),
            "status": apt['status'],
            "total_price": total_price,
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

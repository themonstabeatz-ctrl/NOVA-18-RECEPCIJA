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
    duration: int = Field(..., description="Duration in minutes: 30, 45, 60, 90, or 120")
    price: float = Field(..., description="Price in RSD")
    description: Optional[str] = None

class ServiceCreate(ServiceBase):
    pass

class Service(ServiceBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now())


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

class AppointmentCreate(AppointmentBase):
    pass

class Appointment(AppointmentBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    end_time: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now())


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
    if service.duration not in [30, 45, 60, 90, 120]:
        raise HTTPException(status_code=400, detail="Duration must be 30, 45, 60, 90, or 120 minutes")
    
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
    if service.duration not in [30, 45, 60, 90, 120]:
        raise HTTPException(status_code=400, detail="Duration must be 30, 45, 60, 90, or 120 minutes")
    
    existing = await db.services.find_one({"id": service_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Service not found")
    
    update_data = service.model_dump()
    await db.services.update_one({"id": service_id}, {"$set": update_data})
    
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
    
    # Check for overlapping appointments
    overlapping = await db.appointments.find({
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
        
        # Get service price
        service = service_map.get(apt['service_id'], {})
        price = service.get('price', 0)
        
        stats_by_therapist[tid]["total_hours"] += duration_hours
        stats_by_therapist[tid]["total_revenue"] += price
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
        total_revenue += service.get('price', 0)
    
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

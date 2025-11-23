"""
Create a test appointment with discount for this week
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timezone
import uuid

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def create_test_appointment():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Create appointment with discount
    appointment = {
        "id": str(uuid.uuid4()),
        "client_first_name": "Ana",
        "client_last_name": "Popović",
        "client_phone": "+381641234567",
        "client_email": "ana@example.com",
        "therapist_id": "4cd2ce85-3e9e-41cd-83fc-81a4a48dda2f",
        "service_id": "d1ee03e7-8c42-478e-854c-8dc38e97f71e",  # Masaža stopala - 60 min
        "start_time": "2025-11-23T15:00:00",
        "end_time": "2025-11-23T16:00:00",
        "status": "scheduled",
        "created_at": datetime.now(timezone.utc),
        "is_viewed": False,
        "snapshot_original_price": 3150.0,
        "snapshot_price": 2835.0,
        "snapshot_discount_percentage": 10.0
    }
    
    result = await db.appointments.insert_one(appointment)
    print(f"✅ Created appointment: Ana Popović")
    print(f"   ID: {appointment['id']}")
    print(f"   Original: {appointment['snapshot_original_price']} RSD")
    print(f"   Final: {appointment['snapshot_price']} RSD")
    print(f"   Discount: {appointment['snapshot_discount_percentage']}%")
    print(f"   Date: {appointment['start_time']}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_test_appointment())

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def reset_viewed():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    result = await db.appointments.update_one(
        {"client_first_name": "Ana"},
        {"$set": {"is_viewed": False}}
    )
    
    print(f"✅ Reset is_viewed to False for Ana")
    client.close()

asyncio.run(reset_viewed())

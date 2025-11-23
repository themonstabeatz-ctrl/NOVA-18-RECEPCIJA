"""
Script to fix couple services: set is_couple=True for all services with category='couple'
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def fix_couple_services():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🔍 Finding services with category='couple' and is_couple=False...")
    
    # Find all services with category='couple' but is_couple=False
    services_to_fix = await db.services.find({
        "category": "couple",
        "is_couple": False
    }).to_list(1000)
    
    print(f"Found {len(services_to_fix)} services to fix")
    
    if len(services_to_fix) == 0:
        print("✅ No services to fix!")
        return
    
    # Update all matching services
    result = await db.services.update_many(
        {"category": "couple", "is_couple": False},
        {"$set": {"is_couple": True}}
    )
    
    print(f"✅ Updated {result.modified_count} services")
    print(f"   Set is_couple=True for all services with category='couple'")
    
    # Verify the fix
    couple_services = await db.services.find({"is_couple": True}).to_list(1000)
    print(f"\n✅ Verification: Now have {len(couple_services)} services with is_couple=True")
    
    # Show first 5 examples
    print("\n📋 Examples:")
    for service in couple_services[:5]:
        print(f"   - {service['name']}: category={service['category']}, is_couple={service['is_couple']}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_couple_services())

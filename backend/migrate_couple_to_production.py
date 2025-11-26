"""
Script to migrate couple services from local to production
"""
import asyncio
import json
import requests
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Production API URL
PRODUCTION_API = "https://spabooking.emergent.host/api"

async def migrate_couple_services():
    # Connect to local MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🔍 Preuzimanje couple services iz lokalne baze...")
    
    # Get all couple services from local DB
    couple_services = await db.services.find({
        "is_couple": True
    }, {"_id": 0}).to_list(1000)
    
    print(f"✅ Pronađeno {len(couple_services)} couple services\n")
    
    # Upload to production via API
    success_count = 0
    error_count = 0
    
    for i, service in enumerate(couple_services, 1):
        try:
            # POST to production API
            response = requests.post(
                f"{PRODUCTION_API}/services",
                json=service,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                success_count += 1
                print(f"✅ {i}/{len(couple_services)} - {service['name'][:50]}")
            else:
                error_count += 1
                print(f"❌ {i}/{len(couple_services)} - {service['name'][:50]} - Error: {response.status_code}")
                
        except Exception as e:
            error_count += 1
            print(f"❌ {i}/{len(couple_services)} - {service['name'][:50]} - Exception: {str(e)[:50]}")
    
    print(f"\n📊 REZULTAT:")
    print(f"   ✅ Uspešno: {success_count}")
    print(f"   ❌ Greške: {error_count}")
    print(f"   📋 Ukupno: {len(couple_services)}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate_couple_services())

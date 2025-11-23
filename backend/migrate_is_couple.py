"""
Migration script to add is_couple field to services.
Marks services in "Kartica Masaza za parove" category as couple services.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']


async def migrate_is_couple():
    """Main migration function"""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print(f"🔄 Starting is_couple migration for database: {db_name}")
    
    # Count services before
    total_services = await db.services.count_documents({})
    print(f"📊 Total services: {total_services}")
    
    # Mark [PAROVI] services as couple services
    # These are services in "Kartica Masaza za parove" category
    result_parovi = await db.services.update_many(
        {"category": "Kartica Masaza za parove"},
        {"$set": {"is_couple": True}}
    )
    
    print(f"✅ Marked {result_parovi.modified_count} services in 'Kartica Masaza za parove' as is_couple=True")
    
    # Mark all other services as single (is_couple=False)
    result_single = await db.services.update_many(
        {"category": {"$ne": "Kartica Masaza za parove"}},
        {"$set": {"is_couple": False}}
    )
    
    print(f"✅ Marked {result_single.modified_count} services as is_couple=False")
    
    # Verify results
    couple_count = await db.services.count_documents({"is_couple": True})
    single_count = await db.services.count_documents({"is_couple": False})
    
    print(f"\n📊 Final count:")
    print(f"   Couple services (is_couple=True): {couple_count}")
    print(f"   Single services (is_couple=False): {single_count}")
    print(f"   Total: {couple_count + single_count}")
    
    # Show some examples
    print(f"\n📋 Example couple services:")
    couple_examples = await db.services.find(
        {"is_couple": True},
        {"name": 1, "category": 1, "is_couple": 1, "_id": 0}
    ).limit(5).to_list(5)
    
    for service in couple_examples:
        print(f"   ✓ {service['name']} (category: {service['category']}, is_couple: {service['is_couple']})")
    
    print(f"\n📋 Example single services:")
    single_examples = await db.services.find(
        {"is_couple": False},
        {"name": 1, "category": 1, "is_couple": 1, "_id": 0}
    ).limit(5).to_list(5)
    
    for service in single_examples:
        print(f"   ✓ {service['name']} (category: {service['category']}, is_couple: {service['is_couple']})")
    
    client.close()
    print(f"\n✅ Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate_is_couple())

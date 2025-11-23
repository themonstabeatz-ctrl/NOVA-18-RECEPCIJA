"""
Migration script to SEPARATE service_code for single and couple services.

WHY: Currently, single and couple services share the same service_code,
causing the system to apply the highest discount from BOTH.

SOLUTION: Give couple services a distinct service_code with _COUPLE suffix.

Example:
- Single: "Tradicionalna tajlandska - 60 min" -> "TRADICIONALNA_TAJLANDSKA_MASAZA_60"
- Couple: "[PAROVI] Tradicionalna tajlandska - 60 min" -> "TRADICIONALNA_TAJLANDSKA_MASAZA_60_COUPLE"
"""

import asyncio
import os
import re
import unicodedata
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']


def generate_service_code(name: str, duration: int, is_couple: bool = False) -> str:
    """
    Generate a unique service code from service name and duration.
    
    IMPORTANT: Single and Couple services have DIFFERENT service codes!
    """
    # Check if this is a couple service from name
    is_couple_from_name = name.startswith('[PAROVI]')
    is_couple_service = is_couple or is_couple_from_name
    
    # Remove [PAROVI] prefix and other category prefixes
    clean_name = re.sub(r'^\[.*?\]\s*', '', name)
    
    # Remove duration suffix if present
    clean_name = re.sub(r'\s*-?\s*\d+\s*min\s*$', '', clean_name, flags=re.IGNORECASE)
    
    # Normalize unicode characters
    clean_name = unicodedata.normalize('NFKD', clean_name)
    clean_name = clean_name.encode('ascii', 'ignore').decode('ascii')
    
    # Convert to uppercase and replace spaces/special chars with underscore
    clean_name = re.sub(r'[^a-zA-Z0-9]+', '_', clean_name.upper())
    
    # Remove leading/trailing underscores
    clean_name = clean_name.strip('_')
    
    # Add duration
    service_code = f"{clean_name}_{duration}"
    
    # CRITICAL: Add _COUPLE suffix for couple services
    if is_couple_service:
        service_code = f"{service_code}_COUPLE"
    
    return service_code


async def migrate_separate_codes():
    """Main migration function"""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print(f"🔄 Starting service_code separation migration for database: {db_name}")
    print(f"📋 Goal: Separate single and couple service codes")
    print("")
    
    # Get all services
    services = await db.services.find({}, {"_id": 0}).to_list(1000)
    
    print(f"📊 Found {len(services)} services to migrate")
    print("")
    
    updated_count = 0
    changes = []
    
    for service in services:
        service_id = service.get('id')
        name = service.get('name')
        duration = service.get('duration')
        old_code = service.get('service_code')
        is_couple = service.get('is_couple', False)
        
        # Generate NEW service_code with couple separation
        new_code = generate_service_code(name, duration, is_couple)
        
        # Only update if changed
        if old_code != new_code:
            await db.services.update_one(
                {"id": service_id},
                {"$set": {"service_code": new_code}}
            )
            updated_count += 1
            changes.append({
                'name': name,
                'old': old_code,
                'new': new_code,
                'is_couple': is_couple
            })
            print(f"✅ {name[:50]:<50}")
            print(f"   OLD: {old_code}")
            print(f"   NEW: {new_code}")
            print("")
    
    print(f"🎉 Migration completed!")
    print(f"📈 Updated {updated_count} services")
    print("")
    
    # Show summary of changes
    if changes:
        print("📋 Summary of Changes:")
        print("=" * 80)
        
        couple_changes = [c for c in changes if c['is_couple']]
        single_changes = [c for c in changes if not c['is_couple']]
        
        if couple_changes:
            print(f"\n✅ Couple services updated: {len(couple_changes)}")
            for c in couple_changes[:5]:
                print(f"   {c['name'][:60]:<60} -> {c['new']}")
        
        if single_changes:
            print(f"\n✅ Single services updated: {len(single_changes)}")
            for c in single_changes[:5]:
                print(f"   {c['name'][:60]:<60} -> {c['new']}")
    
    # Verify no more shared codes between single and couple
    print(f"\n🔍 Verification:")
    print("=" * 80)
    
    # Find if any single and couple still share service_code
    pipeline = [
        {"$group": {
            "_id": "$service_code",
            "services": {"$push": {"name": "$name", "is_couple": "$is_couple"}},
            "count": {"$sum": 1}
        }},
        {"$match": {"count": {"$gt": 1}}}
    ]
    
    shared_codes = await db.services.aggregate(pipeline).to_list(100)
    
    problems = []
    for item in shared_codes:
        service_code = item['_id']
        services = item['services']
        
        # Check if both single and couple exist
        has_single = any(not s['is_couple'] for s in services)
        has_couple = any(s['is_couple'] for s in services)
        
        if has_single and has_couple:
            problems.append(service_code)
            print(f"⚠️ service_code '{service_code}' still shared:")
            for s in services:
                print(f"   - {s['name']} (is_couple={s['is_couple']})")
    
    if not problems:
        print("✅ NO SHARED CODES between single and couple services!")
        print("✅ Single and Couple services are now COMPLETELY SEPARATED!")
    else:
        print(f"⚠️ Found {len(problems)} service_codes still shared")
    
    client.close()
    print(f"\n✅ Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate_separate_codes())

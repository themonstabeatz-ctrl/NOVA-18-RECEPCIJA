"""
Migration script to add service_code to all existing services.
This script will:
1. Generate service_code for each service based on name and duration
2. Ensure original_price is stored in metadata
3. Update all services in the database
"""

import asyncio
import os
import sys
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


def generate_service_code(name: str, duration: int) -> str:
    """
    Generate a unique service code from service name and duration.
    """
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
    
    return service_code


async def migrate_service_codes():
    """Main migration function"""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print(f"🔄 Starting migration for database: {db_name}")
    
    # Get all services
    services = await db.services.find({}, {"_id": 0}).to_list(1000)
    
    print(f"📊 Found {len(services)} services to migrate")
    
    updated_count = 0
    service_code_map = {}  # Track service codes for reporting
    
    for service in services:
        service_id = service.get('id')
        name = service.get('name')
        duration = service.get('duration')
        price = service.get('price', 0.0)
        metadata = service.get('metadata', {})
        
        # Generate service_code
        service_code = generate_service_code(name, duration)
        
        # Track for reporting
        if service_code not in service_code_map:
            service_code_map[service_code] = []
        service_code_map[service_code].append({
            'name': name,
            'category': service.get('category', 'N/A'),
            'discount': service.get('discount_percentage', 0)
        })
        
        # Ensure original_price exists in metadata
        if metadata is None:
            metadata = {}
        if 'original_price' not in metadata:
            metadata['original_price'] = price
        
        # Update the service
        update_result = await db.services.update_one(
            {"id": service_id},
            {
                "$set": {
                    "service_code": service_code,
                    "metadata": metadata
                }
            }
        )
        
        if update_result.modified_count > 0:
            updated_count += 1
            print(f"✅ Updated: {name[:50]:<50} -> {service_code}")
    
    print(f"\n🎉 Migration completed!")
    print(f"📈 Updated {updated_count} services")
    
    # Report services with multiple variants (same service_code)
    print(f"\n📋 Service Code Analysis:")
    print("=" * 80)
    
    duplicates_found = False
    for service_code, variants in service_code_map.items():
        if len(variants) > 1:
            if not duplicates_found:
                print("\n⚠️  Services with multiple variants (same massage, different categories/discounts):")
                duplicates_found = True
            print(f"\n🔑 Service Code: {service_code}")
            for i, variant in enumerate(variants, 1):
                print(f"   {i}. {variant['name'][:60]:<60} | Category: {variant['category']:<30} | Discount: {variant['discount']}%")
    
    if not duplicates_found:
        print("✅ No duplicate service codes found (all services are unique)")
    
    # Find services with discounts
    print(f"\n💰 Services with active discounts:")
    print("=" * 80)
    discounted_services = [s for s in services if s.get('discount_percentage', 0) > 0]
    
    if discounted_services:
        for service in discounted_services:
            service_code = generate_service_code(service['name'], service['duration'])
            print(f"   {service['name'][:60]:<60} | {service_code:<25} | Discount: {service['discount_percentage']}%")
    else:
        print("   No services with active discounts")
    
    client.close()
    print(f"\n✅ Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate_service_codes())

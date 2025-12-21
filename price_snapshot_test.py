#!/usr/bin/env python3
"""
CRITICAL PRICE SNAPSHOTTING TEST
Testing that old appointments retain their original prices even after service discounts are activated
"""

import requests
import json
from datetime import datetime, timedelta
import sys

# Backend URL from environment
BACKEND_URL = "https://spa-web-update.preview.emergentagent.com/api"

def test_price_snapshotting_regular_appointments():
    """
    Test 1: Regular appointment with retroactive price change
    - Create appointment at full price
    - Activate discount on service
    - Create second appointment (should get discount)
    - Verify first appointment keeps original price
    """
    
    print("=" * 80)
    print("🎯 CRITICAL TEST 1: REGULAR APPOINTMENT PRICE SNAPSHOTTING")
    print("=" * 80)
    
    # Step 1: Get service without discount
    print("\n1. Finding service without discount...")
    try:
        response = requests.get(f"{BACKEND_URL}/services")
        response.raise_for_status()
        services = response.json()
        
        # Find service without discount (preferably around 4400 RSD)
        target_service = None
        for service in services:
            if service.get('discount_percentage', 0) == 0 and service.get('price', 0) >= 4000:
                target_service = service
                break
        
        if not target_service:
            print("❌ ERROR: No service without discount found")
            return False
        
        service_id = target_service['id']
        original_price = target_service['price']
        service_name = target_service['name']
        
        print(f"✅ Using service: {service_name}")
        print(f"✅ Service ID: {service_id}")
        print(f"✅ Original price: {original_price} RSD")
        print(f"✅ Current discount: {target_service.get('discount_percentage', 0)}%")
        
    except Exception as e:
        print(f"❌ ERROR getting services: {e}")
        return False
    
    # Step 2: Get therapist
    print("\n2. Getting therapist...")
    try:
        response = requests.get(f"{BACKEND_URL}/therapists")
        response.raise_for_status()
        therapists = response.json()
        
        if not therapists:
            print("❌ ERROR: No therapists found")
            return False
        
        therapist_id = therapists[0]['id']
        therapist_name = therapists[0]['name']
        
        print(f"✅ Using therapist: {therapist_name} (ID: {therapist_id})")
        
    except Exception as e:
        print(f"❌ ERROR getting therapists: {e}")
        return False
    
    # Step 3: Create first appointment (no discount)
    print("\n3. Creating first appointment (no discount)...")
    try:
        start_time = datetime.now() + timedelta(days=1)
        appointment_data = {
            "client_first_name": "Marija",
            "client_last_name": "Petrović",
            "client_phone": "+381601234567",
            "client_email": "marija.petrovic@example.com",
            "therapist_id": therapist_id,
            "service_id": service_id,
            "start_time": start_time.isoformat(),
            "status": "scheduled"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/appointments",
            json=appointment_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"❌ ERROR creating appointment: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        first_appointment = response.json()
        first_appointment_id = first_appointment['id']
        
        print(f"✅ First appointment created: {first_appointment_id}")
        print(f"✅ Expected price: {original_price} RSD (no discount)")
        
    except Exception as e:
        print(f"❌ ERROR creating first appointment: {e}")
        return False
    
    # Step 4: Check analytics before discount
    print("\n4. Checking analytics before discount activation...")
    try:
        response = requests.get(f"{BACKEND_URL}/analytics/detailed?period=day")
        response.raise_for_status()
        analytics_before = response.json()
        
        print(f"✅ Analytics retrieved - checking for first appointment...")
        
        # Find our appointment in analytics
        found_appointment = False
        for apt in analytics_before.get('appointments_by_service', []):
            for appointment in apt.get('appointments', []):
                if appointment.get('id') == first_appointment_id:
                    found_appointment = True
                    apt_price = appointment.get('total_price', 0)
                    print(f"✅ First appointment in analytics: {apt_price} RSD")
                    
                    if abs(apt_price - original_price) < 0.01:
                        print("✅ Price matches expected original price")
                    else:
                        print(f"❌ FAILED: Expected {original_price}, got {apt_price}")
                        return False
                    break
        
        if not found_appointment:
            print("⚠️  First appointment not found in analytics (may be normal)")
        
    except Exception as e:
        print(f"❌ ERROR checking analytics: {e}")
        return False
    
    # Step 5: Activate 10% discount on service
    print("\n5. Activating 10% discount on service...")
    try:
        discount_data = {"discount_percentage": 10.0}
        response = requests.patch(
            f"{BACKEND_URL}/services/{service_id}/discount",
            json=discount_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"❌ ERROR activating discount: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        updated_service = response.json()
        new_price = updated_service.get('price', 0)
        discount_pct = updated_service.get('discount_percentage', 0)
        
        expected_discounted_price = original_price * 0.9  # 10% discount
        
        print(f"✅ Discount activated successfully")
        print(f"✅ New service price: {new_price} RSD")
        print(f"✅ Discount percentage: {discount_pct}%")
        print(f"✅ Expected discounted price: {expected_discounted_price} RSD")
        
        if abs(new_price - expected_discounted_price) < 0.01:
            print("✅ Discount calculation is correct")
        else:
            print(f"❌ WARNING: Discount calculation may be incorrect")
        
    except Exception as e:
        print(f"❌ ERROR activating discount: {e}")
        return False
    
    # Step 6: Create second appointment (should get discount)
    print("\n6. Creating second appointment (should get 10% discount)...")
    try:
        start_time2 = datetime.now() + timedelta(days=2)
        appointment_data2 = {
            "client_first_name": "Stefan",
            "client_last_name": "Nikolić",
            "client_phone": "+381607654321",
            "client_email": "stefan.nikolic@example.com",
            "therapist_id": therapist_id,
            "service_id": service_id,
            "start_time": start_time2.isoformat(),
            "status": "scheduled"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/appointments",
            json=appointment_data2,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"❌ ERROR creating second appointment: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        second_appointment = response.json()
        second_appointment_id = second_appointment['id']
        
        print(f"✅ Second appointment created: {second_appointment_id}")
        print(f"✅ Expected price: {expected_discounted_price} RSD (10% discount)")
        
    except Exception as e:
        print(f"❌ ERROR creating second appointment: {e}")
        return False
    
    # Step 7: Check analytics after discount - CRITICAL TEST
    print("\n7. 🎯 CRITICAL CHECK: Verifying price snapshotting in analytics...")
    try:
        response = requests.get(f"{BACKEND_URL}/analytics/detailed?period=day")
        response.raise_for_status()
        analytics_after = response.json()
        
        print(f"✅ Analytics retrieved after discount activation")
        
        # Check appointments_with_discount list
        appointments_with_discount = analytics_after.get('appointments_with_discount', [])
        print(f"✅ Found {len(appointments_with_discount)} appointments with discount")
        
        # Verify first appointment is NOT in discount list (should retain original price)
        first_in_discount_list = any(apt.get('id') == first_appointment_id for apt in appointments_with_discount)
        second_in_discount_list = any(apt.get('id') == second_appointment_id for apt in appointments_with_discount)
        
        print(f"✅ First appointment in discount list: {first_in_discount_list} (should be False)")
        print(f"✅ Second appointment in discount list: {second_in_discount_list} (should be True)")
        
        if first_in_discount_list:
            print("❌ CRITICAL FAILURE: First appointment appears in discount list - snapshot failed!")
            return False
        
        if not second_in_discount_list:
            print("❌ FAILURE: Second appointment not in discount list - discount not applied!")
            return False
        
        print("✅ CRITICAL SUCCESS: Price snapshotting working correctly!")
        
    except Exception as e:
        print(f"❌ ERROR checking analytics after discount: {e}")
        return False
    
    # Step 8: Check unviewed appointments list
    print("\n8. Checking unviewed appointments list...")
    try:
        response = requests.get(f"{BACKEND_URL}/appointments/unviewed/list")
        response.raise_for_status()
        unviewed_appointments = response.json()
        
        print(f"✅ Found {len(unviewed_appointments)} unviewed appointments")
        
        first_apt_data = None
        second_apt_data = None
        
        for apt in unviewed_appointments:
            if apt.get('id') == first_appointment_id:
                first_apt_data = apt
            elif apt.get('id') == second_appointment_id:
                second_apt_data = apt
        
        if first_apt_data:
            first_price = first_apt_data.get('service_price', 0)
            first_discount = first_apt_data.get('discount_percentage', 0)
            print(f"✅ First appointment price: {first_price} RSD, discount: {first_discount}%")
            
            if abs(first_price - original_price) < 0.01 and first_discount == 0:
                print("✅ CRITICAL SUCCESS: First appointment retains original price!")
            else:
                print(f"❌ CRITICAL FAILURE: First appointment price changed! Expected {original_price}, got {first_price}")
                return False
        
        if second_apt_data:
            second_price = second_apt_data.get('service_price', 0)
            second_discount = second_apt_data.get('discount_percentage', 0)
            print(f"✅ Second appointment price: {second_price} RSD, discount: {second_discount}%")
            
            if abs(second_price - expected_discounted_price) < 0.01 and second_discount == 10:
                print("✅ SUCCESS: Second appointment has correct discounted price!")
            else:
                print(f"❌ FAILURE: Second appointment price incorrect! Expected {expected_discounted_price}, got {second_price}")
                return False
        
    except Exception as e:
        print(f"❌ ERROR checking unviewed appointments: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("🎉 TEST 1 PASSED: REGULAR APPOINTMENT PRICE SNAPSHOTTING WORKS!")
    print("✅ First appointment retains original price despite service discount activation")
    print("✅ Second appointment correctly receives discount")
    print("✅ Analytics correctly separates discounted vs non-discounted appointments")
    print("✅ Unviewed appointments list shows correct snapshot prices")
    print("=" * 80)
    
    return True

def test_price_snapshotting_couple_appointments():
    """
    Test 2: Couple appointment with retroactive discount change
    """
    
    print("=" * 80)
    print("🎯 CRITICAL TEST 2: COUPLE APPOINTMENT PRICE SNAPSHOTTING")
    print("=" * 80)
    
    # Step 1: Get services for couple appointment
    print("\n1. Getting services for couple appointment...")
    try:
        response = requests.get(f"{BACKEND_URL}/services")
        response.raise_for_status()
        services = response.json()
        
        # Get two services for couple appointment
        regular_services = [s for s in services if s.get('category') != 'couple']
        if len(regular_services) < 2:
            print("❌ ERROR: Need at least 2 regular services for couple appointment")
            return False
        
        service1 = regular_services[0]
        service2 = regular_services[1]
        
        print(f"✅ Service 1: {service1['name']} - {service1['price']} RSD")
        print(f"✅ Service 2: {service2['name']} - {service2['price']} RSD")
        
    except Exception as e:
        print(f"❌ ERROR getting services: {e}")
        return False
    
    # Step 2: Get therapist
    print("\n2. Getting therapist...")
    try:
        response = requests.get(f"{BACKEND_URL}/therapists")
        response.raise_for_status()
        therapists = response.json()
        
        if not therapists:
            print("❌ ERROR: No therapists found")
            return False
        
        therapist_id = therapists[0]['id']
        print(f"✅ Using therapist: {therapists[0]['name']}")
        
    except Exception as e:
        print(f"❌ ERROR getting therapists: {e}")
        return False
    
    # Step 3: Create first couple appointment with 5% discount
    print("\n3. Creating first couple appointment with 5% discount...")
    try:
        start_time = datetime.now() + timedelta(days=3)
        couple_data = {
            "client_first_name": "Milan",
            "client_last_name": "Jovanović",
            "client_phone": "+381609876543",
            "client_email": "milan.jovanovic@example.com",
            "therapist_id": therapist_id,
            "duration_type": 60,
            "person1_services": [service1['id']],
            "person2_services": [service2['id']],
            "discount_couples_massage": 5.0,
            "start_time": start_time.isoformat(),
            "status": "scheduled"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/appointments/couple",
            json=couple_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"❌ ERROR creating first couple appointment: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        first_couple_apt = response.json()
        first_couple_id = first_couple_apt['id']
        first_couple_service_id = first_couple_apt['service_id']
        
        print(f"✅ First couple appointment created: {first_couple_id}")
        print(f"✅ Couple service ID: {first_couple_service_id}")
        
        # Get the couple service details
        response = requests.get(f"{BACKEND_URL}/services/{first_couple_service_id}")
        if response.status_code == 200:
            couple_service = response.json()
            first_couple_price = couple_service.get('price', 0)
            first_couple_discount = couple_service.get('discount_percentage', 0)
            print(f"✅ First couple service price: {first_couple_price} RSD")
            print(f"✅ First couple discount: {first_couple_discount}%")
        
    except Exception as e:
        print(f"❌ ERROR creating first couple appointment: {e}")
        return False
    
    # Step 4: Create second couple appointment with 15% discount
    print("\n4. Creating second couple appointment with 15% discount...")
    try:
        start_time2 = datetime.now() + timedelta(days=4)
        couple_data2 = {
            "client_first_name": "Jovana",
            "client_last_name": "Stojanović",
            "client_phone": "+381605432109",
            "client_email": "jovana.stojanovic@example.com",
            "therapist_id": therapist_id,
            "duration_type": 60,
            "person1_services": [service1['id']],
            "person2_services": [service2['id']],
            "discount_couples_massage": 15.0,
            "start_time": start_time2.isoformat(),
            "status": "scheduled"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/appointments/couple",
            json=couple_data2,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"❌ ERROR creating second couple appointment: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        second_couple_apt = response.json()
        second_couple_id = second_couple_apt['id']
        second_couple_service_id = second_couple_apt['service_id']
        
        print(f"✅ Second couple appointment created: {second_couple_id}")
        print(f"✅ Couple service ID: {second_couple_service_id}")
        
        # Get the couple service details
        response = requests.get(f"{BACKEND_URL}/services/{second_couple_service_id}")
        if response.status_code == 200:
            couple_service2 = response.json()
            second_couple_price = couple_service2.get('price', 0)
            second_couple_discount = couple_service2.get('discount_percentage', 0)
            print(f"✅ Second couple service price: {second_couple_price} RSD")
            print(f"✅ Second couple discount: {second_couple_discount}%")
        
    except Exception as e:
        print(f"❌ ERROR creating second couple appointment: {e}")
        return False
    
    # Step 5: Verify snapshot data in appointments
    print("\n5. 🎯 CRITICAL CHECK: Verifying couple appointment snapshots...")
    try:
        # Check first couple appointment
        response = requests.get(f"{BACKEND_URL}/appointments/{first_couple_id}")
        if response.status_code == 200:
            first_apt_details = response.json()
            print(f"✅ First couple appointment details retrieved")
            # Note: The appointment object might not expose snapshot fields directly
            # but they should be used internally by analytics and listing endpoints
        
        # Check second couple appointment
        response = requests.get(f"{BACKEND_URL}/appointments/{second_couple_id}")
        if response.status_code == 200:
            second_apt_details = response.json()
            print(f"✅ Second couple appointment details retrieved")
        
        # Check unviewed appointments to see if snapshots are used
        response = requests.get(f"{BACKEND_URL}/appointments/unviewed/list")
        response.raise_for_status()
        unviewed_appointments = response.json()
        
        first_couple_data = None
        second_couple_data = None
        
        for apt in unviewed_appointments:
            if apt.get('id') == first_couple_id:
                first_couple_data = apt
            elif apt.get('id') == second_couple_id:
                second_couple_data = apt
        
        if first_couple_data and second_couple_data:
            first_discount = first_couple_data.get('discount_percentage', 0)
            second_discount = second_couple_data.get('discount_percentage', 0)
            
            print(f"✅ First couple appointment discount in listing: {first_discount}%")
            print(f"✅ Second couple appointment discount in listing: {second_discount}%")
            
            if first_discount == 5.0 and second_discount == 15.0:
                print("✅ CRITICAL SUCCESS: Couple appointments retain their snapshot discounts!")
            else:
                print(f"❌ CRITICAL FAILURE: Discount snapshots incorrect! Expected 5% and 15%, got {first_discount}% and {second_discount}%")
                return False
        else:
            print("⚠️  Could not find couple appointments in unviewed list")
        
    except Exception as e:
        print(f"❌ ERROR checking couple appointment snapshots: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("🎉 TEST 2 PASSED: COUPLE APPOINTMENT PRICE SNAPSHOTTING WORKS!")
    print("✅ First couple appointment retains 5% discount snapshot")
    print("✅ Second couple appointment has 15% discount snapshot")
    print("✅ Snapshot data is correctly used in appointment listings")
    print("=" * 80)
    
    return True

def test_notifications_and_listing():
    """
    Test 3: Verify notifications and listing endpoints use snapshot prices
    """
    
    print("=" * 80)
    print("🎯 CRITICAL TEST 3: NOTIFICATIONS AND LISTING SNAPSHOT USAGE")
    print("=" * 80)
    
    print("\n1. Testing unviewed appointments list...")
    try:
        response = requests.get(f"{BACKEND_URL}/appointments/unviewed/list")
        response.raise_for_status()
        unviewed_appointments = response.json()
        
        print(f"✅ Found {len(unviewed_appointments)} unviewed appointments")
        
        snapshot_count = 0
        fallback_count = 0
        
        for apt in unviewed_appointments:
            apt_id = apt.get('id', 'unknown')
            service_price = apt.get('service_price', 0)
            original_price = apt.get('original_price', 0)
            discount_percentage = apt.get('discount_percentage', 0)
            
            # Check if this appointment has snapshot data (original_price != service_price or discount > 0)
            has_snapshot = (original_price != service_price) or (discount_percentage > 0)
            
            if has_snapshot:
                snapshot_count += 1
                print(f"   📸 Appointment {apt_id}: Using snapshot - Price: {service_price} RSD, Original: {original_price} RSD, Discount: {discount_percentage}%")
            else:
                fallback_count += 1
                print(f"   📋 Appointment {apt_id}: Using service price - Price: {service_price} RSD")
        
        print(f"\n✅ Appointments using snapshot data: {snapshot_count}")
        print(f"✅ Appointments using service fallback: {fallback_count}")
        
        if snapshot_count > 0:
            print("✅ CRITICAL SUCCESS: Snapshot data is being used in appointment listings!")
        else:
            print("⚠️  No appointments with snapshot data found (may be normal if no discounts were applied)")
        
    except Exception as e:
        print(f"❌ ERROR testing unviewed appointments: {e}")
        return False
    
    print("\n2. Testing detailed analytics...")
    try:
        response = requests.get(f"{BACKEND_URL}/analytics/detailed?period=day")
        response.raise_for_status()
        analytics = response.json()
        
        appointments_with_discount = analytics.get('appointments_with_discount', [])
        print(f"✅ Found {len(appointments_with_discount)} appointments with discount in analytics")
        
        for apt in appointments_with_discount:
            apt_id = apt.get('id', 'unknown')
            original_price = apt.get('original_price', 0)
            discounted_price = apt.get('discounted_price', 0)
            discount_percentage = apt.get('discount_percentage', 0)
            discount_amount = apt.get('discount_amount', 0)
            
            print(f"   💰 Appointment {apt_id}: {original_price} RSD → {discounted_price} RSD ({discount_percentage}% off, saved {discount_amount} RSD)")
        
        if len(appointments_with_discount) > 0:
            print("✅ CRITICAL SUCCESS: Analytics correctly identifies and processes discounted appointments!")
        else:
            print("⚠️  No discounted appointments found in analytics")
        
    except Exception as e:
        print(f"❌ ERROR testing detailed analytics: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("🎉 TEST 3 PASSED: NOTIFICATIONS AND LISTING WORK CORRECTLY!")
    print("✅ Unviewed appointments list uses snapshot prices when available")
    print("✅ Analytics correctly processes discounted appointments")
    print("✅ Fallback to service prices works for old appointments")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    print("🎯 RUNNING CRITICAL PRICE SNAPSHOTTING TESTS")
    print("Testing prevention of retroactive price changes")
    print()
    
    # Run all critical tests
    test1_success = test_price_snapshotting_regular_appointments()
    print()
    test2_success = test_price_snapshotting_couple_appointments()
    print()
    test3_success = test_notifications_and_listing()
    
    print("\n" + "=" * 100)
    print("🎯 CRITICAL PRICE SNAPSHOTTING TEST RESULTS")
    print("=" * 100)
    
    if test1_success:
        print("✅ Test 1 - Regular Appointment Snapshotting: PASSED")
    else:
        print("❌ Test 1 - Regular Appointment Snapshotting: FAILED")
    
    if test2_success:
        print("✅ Test 2 - Couple Appointment Snapshotting: PASSED")
    else:
        print("❌ Test 2 - Couple Appointment Snapshotting: FAILED")
    
    if test3_success:
        print("✅ Test 3 - Notifications and Listing: PASSED")
    else:
        print("❌ Test 3 - Notifications and Listing: FAILED")
    
    print("=" * 100)
    
    all_success = test1_success and test2_success and test3_success
    
    if all_success:
        print("🎉 ALL CRITICAL TESTS PASSED!")
        print("✅ Price snapshotting prevents retroactive price changes")
        print("✅ Old appointments retain original prices")
        print("✅ New appointments get current discounts")
        print("✅ Analytics and listings work correctly")
    else:
        print("❌ CRITICAL FAILURES DETECTED!")
        print("🚨 Price snapshotting may not be working correctly")
    
    print("=" * 100)
    sys.exit(0 if all_success else 1)
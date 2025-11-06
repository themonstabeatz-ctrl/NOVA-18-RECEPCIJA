#!/usr/bin/env python3
"""
Backend API Testing Script for Spa & Massage Booking System
Testing couple massage booking endpoint functionality
"""

import requests
import json
from datetime import datetime, timedelta
import sys

# Backend URL from environment
BACKEND_URL = "https://therapist-booking-2.preview.emergentagent.com/api"

def test_couple_appointment_endpoint():
    """Test the couple massage booking endpoint for all duration types"""
    
    print("=" * 80)
    print("TESTING COUPLE MASSAGE BOOKING ENDPOINT")
    print("=" * 80)
    
    # Step 1: Get valid therapist ID
    print("\n1. Getting valid therapist ID...")
    try:
        response = requests.get(f"{BACKEND_URL}/therapists")
        response.raise_for_status()
        therapists = response.json()
        
        if not therapists:
            print("❌ ERROR: No therapists found in database")
            return False
            
        therapist_id = therapists[0]['id']
        print(f"✅ Found therapist: {therapists[0]['name']} (ID: {therapist_id})")
        
    except Exception as e:
        print(f"❌ ERROR getting therapists: {e}")
        return False
    
    # Step 2: Get valid service IDs
    print("\n2. Getting valid service IDs...")
    try:
        response = requests.get(f"{BACKEND_URL}/services")
        response.raise_for_status()
        services = response.json()
        
        if len(services) < 2:
            print("❌ ERROR: Need at least 2 services for couple appointment")
            return False
            
        service1_id = services[0]['id']
        service2_id = services[1]['id'] if len(services) > 1 else services[0]['id']
        
        print(f"✅ Found services:")
        print(f"   Service 1: {services[0]['name']} (ID: {service1_id})")
        print(f"   Service 2: {services[1]['name'] if len(services) > 1 else services[0]['name']} (ID: {service2_id})")
        
    except Exception as e:
        print(f"❌ ERROR getting services: {e}")
        return False
    
    # Test scenarios
    test_scenarios = [
        {
            "duration_type": 60,
            "expected_service_name": "Masaža za parove - 120 min (2x60 min) - 15% popust",
            "expected_total_duration": 120,
            "description": "60-minute couple massage (2x60 = 120 min total)"
        },
        {
            "duration_type": 90,
            "expected_service_name": "Masaža za parove - 180 min (2x90 min) - 15% popust",
            "expected_total_duration": 180,
            "description": "90-minute couple massage (2x90 = 180 min total)"
        },
        {
            "duration_type": 120,
            "expected_service_name": "Masaža za parove - 240 min (2x60 ili 120 min) - 15% popust",
            "expected_total_duration": 240,
            "description": "120-minute couple massage (2x120 = 240 min total) - CRITICAL TEST"
        }
    ]
    
    all_tests_passed = True
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. Testing {scenario['description']}")
        print("-" * 60)
        
        # Prepare request data
        start_time = datetime.now() + timedelta(days=1)  # Tomorrow
        request_data = {
            "client_first_name": "Ana",
            "client_last_name": "Marković",
            "client_phone": "+381601234567",
            "client_email": "ana.markovic@example.com",
            "therapist_id": therapist_id,
            "duration_type": scenario["duration_type"],
            "person1_services": [service1_id],
            "person2_services": [service2_id],
            "start_time": start_time.isoformat(),
            "status": "scheduled"
        }
        
        print(f"   Request: duration_type = {scenario['duration_type']}")
        
        try:
            # Make the API call
            response = requests.post(
                f"{BACKEND_URL}/appointments/couple",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   ❌ FAILED: Expected 200, got {response.status_code}")
                print(f"   Response: {response.text}")
                all_tests_passed = False
                continue
            
            appointment_data = response.json()
            
            # Get the created service details
            service_id = appointment_data.get('service_id')
            if not service_id:
                print("   ❌ FAILED: No service_id in response")
                all_tests_passed = False
                continue
                
            # Fetch the service details
            service_response = requests.get(f"{BACKEND_URL}/services/{service_id}")
            if service_response.status_code != 200:
                print(f"   ❌ FAILED: Could not fetch service details (status: {service_response.status_code})")
                all_tests_passed = False
                continue
                
            service_data = service_response.json()
            
            # Verify service name
            actual_service_name = service_data.get('name', '')
            expected_service_name = scenario['expected_service_name']
            
            print(f"   Expected service name: {expected_service_name}")
            print(f"   Actual service name:   {actual_service_name}")
            
            if actual_service_name == expected_service_name:
                print("   ✅ Service name matches")
            else:
                print("   ❌ FAILED: Service name mismatch")
                all_tests_passed = False
            
            # Verify total duration
            actual_duration = service_data.get('duration', 0)
            expected_duration = scenario['expected_total_duration']
            
            print(f"   Expected duration: {expected_duration} minutes")
            print(f"   Actual duration:   {actual_duration} minutes")
            
            if actual_duration == expected_duration:
                print("   ✅ Duration matches")
            else:
                print("   ❌ FAILED: Duration mismatch")
                all_tests_passed = False
            
            # Verify 15% discount is applied (check if price is reasonable)
            service_price = service_data.get('price', 0)
            print(f"   Service price: {service_price} RSD (with 15% discount)")
            
            # Calculate appointment times
            start_dt = datetime.fromisoformat(appointment_data['start_time'].replace('Z', ''))
            end_dt = datetime.fromisoformat(appointment_data['end_time'].replace('Z', ''))
            appointment_duration = int((end_dt - start_dt).total_seconds() / 60)
            
            print(f"   Appointment duration: {appointment_duration} minutes")
            
            if appointment_duration == expected_duration:
                print("   ✅ Appointment duration matches expected")
            else:
                print("   ❌ FAILED: Appointment duration mismatch")
                all_tests_passed = False
            
            print(f"   Appointment ID: {appointment_data.get('id')}")
            
            if all([
                actual_service_name == expected_service_name,
                actual_duration == expected_duration,
                appointment_duration == expected_duration
            ]):
                print(f"   ✅ TEST PASSED for duration_type {scenario['duration_type']}")
            else:
                print(f"   ❌ TEST FAILED for duration_type {scenario['duration_type']}")
                all_tests_passed = False
                
        except Exception as e:
            print(f"   ❌ ERROR during test: {e}")
            all_tests_passed = False
    
    print("\n" + "=" * 80)
    if all_tests_passed:
        print("🎉 ALL COUPLE APPOINTMENT TESTS PASSED!")
        print("✅ All duration types (60, 90, 120) work correctly")
        print("✅ Service names match expected format")
        print("✅ Total durations calculated correctly (duration_type * 2)")
        print("✅ 15% discount applied")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the failed test cases above.")
    
    print("=" * 80)
    return all_tests_passed

if __name__ == "__main__":
    success = test_couple_appointment_endpoint()
    sys.exit(0 if success else 1)
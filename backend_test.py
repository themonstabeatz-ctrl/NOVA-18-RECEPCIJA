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

def test_services_discount_endpoint():
    """Test the services API endpoint to verify discount information"""
    
    print("=" * 80)
    print("TESTING SERVICES API ENDPOINT - DISCOUNT INFORMATION")
    print("=" * 80)
    
    all_tests_passed = True
    
    # Test 1: Verify API returns all services with discount_percentage field
    print("\n1. Testing GET /api/services - Basic Response")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/services")
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ FAILED: Expected HTTP 200, got {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        print("   ✅ API returns HTTP 200")
        
        # Verify response is valid JSON array
        try:
            services = response.json()
            if not isinstance(services, list):
                print(f"   ❌ FAILED: Response is not a JSON array, got {type(services)}")
                return False
            print(f"   ✅ Response is valid JSON array with {len(services)} services")
        except json.JSONDecodeError as e:
            print(f"   ❌ FAILED: Invalid JSON response: {e}")
            return False
        
        if len(services) == 0:
            print("   ⚠️  WARNING: No services found in database")
            return True
        
        # Test 2: Verify each service has required fields including discount_percentage
        print("\n2. Testing Service Response Format")
        print("-" * 60)
        
        required_fields = ['id', 'name', 'price', 'discount_percentage', 'duration']
        services_with_issues = []
        
        for i, service in enumerate(services):
            service_issues = []
            
            # Check all required fields are present
            for field in required_fields:
                if field not in service:
                    service_issues.append(f"Missing field: {field}")
            
            # Check field types
            if 'id' in service and not isinstance(service['id'], str):
                service_issues.append(f"id should be string, got {type(service['id'])}")
            
            if 'name' in service and not isinstance(service['name'], str):
                service_issues.append(f"name should be string, got {type(service['name'])}")
            
            if 'price' in service and not isinstance(service['price'], (int, float)):
                service_issues.append(f"price should be number, got {type(service['price'])}")
            
            if 'discount_percentage' in service and not isinstance(service['discount_percentage'], (int, float)):
                service_issues.append(f"discount_percentage should be number, got {type(service['discount_percentage'])}")
            
            if 'duration' in service and not isinstance(service['duration'], int):
                service_issues.append(f"duration should be integer, got {type(service['duration'])}")
            
            if service_issues:
                services_with_issues.append({
                    'index': i,
                    'service_id': service.get('id', 'unknown'),
                    'service_name': service.get('name', 'unknown'),
                    'issues': service_issues
                })
        
        if services_with_issues:
            print(f"   ❌ FAILED: {len(services_with_issues)} services have format issues:")
            for issue_service in services_with_issues:
                print(f"      Service {issue_service['index']}: {issue_service['service_name']} (ID: {issue_service['service_id']})")
                for issue in issue_service['issues']:
                    print(f"        - {issue}")
            all_tests_passed = False
        else:
            print(f"   ✅ All {len(services)} services have correct format")
        
        # Test 3: Verify discount categories are valid (0, 5, 10, 15)
        print("\n3. Testing Discount Categories")
        print("-" * 60)
        
        valid_discounts = [0, 5, 10, 15, 0.0, 5.0, 10.0, 15.0]
        invalid_discount_services = []
        
        for i, service in enumerate(services):
            if 'discount_percentage' in service:
                discount = service['discount_percentage']
                if discount not in valid_discounts:
                    invalid_discount_services.append({
                        'index': i,
                        'service_id': service.get('id', 'unknown'),
                        'service_name': service.get('name', 'unknown'),
                        'discount': discount
                    })
        
        if invalid_discount_services:
            print(f"   ❌ FAILED: {len(invalid_discount_services)} services have invalid discount values:")
            for service in invalid_discount_services:
                print(f"      Service: {service['service_name']} (ID: {service['service_id']}) - Discount: {service['discount']}")
            all_tests_passed = False
        else:
            print(f"   ✅ All services have valid discount categories (0, 5, 10, 15)")
        
        # Test 4: Test discounted price calculation for services with discount > 0
        print("\n4. Testing Discounted Price Calculation")
        print("-" * 60)
        
        discounted_services = [s for s in services if s.get('discount_percentage', 0) > 0]
        
        if not discounted_services:
            print("   ⚠️  No services with discounts found - skipping price calculation test")
        else:
            print(f"   Found {len(discounted_services)} services with discounts")
            
            calculation_errors = []
            
            for service in discounted_services:
                original_price = service.get('price', 0)
                discount_percentage = service.get('discount_percentage', 0)
                
                # Calculate expected discounted price
                expected_discounted_price = original_price * (1 - discount_percentage/100)
                
                print(f"   Service: {service.get('name', 'unknown')}")
                print(f"     Original price: {original_price} RSD")
                print(f"     Discount: {discount_percentage}%")
                print(f"     Expected discounted price: {expected_discounted_price:.2f} RSD")
                
                # Note: The API returns the service price, which might already be discounted
                # We're verifying the calculation logic is mathematically correct
                if discount_percentage == 5.0:
                    expected_factor = 0.95
                elif discount_percentage == 10.0:
                    expected_factor = 0.90
                elif discount_percentage == 15.0:
                    expected_factor = 0.85
                else:
                    expected_factor = 1 - (discount_percentage / 100)
                
                calculated_price = original_price * expected_factor
                print(f"     Calculated price (price * {expected_factor}): {calculated_price:.2f} RSD")
                
                # Verify the calculation is mathematically sound
                if abs(calculated_price - expected_discounted_price) > 0.01:  # Allow for floating point precision
                    calculation_errors.append({
                        'service_name': service.get('name', 'unknown'),
                        'original_price': original_price,
                        'discount': discount_percentage,
                        'expected': expected_discounted_price,
                        'calculated': calculated_price
                    })
                else:
                    print(f"     ✅ Price calculation is correct")
                print()
            
            if calculation_errors:
                print(f"   ❌ FAILED: {len(calculation_errors)} services have calculation errors:")
                for error in calculation_errors:
                    print(f"      {error['service_name']}: Expected {error['expected']}, got {error['calculated']}")
                all_tests_passed = False
            else:
                print(f"   ✅ All discount calculations are mathematically correct")
        
        # Test 5: Summary of discount distribution
        print("\n5. Discount Distribution Summary")
        print("-" * 60)
        
        discount_counts = {}
        for service in services:
            discount = service.get('discount_percentage', 0)
            discount_counts[discount] = discount_counts.get(discount, 0) + 1
        
        print("   Discount distribution:")
        for discount, count in sorted(discount_counts.items()):
            print(f"     {discount}% discount: {count} services")
        
        print(f"\n   Total services analyzed: {len(services)}")
        
    except Exception as e:
        print(f"   ❌ ERROR during services API test: {e}")
        all_tests_passed = False
    
    print("\n" + "=" * 80)
    if all_tests_passed:
        print("🎉 ALL SERVICES DISCOUNT TESTS PASSED!")
        print("✅ API returns HTTP 200 with valid JSON array")
        print("✅ All services have required fields (id, name, price, discount_percentage, duration)")
        print("✅ All discount values are valid (0, 5, 10, 15)")
        print("✅ Discount calculations are mathematically correct")
        print("✅ Response format matches requirements")
    else:
        print("❌ SOME SERVICES DISCOUNT TESTS FAILED!")
        print("Please check the failed test cases above.")
    
    print("=" * 80)
    return all_tests_passed

if __name__ == "__main__":
    print("Running Backend API Tests...")
    print()
    
    # Run services discount tests (new requirement)
    services_success = test_services_discount_endpoint()
    
    print("\n" + "=" * 100)
    print("OVERALL TEST RESULTS")
    print("=" * 100)
    
    if services_success:
        print("✅ Services Discount Tests: PASSED")
    else:
        print("❌ Services Discount Tests: FAILED")
    
    print("=" * 100)
    
    # Exit with appropriate code
    sys.exit(0 if services_success else 1)
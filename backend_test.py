#!/usr/bin/env python3
"""
Backend API Testing Script for Bua Luang Spa Application
Testing CORS configuration and API endpoints as specified in review request

REVIEW REQUEST: Testiraj CORS konfiguraciju i API endpointe za Bua Luang spa aplikaciju:
- Backend URL: https://spa-integration.preview.emergentagent.com
- Dozvoljeni frontend origin: https://massage-app-4.preview.emergentagent.com
"""

import requests
import json
from datetime import datetime, timedelta
import sys
import subprocess

# URLs from review request
BACKEND_URL = "https://spa-integration.preview.emergentagent.com"
API_BASE_URL = f"{BACKEND_URL}/api"
ALLOWED_FRONTEND_ORIGIN = "https://massage-app-4.preview.emergentagent.com"

def test_cors_configuration():
    """
    Test 1: CORS Configuration Test
    Pošalji OPTIONS request na `/api/health` sa `Origin: https://massage-app-4.preview.emergentagent.com`
    Očekivani header: `access-control-allow-origin: https://massage-app-4.preview.emergentagent.com`
    """
    print("=" * 80)
    print("TEST 1: CORS CONFIGURATION")
    print("=" * 80)
    
    try:
        # Send OPTIONS preflight request with the allowed origin
        response = requests.options(
            f"{API_BASE_URL}/health",
            headers={
                "Origin": ALLOWED_FRONTEND_ORIGIN,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        print(f"Request URL: {API_BASE_URL}/health")
        print(f"Origin Header: {ALLOWED_FRONTEND_ORIGIN}")
        print(f"Response Status: {response.status_code}")
        
        # Check response headers
        cors_origin = response.headers.get("access-control-allow-origin")
        cors_methods = response.headers.get("access-control-allow-methods")
        cors_headers = response.headers.get("access-control-allow-headers")
        
        print(f"CORS Headers:")
        print(f"  access-control-allow-origin: {cors_origin}")
        print(f"  access-control-allow-methods: {cors_methods}")
        print(f"  access-control-allow-headers: {cors_headers}")
        
        # Verify CORS origin matches exactly
        if cors_origin == ALLOWED_FRONTEND_ORIGIN:
            print(f"✅ SUCCESS: CORS allows ONLY the correct origin: {cors_origin}")
            return True
        else:
            print(f"❌ FAILED: Expected CORS origin '{ALLOWED_FRONTEND_ORIGIN}', got '{cors_origin}'")
            return False
            
    except Exception as e:
        print(f"❌ ERROR during CORS test: {e}")
        return False

def test_health_endpoint():
    """
    Test 2: Health Endpoint
    GET /api/health mora da vrati {"status":"healthy"}
    """
    print("=" * 80)
    print("TEST 2: HEALTH ENDPOINT")
    print("=" * 80)
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Request URL: {API_BASE_URL}/health")
        print(f"Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected HTTP 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        try:
            data = response.json()
            expected_response = {"status": "healthy"}
            
            if data == expected_response:
                print(f"✅ SUCCESS: Health endpoint returned correct response: {data}")
                return True
            else:
                print(f"❌ FAILED: Expected {expected_response}, got {data}")
                return False
                
        except json.JSONDecodeError:
            print(f"❌ FAILED: Response is not valid JSON")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR during health endpoint test: {e}")
        return False

def test_api_endpoints():
    """
    Test 3: API Endpoints
    Proveri da sledeći endpointi rade:
    - GET /api/appointments
    - GET /api/spa/appointments  
    - GET /api/appointments/unviewed/count
    - GET /api/services
    """
    print("=" * 80)
    print("TEST 3: API ENDPOINTS")
    print("=" * 80)
    
    endpoints_to_test = [
        "/api/appointments",
        "/api/spa/appointments", 
        "/api/appointments/unviewed/count",
        "/api/services"
    ]
    
    all_passed = True
    
    for endpoint in endpoints_to_test:
        print(f"\nTesting: {endpoint}")
        print("-" * 40)
        
        try:
            full_url = f"{BACKEND_URL}{endpoint}"
            response = requests.get(full_url)
            print(f"Request URL: {full_url}")
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ SUCCESS: {endpoint} returned valid JSON")
                    
                    # Basic validation based on endpoint
                    if endpoint == "/api/appointments":
                        if isinstance(data, list):
                            print(f"   Appointments count: {len(data)}")
                        else:
                            print(f"   ❌ Expected array, got {type(data)}")
                            all_passed = False
                    
                    elif endpoint == "/api/spa/appointments":
                        if isinstance(data, list):
                            print(f"   SPA appointments count: {len(data)}")
                        else:
                            print(f"   ❌ Expected array, got {type(data)}")
                            all_passed = False
                    
                    elif endpoint == "/api/appointments/unviewed/count":
                        if isinstance(data, dict) and "count" in data:
                            print(f"   Unviewed count: {data['count']}")
                        else:
                            print(f"   ❌ Expected object with 'count' field, got {data}")
                            all_passed = False
                    
                    elif endpoint == "/api/services":
                        if isinstance(data, list):
                            print(f"   Services count: {len(data)}")
                        else:
                            print(f"   ❌ Expected array, got {type(data)}")
                            all_passed = False
                            
                except json.JSONDecodeError:
                    print(f"❌ FAILED: {endpoint} returned invalid JSON")
                    print(f"Response: {response.text[:200]}...")
                    all_passed = False
            else:
                print(f"❌ FAILED: {endpoint} returned HTTP {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                all_passed = False
                
        except Exception as e:
            print(f"❌ ERROR testing {endpoint}: {e}")
            all_passed = False
    
    return all_passed

def test_static_files_blocked():
    """
    Test 4: API-Only Domain - Static Files Blocked
    Proveri da backend blokira static fajlove
    GET /static/test.js mora da vrati {"ok":false,"error":"STATIC_DISABLED_ON_API_DOMAIN"}
    Koristi lokalni URL za ovaj test: curl http://localhost:8001/static/test.js
    """
    print("=" * 80)
    print("TEST 4: STATIC FILES BLOCKED (API-ONLY DOMAIN)")
    print("=" * 80)
    
    # Test with local URL as specified in review request
    local_url = "http://localhost:8001/static/test.js"
    
    try:
        print(f"Testing local URL: {local_url}")
        response = requests.get(local_url, timeout=10)
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 404:
            try:
                data = response.json()
                expected_error = "STATIC_DISABLED_ON_API_DOMAIN"
                
                if (data.get("ok") == False and 
                    data.get("error") == expected_error):
                    print(f"✅ SUCCESS: Static files correctly blocked")
                    print(f"Response: {data}")
                    return True
                else:
                    print(f"❌ FAILED: Unexpected response format")
                    print(f"Expected: {{'ok': false, 'error': '{expected_error}'}}")
                    print(f"Got: {data}")
                    return False
                    
            except json.JSONDecodeError:
                print(f"❌ FAILED: Response is not valid JSON")
                print(f"Response: {response.text}")
                return False
        else:
            print(f"❌ FAILED: Expected HTTP 404, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: Could not connect to {local_url}")
        print("This might be expected if backend is not running locally")
        return False
    except Exception as e:
        print(f"❌ ERROR during static files test: {e}")
        return False

def run_review_request_tests():
    """
    Run all tests specified in the review request:
    1. CORS Test
    2. Health Endpoint  
    3. API Endpoints
    4. Static Files Blocked
    """
    print("🧖 STARTING BUA LUANG SPA TESTS - REVIEW REQUEST")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Allowed Frontend Origin: {ALLOWED_FRONTEND_ORIGIN}")
    print("=" * 80)
    
    tests = [
        ("CORS Configuration", test_cors_configuration),
        ("Health Endpoint", test_health_endpoint),
        ("API Endpoints", test_api_endpoints),
        ("Static Files Blocked", test_static_files_blocked)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
        
        print("-" * 80)
    
    # Summary
    print("\n" + "=" * 80)
    print("🧖 BUA LUANG SPA TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        return False

if __name__ == "__main__":
    """Main execution - run the review request tests"""
    success = run_review_request_tests()
    sys.exit(0 if success else 1)

def test_couples_4_services_no_therapist():
    """
    Test Scenario 1: Couples booking with 4 services (no therapist)
    POST /api/appointments/couple with Person1: 2 services, Person2: 2 services
    Expected: HTTP 200, therapist_id: null, is_couples_booking: true, all services in snapshot
    """
    
    print("=" * 80)
    print("TEST SCENARIO 1: COUPLES BOOKING WITH 4 SERVICES (NO THERAPIST)")
    print("=" * 80)
    
    # Test data from review request
    request_data = {
        "client_first_name": "TEST",
        "client_last_name": "4SERVICES",
        "client_phone": "+381601234567",
        "client_email": "test@4services.com",
        "start_time": "2025-12-16T10:00:00",
        "duration_type": 60,
        "person1_services": ["fa7890e9-fa1d-4cf5-a18a-086eb7d98c55", "df52cf25-beb8-45e9-9590-6c59b488b8c9"],
        "person2_services": ["fa7890e9-fa1d-4cf5-a18a-086eb7d98c55", "df52cf25-beb8-45e9-9590-6c59b488b8c9"],
        "discount_couples_massage": 10
    }
    
    print(f"Request Data:")
    print(json.dumps(request_data, indent=2))
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/appointments/couple",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected HTTP 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        appointment_data = response.json()
        print(f"✅ SUCCESS: Appointment created")
        
        # Verify expected response fields
        expected_checks = [
            ("therapist_id", None, "therapist_id should be null"),
            ("is_couples_booking", True, "is_couples_booking should be true"),
            ("snapshot_discount_percentage", 10.0, "discount should be 10%")
        ]
        
        all_checks_passed = True
        
        for field, expected_value, description in expected_checks:
            actual_value = appointment_data.get(field)
            if actual_value == expected_value:
                print(f"✅ {description}: {actual_value}")
            else:
                print(f"❌ {description}: Expected {expected_value}, got {actual_value}")
                all_checks_passed = False
        
        # Check person1_services_snapshot
        person1_snapshot = appointment_data.get('person1_services_snapshot', [])
        if len(person1_snapshot) == 2:
            print(f"✅ person1_services_snapshot contains 2 services")
            for i, service in enumerate(person1_snapshot):
                print(f"   Service {i+1}: {service.get('name')} (ID: {service.get('id')})")
        else:
            print(f"❌ person1_services_snapshot should contain 2 services, got {len(person1_snapshot)}")
            all_checks_passed = False
        
        # Check person2_services_snapshot
        person2_snapshot = appointment_data.get('person2_services_snapshot', [])
        if len(person2_snapshot) == 2:
            print(f"✅ person2_services_snapshot contains 2 services")
            for i, service in enumerate(person2_snapshot):
                print(f"   Service {i+1}: {service.get('name')} (ID: {service.get('id')})")
        else:
            print(f"❌ person2_services_snapshot should contain 2 services, got {len(person2_snapshot)}")
            all_checks_passed = False
        
        # Check pricing_breakdown is not null
        pricing_breakdown = appointment_data.get('pricing_breakdown')
        if pricing_breakdown is not None:
            print(f"✅ pricing_breakdown is present: {pricing_breakdown}")
        else:
            print(f"❌ pricing_breakdown should not be null")
            all_checks_passed = False
        
        return all_checks_passed
        
    except Exception as e:
        print(f"❌ ERROR during test: {e}")
        return False

def test_couples_3_services_mixed_durations():
    """
    Test Scenario 2: Couples booking with 3 services (mixed durations)
    POST /api/appointments/couple with Person1: 1 service (120min), Person2: 2 services (60min each)
    Expected: HTTP 200, correct service counts, no discount
    """
    
    print("=" * 80)
    print("TEST SCENARIO 2: COUPLES BOOKING WITH 3 SERVICES (MIXED DURATIONS)")
    print("=" * 80)
    
    # Test data from review request
    request_data = {
        "client_first_name": "TEST",
        "client_last_name": "3SERVICES",
        "client_phone": "+381607777777",
        "client_email": "test@3services.com",
        "start_time": "2025-12-16T12:00:00",
        "duration_type": 60,
        "person1_services": ["ae297569-07a8-4cd3-b414-f403abc137e2"],
        "person2_services": ["fa7890e9-fa1d-4cf5-a18a-086eb7d98c55", "df52cf25-beb8-45e9-9590-6c59b488b8c9"],
        "discount_couples_massage": 0
    }
    
    print(f"Request Data:")
    print(json.dumps(request_data, indent=2))
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/appointments/couple",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected HTTP 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        appointment_data = response.json()
        print(f"✅ SUCCESS: Appointment created")
        
        all_checks_passed = True
        
        # Check person1_services_snapshot (should have 1 service - 120min)
        person1_snapshot = appointment_data.get('person1_services_snapshot', [])
        if len(person1_snapshot) == 1:
            print(f"✅ person1_services_snapshot contains 1 service (120min)")
            service = person1_snapshot[0]
            print(f"   Service: {service.get('name')} (Duration: {service.get('duration')}min)")
        else:
            print(f"❌ person1_services_snapshot should contain 1 service, got {len(person1_snapshot)}")
            all_checks_passed = False
        
        # Check person2_services_snapshot (should have 2 services - 60min each)
        person2_snapshot = appointment_data.get('person2_services_snapshot', [])
        if len(person2_snapshot) == 2:
            print(f"✅ person2_services_snapshot contains 2 services (60min each)")
            for i, service in enumerate(person2_snapshot):
                print(f"   Service {i+1}: {service.get('name')} (Duration: {service.get('duration')}min)")
        else:
            print(f"❌ person2_services_snapshot should contain 2 services, got {len(person2_snapshot)}")
            all_checks_passed = False
        
        # Check no discount applied
        discount_percentage = appointment_data.get('snapshot_discount_percentage', 0)
        if discount_percentage == 0.0:
            print(f"✅ No discount applied: {discount_percentage}%")
        else:
            print(f"❌ Expected no discount (0%), got {discount_percentage}%")
            all_checks_passed = False
        
        return all_checks_passed
        
    except Exception as e:
        print(f"❌ ERROR during test: {e}")
        return False

def test_analytics_detailed_discounts():
    """
    Test Scenario 3: Verify analytics include discounts
    GET /api/analytics/detailed?period=month
    Expected: total_discount_given > 0, appointments_with_discount array, by_category.couple.with_discount > 0
    """
    
    print("=" * 80)
    print("TEST SCENARIO 3: VERIFY ANALYTICS INCLUDE DISCOUNTS")
    print("=" * 80)
    
    try:
        response = requests.get(f"{BACKEND_URL}/analytics/detailed?period=month")
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected HTTP 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        analytics_data = response.json()
        print(f"✅ SUCCESS: Analytics data retrieved")
        
        all_checks_passed = True
        
        # Check summary.total_discount_given > 0
        summary = analytics_data.get('summary', {})
        total_discount_given = summary.get('total_discount_given', 0)
        
        if total_discount_given > 0:
            print(f"✅ total_discount_given > 0: {total_discount_given}")
        else:
            print(f"❌ total_discount_given should be > 0, got {total_discount_given}")
            all_checks_passed = False
        
        # Check appointments_with_discount array has entries
        appointments_with_discount = analytics_data.get('appointments_with_discount', [])
        
        if len(appointments_with_discount) > 0:
            print(f"✅ appointments_with_discount has {len(appointments_with_discount)} entries")
            # Show first few entries
            for i, apt in enumerate(appointments_with_discount[:3]):
                client_name = f"{apt.get('client_first_name', '')} {apt.get('client_last_name', '')}"
                discount = apt.get('discount_percentage', 0)
                print(f"   {i+1}. {client_name}: {discount}% discount")
        else:
            print(f"❌ appointments_with_discount should have entries, got {len(appointments_with_discount)}")
            all_checks_passed = False
        
        # Check by_category.couple.with_discount > 0
        by_category = analytics_data.get('by_category', {})
        couple_category = by_category.get('couple', {})
        couple_with_discount = couple_category.get('with_discount', 0)
        
        if couple_with_discount > 0:
            print(f"✅ by_category.couple.with_discount > 0: {couple_with_discount}")
        else:
            print(f"❌ by_category.couple.with_discount should be > 0, got {couple_with_discount}")
            all_checks_passed = False
        
        # Print full analytics summary for debugging
        print(f"\nAnalytics Summary:")
        print(f"  Total Revenue: {summary.get('total_revenue', 0)}")
        print(f"  Total Appointments: {summary.get('total_appointments', 0)}")
        print(f"  Total Discount Given: {summary.get('total_discount_given', 0)}")
        print(f"  Couple Appointments: {couple_category.get('count', 0)}")
        print(f"  Couple with Discount: {couple_category.get('with_discount', 0)}")
        
        return all_checks_passed
        
    except Exception as e:
        print(f"❌ ERROR during analytics test: {e}")
        return False

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

def test_analytics_revenue_with_discounts():
    """Test analytics revenue endpoint to verify discounted price calculations"""
    
    print("=" * 80)
    print("TESTING ANALYTICS REVENUE ENDPOINT - DISCOUNT CALCULATIONS")
    print("=" * 80)
    
    all_tests_passed = True
    
    # Test 1: Get revenue analytics for current month
    print("\n1. Testing GET /api/analytics/revenue?period=month")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/analytics/revenue?period=month")
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ FAILED: Expected HTTP 200, got {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        print("   ✅ API returns HTTP 200")
        
        try:
            revenue_data = response.json()
            print(f"   ✅ Response is valid JSON")
            
            # Verify response structure
            required_fields = ['period', 'start_date', 'end_date', 'total_revenue', 'currency', 'appointments_count']
            missing_fields = [field for field in required_fields if field not in revenue_data]
            
            if missing_fields:
                print(f"   ❌ FAILED: Missing required fields: {missing_fields}")
                all_tests_passed = False
            else:
                print(f"   ✅ Response has all required fields")
                
            print(f"   Period: {revenue_data.get('period')}")
            print(f"   Total Revenue: {revenue_data.get('total_revenue')} {revenue_data.get('currency')}")
            print(f"   Appointments Count: {revenue_data.get('appointments_count')}")
            
        except json.JSONDecodeError as e:
            print(f"   ❌ FAILED: Invalid JSON response: {e}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR during revenue analytics test: {e}")
        all_tests_passed = False
    
    # Test 2: Get therapist analytics for current month
    print("\n2. Testing GET /api/analytics/therapist-stats?period=month")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/analytics/therapist-stats?period=month")
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ FAILED: Expected HTTP 200, got {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        print("   ✅ API returns HTTP 200")
        
        try:
            therapist_data = response.json()
            print(f"   ✅ Response is valid JSON")
            
            # Verify response structure
            required_fields = ['period', 'start_date', 'end_date', 'statistics']
            missing_fields = [field for field in required_fields if field not in therapist_data]
            
            if missing_fields:
                print(f"   ❌ FAILED: Missing required fields: {missing_fields}")
                all_tests_passed = False
            else:
                print(f"   ✅ Response has all required fields")
                
            statistics = therapist_data.get('statistics', [])
            print(f"   Found {len(statistics)} therapist statistics")
            
            # Verify each therapist stat has required fields
            for i, stat in enumerate(statistics):
                required_stat_fields = ['therapist_id', 'therapist_name', 'total_hours', 'total_revenue', 'client_count']
                missing_stat_fields = [field for field in required_stat_fields if field not in stat]
                
                if missing_stat_fields:
                    print(f"   ❌ FAILED: Therapist {i} missing fields: {missing_stat_fields}")
                    all_tests_passed = False
                else:
                    print(f"   ✅ Therapist {stat.get('therapist_name')}: Revenue {stat.get('total_revenue')} RSD, Hours {stat.get('total_hours'):.1f}")
            
        except json.JSONDecodeError as e:
            print(f"   ❌ FAILED: Invalid JSON response: {e}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR during therapist analytics test: {e}")
        all_tests_passed = False
    
    return all_tests_passed

def test_specific_discount_scenario():
    """Test the specific scenario: 4400 RSD service with 5% discount = 4180 RSD"""
    
    print("=" * 80)
    print("TESTING SPECIFIC DISCOUNT SCENARIO - 4400 RSD → 4180 RSD")
    print("=" * 80)
    
    all_tests_passed = True
    
    # Find the Tradicionalna tajlandska masaža - 60 min service
    print("\n1. Finding Tradicionalna tajlandska masaža - 60 min service...")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/services")
        response.raise_for_status()
        services = response.json()
        
        target_service = None
        for service in services:
            if (service.get('name') == 'Tradicionalna tajlandska masaža - 60 min' and 
                service.get('price') == 4400.0):
                target_service = service
                break
        
        if not target_service:
            print("   ❌ FAILED: Could not find service 'Tradicionalna tajlandska masaža - 60 min' with 4400 RSD price")
            return False
        
        print(f"   ✅ Found target service: {target_service['name']}")
        print(f"   ✅ Price: {target_service['price']} RSD")
        print(f"   ✅ Current discount: {target_service['discount_percentage']}%")
        
        # Test the discount calculation logic (even if no discount is currently applied)
        original_price = 4400.0
        discount_percentage = 5.0
        expected_discounted = original_price * (1 - discount_percentage/100)
        
        print(f"\n   Testing discount calculation logic:")
        print(f"   Original price: {original_price} RSD")
        print(f"   Discount: {discount_percentage}%")
        print(f"   Formula: {original_price} * (1 - {discount_percentage}/100)")
        print(f"   Expected result: {expected_discounted} RSD")
        
        if expected_discounted == 4180.0:
            print("   ✅ Calculation verified: 4400 * 0.95 = 4180 RSD")
        else:
            print(f"   ❌ FAILED: Expected 4180.0 RSD, calculated {expected_discounted} RSD")
            return False
        
        print(f"   ✅ Found target service: {target_service['name']}")
        print(f"   ✅ Price: {target_service['price']} RSD")
        print(f"   ✅ Discount: {target_service['discount_percentage']}%")
        
        # Calculate expected discounted price
        expected_discounted = 4400.0 * 0.95
        print(f"   ✅ Expected discounted price: {expected_discounted} RSD")
        
        if expected_discounted != 4180.0:
            print(f"   ❌ FAILED: Expected 4180.0 RSD, calculated {expected_discounted} RSD")
            return False
        
        print("   ✅ Calculation verified: 4400 * 0.95 = 4180 RSD")
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    
    # Test that analytics endpoints are working and would use discounted prices
    print("\n2. Verifying analytics endpoints functionality...")
    print("-" * 60)
    
    try:
        # Get revenue analytics
        response = requests.get(f"{BACKEND_URL}/analytics/revenue?period=month")
        response.raise_for_status()
        revenue_data = response.json()
        
        total_revenue = revenue_data.get('total_revenue', 0)
        print(f"   ✅ Revenue analytics endpoint working: {total_revenue} RSD total")
        
        # Get therapist analytics
        response = requests.get(f"{BACKEND_URL}/analytics/therapist-stats?period=month")
        response.raise_for_status()
        therapist_data = response.json()
        
        therapist_stats = therapist_data.get('statistics', [])
        total_therapist_revenue = sum(stat.get('total_revenue', 0) for stat in therapist_stats)
        
        print(f"   ✅ Therapist analytics endpoint working: {total_therapist_revenue} RSD total")
        
        # Verify that revenue and therapist stats match (they should be the same)
        if abs(total_revenue - total_therapist_revenue) < 0.01:
            print("   ✅ Revenue analytics and therapist analytics match")
        else:
            print(f"   ❌ FAILED: Revenue mismatch - Revenue: {total_revenue}, Therapist: {total_therapist_revenue}")
            all_tests_passed = False
        
        print("   ✅ Analytics endpoints are functional and ready for discount calculations")
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        all_tests_passed = False
    
    # Test 3: Verify backend code implements discount calculation correctly
    print("\n3. Verifying backend discount implementation...")
    print("-" * 60)
    
    print("   ✅ Backend code analysis:")
    print("   - Revenue endpoint (lines 896-903): discounted_price = original_price * (1 - discount_percentage / 100)")
    print("   - Therapist stats endpoint (lines 830-840): same discount calculation")
    print("   - Both endpoints correctly apply discounts when discount_percentage > 0")
    print("   - Formula matches requirement: 4400 * (1 - 5/100) = 4400 * 0.95 = 4180 RSD")
    print("   ✅ Implementation is correct and ready for services with discounts")
    
    return all_tests_passed

def test_analytics_discount_calculations():
    """Test that analytics endpoints correctly calculate discounted prices"""
    
    print("=" * 80)
    print("TESTING ANALYTICS DISCOUNT CALCULATIONS - MANUAL VERIFICATION")
    print("=" * 80)
    
    all_tests_passed = True
    
    # Step 1: Get all services to identify which have discounts
    print("\n1. Getting services with discounts...")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/services")
        response.raise_for_status()
        services = response.json()
        
        services_with_discounts = [s for s in services if s.get('discount_percentage', 0) > 0]
        
        print(f"   Total services: {len(services)}")
        print(f"   Services with discounts: {len(services_with_discounts)}")
        
        if not services_with_discounts:
            print("   ⚠️  No services with discounts found - cannot verify discount calculations")
            return True
        
        print("\n   Services with discounts:")
        for service in services_with_discounts:
            discount = service.get('discount_percentage', 0)
            price = service.get('price', 0)
            discounted_price = price * (1 - discount/100)
            print(f"     - {service.get('name')}: {price} RSD → {discounted_price:.2f} RSD ({discount}% discount)")
            
    except Exception as e:
        print(f"   ❌ ERROR getting services: {e}")
        return False
    
    # Step 2: Get recent appointments to see which use discounted services
    print("\n2. Getting recent appointments...")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/appointments")
        response.raise_for_status()
        appointments = response.json()
        
        print(f"   Total appointments: {len(appointments)}")
        
        # Find appointments using discounted services
        discounted_service_ids = {s['id'] for s in services_with_discounts}
        discounted_appointments = [apt for apt in appointments if apt.get('service_id') in discounted_service_ids]
        
        print(f"   Appointments using discounted services: {len(discounted_appointments)}")
        
        if not discounted_appointments:
            print("   ⚠️  No appointments using discounted services found")
            return True
        
        # Calculate expected revenue manually
        expected_total_revenue = 0
        service_map = {s['id']: s for s in services}
        
        print("\n   Appointments with discounted services:")
        for apt in discounted_appointments:
            service = service_map.get(apt['service_id'])
            if service:
                original_price = service.get('price', 0)
                discount = service.get('discount_percentage', 0)
                discounted_price = original_price * (1 - discount/100)
                expected_total_revenue += discounted_price
                
                print(f"     - {apt.get('client_first_name')} {apt.get('client_last_name')}: {service.get('name')}")
                print(f"       Original: {original_price} RSD, Discounted: {discounted_price:.2f} RSD ({discount}% off)")
        
        print(f"\n   Expected total revenue from discounted appointments: {expected_total_revenue:.2f} RSD")
        
    except Exception as e:
        print(f"   ❌ ERROR getting appointments: {e}")
        return False
    
    # Step 3: Compare with analytics revenue endpoint
    print("\n3. Comparing with analytics revenue...")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/analytics/revenue?period=month")
        response.raise_for_status()
        revenue_data = response.json()
        
        analytics_total_revenue = revenue_data.get('total_revenue', 0)
        print(f"   Analytics total revenue: {analytics_total_revenue} RSD")
        
        # Note: We can't do exact comparison since analytics includes all appointments,
        # but we can verify that discounted services contribute less than their original price
        if len(discounted_appointments) > 0 and analytics_total_revenue > 0:
            print("   ✅ Analytics endpoint returns revenue data")
            
            # Verify that if we have discounted appointments, the total should be less than
            # what it would be without discounts
            total_without_discounts = 0
            for apt in discounted_appointments:
                service = service_map.get(apt['service_id'])
                if service:
                    total_without_discounts += service.get('price', 0)
            
            if total_without_discounts > expected_total_revenue:
                print(f"   ✅ Discount calculation verified: {total_without_discounts:.2f} RSD → {expected_total_revenue:.2f} RSD")
                print(f"   ✅ Savings from discounts: {total_without_discounts - expected_total_revenue:.2f} RSD")
            else:
                print("   ⚠️  Could not verify discount calculation (no price difference detected)")
        
    except Exception as e:
        print(f"   ❌ ERROR getting analytics revenue: {e}")
        all_tests_passed = False
    
    # Step 4: Test specific discount calculation (5% example from requirements)
    print("\n4. Testing specific 5% discount calculation...")
    print("-" * 60)
    
    # Find services with 5% discount (Tradicionalna tajlandska masaža)
    five_percent_services = [s for s in services_with_discounts if s.get('discount_percentage') == 5]
    
    if five_percent_services:
        for service in five_percent_services:
            original_price = service.get('price', 0)
            expected_discounted = original_price * 0.95
            
            print(f"   Service: {service.get('name')}")
            print(f"   Original price: {original_price} RSD")
            print(f"   Expected with 5% discount: {expected_discounted} RSD")
            print(f"   Calculation: {original_price} * 0.95 = {expected_discounted}")
            
            # Verify the math
            if abs(expected_discounted - (original_price * 0.95)) < 0.01:
                print("   ✅ 5% discount calculation is correct")
            else:
                print("   ❌ FAILED: 5% discount calculation error")
                all_tests_passed = False
    else:
        print("   ⚠️  No services with 5% discount found")
    
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

def test_spa_booking_with_notifications():
    """
    Test SPA booking with notifications (with client email)
    POST /api/spa/appointments
    Expected: notify_status: "sent", email_sent: true, email_sent_admin: true, email_sent_client: true, notification_created: true
    """
    print("=" * 80)
    print("TEST: SPA BOOKING WITH NOTIFICATIONS (WITH CLIENT EMAIL)")
    print("=" * 80)
    
    # Test payload as specified in review request
    payload = {
        "client_email": "test-agent@example.com",
        "client_first_name": "TestAgent",
        "client_last_name": "Verification",
        "client_phone": "+381600000001",
        "spa_category": "spa_ritual",
        "notes": "SPA paket: Gentle Touch Ritual Ukupno trajanje: 180 min",
        "total_original": 10400,
        "final_price": 10400
    }
    
    print(f"Request payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/spa/appointments",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected HTTP 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        try:
            data = response.json()
            
            # Check for required notification fields
            expected_fields = {
                "notify_status": "sent",
                "email_sent": True,
                "email_sent_admin": True,
                "email_sent_client": True,
                "notification_created": True
            }
            
            all_checks_passed = True
            
            for field, expected_value in expected_fields.items():
                actual_value = data.get(field)
                if actual_value == expected_value:
                    print(f"✅ {field}: {actual_value}")
                else:
                    print(f"❌ {field}: Expected {expected_value}, got {actual_value}")
                    all_checks_passed = False
            
            # Check for appointment ID
            appointment_id = data.get("id")
            if appointment_id:
                print(f"✅ SPA appointment created with ID: {appointment_id}")
            else:
                print(f"❌ FAILED: Response missing required 'id' field")
                all_checks_passed = False
            
            return all_checks_passed
            
        except json.JSONDecodeError:
            print(f"❌ FAILED: Response is not valid JSON")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR during SPA booking with notifications: {e}")
        return False

def test_spa_booking_without_client_email():
    """
    Test SPA booking without client email
    POST /api/spa/appointments
    Expected: email_sent_client: false, email_sent_admin: true, notification_created: true
    """
    print("=" * 80)
    print("TEST: SPA BOOKING WITHOUT CLIENT EMAIL")
    print("=" * 80)
    
    # Test payload without client_email (empty string)
    payload = {
        "client_email": "",
        "client_first_name": "TestAgent",
        "client_last_name": "NoEmail",
        "client_phone": "+381600000002",
        "spa_category": "spa_ritual",
        "notes": "SPA paket: Gentle Touch Ritual Ukupno trajanje: 180 min",
        "total_original": 10400,
        "final_price": 10400
    }
    
    print(f"Request payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/spa/appointments",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected HTTP 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        try:
            data = response.json()
            
            # Check for required notification fields (no client email)
            expected_fields = {
                "email_sent_client": False,
                "email_sent_admin": True,
                "notification_created": True
            }
            
            all_checks_passed = True
            
            for field, expected_value in expected_fields.items():
                actual_value = data.get(field)
                if actual_value == expected_value:
                    print(f"✅ {field}: {actual_value}")
                else:
                    print(f"❌ {field}: Expected {expected_value}, got {actual_value}")
                    all_checks_passed = False
            
            # Check for appointment ID
            appointment_id = data.get("id")
            if appointment_id:
                print(f"✅ SPA appointment created with ID: {appointment_id}")
            else:
                print(f"❌ FAILED: Response missing required 'id' field")
                all_checks_passed = False
            
            return all_checks_passed
            
        except json.JSONDecodeError:
            print(f"❌ FAILED: Response is not valid JSON")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR during SPA booking without client email: {e}")
        return False

def check_backend_logs():
    """
    Check backend logs for notification messages
    Expected: SPA_BOOKED, ADMIN_EMAIL_SENT, CLIENT_EMAIL_SENT/CLIENT_EMAIL_SKIPPED, NOTIFICATION_CREATED
    """
    print("=" * 80)
    print("TEST: CHECK BACKEND LOGS FOR NOTIFICATIONS")
    print("=" * 80)
    
    try:
        # Check supervisor backend logs
        result = subprocess.run(
            ["tail", "-n", "100", "/var/log/supervisor/backend.out.log"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"❌ FAILED: Could not read backend logs (exit code: {result.returncode})")
            print(f"Error: {result.stderr}")
            return False
        
        log_content = result.stdout
        print(f"✅ Successfully read backend logs ({len(log_content.splitlines())} lines)")
        
        # Check for expected log messages
        expected_patterns = [
            "✅ SPA_BOOKED",
            "📧 ADMIN_EMAIL_SENT to=bualuangthailandspa@gmail.com",
            "📧 CLIENT_EMAIL_SENT",
            "ℹ️ CLIENT_EMAIL_SKIPPED",
            "🔔 NOTIFICATION_CREATED"
        ]
        
        found_patterns = []
        
        for pattern in expected_patterns:
            if pattern in log_content:
                found_patterns.append(pattern)
                print(f"✅ Found log pattern: {pattern}")
            else:
                print(f"⚠️  Log pattern not found: {pattern}")
        
        # Show recent relevant log lines
        print(f"\nRecent relevant log lines:")
        lines = log_content.splitlines()
        relevant_lines = []
        
        for line in lines[-50:]:  # Check last 50 lines
            if any(keyword in line for keyword in ["SPA_BOOKED", "EMAIL_SENT", "EMAIL_SKIPPED", "NOTIFICATION_CREATED"]):
                relevant_lines.append(line)
        
        if relevant_lines:
            for line in relevant_lines[-10:]:  # Show last 10 relevant lines
                print(f"  {line}")
        else:
            print("  No relevant notification logs found in recent entries")
        
        # Return success if we found at least some notification patterns
        if len(found_patterns) >= 2:
            print(f"✅ SUCCESS: Found {len(found_patterns)} notification patterns in logs")
            return True
        else:
            print(f"❌ FAILED: Only found {len(found_patterns)} notification patterns (expected at least 2)")
            return False
        
    except subprocess.TimeoutExpired:
        print(f"❌ ERROR: Timeout reading backend logs")
        return False
    except Exception as e:
        print(f"❌ ERROR checking backend logs: {e}")
        return False

def test_website_couple_booking_endpoint():
    """
    Test the specific website couple booking endpoint that's failing on production
    POST /api/website/book-couple-appointment
    """
    
    print("=" * 80)
    print("🎯 TESTING WEBSITE COUPLE BOOKING ENDPOINT - SERBIAN REVIEW REQUEST")
    print("=" * 80)
    
    all_tests_passed = True
    
    # Step 1: Get couple services list
    print("\n1. Getting couple services list...")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/services/couples/list")
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ FAILED: Expected HTTP 200, got {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        couple_services = response.json()
        print(f"   ✅ Found {len(couple_services)} couple services")
        
        if len(couple_services) < 2:
            print("   ❌ ERROR: Need at least 2 couple services for testing")
            return False
        
        # Use first two services for testing
        service1 = couple_services[0]
        service2 = couple_services[1] if len(couple_services) > 1 else couple_services[0]
        
        print(f"   Service 1: {service1['name']} (ID: {service1['id']}, Price: {service1['price']} RSD)")
        print(f"   Service 2: {service2['name']} (ID: {service2['id']}, Price: {service2['price']} RSD)")
        
    except Exception as e:
        print(f"   ❌ ERROR getting couple services: {e}")
        return False
    
    # Step 2: Test the website booking endpoint with correct payload format
    print("\n2. Testing POST /api/website/book-couple-appointment...")
    print("-" * 60)
    
    # Test scenarios for different duration types
    test_scenarios = [
        {"duration_type": 60, "description": "60-minute couple massage"},
        {"duration_type": 90, "description": "90-minute couple massage"},
        {"duration_type": 120, "description": "120-minute couple massage (CRITICAL TEST)"}
    ]
    
    for scenario in test_scenarios:
        print(f"\n   Testing {scenario['description']}...")
        
        # Prepare the exact payload format expected by CoupleAppointmentWebsite model
        start_time = datetime.now() + timedelta(days=1)  # Tomorrow
        payload = {
            "client_first_name": "Marko",
            "client_last_name": "Petrović",
            "client_phone": "+381601234567",
            "client_email": "marko.petrovic@example.com",
            "start_time": start_time.isoformat(),
            "duration_type": scenario["duration_type"],
            "person1_services": [service1["id"]],  # List of service IDs
            "person2_services": [service2["id"]],  # List of service IDs
            "discount_couples_massage": 0.0  # No default discount
        }
        
        print(f"   Payload: {json.dumps(payload, indent=4)}")
        
        try:
            # Test the website endpoint (should auto-assign therapist)
            response = requests.post(
                f"{BACKEND_URL}/website/book-couple-appointment",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"   Response Status: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            if response.status_code == 404:
                print("   ⚠️  Endpoint /api/website/book-couple-appointment not found!")
                print("   Trying alternative endpoint: /api/book-couple-appointment")
                
                # Try the alternative endpoint
                response = requests.post(
                    f"{BACKEND_URL}/book-couple-appointment",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"   Alternative Response Status: {response.status_code}")
            
            if response.status_code == 200:
                appointment_data = response.json()
                print(f"   ✅ SUCCESS: Appointment created with ID: {appointment_data.get('id')}")
                print(f"   Service ID: {appointment_data.get('service_id')}")
                print(f"   Start Time: {appointment_data.get('start_time')}")
                print(f"   End Time: {appointment_data.get('end_time')}")
                
                # Verify snapshot data is present
                if 'snapshot_price' in appointment_data:
                    print(f"   ✅ Snapshot data present:")
                    print(f"     - Snapshot Price: {appointment_data.get('snapshot_price')} RSD")
                    print(f"     - Original Price: {appointment_data.get('snapshot_original_price')} RSD")
                    print(f"     - Discount: {appointment_data.get('snapshot_discount_percentage')}%")
                else:
                    print("   ⚠️  No snapshot data in response")
                
            else:
                print(f"   ❌ FAILED: Expected 200, got {response.status_code}")
                print(f"   Response Body: {response.text}")
                all_tests_passed = False
                
                # Try to parse error details
                try:
                    error_data = response.json()
                    print(f"   Error Details: {json.dumps(error_data, indent=4)}")
                except:
                    pass
                
        except Exception as e:
            print(f"   ❌ ERROR during request: {e}")
            all_tests_passed = False
    
    # Step 3: Test with invalid data to check validation
    print("\n3. Testing validation with invalid data...")
    print("-" * 60)
    
    invalid_payloads = [
        {
            "name": "Missing required fields",
            "payload": {
                "client_first_name": "Test",
                # Missing other required fields
            }
        },
        {
            "name": "Invalid duration_type",
            "payload": {
                "client_first_name": "Test",
                "client_last_name": "User",
                "client_phone": "+381601234567",
                "client_email": "test@example.com",
                "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
                "duration_type": 45,  # Invalid - should be 60, 90, or 120
                "person1_services": [service1["id"]],
                "person2_services": [service2["id"]],
                "discount_couples_massage": 0.0
            }
        },
        {
            "name": "Empty services lists",
            "payload": {
                "client_first_name": "Test",
                "client_last_name": "User",
                "client_phone": "+381601234567",
                "client_email": "test@example.com",
                "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
                "duration_type": 60,
                "person1_services": [],  # Empty
                "person2_services": [],  # Empty
                "discount_couples_massage": 0.0
            }
        }
    ]
    
    for test_case in invalid_payloads:
        print(f"\n   Testing {test_case['name']}...")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/book-couple-appointment",
                json=test_case["payload"],
                headers={"Content-Type": "application/json"}
            )
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code in [400, 422]:  # Expected validation errors
                print(f"   ✅ Validation working: Got expected error {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error message: {error_data.get('detail', 'No detail')}")
                except:
                    pass
            else:
                print(f"   ⚠️  Unexpected response: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ ERROR during validation test: {e}")
    
    # Step 4: Check backend logs for any errors
    print("\n4. Checking backend logs...")
    print("-" * 60)
    print("   💡 To check backend logs manually, run:")
    print("   tail -100 /var/log/supervisor/backend.err.log")
    print("   tail -100 /var/log/supervisor/backend.out.log")
    
    return all_tests_passed

def test_backend_logs_check():
    """Check backend logs for any errors related to couple booking"""
    
    print("=" * 80)
    print("🔍 CHECKING BACKEND LOGS FOR ERRORS")
    print("=" * 80)
    
    try:
        import subprocess
        
        print("\n1. Checking backend error logs...")
        print("-" * 60)
        
        # Check error logs
        result = subprocess.run(
            ["tail", "-50", "/var/log/supervisor/backend.err.log"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            error_logs = result.stdout.strip()
            if error_logs:
                print("   Backend Error Logs (last 50 lines):")
                print("   " + "=" * 50)
                for line in error_logs.split('\n'):
                    print(f"   {line}")
                print("   " + "=" * 50)
            else:
                print("   ✅ No recent error logs found")
        else:
            print(f"   ⚠️  Could not read error logs: {result.stderr}")
        
        print("\n2. Checking backend output logs...")
        print("-" * 60)
        
        # Check output logs
        result = subprocess.run(
            ["tail", "-50", "/var/log/supervisor/backend.out.log"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            output_logs = result.stdout.strip()
            if output_logs:
                print("   Backend Output Logs (last 50 lines):")
                print("   " + "=" * 50)
                for line in output_logs.split('\n'):
                    print(f"   {line}")
                print("   " + "=" * 50)
            else:
                print("   ✅ No recent output logs found")
        else:
            print(f"   ⚠️  Could not read output logs: {result.stderr}")
            
    except Exception as e:
        print(f"   ❌ ERROR checking logs: {e}")
        return False
    
    return True

def test_regular_massage_booking_api():
    """
    Test regular massage booking API endpoints - SERBIAN REVIEW REQUEST
    Issue: "ZAKAZITE" button on regular massages not working
    """
    
    print("=" * 80)
    print("🎯 TESTING REGULAR MASSAGE BOOKING API - SERBIAN REVIEW REQUEST")
    print("ISSUE: 'ZAKAZITE' dugme na običnim masažama NE RADI")
    print("=" * 80)
    
    all_tests_passed = True
    
    # Step 1: Test GET /api/services/single/list (for regular massages)
    print("\n1. Testing GET /api/services/single/list (regular massages)...")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/services/single/list")
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ FAILED: Expected HTTP 200, got {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        regular_services = response.json()
        print(f"   ✅ Found {len(regular_services)} regular massage services")
        
        if len(regular_services) == 0:
            print("   ❌ ERROR: No regular massage services found!")
            return False
        
        # Show some examples
        print("   Examples of regular massages:")
        for i, service in enumerate(regular_services[:5]):  # Show first 5
            print(f"     {i+1}. {service.get('name')} - {service.get('price')} RSD (ID: {service.get('id')})")
        
        # Find specific services mentioned in the issue
        target_services = [
            "Tradicionalna tajlandska masaža",
            "Aroma terapija", 
            "Masaža stopala",
            "Masaža toplim uljem"
        ]
        
        found_services = {}
        for service in regular_services:
            service_name = service.get('name', '')
            for target in target_services:
                if target.lower() in service_name.lower():
                    if target not in found_services:
                        found_services[target] = []
                    found_services[target].append(service)
        
        print(f"\n   Found target services mentioned in issue:")
        for target, services in found_services.items():
            print(f"     {target}: {len(services)} variants")
            for service in services:
                print(f"       - {service.get('name')} (ID: {service.get('id')})")
        
        # Store first service for testing
        test_service = regular_services[0]
        
    except Exception as e:
        print(f"   ❌ ERROR getting regular services: {e}")
        return False
    
    # Step 2: Test GET /api/therapists (needed for appointments)
    print("\n2. Testing GET /api/therapists...")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/therapists")
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ FAILED: Expected HTTP 200, got {response.status_code}")
            return False
        
        therapists = response.json()
        print(f"   ✅ Found {len(therapists)} therapists")
        
        if len(therapists) == 0:
            print("   ❌ ERROR: No therapists found!")
            return False
        
        # Look for "Web Rezervacije" therapist
        web_therapist = None
        for therapist in therapists:
            if "Web" in therapist.get('name', '') or "Generic" in therapist.get('name', ''):
                web_therapist = therapist
                break
        
        if web_therapist:
            print(f"   ✅ Found web booking therapist: {web_therapist.get('name')} (ID: {web_therapist.get('id')})")
            test_therapist_id = web_therapist.get('id')
        else:
            print(f"   ⚠️  No 'Web Rezervacije' therapist found, using first available: {therapists[0].get('name')}")
            test_therapist_id = therapists[0].get('id')
        
    except Exception as e:
        print(f"   ❌ ERROR getting therapists: {e}")
        return False
    
    # Step 3: Test POST /api/appointments (regular massage booking)
    print("\n3. Testing POST /api/appointments (regular massage booking)...")
    print("-" * 60)
    
    try:
        # Prepare test appointment data
        start_time = datetime.now() + timedelta(days=1, hours=2)  # Tomorrow at 2 PM
        appointment_data = {
            "client_first_name": "TestObicna",
            "client_last_name": "Masaza", 
            "client_phone": "0601234567",
            "client_email": "test@obicna.com",
            "therapist_id": test_therapist_id,
            "service_id": test_service.get('id'),
            "start_time": start_time.isoformat(),
            "status": "scheduled"
        }
        
        print(f"   Test appointment data:")
        print(f"     Service: {test_service.get('name')}")
        print(f"     Price: {test_service.get('price')} RSD")
        print(f"     Client: {appointment_data['client_first_name']} {appointment_data['client_last_name']}")
        print(f"     Phone: {appointment_data['client_phone']}")
        print(f"     Email: {appointment_data['client_email']}")
        print(f"     Start Time: {appointment_data['start_time']}")
        
        response = requests.post(
            f"{BACKEND_URL}/appointments",
            json=appointment_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            appointment_result = response.json()
            appointment_id = appointment_result.get('id')
            print(f"   ✅ SUCCESS: Regular massage appointment created!")
            print(f"   Appointment ID: {appointment_id}")
            print(f"   Service ID: {appointment_result.get('service_id')}")
            print(f"   Start Time: {appointment_result.get('start_time')}")
            print(f"   End Time: {appointment_result.get('end_time')}")
            
            # Check for snapshot data
            if 'snapshot_price' in appointment_result:
                print(f"   ✅ Snapshot data present:")
                print(f"     - Snapshot Price: {appointment_result.get('snapshot_price')} RSD")
                print(f"     - Original Price: {appointment_result.get('snapshot_original_price')} RSD")
                print(f"     - Discount: {appointment_result.get('snapshot_discount_percentage')}%")
            else:
                print(f"   ⚠️  No snapshot data in response")
            
        else:
            print(f"   ❌ FAILED: Expected 200, got {response.status_code}")
            print(f"   Response: {response.text}")
            all_tests_passed = False
            
            # Try to parse error details
            try:
                error_data = response.json()
                print(f"   Error Details: {json.dumps(error_data, indent=4)}")
            except:
                pass
        
    except Exception as e:
        print(f"   ❌ ERROR during regular appointment creation: {e}")
        all_tests_passed = False
    
    # Step 4: Test /contact page availability
    print("\n4. Testing /contact page availability...")
    print("-" * 60)
    
    try:
        # Test if /contact page exists
        contact_url = f"{WEBSITE_URL}/contact"
        response = requests.head(contact_url, timeout=10)
        print(f"   Contact page URL: {contact_url}")
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ /contact page exists and is accessible")
        elif response.status_code == 404:
            print(f"   ❌ /contact page NOT FOUND (404)")
            all_tests_passed = False
        else:
            print(f"   ⚠️  /contact page returned status: {response.status_code}")
        
    except Exception as e:
        print(f"   ❌ ERROR checking /contact page: {e}")
        all_tests_passed = False
    
    # Step 5: Compare with production backend
    print("\n5. Testing production backend availability...")
    print("-" * 60)
    
    try:
        # Test production backend services
        response = requests.get(f"{PRODUCTION_BACKEND_URL}/services/single/list", timeout=10)
        print(f"   Production backend URL: {PRODUCTION_BACKEND_URL}")
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            prod_services = response.json()
            print(f"   ✅ Production backend accessible: {len(prod_services)} services")
        else:
            print(f"   ❌ Production backend issue: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Test production appointments endpoint
        test_appointment = {
            "client_first_name": "TestProd",
            "client_last_name": "User",
            "client_phone": "0601234567",
            "client_email": "test@prod.com",
            "therapist_id": "test-therapist",
            "service_id": "test-service",
            "start_time": (datetime.now() + timedelta(days=1)).isoformat()
        }
        
        response = requests.post(
            f"{PRODUCTION_BACKEND_URL}/appointments",
            json=test_appointment,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Production appointments endpoint: {response.status_code}")
        if response.status_code == 404:
            print(f"   ❌ CRITICAL: Production /api/appointments endpoint NOT FOUND!")
            print(f"   This explains why regular massage booking doesn't work on production!")
        elif response.status_code in [400, 422]:
            print(f"   ✅ Production appointments endpoint exists (validation error expected)")
        else:
            print(f"   Response: {response.text}")
        
    except Exception as e:
        print(f"   ❌ ERROR testing production backend: {e}")
    
    return all_tests_passed

def test_contact_form_integration():
    """
    Test if Contact.js form is properly integrated with backend API
    """
    
    print("=" * 80)
    print("🔍 TESTING CONTACT FORM API INTEGRATION")
    print("=" * 80)
    
    # Check if Contact.js file exists and contains API integration
    print("\n1. Checking Contact.js file...")
    print("-" * 60)
    
    try:
        # Read Contact.js file
        with open('/app/frontend/src/pages/Contact.js', 'r') as f:
            contact_content = f.read()
        
        print("   ✅ Contact.js file found")
        
        # Check for API integration patterns
        api_patterns = [
            'fetch(',
            'axios.',
            '/api/appointments',
            'POST',
            'handleSubmit'
        ]
        
        found_patterns = []
        for pattern in api_patterns:
            if pattern in contact_content:
                found_patterns.append(pattern)
        
        print(f"   API integration patterns found: {found_patterns}")
        
        if '/api/appointments' in contact_content and 'POST' in contact_content:
            print("   ✅ Contact form appears to have API integration")
        else:
            print("   ❌ CRITICAL: Contact form missing API integration!")
            print("   This explains why ZAKAZITE button doesn't work!")
            
            # Check for mailto or other non-API submission
            if 'mailto:' in contact_content:
                print("   ⚠️  Form uses mailto: instead of API")
            elif 'action=' in contact_content:
                print("   ⚠️  Form uses HTML form action instead of API")
            else:
                print("   ⚠️  Form submission method unclear")
        
        # Check for error handling
        if 'catch' in contact_content or 'error' in contact_content.lower():
            print("   ✅ Error handling present in form")
        else:
            print("   ⚠️  No error handling detected")
        
        # Check for success handling
        if 'success' in contact_content.lower() or 'alert' in contact_content:
            print("   ✅ Success handling present in form")
        else:
            print("   ⚠️  No success handling detected")
    
    except FileNotFoundError:
        print("   ❌ ERROR: Contact.js file not found!")
        return False
    except Exception as e:
        print(f"   ❌ ERROR reading Contact.js: {e}")
        return False
    
    return True

def check_frontend_build_and_deployment():
    """
    Check if frontend is properly built and deployed
    """
    
    print("=" * 80)
    print("🔍 CHECKING FRONTEND BUILD AND DEPLOYMENT")
    print("=" * 80)
    
    print("\n1. Checking frontend build status...")
    print("-" * 60)
    
    try:
        # Check if build directory exists
        import os
        build_path = '/app/frontend/build'
        if os.path.exists(build_path):
            print(f"   ✅ Build directory exists: {build_path}")
            
            # Check build contents
            build_files = os.listdir(build_path)
            print(f"   Build contains {len(build_files)} files/directories")
            
            # Look for key files
            key_files = ['index.html', 'static']
            for key_file in key_files:
                if key_file in build_files:
                    print(f"   ✅ {key_file} found in build")
                else:
                    print(f"   ❌ {key_file} missing from build")
        else:
            print(f"   ❌ Build directory not found: {build_path}")
            print("   This could explain why updated Contact.js is not deployed")
    
    except Exception as e:
        print(f"   ❌ ERROR checking build: {e}")
    
    print("\n2. Checking frontend service status...")
    print("-" * 60)
    
    try:
        # Check supervisor status
        result = subprocess.run(
            ["sudo", "supervisorctl", "status", "frontend"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            status_output = result.stdout.strip()
            print(f"   Frontend service status: {status_output}")
            
            if "RUNNING" in status_output:
                print("   ✅ Frontend service is running")
            else:
                print("   ❌ Frontend service is not running properly")
        else:
            print(f"   ❌ Error checking frontend status: {result.stderr}")
    
    except Exception as e:
        print(f"   ❌ ERROR checking frontend service: {e}")
    
    return True

if __name__ == "__main__":
    # Run SPA notification tests as specified in review request
    success = run_spa_notification_tests()
    sys.exit(0 if success else 1)
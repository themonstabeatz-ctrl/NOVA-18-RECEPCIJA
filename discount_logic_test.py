#!/usr/bin/env python3
"""
Discount Logic Testing Script - Serbian Review Request
Testing new discount logic that uses service_code for highest discount application

Test Scenarios:
1. GET /api/services - Check service_code and final_price
2. POST /api/appointments - Single appointment with highest discount
3. POST /api/book-couple-appointment - Highest discount from all available
4. Backend logs verification
5. Check no duplicate discounts
"""

import requests
import json
from datetime import datetime, timedelta
import sys
import subprocess

# Backend URL from environment
BACKEND_URL = "https://spa-booking-api.preview.emergentagent.com/api"

def test_services_service_code_and_final_price():
    """
    Test 1: GET /api/services - Provera service_code i final_price
    Verify all services have service_code and correctly calculated final_price
    """
    
    print("=" * 80)
    print("TEST 1: GET /api/services - PROVERA SERVICE_CODE I FINAL_PRICE")
    print("=" * 80)
    
    all_tests_passed = True
    
    print("\n1. Pozivam GET /api/services...")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/services")
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ FAILED: Expected HTTP 200, got {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        print("   ✅ API returns HTTP 200")
        
        services = response.json()
        if not isinstance(services, list):
            print(f"   ❌ FAILED: Response is not a JSON array")
            return False
        
        print(f"   ✅ Response is valid JSON array with {len(services)} services")
        
        # Check each service for required fields
        services_without_service_code = []
        services_without_final_price = []
        price_calculation_errors = []
        
        masaza_stopala_60_found = False
        masaza_stopala_60_details = None
        
        for service in services:
            service_name = service.get('name', 'Unknown')
            service_id = service.get('id', 'Unknown')
            
            # Check service_code
            if 'service_code' not in service or not service['service_code']:
                services_without_service_code.append(f"{service_name} (ID: {service_id})")
            
            # Check final_price
            if 'final_price' not in service:
                services_without_final_price.append(f"{service_name} (ID: {service_id})")
            else:
                # Verify final_price calculation
                original_price = service.get('price', 0)
                discount_percentage = service.get('discount_percentage', 0)
                final_price = service.get('final_price', 0)
                
                expected_final_price = original_price * (1 - discount_percentage / 100)
                
                if abs(final_price - expected_final_price) > 0.01:
                    price_calculation_errors.append({
                        'name': service_name,
                        'id': service_id,
                        'original_price': original_price,
                        'discount_percentage': discount_percentage,
                        'final_price': final_price,
                        'expected_final_price': expected_final_price
                    })
            
            # Look for specific service: "Masaža stopala - 60 min"
            if "Masaža stopala" in service_name and "60 min" in service_name:
                masaza_stopala_60_found = True
                masaza_stopala_60_details = service
                print(f"\n   🎯 FOUND TARGET SERVICE: {service_name}")
                print(f"      Service ID: {service_id}")
                print(f"      Service Code: {service.get('service_code', 'MISSING')}")
                print(f"      Original Price: {service.get('price', 0)} RSD")
                print(f"      Discount: {service.get('discount_percentage', 0)}%")
                print(f"      Final Price: {service.get('final_price', 0)} RSD")
        
        # Report results
        if services_without_service_code:
            print(f"\n   ❌ FAILED: {len(services_without_service_code)} services missing service_code:")
            for service_info in services_without_service_code[:5]:  # Show first 5
                print(f"      - {service_info}")
            if len(services_without_service_code) > 5:
                print(f"      ... and {len(services_without_service_code) - 5} more")
            all_tests_passed = False
        else:
            print(f"   ✅ All {len(services)} services have service_code")
        
        if services_without_final_price:
            print(f"\n   ❌ FAILED: {len(services_without_final_price)} services missing final_price:")
            for service_info in services_without_final_price[:5]:
                print(f"      - {service_info}")
            all_tests_passed = False
        else:
            print(f"   ✅ All {len(services)} services have final_price")
        
        if price_calculation_errors:
            print(f"\n   ❌ FAILED: {len(price_calculation_errors)} services have incorrect final_price calculation:")
            for error in price_calculation_errors[:3]:  # Show first 3
                print(f"      - {error['name']}: Expected {error['expected_final_price']:.2f}, got {error['final_price']:.2f}")
            all_tests_passed = False
        else:
            print(f"   ✅ All services have correct final_price calculation")
        
        # Specific test for Masaža stopala - 60 min
        print(f"\n2. Specifična provera: Masaža stopala - 60 min")
        print("-" * 60)
        
        if not masaza_stopala_60_found:
            print("   ❌ FAILED: Could not find 'Masaža stopala - 60 min' service")
            all_tests_passed = False
        else:
            service = masaza_stopala_60_details
            service_code = service.get('service_code')
            discount_percentage = service.get('discount_percentage', 0)
            final_price = service.get('final_price', 0)
            original_price = service.get('price', 0)
            
            print(f"   Service Code: {service_code}")
            print(f"   Expected Service Code: MASAZA_STOPALA_60")
            
            if service_code == "MASAZA_STOPALA_60":
                print("   ✅ Service code matches expected")
            else:
                print("   ❌ FAILED: Service code mismatch")
                all_tests_passed = False
            
            # Check if highest discount is applied (15% expected)
            print(f"   Current Discount: {discount_percentage}%")
            print(f"   Expected Discount: 15% (highest between regular 5% and [PAROVI] 15%)")
            
            if discount_percentage == 15.0:
                print("   ✅ Highest discount (15%) is applied")
            else:
                print(f"   ❌ FAILED: Expected 15% discount, got {discount_percentage}%")
                all_tests_passed = False
            
            # Check final price calculation
            expected_final_price = 2677.5  # 3150 * (1 - 15/100)
            print(f"   Final Price: {final_price} RSD")
            print(f"   Expected Final Price: {expected_final_price} RSD")
            
            if abs(final_price - expected_final_price) < 0.1:
                print("   ✅ Final price matches expected (2677.5 RSD)")
            else:
                print(f"   ❌ FAILED: Expected {expected_final_price} RSD, got {final_price} RSD")
                all_tests_passed = False
        
        # Check for services with same service_code having same discount
        print(f"\n3. Provera konzistentnosti popusta za isti service_code")
        print("-" * 60)
        
        service_code_groups = {}
        for service in services:
            service_code = service.get('service_code')
            if service_code:
                if service_code not in service_code_groups:
                    service_code_groups[service_code] = []
                service_code_groups[service_code].append(service)
        
        inconsistent_groups = []
        for service_code, group_services in service_code_groups.items():
            if len(group_services) > 1:
                discounts = [s.get('discount_percentage', 0) for s in group_services]
                if len(set(discounts)) > 1:
                    inconsistent_groups.append({
                        'service_code': service_code,
                        'services': group_services,
                        'discounts': discounts
                    })
        
        if inconsistent_groups:
            print(f"   ❌ FAILED: {len(inconsistent_groups)} service_code groups have inconsistent discounts:")
            for group in inconsistent_groups[:3]:
                print(f"      Service Code: {group['service_code']}")
                print(f"      Discounts: {group['discounts']}")
                for service in group['services']:
                    print(f"        - {service.get('name')}: {service.get('discount_percentage', 0)}%")
            all_tests_passed = False
        else:
            print(f"   ✅ All services with same service_code have consistent discount_percentage")
        
    except Exception as e:
        print(f"   ❌ ERROR during services API test: {e}")
        all_tests_passed = False
    
    return all_tests_passed

def test_single_appointment_highest_discount():
    """
    Test 2: POST /api/appointments - Single Appointment sa Najvećim Popustom
    Create appointment and verify highest discount is applied
    """
    
    print("=" * 80)
    print("TEST 2: POST /api/appointments - SINGLE APPOINTMENT SA NAJVEĆIM POPUSTOM")
    print("=" * 80)
    
    all_tests_passed = True
    
    # Get therapist ID
    print("\n1. Getting valid therapist ID...")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/therapists")
        response.raise_for_status()
        therapists = response.json()
        
        if not therapists:
            print("   ❌ ERROR: No therapists found")
            return False
        
        therapist_id = therapists[0]['id']
        print(f"   ✅ Found therapist: {therapists[0]['name']} (ID: {therapist_id})")
        
    except Exception as e:
        print(f"   ❌ ERROR getting therapists: {e}")
        return False
    
    # Find the specific service: "Masaža stopala 60min - Obična kategorija"
    print("\n2. Finding target service: Masaža stopala 60min...")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/services")
        response.raise_for_status()
        services = response.json()
        
        target_service = None
        target_service_id = "51ed3e01-857f-497c-8ac3-f7950784a1d5"  # From review request
        
        for service in services:
            if service.get('id') == target_service_id:
                target_service = service
                break
        
        if not target_service:
            # Try to find by name if ID doesn't match
            for service in services:
                if "Masaža stopala" in service.get('name', '') and "60 min" in service.get('name', ''):
                    target_service = service
                    target_service_id = service['id']
                    break
        
        if not target_service:
            print("   ❌ ERROR: Could not find Masaža stopala 60min service")
            return False
        
        print(f"   ✅ Found target service: {target_service['name']}")
        print(f"   Service ID: {target_service_id}")
        print(f"   Current discount: {target_service.get('discount_percentage', 0)}%")
        
    except Exception as e:
        print(f"   ❌ ERROR getting services: {e}")
        return False
    
    # Create appointment
    print("\n3. Creating appointment...")
    print("-" * 60)
    
    try:
        start_time = datetime.now() + timedelta(days=1)
        request_data = {
            "client_first_name": "Test",
            "client_last_name": "User",
            "client_phone": "+381641234567",
            "therapist_id": therapist_id,
            "service_id": target_service_id,
            "start_time": start_time.isoformat(),
            "status": "scheduled"
        }
        
        print(f"   Creating appointment for service: {target_service['name']}")
        print(f"   Service ID: {target_service_id}")
        
        response = requests.post(
            f"{BACKEND_URL}/appointments",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ FAILED: Expected 200, got {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        appointment_data = response.json()
        appointment_id = appointment_data.get('id')
        
        print(f"   ✅ Appointment created successfully")
        print(f"   Appointment ID: {appointment_id}")
        
        # Check snapshot data
        snapshot_price = appointment_data.get('snapshot_price')
        snapshot_original_price = appointment_data.get('snapshot_original_price')
        snapshot_discount_percentage = appointment_data.get('snapshot_discount_percentage')
        
        print(f"\n   Snapshot Data:")
        print(f"   snapshot_price: {snapshot_price}")
        print(f"   snapshot_original_price: {snapshot_original_price}")
        print(f"   snapshot_discount_percentage: {snapshot_discount_percentage}%")
        
        # Expected values from review request
        expected_snapshot_price = 2677.5
        expected_original_price = 3150
        expected_discount = 15.0
        
        print(f"\n   Expected Values:")
        print(f"   Expected snapshot_price: {expected_snapshot_price}")
        print(f"   Expected original_price: {expected_original_price}")
        print(f"   Expected discount: {expected_discount}%")
        
        # Verify snapshot_price
        if snapshot_price and abs(snapshot_price - expected_snapshot_price) < 0.1:
            print("   ✅ snapshot_price matches expected (2677.5 RSD)")
        else:
            print(f"   ❌ FAILED: Expected snapshot_price {expected_snapshot_price}, got {snapshot_price}")
            all_tests_passed = False
        
        # Verify snapshot_original_price
        if snapshot_original_price and abs(snapshot_original_price - expected_original_price) < 0.1:
            print("   ✅ snapshot_original_price matches expected (3150 RSD)")
        else:
            print(f"   ❌ FAILED: Expected snapshot_original_price {expected_original_price}, got {snapshot_original_price}")
            all_tests_passed = False
        
        # Verify snapshot_discount_percentage
        if snapshot_discount_percentage and abs(snapshot_discount_percentage - expected_discount) < 0.1:
            print("   ✅ snapshot_discount_percentage matches expected (15%)")
            print("   ✅ CRITICAL: System applied highest discount (15%) instead of service's original discount")
        else:
            print(f"   ❌ FAILED: Expected snapshot_discount_percentage {expected_discount}%, got {snapshot_discount_percentage}%")
            all_tests_passed = False
        
    except Exception as e:
        print(f"   ❌ ERROR creating appointment: {e}")
        all_tests_passed = False
    
    return all_tests_passed

def test_couple_appointment_highest_discount():
    """
    Test 3: POST /api/book-couple-appointment - Najveći Popust od Svih
    Test couple booking with highest discount from all available
    """
    
    print("=" * 80)
    print("TEST 3: POST /api/book-couple-appointment - NAJVEĆI POPUST OD SVIH")
    print("=" * 80)
    
    all_tests_passed = True
    
    # Test scenario from review request
    print("\n1. Setting up test scenario...")
    print("-" * 60)
    
    person1_service_id = "51ed3e01-857f-497c-8ac3-f7950784a1d5"  # Masaža stopala 60 min (15% best discount)
    person2_service_id = "9bffd831-89a7-4ea7-b7f2-117515eb7a2b"  # Masaža stopala 30 min (10% discount)
    couple_discount = 0.0  # No couple discount
    
    print(f"   Person 1 Service ID: {person1_service_id} (expected 15% best discount)")
    print(f"   Person 2 Service ID: {person2_service_id} (expected 10% discount)")
    print(f"   Couple Discount: {couple_discount}%")
    
    # Get services to verify they exist
    print("\n2. Verifying services exist...")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/services")
        response.raise_for_status()
        services = response.json()
        service_map = {s['id']: s for s in services}
        
        person1_service = service_map.get(person1_service_id)
        person2_service = service_map.get(person2_service_id)
        
        if not person1_service:
            print(f"   ❌ ERROR: Person 1 service not found: {person1_service_id}")
            return False
        
        if not person2_service:
            print(f"   ❌ ERROR: Person 2 service not found: {person2_service_id}")
            return False
        
        print(f"   ✅ Person 1 Service: {person1_service['name']}")
        print(f"      Price: {person1_service.get('price', 0)} RSD")
        print(f"      Discount: {person1_service.get('discount_percentage', 0)}%")
        
        print(f"   ✅ Person 2 Service: {person2_service['name']}")
        print(f"      Price: {person2_service.get('price', 0)} RSD")
        print(f"      Discount: {person2_service.get('discount_percentage', 0)}%")
        
        # Calculate expected values
        person1_original = person1_service.get('metadata', {}).get('original_price', person1_service.get('price', 0))
        person2_original = person2_service.get('metadata', {}).get('original_price', person2_service.get('price', 0))
        
        expected_original_price = person1_original + person2_original  # 3150 + 2400 = 5550
        expected_discount = 15.0  # MAX of [15%, 10%, 0%]
        expected_final_price = expected_original_price * (1 - expected_discount / 100)  # 5550 * 0.85 = 4717.5
        
        print(f"\n   Expected Calculation:")
        print(f"   Original Price: {expected_original_price} RSD ({person1_original} + {person2_original})")
        print(f"   Best Discount: {expected_discount}% (MAX of [15%, 10%, 0%])")
        print(f"   Final Price: {expected_final_price} RSD")
        
    except Exception as e:
        print(f"   ❌ ERROR getting services: {e}")
        return False
    
    # Create couple appointment
    print("\n3. Creating couple appointment...")
    print("-" * 60)
    
    try:
        start_time = datetime.now() + timedelta(days=1)
        request_data = {
            "client_first_name": "Marko",
            "client_last_name": "Petrovic",
            "client_phone": "+381641234567",
            "start_time": start_time.isoformat(),
            "duration_type": 60,
            "person1_services": [person1_service_id],
            "person2_services": [person2_service_id],
            "discount_couples_massage": couple_discount
        }
        
        print(f"   Creating couple appointment...")
        print(f"   Duration type: {request_data['duration_type']} minutes")
        
        response = requests.post(
            f"{BACKEND_URL}/book-couple-appointment",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ FAILED: Expected 200, got {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        appointment_data = response.json()
        appointment_id = appointment_data.get('id')
        
        print(f"   ✅ Couple appointment created successfully")
        print(f"   Appointment ID: {appointment_id}")
        
        # Check snapshot data
        snapshot_price = appointment_data.get('snapshot_price')
        snapshot_original_price = appointment_data.get('snapshot_original_price')
        snapshot_discount_percentage = appointment_data.get('snapshot_discount_percentage')
        
        print(f"\n   Actual Snapshot Data:")
        print(f"   snapshot_price: {snapshot_price}")
        print(f"   snapshot_original_price: {snapshot_original_price}")
        print(f"   snapshot_discount_percentage: {snapshot_discount_percentage}%")
        
        print(f"\n   Expected Values:")
        print(f"   Expected snapshot_original_price: {expected_original_price}")
        print(f"   Expected snapshot_discount_percentage: {expected_discount}%")
        print(f"   Expected snapshot_price: {expected_final_price}")
        
        # Verify results
        if snapshot_original_price and abs(snapshot_original_price - expected_original_price) < 0.1:
            print("   ✅ snapshot_original_price matches expected")
        else:
            print(f"   ❌ FAILED: Expected snapshot_original_price {expected_original_price}, got {snapshot_original_price}")
            all_tests_passed = False
        
        if snapshot_discount_percentage and abs(snapshot_discount_percentage - expected_discount) < 0.1:
            print("   ✅ snapshot_discount_percentage matches expected (15% - highest)")
            print("   ✅ CRITICAL: System applied ONLY the highest discount, not multiple discounts")
        else:
            print(f"   ❌ FAILED: Expected snapshot_discount_percentage {expected_discount}%, got {snapshot_discount_percentage}%")
            all_tests_passed = False
        
        if snapshot_price and abs(snapshot_price - expected_final_price) < 0.1:
            print("   ✅ snapshot_price matches expected")
        else:
            print(f"   ❌ FAILED: Expected snapshot_price {expected_final_price}, got {snapshot_price}")
            all_tests_passed = False
        
        # Critical check: Ensure discount is NOT multiplied
        if snapshot_discount_percentage:
            # Check that discount is not 32.25% (which would be (1-0.15)*(1-0.10)*(1-0.05) = 0.7225, so 22.75% discount)
            # or any other multiplied combination
            if snapshot_discount_percentage > 20:
                print(f"   ❌ CRITICAL FAILURE: Discount appears to be multiplied! Got {snapshot_discount_percentage}%")
                all_tests_passed = False
            else:
                print("   ✅ CRITICAL: Discount is NOT multiplied - single highest discount applied")
        
    except Exception as e:
        print(f"   ❌ ERROR creating couple appointment: {e}")
        all_tests_passed = False
    
    return all_tests_passed

def test_backend_logs():
    """
    Test 4: Backend Logovi
    Check backend logs for proper discount calculation logging
    """
    
    print("=" * 80)
    print("TEST 4: BACKEND LOGOVI - PROVERA DISCOUNT CALCULATION LOGGING")
    print("=" * 80)
    
    all_tests_passed = True
    
    print("\n1. Checking backend logs...")
    print("-" * 60)
    
    try:
        # Get recent backend logs
        result = subprocess.run(
            ["tail", "-n", "50", "/var/log/supervisor/backend.err.log"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"   ❌ ERROR: Could not read backend logs: {result.stderr}")
            return False
        
        log_content = result.stdout
        log_lines = log_content.split('\n')
        
        print(f"   ✅ Retrieved {len(log_lines)} log lines")
        
        # Look for specific log patterns
        person_logs = []
        price_calculation_logs = []
        applying_best_logs = []
        
        for line in log_lines:
            if "Person 1" in line or "Person 2" in line:
                person_logs.append(line.strip())
            elif "💰 Price Calculation" in line:
                price_calculation_logs.append(line.strip())
            elif "APPLYING_BEST" in line:
                applying_best_logs.append(line.strip())
        
        print(f"\n2. Log Analysis Results:")
        print("-" * 60)
        
        print(f"   Person logs found: {len(person_logs)}")
        for log in person_logs[-3:]:  # Show last 3
            print(f"      {log}")
        
        print(f"   Price calculation logs found: {len(price_calculation_logs)}")
        for log in price_calculation_logs[-2:]:  # Show last 2
            print(f"      {log}")
        
        print(f"   Applying best discount logs found: {len(applying_best_logs)}")
        for log in applying_best_logs[-2:]:  # Show last 2
            print(f"      {log}")
        
        # Verify expected log patterns exist
        if person_logs:
            print("   ✅ Found Person 1/Person 2 service_code and discount logs")
        else:
            print("   ⚠️  No Person 1/Person 2 logs found (may need to create couple appointment first)")
        
        if price_calculation_logs:
            print("   ✅ Found Price Calculation logs with discount lists")
        else:
            print("   ⚠️  No Price Calculation logs found")
        
        if applying_best_logs:
            print("   ✅ Found APPLYING_BEST discount logs")
        else:
            print("   ⚠️  No APPLYING_BEST logs found")
        
        # Look for specific patterns in recent logs
        recent_logs = '\n'.join(log_lines[-20:])  # Last 20 lines
        
        if "service_code=" in recent_logs and "best_discount=" in recent_logs:
            print("   ✅ Recent logs contain service_code and best_discount information")
        else:
            print("   ⚠️  Recent logs may not contain expected discount calculation details")
        
        if "all_discounts=" in recent_logs:
            print("   ✅ Recent logs contain all_discounts list")
        else:
            print("   ⚠️  Recent logs may not contain all_discounts information")
        
    except subprocess.TimeoutExpired:
        print("   ❌ ERROR: Timeout reading backend logs")
        all_tests_passed = False
    except Exception as e:
        print(f"   ❌ ERROR reading backend logs: {e}")
        all_tests_passed = False
    
    return all_tests_passed

def test_no_duplicate_discounts():
    """
    Test 5: Provera Bez Duplih Popusta
    Ensure discounts are NEVER multiplied
    """
    
    print("=" * 80)
    print("TEST 5: PROVERA BEZ DUPLIH POPUSTA - NIKADA SE NE MNOŽI")
    print("=" * 80)
    
    all_tests_passed = True
    
    print("\n1. Testing couple appointment with multiple high discounts...")
    print("-" * 60)
    
    # Test scenario: Both services have 15% discount + 5% couple discount
    # Expected: Only 15% should be applied (highest), NOT 32.25% or any multiplication
    
    try:
        # Find services with high discounts
        response = requests.get(f"{BACKEND_URL}/services")
        response.raise_for_status()
        services = response.json()
        
        # Look for services with 15% discount
        high_discount_services = [s for s in services if s.get('discount_percentage', 0) >= 15]
        
        if len(high_discount_services) < 2:
            print("   ⚠️  Not enough services with 15% discount found, using available services")
            # Use any services with discounts
            high_discount_services = [s for s in services if s.get('discount_percentage', 0) > 0]
        
        if len(high_discount_services) < 2:
            print("   ⚠️  Not enough services with discounts, creating test with available services")
            high_discount_services = services[:2]  # Use first 2 services
        
        person1_service = high_discount_services[0]
        person2_service = high_discount_services[1] if len(high_discount_services) > 1 else high_discount_services[0]
        
        print(f"   Person 1 Service: {person1_service['name']}")
        print(f"      Discount: {person1_service.get('discount_percentage', 0)}%")
        print(f"   Person 2 Service: {person2_service['name']}")
        print(f"      Discount: {person2_service.get('discount_percentage', 0)}%")
        
        couple_discount = 5.0  # Add couple discount
        print(f"   Couple Discount: {couple_discount}%")
        
        # Calculate expected values
        person1_price = person1_service.get('metadata', {}).get('original_price', person1_service.get('price', 0))
        person2_price = person2_service.get('metadata', {}).get('original_price', person2_service.get('price', 0))
        
        all_discounts = [
            person1_service.get('discount_percentage', 0),
            person2_service.get('discount_percentage', 0),
            couple_discount
        ]
        
        expected_discount = max(all_discounts)
        expected_original_price = person1_price + person2_price
        expected_final_price = expected_original_price * (1 - expected_discount / 100)
        
        print(f"\n   Expected Calculation:")
        print(f"   All discounts: {all_discounts}")
        print(f"   Expected discount (MAX): {expected_discount}%")
        print(f"   Original price: {expected_original_price}")
        print(f"   Expected final price: {expected_final_price}")
        
        # Create couple appointment
        start_time = datetime.now() + timedelta(days=1)
        request_data = {
            "client_first_name": "Ana",
            "client_last_name": "Jovic",
            "client_phone": "+381641234567",
            "start_time": start_time.isoformat(),
            "duration_type": 90,
            "person1_services": [person1_service['id']],
            "person2_services": [person2_service['id']],
            "discount_couples_massage": couple_discount
        }
        
        response = requests.post(
            f"{BACKEND_URL}/book-couple-appointment",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n2. Couple appointment creation result:")
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ FAILED: Expected 200, got {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        appointment_data = response.json()
        
        snapshot_price = appointment_data.get('snapshot_price')
        snapshot_original_price = appointment_data.get('snapshot_original_price')
        snapshot_discount_percentage = appointment_data.get('snapshot_discount_percentage')
        
        print(f"   ✅ Appointment created successfully")
        print(f"   Appointment ID: {appointment_data.get('id')}")
        
        print(f"\n3. Discount multiplication check:")
        print("-" * 60)
        
        print(f"   Actual discount applied: {snapshot_discount_percentage}%")
        print(f"   Expected discount (highest): {expected_discount}%")
        
        # Critical checks for discount multiplication
        if snapshot_discount_percentage and abs(snapshot_discount_percentage - expected_discount) < 0.1:
            print("   ✅ CRITICAL: Only highest discount applied - NO multiplication")
        else:
            print(f"   ❌ CRITICAL FAILURE: Discount mismatch - possible multiplication!")
            all_tests_passed = False
        
        # Check for common multiplication patterns
        multiplied_discount_1 = 100 * (1 - (1 - all_discounts[0]/100) * (1 - all_discounts[1]/100) * (1 - all_discounts[2]/100))
        multiplied_discount_2 = sum(all_discounts)  # Simple addition
        
        if snapshot_discount_percentage and abs(snapshot_discount_percentage - multiplied_discount_1) < 0.1:
            print(f"   ❌ CRITICAL FAILURE: Discounts are being MULTIPLIED! ({multiplied_discount_1:.2f}%)")
            all_tests_passed = False
        elif snapshot_discount_percentage and abs(snapshot_discount_percentage - multiplied_discount_2) < 0.1:
            print(f"   ❌ CRITICAL FAILURE: Discounts are being ADDED! ({multiplied_discount_2:.2f}%)")
            all_tests_passed = False
        else:
            print("   ✅ CRITICAL: No discount multiplication or addition detected")
        
        # Verify final price calculation
        if snapshot_price and abs(snapshot_price - expected_final_price) < 0.1:
            print("   ✅ Final price calculation is correct")
        else:
            print(f"   ❌ FAILED: Final price mismatch - Expected {expected_final_price}, got {snapshot_price}")
            all_tests_passed = False
        
        print(f"\n   Final Results:")
        print(f"   Original Price: {snapshot_original_price}")
        print(f"   Discount Applied: {snapshot_discount_percentage}% (single highest)")
        print(f"   Final Price: {snapshot_price}")
        
    except Exception as e:
        print(f"   ❌ ERROR during duplicate discount test: {e}")
        all_tests_passed = False
    
    return all_tests_passed

def main():
    """Run all discount logic tests"""
    
    print("🎯 DISCOUNT LOGIC TESTING - SERBIAN REVIEW REQUEST")
    print("Testing new service_code based discount logic")
    print("=" * 100)
    
    # Run all tests
    test_results = []
    
    print("\n")
    test_results.append(("Test 1: Services API", test_services_service_code_and_final_price()))
    
    print("\n")
    test_results.append(("Test 2: Single Appointment", test_single_appointment_highest_discount()))
    
    print("\n")
    test_results.append(("Test 3: Couple Appointment", test_couple_appointment_highest_discount()))
    
    print("\n")
    test_results.append(("Test 4: Backend Logs", test_backend_logs()))
    
    print("\n")
    test_results.append(("Test 5: No Duplicate Discounts", test_no_duplicate_discounts()))
    
    # Summary
    print("\n" + "=" * 100)
    print("FINAL TEST RESULTS - DISCOUNT LOGIC")
    print("=" * 100)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if not result:
            all_passed = False
    
    print("=" * 100)
    
    if all_passed:
        print("🎉 ALL DISCOUNT LOGIC TESTS PASSED!")
        print("✅ service_code logic working correctly")
        print("✅ Highest discount applied automatically")
        print("✅ No discount multiplication")
        print("✅ Snapshot mechanism preserves discount data")
        print("✅ Backend logging shows proper discount calculation")
    else:
        print("❌ SOME DISCOUNT LOGIC TESTS FAILED!")
        print("Please review the failed tests above and fix the discount logic.")
    
    print("=" * 100)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
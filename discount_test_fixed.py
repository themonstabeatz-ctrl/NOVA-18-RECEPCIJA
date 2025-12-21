#!/usr/bin/env python3
"""
🎯 KRITIČNI TEST: Kompletna Provera Popusta na SVIM Uslugama
Testing comprehensive discount functionality for all services
"""

import requests
import json
from datetime import datetime, timedelta
import sys

# Backend URL from environment
BACKEND_URL = "https://spa-web-update.preview.emergentagent.com/api"

def test_discount_activation_masaza_stopala():
    """Test 1: Popusti na "Masaža stopala" (trenutno 0% na svima)"""
    
    print("=" * 80)
    print("TEST 1: MASAŽA STOPALA - AKTIVIRANJE 5% POPUSTA")
    print("=" * 80)
    
    all_tests_passed = True
    
    # Step 1: Find "Masaža stopala" services
    print("\n1. Pronalaženje 'Masaža stopala' usluga...")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/services")
        response.raise_for_status()
        services = response.json()
        
        # Find all "Masaža stopala" services
        masaza_stopala_services = []
        for service in services:
            if "Masaža stopala" in service.get('name', ''):
                masaza_stopala_services.append(service)
        
        if not masaza_stopala_services:
            print("   ❌ FAILED: Nisu pronađene 'Masaža stopala' usluge")
            return False
        
        print(f"   ✅ Pronađeno {len(masaza_stopala_services)} 'Masaža stopala' usluga:")
        for service in masaza_stopala_services:
            print(f"     - {service['name']}: {service['duration']} min, {service['price']} RSD, {service['discount_percentage']}% popust")
        
        # Focus on services without discount
        services_without_discount = [s for s in masaza_stopala_services if s.get('discount_percentage', 0) == 0]
        print(f"   ✅ Usluge bez popusta: {len(services_without_discount)}")
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    
    # Step 2: Test discount activation on services without discount
    print("\n2. Aktiviranje 5% popusta na uslugama bez popusta...")
    print("-" * 60)
    
    activated_services = []
    
    for i, service in enumerate(services_without_discount, 1):
        service_id = service['id']
        service_name = service['name']
        original_price = service['price']
        
        print(f"\n   Test {i}: {service_name}")
        print(f"   Service ID: {service_id}")
        print(f"   Originalna cena: {original_price} RSD")
        
        try:
            # Activate 5% discount using query parameter
            response = requests.patch(f"{BACKEND_URL}/services/{service_id}/discount?discount=5")
            
            print(f"   PATCH /services/{service_id}/discount?discount=5 Response: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   ❌ FAILED: Aktiviranje popusta neuspešno - Status {response.status_code}")
                print(f"   Response: {response.text}")
                all_tests_passed = False
                continue
            
            updated_service = response.json()
            new_price = updated_service.get('price', 0)
            discount_percentage = updated_service.get('discount_percentage', 0)
            metadata = updated_service.get('metadata', {})
            
            print(f"   ✅ Popust aktiviran uspešno")
            print(f"   Nova cena: {new_price} RSD")
            print(f"   Popust: {discount_percentage}%")
            
            # Verify discount calculation
            expected_price = original_price * 0.95  # 5% discount
            if abs(new_price - expected_price) < 0.01:
                print(f"   ✅ Cena ispravno snižena: {original_price} * 0.95 = {expected_price}")
            else:
                print(f"   ❌ FAILED: Pogrešna cena - očekivano {expected_price}, dobijeno {new_price}")
                all_tests_passed = False
            
            # Verify metadata contains original price
            if metadata and 'original_price' in metadata:
                if metadata['original_price'] == original_price:
                    print(f"   ✅ Originalna cena sačuvana u metadata: {metadata['original_price']}")
                else:
                    print(f"   ❌ FAILED: Pogrešna originalna cena u metadata")
                    all_tests_passed = False
            else:
                print(f"   ❌ FAILED: Metadata ne sadrži original_price")
                all_tests_passed = False
            
            activated_services.append({
                'service_id': service_id,
                'service_name': service_name,
                'original_price': original_price,
                'new_price': new_price,
                'discount_percentage': discount_percentage
            })
            
        except Exception as e:
            print(f"   ❌ ERROR aktiviranja popusta: {e}")
            all_tests_passed = False
    
    # Step 3: Create test reservations and verify snapshot
    if activated_services:
        print("\n3. Kreiranje test rezervacija i provera snapshot-a...")
        print("-" * 60)
        
        # Get first available therapist
        try:
            response = requests.get(f"{BACKEND_URL}/therapists")
            response.raise_for_status()
            therapists = response.json()
            
            if not therapists:
                print("   ❌ ERROR: Nema dostupnih terapeuta")
                return False
            
            therapist_id = therapists[0]['id']
            print(f"   ✅ Koristi terapeuta: {therapists[0]['name']} (ID: {therapist_id})")
            
        except Exception as e:
            print(f"   ❌ ERROR dobijanja terapeuta: {e}")
            return False
        
        # Create appointments for each activated service
        for i, service_info in enumerate(activated_services, 1):
            print(f"\n   Rezervacija {i}: {service_info['service_name']}")
            
            try:
                # Create appointment
                start_time = datetime.now() + timedelta(days=i)  # Different days to avoid conflicts
                appointment_data = {
                    "client_first_name": "Marija",
                    "client_last_name": "Petrović",
                    "client_phone": "+381601234567",
                    "client_email": "marija.petrovic@example.com",
                    "therapist_id": therapist_id,
                    "service_id": service_info['service_id'],
                    "start_time": start_time.isoformat(),
                    "status": "scheduled"
                }
                
                response = requests.post(
                    f"{BACKEND_URL}/appointments",
                    json=appointment_data,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"   POST /appointments Response: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"   ❌ FAILED: Kreiranje rezervacije neuspešno - Status {response.status_code}")
                    print(f"   Response: {response.text}")
                    all_tests_passed = False
                    continue
                
                appointment = response.json()
                appointment_id = appointment.get('id')
                
                print(f"   ✅ Rezervacija kreirana: {appointment_id}")
                
                # Get appointment details to verify snapshot
                response = requests.get(f"{BACKEND_URL}/appointments/{appointment_id}")
                if response.status_code == 200:
                    appointment_details = response.json()
                    
                    snapshot_price = appointment_details.get('snapshot_price')
                    snapshot_original_price = appointment_details.get('snapshot_original_price')
                    snapshot_discount_percentage = appointment_details.get('snapshot_discount_percentage')
                    
                    print(f"   Snapshot price: {snapshot_price}")
                    print(f"   Snapshot original price: {snapshot_original_price}")
                    print(f"   Snapshot discount: {snapshot_discount_percentage}%")
                    
                    # Verify snapshot values
                    if snapshot_discount_percentage == 5:
                        print(f"   ✅ Snapshot discount percentage = 5%")
                    else:
                        print(f"   ❌ FAILED: Pogrešan snapshot discount - očekivano 5%, dobijeno {snapshot_discount_percentage}%")
                        all_tests_passed = False
                    
                    if abs(snapshot_price - service_info['new_price']) < 0.01:
                        print(f"   ✅ Snapshot price odgovara sniženoj ceni")
                    else:
                        print(f"   ❌ FAILED: Pogrešan snapshot price")
                        all_tests_passed = False
                    
                    if abs(snapshot_original_price - service_info['original_price']) < 0.01:
                        print(f"   ✅ Snapshot original price odgovara originalnoj ceni")
                    else:
                        print(f"   ❌ FAILED: Pogrešan snapshot original price")
                        all_tests_passed = False
                
            except Exception as e:
                print(f"   ❌ ERROR kreiranja rezervacije: {e}")
                all_tests_passed = False
    
    print("\n" + "=" * 80)
    if all_tests_passed:
        print("🎉 TEST 1 PROŠAO: Masaža stopala popusti rade ispravno!")
        print(f"✅ Aktiviran 5% popust na {len(activated_services)} usluga")
        print("✅ Cene ispravno snižene")
        print("✅ Metadata čuva originalne cene")
        print("✅ Rezervacije snapshot-uju ispravne vrednosti")
    else:
        print("❌ TEST 1 NEUSPEŠAN: Problemi sa popustima na Masaža stopala")
    
    print("=" * 80)
    return all_tests_passed

def test_discount_masaza_toplim_uljem_90min():
    """Test 2: Popusti na "Masaža toplim uljem 90 min" (trenutno 0%)"""
    
    print("=" * 80)
    print("TEST 2: MASAŽA TOPLIM ULJEM 90 MIN - AKTIVIRANJE 10% POPUSTA")
    print("=" * 80)
    
    all_tests_passed = True
    
    # Step 1: Find "Masaža toplim uljem" 90 min service
    print("\n1. Pronalaženje 'Masaža toplim uljem - 90 min' usluge...")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/services")
        response.raise_for_status()
        services = response.json()
        
        # Find "Masaža toplim uljem" 90 min service
        target_service = None
        for service in services:
            name = service.get('name', '')
            duration = service.get('duration', 0)
            if "Masaža toplim uljem" in name and duration == 90:
                target_service = service
                break
        
        if not target_service:
            print("   ❌ FAILED: Nije pronađena 'Masaža toplim uljem - 90 min' usluga")
            return False
        
        print(f"   ✅ Pronađena usluga: {target_service['name']}")
        print(f"   Duration: {target_service['duration']} min")
        print(f"   Cena: {target_service['price']} RSD")
        print(f"   Trenutni popust: {target_service['discount_percentage']}%")
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    
    # Step 2: Activate 10% discount
    print("\n2. Aktiviranje 10% popusta...")
    print("-" * 60)
    
    service_id = target_service['id']
    original_price = target_service['price']
    
    try:
        response = requests.patch(f"{BACKEND_URL}/services/{service_id}/discount?discount=10")
        
        print(f"   PATCH /services/{service_id}/discount?discount=10 Response: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ FAILED: Aktiviranje popusta neuspešno - Status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        updated_service = response.json()
        new_price = updated_service.get('price', 0)
        discount_percentage = updated_service.get('discount_percentage', 0)
        
        print(f"   ✅ Popust aktiviran uspešno")
        print(f"   Nova cena: {new_price} RSD")
        print(f"   Popust: {discount_percentage}%")
        
        # Verify discount calculation
        expected_price = original_price * 0.90  # 10% discount
        if abs(new_price - expected_price) < 0.01:
            print(f"   ✅ Cena ispravno snižena: {original_price} * 0.90 = {expected_price}")
        else:
            print(f"   ❌ FAILED: Pogrešna cena - očekivano {expected_price}, dobijeno {new_price}")
            all_tests_passed = False
        
    except Exception as e:
        print(f"   ❌ ERROR aktiviranja popusta: {e}")
        return False
    
    # Step 3: Create test reservation
    print("\n3. Kreiranje test rezervacije...")
    print("-" * 60)
    
    try:
        # Get therapist
        response = requests.get(f"{BACKEND_URL}/therapists")
        response.raise_for_status()
        therapists = response.json()
        therapist_id = therapists[0]['id']
        
        # Create appointment
        start_time = datetime.now() + timedelta(days=2)
        appointment_data = {
            "client_first_name": "Stefan",
            "client_last_name": "Nikolić",
            "client_phone": "+381602345678",
            "client_email": "stefan.nikolic@example.com",
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
            print(f"   ❌ FAILED: Kreiranje rezervacije neuspešno")
            return False
        
        appointment = response.json()
        appointment_id = appointment.get('id')
        print(f"   ✅ Rezervacija kreirana: {appointment_id}")
        
        # Verify snapshot data
        response = requests.get(f"{BACKEND_URL}/appointments/{appointment_id}")
        if response.status_code == 200:
            appointment_details = response.json()
            
            snapshot_discount = appointment_details.get('snapshot_discount_percentage')
            snapshot_price = appointment_details.get('snapshot_price')
            
            if snapshot_discount == 10:
                print(f"   ✅ Snapshot discount = 10%")
            else:
                print(f"   ❌ FAILED: Pogrešan snapshot discount - očekivano 10%, dobijeno {snapshot_discount}%")
                all_tests_passed = False
            
            if abs(snapshot_price - new_price) < 0.01:
                print(f"   ✅ Snapshot price = {snapshot_price} RSD (snižena cena)")
            else:
                print(f"   ❌ FAILED: Pogrešan snapshot price")
                all_tests_passed = False
        
    except Exception as e:
        print(f"   ❌ ERROR kreiranja rezervacije: {e}")
        all_tests_passed = False
    
    print("\n" + "=" * 80)
    if all_tests_passed:
        print("🎉 TEST 2 PROŠAO: Masaža toplim uljem 90 min popust radi ispravno!")
        print("✅ Aktiviran 10% popust")
        print("✅ Cena ispravno snižena")
        print("✅ Rezervacija snapshot-uje ispravne vrednosti")
    else:
        print("❌ TEST 2 NEUSPEŠAN: Problemi sa popustom na Masaža toplim uljem 90 min")
    
    print("=" * 80)
    return all_tests_passed

def test_different_discount_percentages():
    """Test 5: Različiti popusti (5%, 10%, 15%) na jednoj usluzi"""
    
    print("=" * 80)
    print("TEST 3: RAZLIČITI POPUSTI NA JEDNOJ USLUZI")
    print("=" * 80)
    
    all_tests_passed = True
    
    # Step 1: Find a service to test different discounts
    print("\n1. Pronalaženje usluge za testiranje različitih popusta...")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/services")
        response.raise_for_status()
        services = response.json()
        
        # Find a service with existing discount or any regular service
        test_service = None
        for service in services:
            name = service.get('name', '')
            if "Glava, vrat, ramena i leđa" in name and "30 min" in name:
                test_service = service
                break
        
        if not test_service:
            # Fallback to any regular service
            regular_services = [s for s in services if s.get('category', 'regular') == 'regular']
            if regular_services:
                test_service = regular_services[0]
        
        if not test_service:
            print("   ❌ FAILED: Nije pronađena usluga za testiranje")
            return False
        
        print(f"   ✅ Odabrana usluga: {test_service['name']}")
        print(f"   Trenutna cena: {test_service['price']} RSD")
        print(f"   Trenutni popust: {test_service['discount_percentage']}%")
        
        service_id = test_service['id']
        
        # Get original price from metadata if available
        metadata = test_service.get('metadata', {})
        if metadata and 'original_price' in metadata:
            original_price = metadata['original_price']
        else:
            original_price = test_service['price']
        
        print(f"   Originalna cena: {original_price} RSD")
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    
    # Step 2: Test different discount percentages
    discount_tests = [
        {"percentage": 10, "description": "10% popust"},
        {"percentage": 15, "description": "15% popust"},
        {"percentage": 5, "description": "5% popust"},
        {"percentage": 0, "description": "Uklanjanje popusta"}
    ]
    
    for i, discount_test in enumerate(discount_tests, 1):
        print(f"\n{i}. Testiranje {discount_test['description']}...")
        print("-" * 40)
        
        discount_percentage = discount_test['percentage']
        
        try:
            response = requests.patch(f"{BACKEND_URL}/services/{service_id}/discount?discount={discount_percentage}")
            
            print(f"   PATCH /services/{service_id}/discount?discount={discount_percentage} Response: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   ❌ FAILED: Postavljanje {discount_percentage}% popusta neuspešno")
                print(f"   Response: {response.text}")
                all_tests_passed = False
                continue
            
            updated_service = response.json()
            new_price = updated_service.get('price', 0)
            new_discount = updated_service.get('discount_percentage', 0)
            
            print(f"   ✅ Popust postavljen na {new_discount}%")
            print(f"   Nova cena: {new_price} RSD")
            
            # Verify calculation
            if discount_percentage == 0:
                expected_price = original_price
            else:
                expected_price = original_price * (1 - discount_percentage / 100)
            
            if abs(new_price - expected_price) < 0.01:
                print(f"   ✅ Cena ispravno izračunata: {original_price} * {1 - discount_percentage/100} = {expected_price}")
            else:
                print(f"   ❌ FAILED: Pogrešna cena - očekivano {expected_price}, dobijeno {new_price}")
                all_tests_passed = False
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            all_tests_passed = False
    
    print("\n" + "=" * 80)
    if all_tests_passed:
        print("🎉 TEST 3 PROŠAO: Različiti popusti rade ispravno!")
        print("✅ Svi procenti popusta (5%, 10%, 15%, 0%) rade")
        print("✅ Cene se ispravno izračunavaju")
    else:
        print("❌ TEST 3 NEUSPEŠAN: Problemi sa različitim popustima")
    
    print("=" * 80)
    return all_tests_passed

def test_couple_appointment_discounts():
    """Test 4: Couple appointment discounts"""
    
    print("=" * 80)
    print("TEST 4: COUPLE APPOINTMENT POPUSTI")
    print("=" * 80)
    
    all_tests_passed = True
    
    # Step 1: Create couple appointment with discount
    print("\n1. Kreiranje couple rezervacije sa popustom...")
    print("-" * 60)
    
    try:
        # Get services for couple appointment
        response = requests.get(f"{BACKEND_URL}/services")
        response.raise_for_status()
        all_services = response.json()
        
        # Find regular services to use in couple appointments
        regular_services = [s for s in all_services if s.get('category', 'regular') in ['regular', 'Obicne masaze']]
        
        if len(regular_services) < 2:
            print("   ❌ FAILED: Potrebno je minimum 2 regularne usluge za couple rezervaciju")
            return False
        
        service1_id = regular_services[0]['id']
        service2_id = regular_services[1]['id']
        
        print(f"   ✅ Koristi usluge: {regular_services[0]['name']} i {regular_services[1]['name']}")
        
        # Create couple appointment with 15% discount
        start_time = datetime.now() + timedelta(days=5)
        couple_data = {
            "client_first_name": "Aleksandar",
            "client_last_name": "Mitrović",
            "client_phone": "+381604567890",
            "client_email": "aleksandar.mitrovic@example.com",
            "start_time": start_time.isoformat(),
            "duration_type": 60,
            "person1_services": [service1_id],
            "person2_services": [service2_id],
            "discount_couples_massage": 15.0
        }
        
        response = requests.post(
            f"{BACKEND_URL}/book-couple-appointment",
            json=couple_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   POST /book-couple-appointment Response: {response.status_code}")
        
        if response.status_code == 200:
            appointment = response.json()
            appointment_id = appointment.get('id')
            print(f"   ✅ Couple rezervacija kreirana: {appointment_id}")
            
            # Verify snapshot discount
            response = requests.get(f"{BACKEND_URL}/appointments/{appointment_id}")
            if response.status_code == 200:
                appointment_details = response.json()
                snapshot_discount = appointment_details.get('snapshot_discount_percentage')
                
                if snapshot_discount == 15:
                    print(f"   ✅ Snapshot discount = 15%")
                else:
                    print(f"   ❌ FAILED: Pogrešan snapshot discount - očekivano 15%, dobijeno {snapshot_discount}%")
                    all_tests_passed = False
        else:
            print(f"   ❌ FAILED: Kreiranje couple rezervacije neuspešno - Status {response.status_code}")
            print(f"   Response: {response.text}")
            all_tests_passed = False
        
    except Exception as e:
        print(f"   ❌ ERROR kreiranja couple rezervacija: {e}")
        all_tests_passed = False
    
    print("\n" + "=" * 80)
    if all_tests_passed:
        print("🎉 TEST 4 PROŠAO: Couple appointment popusti rade ispravno!")
        print("✅ Couple rezervacije sa 15% popustom uspešno kreirane")
        print("✅ Snapshot discount = 15%")
    else:
        print("❌ TEST 4 NEUSPEŠAN: Problemi sa couple appointment popustima")
    
    print("=" * 80)
    return all_tests_passed

if __name__ == "__main__":
    print("🎯 KRITIČNI TEST: Kompletna Provera Popusta na SVIM Uslugama")
    print("=" * 100)
    print("Testiranje svih identifikovanih problema sa popustima...")
    print("=" * 100)
    
    # Run all tests
    test_results = []
    
    print("\n")
    test_results.append(("Test 1: Masaža stopala", test_discount_activation_masaza_stopala()))
    
    print("\n")
    test_results.append(("Test 2: Masaža toplim uljem 90 min", test_discount_masaza_toplim_uljem_90min()))
    
    print("\n")
    test_results.append(("Test 3: Različiti popusti", test_different_discount_percentages()))
    
    print("\n")
    test_results.append(("Test 4: Couple appointment popusti", test_couple_appointment_discounts()))
    
    # Final results
    print("\n" + "=" * 100)
    print("🎯 FINALNI REZULTATI KRITIČNOG TESTA")
    print("=" * 100)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        if result:
            print(f"✅ {test_name}: PROŠAO")
            passed_tests += 1
        else:
            print(f"❌ {test_name}: NEUSPEŠAN")
    
    print("=" * 100)
    print(f"UKUPNO: {passed_tests}/{total_tests} testova prošlo")
    
    if passed_tests == total_tests:
        print("🎉 SVI TESTOVI PROŠLI! Popusti rade ispravno na svim uslugama!")
        print("✅ Endpoint /api/services/{service_id}/discount radi")
        print("✅ Cene se menjaju u bazi nakon aktiviranja popusta")
        print("✅ metadata.original_price se čuva")
        print("✅ Nove rezervacije snapshot-uju ispravne vrednosti")
    else:
        print("❌ NEKI TESTOVI NISU PROŠLI! Potrebne su dodatne ispravke.")
        print("Molimo proverite neuspešne testove i ispravite probleme.")
    
    print("=" * 100)
    
    # Exit with appropriate code
    sys.exit(0 if passed_tests == total_tests else 1)
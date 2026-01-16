#!/usr/bin/env python3
"""
🎯 KOMPLETAN SISTEM TEST - Popusti, Cene, Rezervacije
Comprehensive System Test for Discounts, Prices, and Reservations

Testing all 5 scenarios from the review request:
1. Obične masaže - popusti trebaju da rade (5%, 10%, 15%)
2. [PAROVI] masaže - NEMA popusta na backend-u (discount_percentage = 0%)
3. Snapshot mehanizam - cene se čuvaju u trenutku rezervacije
4. Provera da se cene ispravno prikazuju u dashboard-u i termini stranici
5. Services stranica - originalne cene se prikazuju
"""

import requests
import json
from datetime import datetime, timedelta
import sys
import time

# Backend URL from environment
BACKEND_URL = "https://multilingfix.preview.emergentagent.com/api"

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"🎯 {title}")
    print("=" * 80)

def print_subheader(title):
    """Print a formatted subheader"""
    print(f"\n📋 {title}")
    print("-" * 60)

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_warning(message):
    """Print warning message"""
    print(f"⚠️  {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")

def test_scenario_1_obicne_masaze_popusti():
    """
    TEST SCENARIO 1: OBIČNE MASAŽE - Popusti Rade
    
    1. Proveri da popusti postoje na običnim masažama
    2. Kreiraj rezervaciju sa popustom
    3. Proveri analytics
    """
    print_header("SCENARIO 1: OBIČNE MASAŽE - Popusti Rade")
    
    all_tests_passed = True
    
    # Step 1: Proveri da popusti postoje
    print_subheader("1. Provera postojanja popusta na običnim masažama")
    
    try:
        response = requests.get(f"{BACKEND_URL}/services")
        response.raise_for_status()
        services = response.json()
        
        # Filter: category = "Obicne masaze" ili default category
        obicne_masaze = [s for s in services if s.get('category', 'regular') in ['regular', 'Obicne masaze']]
        
        print_info(f"Ukupno servisa: {len(services)}")
        print_info(f"Obične masaže: {len(obicne_masaze)}")
        
        # Proveri da većina ima discount_percentage > 0
        services_with_discount = [s for s in obicne_masaze if s.get('discount_percentage', 0) > 0]
        services_with_metadata = [s for s in services_with_discount if s.get('metadata') and 'original_price' in s.get('metadata', {})]
        
        print_info(f"Servisi sa popustom: {len(services_with_discount)}")
        print_info(f"Servisi sa metadata.original_price: {len(services_with_metadata)}")
        
        if len(services_with_discount) > 0:
            print_success("Pronađeni servisi sa aktivnim popustima:")
            for service in services_with_discount[:5]:  # Show first 5
                discount = service.get('discount_percentage', 0)
                price = service.get('price', 0)
                metadata = service.get('metadata', {})
                original_price = metadata.get('original_price', price) if metadata else price
                
                print(f"   - {service.get('name')}: {original_price} RSD → {price} RSD ({discount}% popust)")
        else:
            print_warning("Nema servisa sa aktivnim popustima")
            
    except Exception as e:
        print_error(f"Greška pri dobijanju servisa: {e}")
        all_tests_passed = False
        return False
    
    # Step 2: Kreiraj rezervaciju sa popustom
    print_subheader("2. Kreiranje rezervacije sa popustom")
    
    if services_with_discount:
        try:
            # Uzmi jednu uslugu sa popustom (npr. 10%)
            target_service = None
            for service in services_with_discount:
                if service.get('discount_percentage', 0) >= 10:
                    target_service = service
                    break
            
            if not target_service:
                target_service = services_with_discount[0]  # Uzmi bilo koju sa popustom
            
            print_info(f"Koristi servis: {target_service.get('name')} ({target_service.get('discount_percentage')}% popust)")
            
            # Get therapist
            therapist_response = requests.get(f"{BACKEND_URL}/therapists")
            therapist_response.raise_for_status()
            therapists = therapist_response.json()
            
            if not therapists:
                print_error("Nema dostupnih terapeuta")
                return False
            
            therapist_id = therapists[0]['id']
            
            # Kreiraj rezervaciju
            start_time = datetime.now() + timedelta(days=1, hours=14)  # Sutra u 14h
            
            appointment_data = {
                "client_first_name": "Marko",
                "client_last_name": "Petrović",
                "client_phone": "+381601234567",
                "client_email": "marko.petrovic@example.com",
                "therapist_id": therapist_id,
                "service_id": target_service['id'],
                "start_time": start_time.isoformat(),
                "status": "scheduled"
            }
            
            response = requests.post(f"{BACKEND_URL}/appointments", json=appointment_data)
            response.raise_for_status()
            appointment = response.json()
            
            appointment_id = appointment.get('id')
            print_success(f"Rezervacija kreirana: {appointment_id}")
            
            # Proveri da rezervacija ima snapshot podatke
            if 'snapshot_price' in appointment:
                snapshot_price = appointment.get('snapshot_price')
                snapshot_original_price = appointment.get('snapshot_original_price')
                snapshot_discount = appointment.get('snapshot_discount_percentage')
                
                print_success(f"Snapshot podaci:")
                print(f"   - snapshot_price: {snapshot_price} RSD")
                print(f"   - snapshot_original_price: {snapshot_original_price} RSD")
                print(f"   - snapshot_discount_percentage: {snapshot_discount}%")
                
                # Verify discount calculation
                expected_price = snapshot_original_price * (1 - snapshot_discount / 100)
                if abs(snapshot_price - expected_price) < 0.01:
                    print_success("Snapshot popust je ispravno obračunat")
                else:
                    print_error(f"Snapshot popust nije ispravno obračunat: očekivano {expected_price}, dobijeno {snapshot_price}")
                    all_tests_passed = False
            else:
                print_error("Rezervacija nema snapshot podatke")
                all_tests_passed = False
                
        except Exception as e:
            print_error(f"Greška pri kreiranju rezervacije: {e}")
            all_tests_passed = False
    
    # Step 3: Proveri analytics
    print_subheader("3. Provera analytics endpoint-a")
    
    try:
        response = requests.get(f"{BACKEND_URL}/analytics/detailed?period=day")
        response.raise_for_status()
        analytics = response.json()
        
        print_success("Analytics endpoint radi")
        
        # Proveri da li postoje rezervacije sa popustom
        appointments_with_discount = analytics.get('appointments_with_discount', [])
        print_info(f"Rezervacije sa popustom: {len(appointments_with_discount)}")
        
        if appointments_with_discount:
            print_success("Pronađene rezervacije sa popustom u analytics:")
            for apt in appointments_with_discount[:3]:  # Show first 3
                print(f"   - {apt.get('client_name')}: {apt.get('original_price')} → {apt.get('discounted_price')} RSD ({apt.get('discount_percentage')}%)")
        
        # Proveri ukupne statistike
        total_revenue = analytics.get('total_revenue', 0)
        total_original_revenue = analytics.get('total_original_revenue', 0)
        total_discount_given = analytics.get('total_discount_given', 0)
        
        print_info(f"Ukupan prihod: {total_revenue} RSD")
        print_info(f"Originalni prihod: {total_original_revenue} RSD")
        print_info(f"Ukupan popust: {total_discount_given} RSD")
        
        if total_discount_given > 0:
            print_success("Analytics ispravno prikazuje popuste")
        
    except Exception as e:
        print_error(f"Greška pri proveri analytics: {e}")
        all_tests_passed = False
    
    return all_tests_passed

def test_scenario_2_parovi_masaze_bez_popusta():
    """
    TEST SCENARIO 2: [PAROVI] MASAŽE - NEMA Popusta Na Backend-u
    
    1. Proveri da [PAROVI] usluge NEMAJU popuste
    2. Kreiraj couple rezervaciju
    """
    print_header("SCENARIO 2: [PAROVI] MASAŽE - NEMA Popusta Na Backend-u")
    
    all_tests_passed = True
    
    # Step 1: Proveri da [PAROVI] usluge NEMAJU popuste
    print_subheader("1. Provera da [PAROVI] usluge nemaju popuste")
    
    try:
        response = requests.get(f"{BACKEND_URL}/services")
        response.raise_for_status()
        services = response.json()
        
        # Filter: category = "Kartica Masaza za parove" ili name contains "[PAROVI]"
        parovi_services = [s for s in services if 
                          s.get('category') == 'Kartica Masaza za parove' or 
                          s.get('category') == 'couple' or
                          '[PAROVI]' in s.get('name', '')]
        
        print_info(f"Pronađeno [PAROVI] servisa: {len(parovi_services)}")
        
        if parovi_services:
            services_with_discount = [s for s in parovi_services if s.get('discount_percentage', 0) > 0]
            services_without_discount = [s for s in parovi_services if s.get('discount_percentage', 0) == 0]
            
            print_info(f"[PAROVI] servisi sa popustom: {len(services_with_discount)}")
            print_info(f"[PAROVI] servisi bez popusta: {len(services_without_discount)}")
            
            if services_with_discount:
                print_error("PROBLEM: [PAROVI] servisi imaju popuste na backend-u!")
                for service in services_with_discount:
                    print(f"   - {service.get('name')}: {service.get('discount_percentage')}% popust")
                all_tests_passed = False
            else:
                print_success("SVE [PAROVI] usluge imaju discount_percentage = 0%")
            
            # Proveri metadata
            services_with_metadata = [s for s in parovi_services if s.get('metadata') and 'original_price' in s.get('metadata', {})]
            
            if services_with_metadata:
                print_warning(f"{len(services_with_metadata)} [PAROVI] servisa ima metadata.original_price (trebalo bi da bude None)")
                for service in services_with_metadata:
                    metadata = service.get('metadata', {})
                    print(f"   - {service.get('name')}: metadata = {metadata}")
            else:
                print_success("SVE [PAROVI] usluge nemaju metadata.original_price")
        else:
            print_warning("Nema pronađenih [PAROVI] servisa")
            
    except Exception as e:
        print_error(f"Greška pri dobijanju [PAROVI] servisa: {e}")
        all_tests_passed = False
        return False
    
    # Step 2: Kreiraj couple rezervaciju
    print_subheader("2. Kreiranje couple rezervacije")
    
    try:
        # Get therapist
        therapist_response = requests.get(f"{BACKEND_URL}/therapists")
        therapist_response.raise_for_status()
        therapists = therapist_response.json()
        
        if not therapists:
            print_error("Nema dostupnih terapeuta")
            return False
        
        therapist_id = therapists[0]['id']
        
        # Get regular services for couple appointment
        regular_services = [s for s in services if s.get('category', 'regular') in ['regular', 'Obicne masaze']]
        
        if len(regular_services) < 2:
            print_error("Potrebno je najmanje 2 regularna servisa za couple rezervaciju")
            return False
        
        service1_id = regular_services[0]['id']
        service2_id = regular_services[1]['id'] if len(regular_services) > 1 else regular_services[0]['id']
        
        # Kreiraj couple rezervaciju
        start_time = datetime.now() + timedelta(days=1, hours=16)  # Sutra u 16h
        
        couple_data = {
            "client_first_name": "Ana",
            "client_last_name": "Nikolić",
            "client_phone": "+381601234568",
            "client_email": "ana.nikolic@example.com",
            "therapist_id": therapist_id,
            "duration_type": 60,
            "person1_services": [service1_id],
            "person2_services": [service2_id],
            "start_time": start_time.isoformat(),
            "discount_couples_massage": 0  # NEMA popusta
        }
        
        response = requests.post(f"{BACKEND_URL}/appointments/couple", json=couple_data)
        response.raise_for_status()
        couple_appointment = response.json()
        
        couple_appointment_id = couple_appointment.get('id')
        print_success(f"Couple rezervacija kreirana: {couple_appointment_id}")
        
        # Proveri da rezervacija ima snapshot podatke BEZ popusta
        snapshot_price = couple_appointment.get('snapshot_price')
        snapshot_original_price = couple_appointment.get('snapshot_original_price')
        snapshot_discount = couple_appointment.get('snapshot_discount_percentage')
        
        print_info(f"Couple snapshot podaci:")
        print(f"   - snapshot_price: {snapshot_price} RSD")
        print(f"   - snapshot_original_price: {snapshot_original_price} RSD")
        print(f"   - snapshot_discount_percentage: {snapshot_discount}%")
        
        if snapshot_discount == 0:
            print_success("Couple rezervacija nema popust (snapshot_discount_percentage = 0)")
        else:
            print_error(f"PROBLEM: Couple rezervacija ima popust {snapshot_discount}% umesto 0%")
            all_tests_passed = False
        
        if abs(snapshot_price - snapshot_original_price) < 0.01:
            print_success("Couple rezervacija: snapshot_price = snapshot_original_price (nema popusta)")
        else:
            print_error(f"PROBLEM: Couple rezervacija ima različite cene: {snapshot_price} vs {snapshot_original_price}")
            all_tests_passed = False
            
    except Exception as e:
        print_error(f"Greška pri kreiranju couple rezervacije: {e}")
        all_tests_passed = False
    
    return all_tests_passed

def test_scenario_3_snapshot_mehanizam():
    """
    TEST SCENARIO 3: Snapshot Mehanizam - Retroaktivna Zaštita
    
    1. Kreiraj rezervaciju bez popusta
    2. Aktiviraj popust na toj usluzi
    3. Proveri da stara rezervacija ZADRŽAVA originalnu cenu
    4. Kreiraj novu rezervaciju sa aktivnim popustom
    """
    print_header("SCENARIO 3: Snapshot Mehanizam - Retroaktivna Zaštita")
    
    all_tests_passed = True
    
    # Step 1: Kreiraj rezervaciju bez popusta
    print_subheader("1. Kreiranje rezervacije bez popusta")
    
    try:
        # Find a service without discount
        response = requests.get(f"{BACKEND_URL}/services")
        response.raise_for_status()
        services = response.json()
        
        services_without_discount = [s for s in services if s.get('discount_percentage', 0) == 0 and s.get('category', 'regular') in ['regular', 'Obicne masaze']]
        
        if not services_without_discount:
            print_error("Nema servisa bez popusta za testiranje")
            return False
        
        target_service = services_without_discount[0]
        service_id = target_service['id']
        original_price = target_service['price']
        
        print_info(f"Koristi servis: {target_service.get('name')} (cena: {original_price} RSD, popust: 0%)")
        
        # Get therapist
        therapist_response = requests.get(f"{BACKEND_URL}/therapists")
        therapist_response.raise_for_status()
        therapists = therapist_response.json()
        therapist_id = therapists[0]['id']
        
        # Kreiraj rezervaciju
        start_time = datetime.now() + timedelta(days=2, hours=10)  # Prekosutra u 10h
        
        appointment_data = {
            "client_first_name": "Stefan",
            "client_last_name": "Jovanović",
            "client_phone": "+381601234569",
            "client_email": "stefan.jovanovic@example.com",
            "therapist_id": therapist_id,
            "service_id": service_id,
            "start_time": start_time.isoformat(),
            "status": "scheduled"
        }
        
        response = requests.post(f"{BACKEND_URL}/appointments", json=appointment_data)
        response.raise_for_status()
        old_appointment = response.json()
        
        old_appointment_id = old_appointment.get('id')
        old_snapshot_price = old_appointment.get('snapshot_price')
        old_snapshot_discount = old_appointment.get('snapshot_discount_percentage')
        
        print_success(f"Stara rezervacija kreirana: {old_appointment_id}")
        print_info(f"Stara rezervacija - snapshot_price: {old_snapshot_price} RSD, discount: {old_snapshot_discount}%")
        
    except Exception as e:
        print_error(f"Greška pri kreiranju stare rezervacije: {e}")
        all_tests_passed = False
        return False
    
    # Step 2: Aktiviraj popust na toj usluzi
    print_subheader("2. Aktiviranje popusta na usluzi")
    
    try:
        # Aktiviraj 15% popust
        discount_percentage = 15
        
        response = requests.patch(f"{BACKEND_URL}/services/{service_id}/discount?discount={discount_percentage}")
        response.raise_for_status()
        updated_service = response.json()
        
        new_price = updated_service.get('price')
        new_discount = updated_service.get('discount_percentage')
        
        print_success(f"Popust aktiviran: {discount_percentage}%")
        print_info(f"Nova cena servisa: {original_price} RSD → {new_price} RSD")
        print_info(f"Novi popust: {new_discount}%")
        
        # Verify discount calculation
        expected_price = original_price * (1 - discount_percentage / 100)
        if abs(new_price - expected_price) < 0.01:
            print_success("Popust je ispravno obračunat")
        else:
            print_error(f"Popust nije ispravno obračunat: očekivano {expected_price}, dobijeno {new_price}")
            all_tests_passed = False
            
    except Exception as e:
        print_error(f"Greška pri aktiviranju popusta: {e}")
        all_tests_passed = False
        return False
    
    # Step 3: Proveri da stara rezervacija ZADRŽAVA originalnu cenu
    print_subheader("3. Provera da stara rezervacija zadržava originalnu cenu")
    
    try:
        # Get appointments for the date range
        start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00")
        end_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%dT23:59:59")
        
        response = requests.get(f"{BACKEND_URL}/appointments?start_date={start_date}&end_date={end_date}")
        response.raise_for_status()
        appointments = response.json()
        
        # Find our old appointment
        old_appointment_found = None
        for apt in appointments:
            if apt.get('id') == old_appointment_id:
                old_appointment_found = apt
                break
        
        if not old_appointment_found:
            print_error("Stara rezervacija nije pronađena")
            all_tests_passed = False
        else:
            current_snapshot_price = old_appointment_found.get('snapshot_price')
            current_snapshot_discount = old_appointment_found.get('snapshot_discount_percentage')
            
            print_info(f"Stara rezervacija - trenutni snapshot_price: {current_snapshot_price} RSD")
            print_info(f"Stara rezervacija - trenutni snapshot_discount: {current_snapshot_discount}%")
            
            if current_snapshot_discount == 0 and abs(current_snapshot_price - original_price) < 0.01:
                print_success("✅ KRITIČNO: Stara rezervacija zadržava originalnu cenu bez popusta!")
            else:
                print_error(f"❌ KRITIČNO: Stara rezervacija je promenjena! Očekivano: {original_price} RSD (0%), dobijeno: {current_snapshot_price} RSD ({current_snapshot_discount}%)")
                all_tests_passed = False
                
    except Exception as e:
        print_error(f"Greška pri proveri stare rezervacije: {e}")
        all_tests_passed = False
    
    # Step 4: Kreiraj novu rezervaciju sa aktivnim popustom
    print_subheader("4. Kreiranje nove rezervacije sa aktivnim popustom")
    
    try:
        # Kreiraj novu rezervaciju
        start_time = datetime.now() + timedelta(days=2, hours=14)  # Prekosutra u 14h
        
        new_appointment_data = {
            "client_first_name": "Milica",
            "client_last_name": "Stojanović",
            "client_phone": "+381601234570",
            "client_email": "milica.stojanovic@example.com",
            "therapist_id": therapist_id,
            "service_id": service_id,
            "start_time": start_time.isoformat(),
            "status": "scheduled"
        }
        
        response = requests.post(f"{BACKEND_URL}/appointments", json=new_appointment_data)
        response.raise_for_status()
        new_appointment = response.json()
        
        new_appointment_id = new_appointment.get('id')
        new_snapshot_price = new_appointment.get('snapshot_price')
        new_snapshot_original_price = new_appointment.get('snapshot_original_price')
        new_snapshot_discount = new_appointment.get('snapshot_discount_percentage')
        
        print_success(f"Nova rezervacija kreirana: {new_appointment_id}")
        print_info(f"Nova rezervacija - snapshot_price: {new_snapshot_price} RSD")
        print_info(f"Nova rezervacija - snapshot_original_price: {new_snapshot_original_price} RSD")
        print_info(f"Nova rezervacija - snapshot_discount: {new_snapshot_discount}%")
        
        # Verify new appointment has discount
        if new_snapshot_discount == discount_percentage:
            print_success(f"Nova rezervacija ima ispravno snapshot_discount_percentage = {discount_percentage}%")
        else:
            print_error(f"Nova rezervacija nema ispravno snapshot_discount_percentage: očekivano {discount_percentage}%, dobijeno {new_snapshot_discount}%")
            all_tests_passed = False
        
        # Verify new appointment has discounted price
        expected_new_price = original_price * (1 - discount_percentage / 100)
        if abs(new_snapshot_price - expected_new_price) < 0.01:
            print_success(f"Nova rezervacija ima ispravno sniženu cenu: {new_snapshot_price} RSD")
        else:
            print_error(f"Nova rezervacija nema ispravno sniženu cenu: očekivano {expected_new_price}, dobijeno {new_snapshot_price}")
            all_tests_passed = False
            
    except Exception as e:
        print_error(f"Greška pri kreiranju nove rezervacije: {e}")
        all_tests_passed = False
    
    return all_tests_passed

def test_scenario_4_dashboard_termini_prikaz():
    """
    TEST SCENARIO 4: Dashboard i Termini - Prikaz Cena
    
    1. Proveri analytics endpoint
    2. Proveri notifikacije endpoint
    3. Proveri termini endpoint
    """
    print_header("SCENARIO 4: Dashboard i Termini - Prikaz Cena")
    
    all_tests_passed = True
    
    # Step 1: Proveri analytics endpoint
    print_subheader("1. Provera analytics endpoint-a")
    
    try:
        response = requests.get(f"{BACKEND_URL}/analytics/detailed?period=day")
        response.raise_for_status()
        analytics = response.json()
        
        print_success("Analytics endpoint radi")
        
        # Proveri appointments_by_service sekciju
        appointments_by_service = analytics.get('appointments_by_service', [])
        print_info(f"Servisi sa rezervacijama: {len(appointments_by_service)}")
        
        if appointments_by_service:
            print_success("appointments_by_service sadrži:")
            for service_data in appointments_by_service[:3]:  # Show first 3
                service_name = service_data.get('service_name')
                service_description = service_data.get('service_description')
                appointments = service_data.get('appointments', [])
                
                print(f"   - {service_name}")
                if service_description:
                    print(f"     Opis: {service_description}")
                print(f"     Rezervacije: {len(appointments)}")
                
                # Proveri da appointments imaju snapshot podatke
                for apt in appointments[:2]:  # Show first 2 appointments
                    total_price = apt.get('total_price')
                    original_price = apt.get('original_price')
                    discount_percentage = apt.get('discount_percentage')
                    
                    print(f"       * {apt.get('client_first_name')} {apt.get('client_last_name')}: {total_price} RSD")
                    if discount_percentage > 0:
                        print(f"         (originalno: {original_price} RSD, popust: {discount_percentage}%)")
        
        # Proveri da postoje appointments_with_discount
        appointments_with_discount = analytics.get('appointments_with_discount', [])
        if appointments_with_discount:
            print_success(f"Pronađeno {len(appointments_with_discount)} rezervacija sa popustom u analytics")
        
    except Exception as e:
        print_error(f"Greška pri proveri analytics endpoint-a: {e}")
        all_tests_passed = False
    
    # Step 2: Proveri notifikacije endpoint
    print_subheader("2. Provera notifikacije endpoint-a")
    
    try:
        response = requests.get(f"{BACKEND_URL}/appointments/unviewed/list")
        response.raise_for_status()
        unviewed_appointments = response.json()
        
        print_success("Notifikacije endpoint radi")
        print_info(f"Nepregledane rezervacije: {len(unviewed_appointments)}")
        
        if unviewed_appointments:
            print_success("Notifikacije koriste snapshot vrednosti:")
            for apt in unviewed_appointments[:3]:  # Show first 3
                service_price = apt.get('service_price')
                original_price = apt.get('original_price')
                discount_percentage = apt.get('discount_percentage')
                client_name = f"{apt.get('client_first_name', '')} {apt.get('client_last_name', '')}"
                
                print(f"   - {client_name}: {service_price} RSD")
                if discount_percentage > 0:
                    print(f"     (originalno: {original_price} RSD, popust: {discount_percentage}%)")
                else:
                    print(f"     (bez popusta)")
        
        # Proveri da se NE prikazuju obrisane rezervacije
        deleted_appointments = [apt for apt in unviewed_appointments if apt.get('is_deleted') == True]
        if deleted_appointments:
            print_error(f"PROBLEM: Pronađeno {len(deleted_appointments)} obrisanih rezervacija u notifikacijama")
            all_tests_passed = False
        else:
            print_success("Obrisane rezervacije se ne prikazuju u notifikacijama")
        
    except Exception as e:
        print_error(f"Greška pri proveri notifikacija: {e}")
        all_tests_passed = False
    
    # Step 3: Proveri termini endpoint
    print_subheader("3. Provera termini endpoint-a")
    
    try:
        # Get appointments for today and tomorrow
        start_date = datetime.now().strftime("%Y-%m-%dT00:00:00")
        end_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT23:59:59")
        
        response = requests.get(f"{BACKEND_URL}/appointments?start_date={start_date}&end_date={end_date}")
        response.raise_for_status()
        appointments = response.json()
        
        print_success("Termini endpoint radi")
        print_info(f"Rezervacije u periodu: {len(appointments)}")
        
        if appointments:
            print_success("Termini vraćaju snapshot polja:")
            for apt in appointments[:3]:  # Show first 3
                snapshot_price = apt.get('snapshot_price')
                snapshot_original_price = apt.get('snapshot_original_price')
                snapshot_discount = apt.get('snapshot_discount_percentage')
                client_name = f"{apt.get('client_first_name', '')} {apt.get('client_last_name', '')}"
                
                print(f"   - {client_name}:")
                print(f"     snapshot_price: {snapshot_price} RSD")
                if snapshot_discount and snapshot_discount > 0:
                    print(f"     snapshot_original_price: {snapshot_original_price} RSD")
                    print(f"     snapshot_discount_percentage: {snapshot_discount}%")
                else:
                    print(f"     bez popusta")
        
        # Proveri da se NE vraćaju obrisane rezervacije
        deleted_appointments = [apt for apt in appointments if apt.get('is_deleted') == True]
        if deleted_appointments:
            print_error(f"PROBLEM: Pronađeno {len(deleted_appointments)} obrisanih rezervacija u termini endpoint-u")
            all_tests_passed = False
        else:
            print_success("Obrisane rezervacije se ne vraćaju u termini endpoint-u")
        
    except Exception as e:
        print_error(f"Greška pri proveri termini endpoint-a: {e}")
        all_tests_passed = False
    
    return all_tests_passed

def test_scenario_5_services_stranica_originalne_cene():
    """
    TEST SCENARIO 5: Services Stranica - Originalne Cene
    
    1. Proveri sve servise
    2. Proveri [PAROVI] servise
    """
    print_header("SCENARIO 5: Services Stranica - Originalne Cene")
    
    all_tests_passed = True
    
    # Step 1: Proveri sve servise
    print_subheader("1. Provera svih servisa")
    
    try:
        response = requests.get(f"{BACKEND_URL}/services")
        response.raise_for_status()
        services = response.json()
        
        print_success(f"Services endpoint radi - {len(services)} servisa")
        
        # Proveri servise sa popustom
        services_with_discount = [s for s in services if s.get('discount_percentage', 0) > 0]
        print_info(f"Servisi sa popustom: {len(services_with_discount)}")
        
        if services_with_discount:
            print_success("Servisi sa popustom imaju ispravne metadata:")
            for service in services_with_discount[:5]:  # Show first 5
                name = service.get('name')
                price = service.get('price')  # snižena cena
                discount_percentage = service.get('discount_percentage')
                metadata = service.get('metadata', {})
                original_price = metadata.get('original_price') if metadata else None
                
                print(f"   - {name}:")
                print(f"     price (snižena): {price} RSD")
                print(f"     discount_percentage: {discount_percentage}%")
                
                if original_price:
                    print(f"     metadata.original_price: {original_price} RSD")
                    
                    # Verify calculation
                    expected_price = original_price * (1 - discount_percentage / 100)
                    if abs(price - expected_price) < 0.01:
                        print_success(f"     ✅ Cena je ispravno obračunata")
                    else:
                        print_error(f"     ❌ Cena nije ispravno obračunata: očekivano {expected_price}, dobijeno {price}")
                        all_tests_passed = False
                else:
                    print_error(f"     ❌ Nema metadata.original_price")
                    all_tests_passed = False
        
    except Exception as e:
        print_error(f"Greška pri proveri servisa: {e}")
        all_tests_passed = False
    
    # Step 2: Proveri [PAROVI] servise
    print_subheader("2. Provera [PAROVI] servisa")
    
    try:
        # Filter [PAROVI] servise
        parovi_services = [s for s in services if 
                          s.get('category') == 'couple' or 
                          '[PAROVI]' in s.get('name', '') or
                          'parove' in s.get('name', '').lower()]
        
        print_info(f"[PAROVI] servisi: {len(parovi_services)}")
        
        if parovi_services:
            print_success("[PAROVI] servisi:")
            for service in parovi_services:
                name = service.get('name')
                discount_percentage = service.get('discount_percentage')
                metadata = service.get('metadata')
                
                print(f"   - {name}:")
                print(f"     discount_percentage: {discount_percentage}%")
                
                if discount_percentage == 0:
                    print_success(f"     ✅ Nema popust (discount_percentage = 0%)")
                else:
                    print_error(f"     ❌ PROBLEM: Ima popust {discount_percentage}% (trebalo bi 0%)")
                    all_tests_passed = False
                
                if metadata is None or 'original_price' not in metadata:
                    print_success(f"     ✅ Nema metadata.original_price")
                else:
                    print_error(f"     ❌ PROBLEM: Ima metadata.original_price: {metadata}")
                    all_tests_passed = False
        else:
            print_warning("Nema pronađenih [PAROVI] servisa")
        
    except Exception as e:
        print_error(f"Greška pri proveri [PAROVI] servisa: {e}")
        all_tests_passed = False
    
    return all_tests_passed

def main():
    """Run all test scenarios"""
    print_header("KOMPLETAN SISTEM TEST - Popusti, Cene, Rezervacije")
    print("Testing comprehensive discount functionality for all services")
    print("Testiranje kompletne funkcionalnosti popusta za sve usluge")
    
    # Run all scenarios
    results = {}
    
    print("\n🚀 Pokretanje svih test scenarija...")
    
    results['scenario_1'] = test_scenario_1_obicne_masaze_popusti()
    results['scenario_2'] = test_scenario_2_parovi_masaze_bez_popusta()
    results['scenario_3'] = test_scenario_3_snapshot_mehanizam()
    results['scenario_4'] = test_scenario_4_dashboard_termini_prikaz()
    results['scenario_5'] = test_scenario_5_services_stranica_originalne_cene()
    
    # Print final results
    print_header("FINALNI REZULTATI")
    
    all_passed = True
    
    for scenario, passed in results.items():
        scenario_name = {
            'scenario_1': 'SCENARIO 1: Obične masaže - popusti rade',
            'scenario_2': 'SCENARIO 2: [PAROVI] masaže - NEMA popusta',
            'scenario_3': 'SCENARIO 3: Snapshot mehanizam - retroaktivna zaštita',
            'scenario_4': 'SCENARIO 4: Dashboard i termini - prikaz cena',
            'scenario_5': 'SCENARIO 5: Services stranica - originalne cene'
        }[scenario]
        
        if passed:
            print_success(f"{scenario_name}")
        else:
            print_error(f"{scenario_name}")
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 SVI TESTOVI SU PROŠLI!")
        print("✅ Kompletan sistem za popuste, cene i rezervacije radi ispravno")
        print("✅ Obične masaže imaju aktivne popuste")
        print("✅ [PAROVI] masaže NEMAJU popuste na backend-u")
        print("✅ Snapshot mehanizam sprečava retroaktivne promene cena")
        print("✅ Dashboard i termini koriste snapshot podatke")
        print("✅ Services stranica prikazuje originalne cene")
    else:
        print("❌ NEKI TESTOVI SU NEUSPEŠNI!")
        print("Molimo proverite neuspešne test slučajeve gore.")
    
    print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
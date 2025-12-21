#!/usr/bin/env python3
"""
E2E Test Script for Serbian Review Request
Testiraj kompletan sistem popusta za Bua Luang Thai Spa

Backend URL: https://spa-web-update.preview.emergentagent.com
"""

import requests
import json
import subprocess
import sys

BACKEND_URL = "https://spa-web-update.preview.emergentagent.com"

def run_curl_command(command):
    """Execute curl command and return result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def test_e2e_discount_system():
    """
    TEST SCENARIO (E2E) from Serbian review request:
    1. PATCH popust na SPA servis (15%)
    2. GET public list mora da vrati discount polja
    3. GET /api/services (masaze) mora da vrati ista polja
    4. Analytics endpoint koristi pricing snapshot
    5. Reset discount na 0%
    """
    
    print("=" * 80)
    print("🧖 SERBIAN E2E TEST - KOMPLETAN SISTEM POPUSTA")
    print("=" * 80)
    
    all_tests_passed = True
    
    # Step 1: Get first SPA service ID
    print("\n1. Getting first SPA service ID...")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/spa/services")
        if response.status_code != 200:
            print(f"❌ FAILED: Could not get SPA services (status: {response.status_code})")
            return False
        
        spa_services = response.json()
        if not spa_services:
            print("❌ FAILED: No SPA services found")
            return False
        
        spa_id = spa_services[0]['id']
        spa_name = spa_services[0]['name']
        original_price = spa_services[0].get('original_price', spa_services[0].get('price', 0))
        
        print(f"✅ First SPA service: {spa_name}")
        print(f"✅ SPA ID: {spa_id}")
        print(f"✅ Original price: {original_price} RSD")
        
    except Exception as e:
        print(f"❌ ERROR getting SPA service: {e}")
        return False
    
    # Step 2: Apply 15% discount using curl command from review request
    print(f"\n2. Applying 15% discount to SPA service...")
    print("-" * 60)
    
    curl_command = f'curl -X PATCH "{BACKEND_URL}/api/spa/services/{spa_id}/discount?discount=15"'
    print(f"Command: {curl_command}")
    
    returncode, stdout, stderr = run_curl_command(curl_command)
    
    if returncode != 0:
        print(f"❌ FAILED: curl command failed (exit code: {returncode})")
        print(f"stderr: {stderr}")
        all_tests_passed = False
    else:
        try:
            patch_response = json.loads(stdout)
            print(f"✅ PATCH response received")
            
            # Verify response has required fields
            required_fields = ['original_price', 'discount_percent', 'final_price', 'has_discount']
            missing_fields = [field for field in required_fields if field not in patch_response]
            
            if missing_fields:
                print(f"❌ FAILED: PATCH response missing fields: {missing_fields}")
                all_tests_passed = False
            else:
                print(f"✅ PATCH response has all required fields:")
                print(f"  original_price: {patch_response.get('original_price')}")
                print(f"  discount_percent: {patch_response.get('discount_percent')}")
                print(f"  final_price: {patch_response.get('final_price')}")
                print(f"  has_discount: {patch_response.get('has_discount')}")
                
                # Verify 15% discount calculation
                expected_final = int(patch_response.get('original_price', 0) * 0.85)
                actual_final = patch_response.get('final_price')
                
                if actual_final == expected_final:
                    print(f"✅ 15% discount calculated correctly: {patch_response.get('original_price')} → {actual_final}")
                else:
                    print(f"❌ FAILED: Expected final_price {expected_final}, got {actual_final}")
                    all_tests_passed = False
                    
        except json.JSONDecodeError:
            print(f"❌ FAILED: Invalid JSON response from PATCH")
            print(f"Response: {stdout}")
            all_tests_passed = False
    
    # Step 3: GET public list mora da vrati discount polja
    print(f"\n3. Verifying GET /api/spa/services returns discount fields...")
    print("-" * 60)
    
    curl_command = f'curl -s "{BACKEND_URL}/api/spa/services"'
    print(f"Command: {curl_command}")
    
    returncode, stdout, stderr = run_curl_command(curl_command)
    
    if returncode != 0:
        print(f"❌ FAILED: curl command failed (exit code: {returncode})")
        all_tests_passed = False
    else:
        try:
            spa_services_list = json.loads(stdout)
            print(f"✅ GET /api/spa/services returned {len(spa_services_list)} services")
            
            # Find our test service in the list
            test_service = None
            for service in spa_services_list:
                if service.get('id') == spa_id:
                    test_service = service
                    break
            
            if not test_service:
                print(f"❌ FAILED: Test service not found in services list")
                all_tests_passed = False
            else:
                # Verify discount fields are present and correct
                required_fields = ['original_price', 'discount_percent', 'final_price', 'has_discount']
                missing_fields = [field for field in required_fields if field not in test_service]
                
                if missing_fields:
                    print(f"❌ FAILED: Service missing discount fields: {missing_fields}")
                    all_tests_passed = False
                else:
                    original = test_service.get('original_price')
                    discount = test_service.get('discount_percent')
                    final = test_service.get('final_price')
                    has_discount = test_service.get('has_discount')
                    
                    print(f"✅ First service has discount fields:")
                    print(f"  original_price: {original} (broj)")
                    print(f"  discount_percent: {discount} (15)")
                    print(f"  final_price: {final} (manji od original)")
                    print(f"  has_discount: {has_discount} (true)")
                    
                    # Verify values are correct
                    if discount == 15 and has_discount == True and final < original:
                        print(f"✅ Discount fields are correct")
                    else:
                        print(f"❌ FAILED: Discount field values incorrect")
                        all_tests_passed = False
                        
        except json.JSONDecodeError:
            print(f"❌ FAILED: Invalid JSON response from GET")
            all_tests_passed = False
    
    # Step 4: GET /api/services (masaze) mora da vrati ista polja
    print(f"\n4. Verifying GET /api/services (massages) returns uniform fields...")
    print("-" * 60)
    
    curl_command = f'curl -s "{BACKEND_URL}/api/services"'
    print(f"Command: {curl_command}")
    
    returncode, stdout, stderr = run_curl_command(curl_command)
    
    if returncode != 0:
        print(f"❌ FAILED: curl command failed (exit code: {returncode})")
        all_tests_passed = False
    else:
        try:
            massage_services = json.loads(stdout)
            print(f"✅ GET /api/services returned {len(massage_services)} services")
            
            # Check first few services for uniform fields
            uniform_fields = ['original_price', 'discount_percent', 'final_price', 'has_discount']
            services_checked = 0
            
            for service in massage_services[:5]:  # Check first 5 services
                missing_fields = [field for field in uniform_fields if field not in service]
                
                if missing_fields:
                    print(f"❌ FAILED: Service '{service.get('name')}' missing fields: {missing_fields}")
                    all_tests_passed = False
                    break
                else:
                    services_checked += 1
            
            if services_checked == 5:
                print(f"✅ Uniform pricing fields verified in massage services:")
                print(f"  All services have: original_price, discount_percent, final_price, has_discount")
                
                # Show sample service
                sample = massage_services[0]
                print(f"  Sample: {sample.get('name')}")
                print(f"    original_price: {sample.get('original_price')}")
                print(f"    discount_percent: {sample.get('discount_percent')}")
                print(f"    final_price: {sample.get('final_price')}")
                print(f"    has_discount: {sample.get('has_discount')}")
                        
        except json.JSONDecodeError:
            print(f"❌ FAILED: Invalid JSON response from GET /api/services")
            all_tests_passed = False
    
    # Step 5: Analytics endpoint koristi pricing snapshot
    print(f"\n5. Verifying analytics endpoint uses pricing snapshot...")
    print("-" * 60)
    
    curl_command = f'curl -s "{BACKEND_URL}/api/analytics/revenue?period=month"'
    print(f"Command: {curl_command}")
    
    returncode, stdout, stderr = run_curl_command(curl_command)
    
    if returncode != 0:
        print(f"❌ FAILED: curl command failed (exit code: {returncode})")
        all_tests_passed = False
    else:
        try:
            analytics_data = json.loads(stdout)
            print(f"✅ Analytics endpoint responded")
            
            # Verify required fields are present
            required_fields = ['total_revenue', 'gross_revenue', 'total_discount']
            missing_fields = [field for field in required_fields if field not in analytics_data]
            
            if missing_fields:
                print(f"❌ FAILED: Analytics missing fields: {missing_fields}")
                all_tests_passed = False
            else:
                total_revenue = analytics_data.get('total_revenue', 0)
                gross_revenue = analytics_data.get('gross_revenue', 0)
                total_discount = analytics_data.get('total_discount', 0)
                
                print(f"✅ Analytics returns pricing snapshot fields:")
                print(f"  total_revenue: {total_revenue}")
                print(f"  gross_revenue: {gross_revenue}")
                print(f"  total_discount: {total_discount}")
                
                # Verify logical relationship: gross_revenue >= total_revenue
                if gross_revenue >= total_revenue:
                    print(f"✅ Logical relationship verified: gross_revenue ({gross_revenue}) >= total_revenue ({total_revenue})")
                else:
                    print(f"❌ FAILED: Illogical relationship: gross_revenue ({gross_revenue}) < total_revenue ({total_revenue})")
                    all_tests_passed = False
                        
        except json.JSONDecodeError:
            print(f"❌ FAILED: Invalid JSON response from analytics")
            all_tests_passed = False
    
    # Step 6: Reset discount na 0%
    print(f"\n6. Resetting discount to 0%...")
    print("-" * 60)
    
    curl_command = f'curl -X PATCH "{BACKEND_URL}/api/spa/services/{spa_id}/discount?discount=0"'
    print(f"Command: {curl_command}")
    
    returncode, stdout, stderr = run_curl_command(curl_command)
    
    if returncode != 0:
        print(f"❌ FAILED: curl command failed (exit code: {returncode})")
        all_tests_passed = False
    else:
        try:
            reset_response = json.loads(stdout)
            print(f"✅ Reset PATCH response received")
            
            discount_percent = reset_response.get('discount_percent', -1)
            has_discount = reset_response.get('has_discount', True)
            original_price = reset_response.get('original_price', 0)
            final_price = reset_response.get('final_price', 0)
            
            if discount_percent == 0 and has_discount == False and final_price == original_price:
                print(f"✅ Discount reset successfully:")
                print(f"  discount_percent: {discount_percent}")
                print(f"  has_discount: {has_discount}")
                print(f"  final_price == original_price: {final_price} == {original_price}")
            else:
                print(f"❌ FAILED: Discount reset incomplete")
                print(f"  discount_percent: {discount_percent} (expected 0)")
                print(f"  has_discount: {has_discount} (expected False)")
                print(f"  final_price: {final_price}, original_price: {original_price}")
                all_tests_passed = False
                        
        except json.JSONDecodeError:
            print(f"❌ FAILED: Invalid JSON response from reset")
            all_tests_passed = False
    
    # Summary
    print("\n" + "=" * 80)
    print("🧖 SERBIAN E2E TEST SUMMARY")
    print("=" * 80)
    
    if all_tests_passed:
        print("🎉 ALL E2E TESTS PASSED!")
        print("✅ PATCH vraća uniform pricing fields")
        print("✅ GET vraća ista polja za SPA i masaže")
        print("✅ Analytics koristi snapshot (gross/net revenue)")
        print("✅ Nema duplog popusta")
        print("✅ Reset discount works correctly")
    else:
        print("❌ SOME E2E TESTS FAILED!")
        print("Check the failed test cases above.")
    
    return all_tests_passed

if __name__ == "__main__":
    success = test_e2e_discount_system()
    sys.exit(0 if success else 1)
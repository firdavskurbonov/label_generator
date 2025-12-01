#!/usr/bin/env python3
"""
Test script for Participant Label Generator API
"""

import requests
import json
import sys

API_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{API_URL}/api/health")
        assert response.status_code == 200
        print("✓ Health check passed")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_formats():
    """Test formats endpoint"""
    print("\nTesting formats endpoint...")
    try:
        response = requests.get(f"{API_URL}/api/formats")
        assert response.status_code == 200
        formats = response.json()
        assert len(formats) == 3
        print(f"✓ Found {len(formats)} label formats")
        for fmt in formats:
            print(f"  - {fmt['name']}: {fmt['labels_per_sheet']} labels/sheet")
        return True
    except Exception as e:
        print(f"✗ Formats test failed: {e}")
        return False

def test_generate_barcode():
    """Test barcode generation"""
    print("\nTesting barcode generation...")
    try:
        payload = {
            "start_code": 1,
            "end_code": 10,
            "code_type": "barcode",
            "label_format": "avery5160",
            "prefix": "TEST-",
            "suffix": "",
            "page_size": "letter"
        }
        
        response = requests.post(f"{API_URL}/api/generate", json=payload)
        assert response.status_code == 200
        result = response.json()
        
        assert result['success'] == True
        assert result['total_labels'] == 10
        
        print(f"✓ Barcode generation successful")
        print(f"  - Total labels: {result['total_labels']}")
        print(f"  - Total pages: {result['total_pages']}")
        print(f"  - Filename: {result['filename']}")
        
        return True
    except Exception as e:
        print(f"✗ Barcode generation failed: {e}")
        return False

def test_generate_qrcode():
    """Test QR code generation"""
    print("\nTesting QR code generation...")
    try:
        payload = {
            "start_code": 100,
            "end_code": 120,
            "code_type": "qrcode",
            "label_format": "avery5163",
            "prefix": "QR-",
            "suffix": "-2024",
            "page_size": "letter"
        }
        
        response = requests.post(f"{API_URL}/api/generate", json=payload)
        assert response.status_code == 200
        result = response.json()
        
        assert result['success'] == True
        assert result['total_labels'] == 21
        
        print(f"✓ QR code generation successful")
        print(f"  - Total labels: {result['total_labels']}")
        print(f"  - Total pages: {result['total_pages']}")
        print(f"  - Filename: {result['filename']}")
        
        return True
    except Exception as e:
        print(f"✗ QR code generation failed: {e}")
        return False

def test_validation():
    """Test input validation"""
    print("\nTesting input validation...")
    
    test_cases = [
        {
            "name": "Invalid range (end < start)",
            "payload": {
                "start_code": 100,
                "end_code": 50,
                "code_type": "barcode",
                "label_format": "avery5160"
            },
            "expect_error": True
        },
        {
            "name": "Negative code",
            "payload": {
                "start_code": -1,
                "end_code": 10,
                "code_type": "barcode",
                "label_format": "avery5160"
            },
            "expect_error": True
        },
        {
            "name": "Invalid code type",
            "payload": {
                "start_code": 1,
                "end_code": 10,
                "code_type": "invalid",
                "label_format": "avery5160"
            },
            "expect_error": True
        }
    ]
    
    passed = 0
    for test in test_cases:
        try:
            response = requests.post(f"{API_URL}/api/generate", json=test["payload"])
            if test["expect_error"] and response.status_code == 422:
                print(f"  ✓ {test['name']}: validation works")
                passed += 1
            else:
                print(f"  ✗ {test['name']}: unexpected response")
        except Exception as e:
            print(f"  ✗ {test['name']}: {e}")
    
    success = passed == len(test_cases)
    if success:
        print(f"✓ All validation tests passed ({passed}/{len(test_cases)})")
    else:
        print(f"✗ Some validation tests failed ({passed}/{len(test_cases)})")
    
    return success

def main():
    """Run all tests"""
    print("=" * 60)
    print("Participant Label Generator API - Test Suite")
    print("=" * 60)
    
    tests = [
        test_health,
        test_formats,
        test_generate_barcode,
        test_generate_qrcode,
        test_validation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()

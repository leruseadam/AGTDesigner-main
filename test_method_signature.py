#!/usr/bin/env python3.11
"""
Simple test script to verify _calculate_product_strain method signature fix.
Run this on PythonAnywhere to test if the fix is working.
"""

def test_method_signature():
    print("🔍 Testing _calculate_product_strain method signature...")
    
    try:
        # Test 1: Import the module
        print("1. Testing module import...")
        from src.core.data.product_database import ProductDatabase
        print("   ✅ Module imported successfully")
        
        # Test 2: Create database instance
        print("2. Testing database instance creation...")
        db = ProductDatabase()
        print("   ✅ Database instance created successfully")
        
        # Test 3: Test dictionary call (should work)
        print("3. Testing dictionary method call...")
        result1 = db._calculate_product_strain({
            'Product Type*': 'Flower', 
            'Product Name*': 'Test', 
            'Description': '', 
            'Ratio': ''
        })
        print(f"   ✅ Dictionary call works: '{result1}'")
        
        # Test 4: Test original method call (should work)
        print("4. Testing original method call...")
        result2 = db._calculate_product_strain_original('Flower', 'Test', '', '')
        print(f"   ✅ Original method call works: '{result2}'")
        
        # Test 5: Test wrong call (should fail)
        print("5. Testing wrong method call (should fail)...")
        try:
            result3 = db._calculate_product_strain('Flower', 'Test', '', '')
            print(f"   ❌ Wrong call should have failed but returned: '{result3}'")
        except Exception as e:
            print(f"   ✅ Wrong call correctly failed: {e}")
        
        # Test 6: Test app import
        print("6. Testing app import...")
        from app import app
        print("   ✅ App imported successfully")
        
        print("\n🎉 ALL TESTS PASSED! Method signature fix is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_method_signature()
    exit(0 if success else 1)

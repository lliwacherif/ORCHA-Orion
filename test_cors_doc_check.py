"""
Test CORS headers on doc-check endpoint
"""
import requests

url = "http://localhost:8000/api/v1/orcha/doc-check"

print("=" * 60)
print("Testing CORS on doc-check endpoint")
print("=" * 60)

# Test 1: OPTIONS request (preflight)
print("\n1. Testing OPTIONS (CORS Preflight):")
print("-" * 60)

try:
    response = requests.options(url, headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "PUT",
        "Access-Control-Request-Headers": "content-type"
    })
    
    print(f"Status Code: {response.status_code}")
    print("\nCORS Headers:")
    for header in ["Access-Control-Allow-Origin", "Access-Control-Allow-Methods", 
                   "Access-Control-Allow-Headers", "Access-Control-Max-Age"]:
        value = response.headers.get(header, "NOT SET")
        print(f"  {header}: {value}")
    
    if response.status_code == 200:
        print("\n✅ OPTIONS request successful!")
    else:
        print(f"\n❌ OPTIONS request failed with status {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: PUT request with file
print("\n\n2. Testing PUT Request with File:")
print("-" * 60)

try:
    # Create a test file
    test_content = b"This is a test passport document for CORS testing."
    files = {'file': ('test_passport.txt', test_content, 'text/plain')}
    data = {'label': 'passport'}
    
    response = requests.put(url, files=files, data=data, headers={
        "Origin": "http://localhost:3000"
    })
    
    print(f"Status Code: {response.status_code}")
    print("\nCORS Headers:")
    for header in ["Access-Control-Allow-Origin", "Access-Control-Allow-Methods", 
                   "Access-Control-Allow-Headers"]:
        value = response.headers.get(header, "NOT SET")
        print(f"  {header}: {value}")
    
    print("\nResponse:")
    print(response.text[:500])  # First 500 chars
    
    if response.status_code == 200:
        print("\n✅ PUT request successful!")
        result = response.json()
        print(f"✅ CORS headers present: {'Access-Control-Allow-Origin' in response.headers}")
    else:
        print(f"\n❌ PUT request failed with status {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)

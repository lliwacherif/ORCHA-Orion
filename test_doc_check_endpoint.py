"""
Test script to verify the /api/v1/orcha/doc-check endpoint is working correctly
"""
import requests
import sys

# Test the endpoint with a simple request
url = "https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check"

print(f"Testing endpoint: {url}")
print("=" * 60)

# First, let's check if the endpoint exists with different HTTP methods
methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]

for method in methods:
    try:
        print(f"\nTrying {method} request...")
        response = requests.request(method, url, timeout=5)
        print(f"  Status Code: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 60)
print("\nNow testing with actual POST + multipart/form-data:")

# Create a simple test file
test_file_content = b"This is a test passport document with sample text."
files = {'file': ('test.txt', test_file_content, 'text/plain')}
data = {'label': 'passport'}

try:
    response = requests.post(url, files=files, data=data, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

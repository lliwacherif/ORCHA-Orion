"""
Specific test for POST request to doc-check endpoint
"""
import requests

url = "https://aura-orcha.vaeerdia.com/api/v1/orcha/doc-check"

print(f"Testing POST to: {url}\n")

# Create a simple test file
test_file_content = b"Test passport document content"
files = {'file': ('test_passport.txt', test_file_content, 'text/plain')}
data = {'label': 'passport'}

try:
    print("Sending POST request...")
    response = requests.post(url, files=files, data=data, timeout=30)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"\nResponse Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    
    print(f"\nResponse Body:")
    print(response.text)
    
except Exception as e:
    print(f"\nError occurred: {e}")
    import traceback
    traceback.print_exc()

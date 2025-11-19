"""Quick test to check if server is running on port 8000"""
import httpx
import time

print("Checking if ORCHA server is running on port 8000...")
time.sleep(2)

try:
    response = httpx.get("http://localhost:8000/docs", timeout=5)
    if response.status_code == 200:
        print("\n[SUCCESS] Server is running on http://localhost:8000")
        print("[INFO] API Documentation: http://localhost:8000/docs")
        print("[INFO] ReDoc: http://localhost:8000/redoc")
    else:
        print(f"\n[WARN] Server responded with status code: {response.status_code}")
except httpx.ConnectError:
    print("\n[ERROR] Cannot connect to server on port 8000")
    print("[INFO] Server might still be starting up...")
    print("[INFO] Try again in a few seconds or check for errors")
except Exception as e:
    print(f"\n[ERROR] {e}")




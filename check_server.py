#!/usr/bin/env python
import httpx
import sys
import time

print("Waiting for server to start...")
time.sleep(5)

try:
    response = httpx.get("http://localhost:8000/docs", timeout=10)
    if response.status_code == 200:
        print("✅ Server is running on http://localhost:8000")
        print("📚 API Documentation: http://localhost:8000/docs")
        print("🔧 ReDoc: http://localhost:8000/redoc")
        sys.exit(0)
    else:
        print(f"⚠️  Server returned status code: {response.status_code}")
        sys.exit(1)
except httpx.ConnectError:
    print("❌ Cannot connect to server on port 8000")
    print("   Make sure:")
    print("   1. PostgreSQL is running (localhost:5432)")
    print("   2. Redis is running (localhost:6379) - optional")
    print("   3. No firewall is blocking port 8000")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)




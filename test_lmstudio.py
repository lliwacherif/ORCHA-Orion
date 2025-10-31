#!/usr/bin/env python3
"""
Test script to verify LM Studio connection and API responses.
Run this before starting your React app to ensure everything works.

Usage:
    python test_lmstudio.py
"""

import asyncio
import httpx
import json

LMSTUDIO_URL = "http://192.168.1.37:1234"

async def test_models():
    """Test GET /v1/models endpoint"""
    print("\n" + "="*60)
    print("Testing: GET /v1/models")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{LMSTUDIO_URL}/v1/models")
            response.raise_for_status()
            data = response.json()
            
            print("✅ SUCCESS - Models endpoint working")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if data.get("data"):
                print(f"\n📋 Available models: {len(data['data'])}")
                for model in data['data']:
                    print(f"  - {model.get('id', 'unknown')}")
            
            return True
    except httpx.ConnectError:
        print(f"❌ FAILED - Cannot connect to LM Studio at {LMSTUDIO_URL}")
        print("   Make sure LM Studio is running and accessible at this address.")
        return False
    except Exception as e:
        print(f"❌ FAILED - Error: {e}")
        return False

async def test_chat():
    """Test POST /v1/chat/completions endpoint"""
    print("\n" + "="*60)
    print("Testing: POST /v1/chat/completions")
    print("="*60)
    
    test_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello in one sentence."}
    ]
    
    payload = {
        "messages": test_messages,
        "temperature": 0.7,
        "stream": False
    }
    
    print(f"Request payload:\n{json.dumps(payload, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{LMSTUDIO_URL}/v1/chat/completions",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            print("\n✅ SUCCESS - Chat endpoint working")
            
            # Extract the assistant's message
            if data.get("choices") and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {}).get("content", "")
                print(f"\n🤖 Assistant response:")
                print(f"   {message}")
                
            print(f"\n📊 Full response structure:")
            print(f"   - ID: {data.get('id')}")
            print(f"   - Model: {data.get('model')}")
            print(f"   - Choices: {len(data.get('choices', []))}")
            print(f"   - Finish reason: {data.get('choices', [{}])[0].get('finish_reason')}")
            
            return True
    except httpx.ConnectError:
        print(f"❌ FAILED - Cannot connect to LM Studio at {LMSTUDIO_URL}")
        return False
    except httpx.ReadTimeout:
        print(f"❌ FAILED - Request timed out. Model might be loading or too slow.")
        return False
    except Exception as e:
        print(f"❌ FAILED - Error: {e}")
        return False

async def test_orcha_api():
    """Test ORCHA API endpoint (requires ORCHA server running)"""
    print("\n" + "="*60)
    print("Testing: ORCHA API at http://localhost:8000")
    print("="*60)
    
    payload = {
        "user_id": "test_user",
        "message": "Hello, this is a test message.",
        "use_rag": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "http://localhost:8000/api/v1/orcha/chat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            print("✅ SUCCESS - ORCHA API working")
            
            if data.get("status") == "ok":
                print(f"\n🤖 Response message:")
                print(f"   {data.get('message', 'No message')}")
                
                if data.get('contexts'):
                    print(f"\n📚 RAG Contexts: {len(data['contexts'])}")
                    
            elif data.get("status") == "error":
                print(f"\n⚠️  API returned error: {data.get('error')}")
            
            return True
    except httpx.ConnectError:
        print("❌ FAILED - Cannot connect to ORCHA API")
        print("   Make sure ORCHA server is running: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ FAILED - Error: {e}")
        return False

async def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║         ORCHA + LM Studio Connection Test               ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    print(f"LM Studio URL: {LMSTUDIO_URL}")
    
    # Test LM Studio endpoints
    models_ok = await test_models()
    await asyncio.sleep(1)
    
    chat_ok = await test_chat()
    await asyncio.sleep(1)
    
    # Test ORCHA API (optional)
    orcha_ok = await test_orcha_api()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"LM Studio Models:  {'✅ PASS' if models_ok else '❌ FAIL'}")
    print(f"LM Studio Chat:    {'✅ PASS' if chat_ok else '❌ FAIL'}")
    print(f"ORCHA API:         {'✅ PASS' if orcha_ok else '❌ FAIL'}")
    
    if models_ok and chat_ok and orcha_ok:
        print("\n🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Start ORCHA: uvicorn app.main:app --reload")
        print("2. Build your React UI using the REACT_INTEGRATION.md guide")
    elif models_ok and chat_ok:
        print("\n⚠️  LM Studio is working, but ORCHA API is not running.")
        print("\nTo start ORCHA:")
        print("  uvicorn app.main:app --reload")
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        print("\nTroubleshooting:")
        print("- Check if LM Studio is running and has a model loaded")
        print("- Verify the IP address and port are correct")
        print("- Ensure your firewall allows connections")

if __name__ == "__main__":
    asyncio.run(main())


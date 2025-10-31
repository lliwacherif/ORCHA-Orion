#!/usr/bin/env python3
"""
Diagnostic script to check LM Studio configuration and available models
"""
import asyncio
import httpx
from app.config import settings

async def check_lm_studio():
    print("=" * 60)
    print("LM STUDIO DIAGNOSTIC CHECK")
    print("=" * 60)
    
    print(f"\n📍 LM Studio URL: {settings.LMSTUDIO_URL}")
    print(f"🎨 Configured Vision Model: {settings.LMSTUDIO_VISION_MODEL}")
    print(f"⏱️  Timeout: {settings.LM_TIMEOUT}s")
    
    # Check if LM Studio is running
    print("\n1️⃣ Checking if LM Studio is accessible...")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            url = f"{settings.LMSTUDIO_URL.rstrip('/')}/v1/models"
            print(f"   Calling: {url}")
            response = await client.get(url)
            response.raise_for_status()
            
            models_data = response.json()
            print("   ✅ LM Studio is running!")
            
            # Display available models
            if "data" in models_data:
                models = models_data["data"]
                print(f"\n2️⃣ Found {len(models)} model(s):")
                for i, model in enumerate(models, 1):
                    model_id = model.get("id", "unknown")
                    print(f"   {i}. {model_id}")
                    
                    # Check if it matches configured vision model
                    if model_id == settings.LMSTUDIO_VISION_MODEL:
                        print(f"      ✅ MATCHES configured vision model")
                    
                # Check if vision model exists
                model_ids = [m.get("id") for m in models]
                if settings.LMSTUDIO_VISION_MODEL not in model_ids:
                    print(f"\n   ⚠️  WARNING: Configured vision model '{settings.LMSTUDIO_VISION_MODEL}' not found!")
                    print(f"   📝 Available models: {', '.join(model_ids)}")
                    print(f"\n   💡 SOLUTION: Update LMSTUDIO_VISION_MODEL in your .env file to match one of the above models")
            else:
                print("   ⚠️  No models found in response")
                print(f"   Response: {models_data}")
                
    except httpx.ConnectError:
        print(f"   ❌ Cannot connect to LM Studio at {settings.LMSTUDIO_URL}")
        print(f"   💡 Make sure LM Studio is running and the URL is correct")
    except httpx.TimeoutException:
        print(f"   ❌ Connection timeout")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test a simple chat request
    print("\n3️⃣ Testing simple chat request (text-only)...")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            url = f"{settings.LMSTUDIO_URL.rstrip('/')}/v1/chat/completions"
            test_payload = {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Hello' in one word"}
                ],
                "temperature": 0.7,
                "max_tokens": 10
            }
            
            response = await client.post(url, json=test_payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0].get("message", {}).get("content", "")
                print(f"   ✅ Chat API working! Response: '{message}'")
            else:
                print(f"   ⚠️  Unexpected response format: {result}")
                
    except Exception as e:
        print(f"   ❌ Chat test failed: {e}")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)
    print("1. Copy .env.example to .env")
    print("2. Set LMSTUDIO_VISION_MODEL to one of the model IDs listed above")
    print("3. Restart your AURA backend")
    print("4. Test vision feature with an image attachment")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    asyncio.run(check_lm_studio())

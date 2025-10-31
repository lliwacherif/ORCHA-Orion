"""
Test script for token tracking functionality.
Run this to verify token tracking works correctly.
"""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"

async def test_token_tracking():
    """Test the token tracking feature end-to-end."""
    
    print("🧪 Testing Token Tracking System\n")
    print("="*60)
    
    # Test user
    user_id = "test_user_123"
    
    async with httpx.AsyncClient(timeout=120) as client:
        
        # 1. Check initial usage (should be 0)
        print("\n1️⃣  Checking initial token usage...")
        response = await client.get(f"{BASE_URL}/tokens/usage/{user_id}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        
        # 2. Send first chat message
        print("\n2️⃣  Sending first chat message...")
        chat_payload = {
            "user_id": user_id,
            "tenant_id": "test_tenant",
            "message": "Hello, this is a test message!",
            "use_rag": False,
            "attachments": []
        }
        
        chat_response = await client.post(
            f"{BASE_URL}/orcha/chat",
            json=chat_payload
        )
        
        chat_result = chat_response.json()
        print(f"   Chat Status: {chat_result.get('status')}")
        
        if "token_usage" in chat_result:
            print(f"   Token Usage Info:")
            print(f"      - Tokens Added: {chat_result['token_usage'].get('tokens_added')}")
            print(f"      - Current Usage: {chat_result['token_usage'].get('current_usage')}")
            print(f"      - Resets At: {chat_result['token_usage'].get('reset_at')}")
            print(f"      - Tracking Enabled: {chat_result['token_usage'].get('tracking_enabled')}")
        else:
            print("   ⚠️  No token usage info in response")
        
        # 3. Send second chat message
        print("\n3️⃣  Sending second chat message...")
        chat_payload["message"] = "Another test message to increment tokens!"
        
        chat_response2 = await client.post(
            f"{BASE_URL}/orcha/chat",
            json=chat_payload
        )
        
        chat_result2 = chat_response2.json()
        
        if "token_usage" in chat_result2:
            print(f"   Token Usage Info (after 2nd message):")
            print(f"      - Tokens Added: {chat_result2['token_usage'].get('tokens_added')}")
            print(f"      - Current Usage: {chat_result2['token_usage'].get('current_usage')}")
            print(f"      - Resets At: {chat_result2['token_usage'].get('reset_at')}")
        
        # 4. Check final usage
        print("\n4️⃣  Checking final token usage...")
        final_response = await client.get(f"{BASE_URL}/tokens/usage/{user_id}")
        print(f"   Response: {json.dumps(final_response.json(), indent=2)}")
        
        # 5. Test reset (optional)
        print("\n5️⃣  Testing manual reset...")
        reset_response = await client.post(f"{BASE_URL}/tokens/reset/{user_id}")
        print(f"   Reset Response: {json.dumps(reset_response.json(), indent=2)}")
        
        # 6. Verify reset
        print("\n6️⃣  Verifying reset...")
        after_reset = await client.get(f"{BASE_URL}/tokens/usage/{user_id}")
        print(f"   Response: {json.dumps(after_reset.json(), indent=2)}")
        
    print("\n" + "="*60)
    print("✅ Token tracking test complete!")
    print("\nNOTE: Make sure your backend server is running on localhost:8000")
    print("      and Redis is connected for this test to work properly.\n")

if __name__ == "__main__":
    try:
        asyncio.run(test_token_tracking())
    except httpx.ConnectError:
        print("❌ ERROR: Could not connect to backend server.")
        print("   Make sure the server is running: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()



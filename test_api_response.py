#!/usr/bin/env python3
"""
Test script to verify API response format matches frontend expectations.
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"

async def test_chat_response_format():
    """Test that chat response has the correct format for frontend."""
    print("🧪 Testing Chat API Response Format")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=90.0) as client:
        # Send a simple chat message
        print("\n1️⃣ Sending chat message...")
        response = await client.post(
            f"{BASE_URL}/orcha/chat",
            json={
                "user_id": "1",
                "tenant_id": "test",
                "message": "Hello, just a quick test message.",
                "conversation_id": None,
                "attachments": [],
                "use_rag": False,
                "conversation_history": []
            }
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        # Parse response
        data = response.json()
        
        print("\n📦 Response Structure:")
        print(json.dumps(data, indent=2, default=str)[:500] + "...")
        
        # Verify required fields
        print("\n✅ Checking Required Fields:")
        required_fields = ["status", "message", "conversation_id"]
        
        for field in required_fields:
            if field in data:
                if field == "message":
                    print(f"   ✅ {field}: '{data[field][:50]}...' (length: {len(data[field])})")
                else:
                    print(f"   ✅ {field}: {data[field]}")
            else:
                print(f"   ❌ MISSING: {field}")
        
        # Check optional fields
        print("\n📋 Optional Fields:")
        optional_fields = ["contexts", "token_usage", "model_response"]
        for field in optional_fields:
            if field in data:
                print(f"   ✅ {field}: present")
            else:
                print(f"   ⚠️  {field}: not present")
        
        # Verify response structure matches frontend expectations
        print("\n🎯 Frontend Compatibility Check:")
        
        if data.get("status") == "ok":
            print("   ✅ Status is 'ok'")
        else:
            print(f"   ❌ Status is '{data.get('status')}' (expected 'ok')")
        
        if isinstance(data.get("message"), str) and len(data.get("message", "")) > 0:
            print(f"   ✅ Message is a non-empty string ({len(data.get('message'))} chars)")
        else:
            print(f"   ❌ Message is invalid: {type(data.get('message'))}")
        
        if isinstance(data.get("conversation_id"), int):
            print(f"   ✅ Conversation ID is an integer: {data.get('conversation_id')}")
        else:
            print(f"   ❌ Conversation ID is invalid: {data.get('conversation_id')}")
        
        # Test retrieving conversation details
        conv_id = data.get("conversation_id")
        if conv_id:
            print(f"\n2️⃣ Retrieving conversation {conv_id} details...")
            conv_response = await client.get(f"{BASE_URL}/conversations/1/{conv_id}")
            
            if conv_response.status_code == 200:
                print(f"   ✅ Conversation retrieved successfully")
                conv_data = conv_response.json()
                print(f"   📝 Title: {conv_data.get('title')}")
                print(f"   💬 Messages: {len(conv_data.get('messages', []))}")
            else:
                print(f"   ❌ Failed to retrieve conversation: {conv_response.status_code}")
                print(f"   Error: {conv_response.text}")
        
        print("\n" + "=" * 60)
        print("✅ API Response Format Test Complete!")
        
        # Summary
        print("\n📋 Summary:")
        print(f"   Backend Status: {'✅ Working' if response.status_code == 200 else '❌ Error'}")
        print(f"   Response Format: {'✅ Valid' if data.get('status') == 'ok' else '❌ Invalid'}")
        print(f"   Message Present: {'✅ Yes' if data.get('message') else '❌ No'}")
        print(f"   Conversation ID: {'✅ Yes' if data.get('conversation_id') else '❌ No'}")
        
        print("\n💡 If frontend not showing response:")
        print("   1. Check browser console for JavaScript errors")
        print("   2. Verify frontend is making the request to the correct endpoint")
        print("   3. Check if frontend is properly parsing the 'message' field")
        print("   4. Ensure frontend updates UI after receiving response")
        print("   5. Check CORS configuration if frontend is on different domain")

if __name__ == "__main__":
    asyncio.run(test_chat_response_format())

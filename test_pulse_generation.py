#!/usr/bin/env python3
"""
Test script to verify pulse generation works correctly.
Run this to debug pulse generation issues.
"""
import asyncio
from app.db.database import AsyncSessionLocal
from app.services.pulse_service import generate_pulse_for_user, update_user_pulse

async def test_pulse_generation(user_id: int = 1):
    """Test pulse generation for a specific user."""
    print(f"🧪 Testing Pulse Generation for User {user_id}")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        try:
            # Step 1: Check if user has conversations
            from app.db.models import Conversation, ChatMessage
            from sqlalchemy import select, desc
            
            print("\n1️⃣ Checking user's conversations...")
            conv_result = await db.execute(
                select(Conversation)
                .where(
                    Conversation.user_id == user_id,
                    Conversation.is_active == True
                )
                .order_by(desc(Conversation.updated_at))
                .limit(5)
            )
            conversations = conv_result.scalars().all()
            
            if not conversations:
                print("   ❌ No conversations found for this user")
                print("   💡 User needs to have some chat history first")
                return
            
            print(f"   ✅ Found {len(conversations)} conversations")
            
            # Step 2: Check message count
            total_messages = 0
            total_chars = 0
            for conv in conversations:
                msg_result = await db.execute(
                    select(ChatMessage).where(ChatMessage.conversation_id == conv.id)
                )
                messages = msg_result.scalars().all()
                total_messages += len(messages)
                for msg in messages:
                    total_chars += len(msg.content)
            
            print(f"   📊 Total messages: {total_messages}")
            print(f"   📊 Total characters: {total_chars}")
            print(f"   📊 Estimated tokens: ~{total_chars // 4}")
            
            # Step 3: Generate pulse
            print("\n2️⃣ Generating pulse...")
            print("   ⏳ This may take 30-60 seconds...")
            
            pulse_content = await generate_pulse_for_user(user_id, db)
            
            if pulse_content:
                print("\n✅ Pulse Generated Successfully!")
                print("=" * 60)
                print(pulse_content)
                print("=" * 60)
                
                # Step 4: Try to save it
                print("\n3️⃣ Saving pulse to database...")
                success = await update_user_pulse(user_id, db)
                
                if success:
                    print("   ✅ Pulse saved successfully!")
                else:
                    print("   ❌ Failed to save pulse")
            else:
                print("\n❌ Pulse generation failed")
                print("   Check the errors above for details")
                
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            
            # Common issues
            print("\n🔍 Common Issues:")
            print("   1. LM Studio not running (check http://192.168.1.37:1234)")
            print("   2. Model not loaded in LM Studio")
            print("   3. Context too large for the model")
            print("   4. User has no conversations")

async def test_api_endpoint(user_id: int = 1):
    """Test the actual API endpoint."""
    print(f"\n\n🌐 Testing API Endpoint")
    print("=" * 60)
    
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            print(f"   GET /api/v1/pulse/{user_id}")
            response = await client.get(f"http://localhost:8000/api/v1/pulse/{user_id}")
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("   ✅ API working!")
                print(f"   Generated at: {data['pulse']['generated_at']}")
                print(f"   Conversations: {data['pulse']['conversations_analyzed']}")
                print(f"   Messages: {data['pulse']['messages_analyzed']}")
            else:
                print(f"   ❌ API returned error: {response.status_code}")
                print(f"   Response: {response.text}")
                
    except Exception as e:
        print(f"   ❌ API test failed: {e}")
        print("   Make sure the server is running on port 8000")

if __name__ == "__main__":
    import sys
    
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    print("🧪 Pulse Generation Test Suite")
    print(f"Testing for User ID: {user_id}\n")
    
    asyncio.run(test_pulse_generation(user_id))
    asyncio.run(test_api_endpoint(user_id))
    
    print("\n✅ Test complete!")

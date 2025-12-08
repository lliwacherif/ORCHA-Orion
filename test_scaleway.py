
import asyncio
import sys
from app.services.chatbot_client import call_lmstudio_chat, get_available_models

async def main():
    print("Testing Scaleway API Integration...")
    
    # 1. Test Listing Models
    print("\n[1] Testing get_available_models()...")
    try:
        models = await get_available_models()
        print(f"Success! Models response: {models}")
    except Exception as e:
        print(f"Failed! Error: {e}")
        return

    # 2. Test Chat Completion
    print("\n[2] Testing call_lmstudio_chat()...")
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'Scaleway API works!'"}
    ]
    try:
        response = await call_lmstudio_chat(messages, max_tokens=50)
        print(f"Success! Response: {response}")
        
        # Verify content
        if 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0]['message']['content']
            print(f"Assistant Content: {content}")
        else:
            print("Warning: Response structure unexpected.")
            
    except Exception as e:
        print(f"Failed! Error: {e}")
        
if __name__ == "__main__":
    asyncio.run(main())

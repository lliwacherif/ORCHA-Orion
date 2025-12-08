
import re

env_path = '.env'

try:
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update LM Studio URL
    content = re.sub(r'LMSTUDIO_URL=.*', 'LMSTUDIO_URL=http://192.168.1.16:1234', content)
    
    # Fix GEMINI_API_KEY syntax
    content = re.sub(r'GEMINI_API_KEY:\s*str\s*=\s*"(.*)"', r'GEMINI_API_KEY="\1"', content)
    
    # Fix GEMINI_MODEL syntax
    content = re.sub(r'GEMINI_MODEL:\s*str\s*=\s*"(.*)"', r'GEMINI_MODEL="\1"', content)

    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ .env file updated successfully.")

except Exception as e:
    print(f"❌ Failed to update .env: {e}")

"""Test PostgreSQL connection with current settings"""
import asyncio
import asyncpg
from app.config import settings

async def test_connection():
    print("\n[TEST] Testing PostgreSQL connection...")
    print(f"[INFO] Connection string: {settings.DATABASE_URL}")
    print()
    
    # Parse the DATABASE_URL to extract credentials
    url = settings.DATABASE_URL
    # postgresql+asyncpg://user:pass@host:port/db
    
    # For asyncpg, we need to remove the +asyncpg part
    if '+asyncpg' in url:
        url = url.replace('+asyncpg', '')
        url = url.replace('postgresql', 'postgres')
    
    print(f"[INFO] Testing connection to PostgreSQL...")
    print(f"[INFO] URL: {url.replace(':1234@', ':****@')}")  # Hide password
    
    try:
        # Try connecting to the postgres database first (should always exist)
        conn_url = url.replace('/orcha_db', '/postgres')
        conn = await asyncpg.connect(conn_url)
        
        # Get PostgreSQL version
        version = await conn.fetchval('SELECT version()')
        print(f"[SUCCESS] Connected to PostgreSQL!")
        print(f"[INFO] PostgreSQL version: {version.split(',')[0]}")
        
        # Check if orcha_db exists
        db_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname='orcha_db'"
        )
        
        if db_exists:
            print(f"[INFO] Database 'orcha_db' exists")
        else:
            print(f"[WARN] Database 'orcha_db' does not exist yet")
        
        await conn.close()
        print("[SUCCESS] Connection test passed!")
        return True
        
    except asyncpg.exceptions.InvalidPasswordError:
        print("[ERROR] Invalid password!")
        print("[HELP] The current password in config is '1234'")
        print("[HELP] Update app/config.py or .env file with the correct password")
        return False
        
    except asyncpg.exceptions.InvalidAuthorizationSpecificationError:
        print("[ERROR] Authentication failed!")
        print("[HELP] Check username and password in config")
        return False
        
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        print(f"[ERROR] Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    if not result:
        print()
        print("[HELP] Please verify PostgreSQL credentials:")
        print("  1. Check what password you set for 'postgres' user")
        print("  2. Update DATABASE_URL in app/config.py")
        print("  3. Or create a .env file with correct credentials")




import asyncio
from sqlalchemy import text
from app.db.database import engine

async def migrate():
    print("[INFO] Starting database migration for Folders feature...")
    async with engine.begin() as conn:
        # 1. Create folders table
        print("[INFO] Creating 'folders' table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS folders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # 2. Create index for folders
        print("[INFO] Creating index on folders(user_id)...")
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_folders_user_id ON folders(user_id);"))
        
        # 3. Add column to conversations
        print("[INFO] Altering 'conversations' table...")
        try:
            await conn.execute(text("""
                ALTER TABLE conversations 
                ADD COLUMN IF NOT EXISTS folder_id INTEGER REFERENCES folders(id) ON DELETE SET NULL;
            """))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_conversations_folder_id ON conversations(folder_id);"))
            print("[OK] 'folder_id' column added successfully.")
        except Exception as e:
            print(f"[WARN] Note: {e}")

    await engine.dispose()
    print("[OK] Migration complete!")

if __name__ == "__main__":
    try:
        asyncio.run(migrate())
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")

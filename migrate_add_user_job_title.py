#!/usr/bin/env python3
"""
Database migration: add job_title column to users.

Adds a constrained job_title column, backfills existing users to "Engineer",
and enforces allowed values (Doctor, Lawyer, Engineer, Accountant).

Usage:
    python migrate_add_user_job_title.py
    python migrate_add_user_job_title.py --rollback

Note: Do NOT run this in local dev here if you prefer running on the server.
"""

import asyncio
import sys
from sqlalchemy import text
from app.db.database import engine
from app.config import settings

ALLOWED_JOB_TITLES = ("Doctor", "Lawyer", "Engineer", "Accountant")

MIGRATION_SQLS = [
    # Add column if missing
    """
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS job_title VARCHAR(50);
    """,
    # Set default for new records
    """
    ALTER TABLE users
    ALTER COLUMN job_title SET DEFAULT 'Engineer';
    """,
    # Backfill existing records
    """
    UPDATE users
    SET job_title = 'Engineer'
    WHERE job_title IS NULL OR job_title = '';
    """,
    # Enforce not-null
    """
    ALTER TABLE users
    ALTER COLUMN job_title SET NOT NULL;
    """,
    # Add constraint to restrict allowed values
    f"""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.table_constraints tc
            WHERE tc.constraint_name = 'ck_users_job_title_valid'
              AND tc.table_name = 'users'
        ) THEN
            ALTER TABLE users
            ADD CONSTRAINT ck_users_job_title_valid
            CHECK (job_title IN {ALLOWED_JOB_TITLES!r});
        END IF;
    END $$;
    """,
    # Add column comment
    """
    COMMENT ON COLUMN users.job_title IS 'User-selected job title (Doctor, Lawyer, Engineer, Accountant)';
    """,
]

ROLLBACK_SQLS = [
    "ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_job_title_valid;",
    "ALTER TABLE users DROP COLUMN IF EXISTS job_title;",
]


async def run_migration():
    """Execute the forward migration."""
    print("🔄 Starting migration: add job_title to users")
    print(f"Database: {settings.DATABASE_URL}")
    print()

    try:
        async with engine.begin() as conn:
            for i, sql in enumerate(MIGRATION_SQLS, 1):
                print(f"  [{i}/{len(MIGRATION_SQLS)}] Executing...")
                await conn.execute(text(sql))

        print()
        print("✅ SUCCESS: job_title column added/updated and existing users set to 'Engineer'")
    except Exception as exc:
        print(f"❌ ERROR: migration failed: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


async def rollback_migration():
    """Rollback the migration (drop column/constraint)."""
    print("↩️  Rolling back migration: remove job_title from users")
    print(f"Database: {settings.DATABASE_URL}")
    print()

    try:
        async with engine.begin() as conn:
            for i, sql in enumerate(ROLLBACK_SQLS, 1):
                print(f"  [{i}/{len(ROLLBACK_SQLS)}] Executing rollback step...")
                await conn.execute(text(sql))

        print()
        print("✅ SUCCESS: rollback completed")
    except Exception as exc:
        print(f"❌ ERROR: rollback failed: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


async def verify_migration():
    """Verify column exists and values are constrained."""
    print("🔍 Verifying migration result...")
    try:
        async with engine.begin() as conn:
            # Check column presence
            result = await conn.execute(
                text(
                    """
                    SELECT column_name, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'users' AND column_name = 'job_title'
                    """
                )
            )
            column = result.fetchone()

            if not column:
                print("❌ job_title column is missing")
                sys.exit(1)

            print(f"  Column found: job_title (nullable={column.is_nullable}, default={column.column_default})")

            # Show value distribution (helps confirm backfill)
            result = await conn.execute(
                text(
                    """
                    SELECT job_title, COUNT(*) as count
                    FROM users
                    GROUP BY job_title
                    ORDER BY count DESC
                    """
                )
            )
            rows = result.fetchall()
            for job_title, count in rows:
                print(f"  {job_title}: {count}")

            # Check constraint presence
            result = await conn.execute(
                text(
                    """
                    SELECT constraint_name
                    FROM information_schema.table_constraints
                    WHERE table_name = 'users' AND constraint_name = 'ck_users_job_title_valid'
                    """
                )
            )
            if result.fetchone():
                print("  Constraint ck_users_job_title_valid is present ✅")
            else:
                print("  Constraint ck_users_job_title_valid is MISSING ⚠️")

        print("Verification finished.")
    except Exception as exc:
        print(f"❌ ERROR: verification failed: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


async def main():
    """Main entrypoint for migration/rollback."""
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        await rollback_migration()
    else:
        await run_migration()
        await verify_migration()


if __name__ == "__main__":
    asyncio.run(main())


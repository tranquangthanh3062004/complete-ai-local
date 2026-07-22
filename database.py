"""
Database engine, session, va initialization.
Dung SQLite async — khong can cai server rieng.
Dung bcrypt truc tiep (khong passlib) cho Python 3.13+.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from config import settings
import bcrypt

# ── Async Engine ──────────────────────────────────────────────────────────────
is_sqlite = settings.database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

import os
import logging
if is_sqlite and os.environ.get("VERCEL"):
    logging.warning("CRITICAL WARNING: You are running SQLite on Vercel (Serverless). All database changes will be lost after the request ends! Please configure a PostgreSQL database (e.g. Supabase) via the DATABASE_URL environment variable.")

# Connection pooling optimizations for production
engine_kwargs = {
    "echo": False,
    "connect_args": connect_args,
}

if not is_sqlite:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

async_engine = create_async_engine(
    settings.database_url,
    **engine_kwargs
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Dependency cho FastAPI ────────────────────────────────────────────────────
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Tao bang ─────────────────────────────────────────────────────────────────
async def create_tables():
    from models import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables ready.")


# ── Seed admin mac dinh ───────────────────────────────────────────────────────
async def seed_superuser():
    from models import User
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == "admin@local.com")
        )
        if result.scalar_one_or_none() is None:
            import os
            admin_pass = os.environ.get("ADMIN_PASSWORD")
            if not admin_pass:
                print("Skipping admin seed: ADMIN_PASSWORD not set in environment.")
                return
            salt   = bcrypt.gensalt()
            hashed = bcrypt.hashpw(admin_pass.encode("utf-8"), salt).decode("utf-8")
            admin  = User(
                email           = "admin@local.com",
                hashed_password = hashed,
                display_name    = "Admin",
                is_active       = True,
                is_superuser    = True,
                role            = "admin",
            )
            db.add(admin)
            await db.commit()
            print("Seeded admin: admin@local.com / admin123")
        else:
            print("Admin already exists.")

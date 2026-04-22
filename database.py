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
async_engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
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
            salt   = bcrypt.gensalt()
            hashed = bcrypt.hashpw(b"admin123", salt).decode("utf-8")
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

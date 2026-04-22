"""
Auth router — JWT authentication thuan, dung bcrypt truc tiep (khong passlib).
Tuong thich Python 3.13+
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from typing import Optional
from pydantic import BaseModel
from config import settings
from database import get_db
from models import User
from datetime import datetime, timedelta, timezone
import bcrypt

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY     = settings.secret_key
ALGORITHM      = "HS256"
EXPIRE_MINUTES = settings.access_token_expire_minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


# ── Schemas ───────────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email       : str
    password    : str
    display_name: str = ""
    role        : str = "user"


class UserOut(BaseModel):
    id          : int
    email       : str
    display_name: str
    role        : str
    is_active   : bool
    is_superuser: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type  : str


# ── Password helpers (bcrypt truc tiep, khong passlib) ───────────────────────
def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def hash_password(password: str) -> str:
    salt   = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


# ── JWT helpers ───────────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire    = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=15)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ── Dependency ────────────────────────────────────────────────────────────────
async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db   : AsyncSession  = Depends(get_db),
) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            return None
    except JWTError:
        return None
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def require_user(user: Optional[User] = Depends(get_current_user)) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vui long dang nhap",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/register", response_model=UserOut)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == user_data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email da duoc dang ky")

    db_user = User(
        email           = user_data.email,
        hashed_password = hash_password(user_data.password),
        display_name    = user_data.display_name or user_data.email.split("@")[0],
        role            = user_data.role,
        is_active       = True,
        is_superuser    = (user_data.role == "admin"),
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db       : AsyncSession              = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user   = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoac mat khau khong dung",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Tai khoan bi khoa")

    token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=EXPIRE_MINUTES),
    )
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(require_user)):
    return current_user

from datetime import datetime, timedelta, timezone
from typing import Optional

import aiosqlite
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from config import settings
from db import get_db


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: aiosqlite.Connection = Depends(get_db),
):
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise credentials_error
    except JWTError as exc:
        raise credentials_error from exc

    cursor = await db.execute(
        "SELECT id, username, email, is_active FROM users WHERE username = ?",
        (username,),
    )
    user = await cursor.fetchone()
    if not user or not user["is_active"]:
        raise credentials_error
    return dict(user)


async def get_optional_current_admin(
    token: str | None = Depends(OAuth2PasswordBearer(tokenUrl="/api/admin/login", auto_error=False)),
    db: aiosqlite.Connection = Depends(get_db),
):
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if not username:
            return None
    except JWTError:
        return None

    cursor = await db.execute(
        "SELECT id, username, email, is_active FROM users WHERE username = ?",
        (username,),
    )
    user = await cursor.fetchone()
    if not user or not user["is_active"]:
        return None
    return dict(user)

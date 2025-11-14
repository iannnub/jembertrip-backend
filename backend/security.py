# backend/security.py

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Annotated # <-- 1. Import 'Annotated'

from dotenv import load_dotenv
from pathlib import Path

from passlib.context import CryptContext
from jose import JWTError, jwt, ExpiredSignatureError # <-- 2. Import 'ExpiredSignatureError'
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# Import file-file yang akan kita buat/gunakan
import crud 
import models 
import schemas 
from database import get_db 

logger = logging.getLogger(__name__)

# --- 1. Konfigurasi Keamanan (dari .env) ---

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# 🔥 3. PERBAIKAN: Validasi SECRET_KEY (Review Poin 5)
if not SECRET_KEY or len(SECRET_KEY) < 32:
    logger.critical("FATAL: SECRET_KEY tidak aman atau terlalu pendek (minimal 32 karakter).")
    raise ValueError("SECRET_KEY tidak aman atau terlalu pendek (minimal 32 karakter).")

# --- 2. Konfigurasi Password Hashing (passlib) ---

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Memverifikasi password polos dengan password yang sudah di-hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Meng-hash password polos."""
    return pwd_context.hash(password)

# --- 3. Logika Pembuatan JWT (Tiket Login) ---

# 🔥 4. PERBAIKAN: Helper UTC (Review Poin 3)
def utcnow() -> datetime:
    """Mengembalikan datetime.now() dengan timezone UTC."""
    return datetime.now(timezone.utc)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Membuat JWT access token baru."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = utcnow() + expires_delta
    else:
        expire = utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 🔥 5. PERBAIKAN: Helper Format Token (Review Poin 4)
def format_access_token(token: str) -> dict:
    """Mengemas token ke format standar OAuth2."""
    return {"access_token": token, "token_type": "bearer"}

# --- 4. Dependensi Proteksi Endpoint ---

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# 🔥 6. PERBAIKAN: Gunakan 'Annotated' (Review Poin 7)
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], 
    db: Annotated[Session, Depends(get_db)]
) -> models.User:
    """
    Dependency FastAPI untuk memproteksi endpoint.
    Membaca token, memvalidasinya, dan mengembalikan data user dari DB.
    
    Jika token tidak valid, akan otomatis me-raise HTTPException 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 🔥 7. PERBAIKAN: Error Handling Spesifik (Review Poin 2)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Token JWT tidak valid: 'sub' (username) tidak ditemukan.")
            raise credentials_exception
            
        token_data = schemas.TokenData(username=username)
    
    except ExpiredSignatureError:
        # Tangkap error jika token sudah kadaluarsa
        logger.warning("Token JWT sudah kadaluarsa.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sudah kadaluarsa",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        # Tangkap semua error JWT lainnya
        logger.warning(f"Error decoding JWT: {e}")
        raise credentials_exception
    
    # (Review Poin 6: Logic CRUD ini sudah benar)
    user = crud.get_user_by_username(db, username=token_data.username)
    
    if user is None:
        logger.warning(f"Token valid, tapi user '{token_data.username}' tidak ditemukan di DB.")
        raise credentials_exception
        
    return user
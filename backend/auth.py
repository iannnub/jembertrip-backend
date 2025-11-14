# backend/auth.py

import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# Import semua 'perkakas' kita
import crud
import schemas
import security
import models
from database import get_db

logger = logging.getLogger(__name__)

# --- 1. Konfigurasi Router ---
router = APIRouter(
    prefix="/auth", # Semua endpoint di file ini akan diawali /auth
    tags=["Authentication"] # Grup di /docs
)

# --- 2. Siapkan Dependensi ---
DbDependency = Annotated[Session, Depends(get_db)]
FormDependency = Annotated[OAuth2PasswordRequestForm, Depends()]
# 🔥 1. TAMBAHKAN DEPENDENSI UNTUK 'GET_CURRENT_USER'
# (Sesuai Poin 4 review kamu, import 'get_current_user' dari security)
UserDependency = Annotated[models.User, Depends(security.get_current_user)]


# ======================================================
# 👤 ENDPOINT: REGISTER
# ======================================================
@router.post(
    "/register", 
    response_model=schemas.UserResponse, # (Ini sudah benar karena ada di schemas.py)
    status_code=status.HTTP_201_CREATED,
    summary="Registrasi User Baru"
)
async def register_user(
    user_create: schemas.UserCreate, 
    db: DbDependency
):
    """
    Membuat akun user baru.
    - Memvalidasi input (min 3 char, min 6 pass).
    - Mengecek jika username sudah ada.
    - Meng-hash password.
    - Menyimpan ke database.
    """
    try:
        # Panggil 'kurir' (crud) untuk membuat user
        # (crud.create_user sudah kita program untuk raise ValueError jika duplikat)
        db_user = crud.create_user(db, user=user_create)
        return db_user
    
    except ValueError as e:
        # (Ini adalah Poin 2 review kamu, sudah ter-handle!)
        # Tangkap 'ValueError' dari crud.py
        logger.warning(f"Gagal registrasi: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error internal saat registrasi: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Terjadi error internal saat registrasi.",
        )

# ======================================================
# 🔐 ENDPOINT: LOGIN & BUAT TOKEN
# ======================================================
@router.post(
    "/login", 
    response_model=schemas.Token, 
    summary="Login User & Dapatkan JWT Token"
)
async def login_for_access_token(
    form_data: FormDependency, # (username & password dari form)
    db: DbDependency
):
    """
    Mengotentikasi user dan mengembalikan JWT Token.
    Ini adalah 'tokenUrl' yang dipakai oleh OAuth2PasswordBearer.
    """
    # 1. Cek User
    # (crud.get_user_by_username sudah case-insensitive)
    user = crud.get_user_by_username(db, username=form_data.username)
    
    # 2. Cek Password
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Login gagal untuk user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Buat Token
    access_token = security.create_access_token(
        data={"sub": user.username}
    )
    
    # 4. Kembalikan Token (sudah pakai helper 'format_access_token')
    logger.info(f"Login sukses untuk user: {user.username}")
    return security.format_access_token(access_token)

# ======================================================
# 🙋‍♂️ ENDPOINT: GET CURRENT USER (Poin 4 Review Kamu)
# ======================================================
# 🔥 2. ENDPOINT BARU UNTUK TES TOKEN
@router.get(
    "/me", 
    response_model=schemas.UserResponse,
    summary="Cek User (Test Token)",
    description="Endpoint terproteksi. Mengembalikan data user yang sedang login berdasarkan token."
)
async def read_users_me(
    current_user: UserDependency # <-- Ini adalah 'Kunci Ajaib'-nya
):
    """
    Endpoint terproteksi untuk mendapatkan data user yang sedang login.
    
    Cara tes di /docs:
    1. Login dulu via /auth/login.
    2. Copy 'access_token' yang didapat.
    3. Klik tombol 'Authorize' (gembok) di kanan atas.
    4. Tulis 'Bearer' (spasi) (tempel token). Cth: Bearer eyJhbGci...
    5. Jalankan endpoint /auth/me ini.
    
    Jika berhasil, akan mengembalikan data user (ID & username).
    Jika token salah/kadaluarsa, akan mengembalikan error 401.
    """
    # 'current_user' adalah objek 'models.User' dari DB
    # 'schemas.UserResponse' akan otomatis memfilternya (hanya id & username)
    return current_user
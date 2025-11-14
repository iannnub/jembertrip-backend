# backend/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Union

# ======================================================
# 🧠 Base untuk ORM Compatibility
# ======================================================
class ORMBase(BaseModel):
    """
    Base class Pydantic yang mengaktifkan 'from_attributes'.
    Membuat model bisa membaca data langsung dari objek SQLAlchemy.
    """
    class Config:
        # 🔥 PERBAIKAN 1: Ganti 'orm_mode' (v1) jadi 'from_attributes' (v2)
        # Ini akan menghilangkan 'UserWarning' di terminal kamu
        from_attributes = True

# ======================================================
# 🎯 Skema untuk Recommender (v1.0)
# ======================================================
class RecommendationRequest(BaseModel):
    """
    Input body untuk endpoint /recommendations.
    """
    history_ids: List[Union[int, str]] = Field(default_factory=list, description="List ID item yang pernah diklik user.")
    query: Optional[str] = Field(None, description="Query pencarian teks bebas dari user.")

# ======================================================
# 👤 Skema untuk Fase 2 (Login & Register)
# ======================================================
class UserCreate(BaseModel):
    """
    Skema validasi untuk membuat user baru (/auth/register).
    """
    username: str = Field(..., min_length=3, max_length=20, description="Nama pengguna unik, 3-20 karakter.")
    
    # 🔥 PERBAIKAN 2 (FIX BUG 400): Tambahkan max_length=72
    # Ini adalah batasan keamanan dari 'bcrypt'
    password: str = Field(
        ..., 
        min_length=6, 
        max_length=72, # <-- PERBAIKAN KRUSIAL DI SINI
        description="Password minimal 6 karakter, maksimal 72 karakter."
    )

class UserLogin(BaseModel):
    """
    Skema validasi untuk login user (/auth/login).
    """
    username: str
    password: str

class Token(BaseModel):
    """
    Skema response yang dikembalikan saat login sukses.
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Skema data yang disimpan di dalam JWT token.
    """
    username: Optional[str] = None

class UserResponse(ORMBase):
    """
    Skema response aman untuk data user (tanpa password).
    """
    id: int
    username: str

# ======================================================
# 🧾 Skema untuk Click History (Fase 2)
# ======================================================
class ClickData(BaseModel):
    """
    Input body untuk endpoint /history/click.
    """
    item_id: int = Field(..., description="ID dari destinasi wisata yang diklik.")

class ClickResponse(ORMBase):
    """
    Skema response setelah klik berhasil disimpan.
    """
    id: int
    item_id: int
    user_id: int

# 🔥 TAMBAHAN BARU (UNTUK PERSONALISASI FEED)
class HistoryIDResponse(BaseModel):
    """
    Skema response ringkas untuk /history/my-ids.
    Hanya mengembalikan list unik dari item_id.
    """
    item_ids: List[int] = Field(default_factory=list, description="List unik dari item_id yang pernah diklik user.")
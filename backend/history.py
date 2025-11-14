# backend/history.py

import logging
from typing import Annotated, List
# 1. Import 'Query' untuk parameter dinamis
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session

# Import semua 'perkakas' kita
import crud
import schemas
import models
import security 
from database import get_db

logger = logging.getLogger(__name__)

# --- Konfigurasi Router ---
router = APIRouter(
    prefix="/api/v1/history", 
    tags=["User History"],    
    dependencies=[Depends(security.get_current_user)] 
)

# --- Siapkan Dependensi ---
DbDependency = Annotated[Session, Depends(get_db)]
UserDependency = Annotated[models.User, Depends(security.get_current_user)]

# ======================================================
# 🧾 ENDPOINT: REKAM KLIK
# ======================================================
@router.post(
    "/click", 
    response_model=schemas.ClickResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Merekam klik destinasi oleh user (Perlu Login)"
)
async def record_click(
    click_data: schemas.ClickData, 
    current_user: UserDependency,
    db: DbDependency
):
    """
    Merekam setiap kali user yang terotentikasi mengklik sebuah destinasi.
    Data ini akan dipakai untuk personalisasi RAG (Fase 4).
    """
    logger.info(f"🖱️ Merekam klik: User '{current_user.username}' -> Item ID {click_data.item_id}")
    return crud.create_click_history(db, click=click_data, user_id=current_user.id)

# ======================================================
# 👀 ENDPOINT: LIHAT HISTORY SENDIRI
# ======================================================
@router.get(
    "/me", 
    response_model=List[schemas.ClickResponse],
    summary="Melihat riwayat klik user sendiri (Perlu Login)"
)
async def read_own_history(
    current_user: UserDependency,
    db: DbDependency,
    
    # 🔥 PERBAIKAN: 'default=20' dipindah ke luar 'Query()'
    limit: Annotated[int, Query(ge=1, le=100)] = 20
):
    """
    Mengambil riwayat klik terakhir untuk user yang sedang login.
    - **limit**: Jumlah riwayat yang ingin diambil (default 20, max 100).
    """
    return crud.get_user_history(db, user_id=current_user.id, limit=limit)

# 🔥 TAMBAHAN BARU (UNTUK PERSONALISASI FEED)
@router.get(
    "/my-ids",
    response_model=schemas.HistoryIDResponse,
    summary="Mengambil daftar ID unik riwayat klik user (Efisien)"
)
async def read_own_history_ids(
    current_user: UserDependency,
    db: DbDependency
):
    """
    Mengambil daftar ID unik (distinct) dari semua item_id
    yang pernah diklik oleh user.
    
    Endpoint ini dioptimalkan untuk 'cold start' personalisasi
    di frontend, karena hanya mengirim list ID, bukan objek penuh.
    """
    # Panggil "Resep" baru kita dari crud.py
    id_list = crud.get_user_history_ids(db, user_id=current_user.id)
    
    # Kembalikan sesuai "Menu" baru kita dari schemas.py
    return schemas.HistoryIDResponse(item_ids=id_list)

# ======================================================
# 🗑️ ENDPOINT: HAPUS HISTORY SENDIRI
# ======================================================
@router.delete(
    "/me", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Menghapus semua riwayat klik user (Perlu Login)"
)
async def delete_own_history(
    current_user: UserDependency,
    db: DbDependency
):
    """
    Menghapus seluruh riwayat klik milik user yang sedang login.
    """
    logger.warning(f"🧹 User '{current_user.username}' menghapus seluruh riwayat kliknya.")
    
    crud.delete_user_history(db, user_id=current_user.id)
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
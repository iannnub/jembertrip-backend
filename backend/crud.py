# backend/crud.py

import logging
from sqlalchemy.orm import Session
from sqlalchemy import func # <-- 🔥 1. TAMBAHKAN IMPORT 'func'
from typing import List, Optional

# 1. Import 'models' (struktur DB) dan 'schemas' (validasi Pydantic)
import models
import schemas
# 2. Import 'security' (HANYA untuk hash password)
import security 

# Inisialisasi logger untuk modul ini
logger = logging.getLogger(__name__)

# ======================================================
# 👤 USER CRUD
# ======================================================

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """Mengambil satu user berdasarkan ID."""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """
    Mengambil satu user berdasarkan username (Case-Insensitive).
    (Profesional tweak: .ilike() digunakan untuk tidak mempedulikan besar/kecil)
    """
    return db.query(models.User).filter(models.User.username.ilike(username)).first()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """
    Membuat user baru di database.
    Termasuk hashing password dan validasi keunikan username.
    (Di-upgrade dengan Review Poin a)
    """
    # 🔥 PERBAIKAN (Review Poin a): Cek jika user sudah ada
    existing_user = get_user_by_username(db, user.username)
    if existing_user:
        # Kita raise ValueError di sini.
        # 'auth.py' nanti yang akan menangkap ini dan mengubahnya jadi HTTP 400
        raise ValueError(f"Username '{user.username}' sudah terdaftar.")
    
    # Panggil helper hashing dari 'security.py'
    hashed_password = security.get_password_hash(user.password)
    
    db_user = models.User(
        username=user.username, 
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # 🔥 PERBAIKAN (Review Poin b): Tambahkan logging
    logger.info(f"✅ User baru berhasil dibuat: {db_user.username} (ID: {db_user.id})")
    
    return db_user

def update_password(db: Session, user: models.User, new_password: str) -> models.User:
    """
    Meng-update password untuk user yang sudah ada.
    (Diambil dari Review Poin d)
    """
    user.hashed_password = security.get_password_hash(new_password)
    db.add(user) # (SQLAlchemy cukup pintar untuk tahu ini 'UPDATE')
    db.commit()
    db.refresh(user)
    logger.info(f"🔑 Password untuk user {user.username} berhasil di-update.")
    return user

# ======================================================
# 🧾 CLICK HISTORY CRUD
# ======================================================

def create_click_history(db: Session, click: schemas.ClickData, user_id: int) -> models.ClickHistory:
    """
    Menyimpan data 'klik' baru ke database,
    terhubung dengan 'user_id' yang spesifik.
    (Di-upgrade dengan Review Poin b)
    """
    # 🔥 PERBAIKAN (Review Poin b): Tambahkan logging
    logger.info(f"🖱️ Merekam klik: User ID {user_id} -> Item ID {click.item_id}")

    db_click = models.ClickHistory(
        item_id=click.item_id, 
        user_id=user_id
    )
    db.add(db_click)
    db.commit()
    db.refresh(db_click)
    return db_click

def get_user_history(db: Session, user_id: int, limit: int = 20) -> List[models.ClickHistory]:
    """
    Mengambil 'limit' item terakhir yang diklik oleh user.
    (Sangat penting untuk Fase 4: RAG)
    """
    return (
        db.query(models.ClickHistory)
        .filter(models.ClickHistory.user_id == user_id)
        .order_by(models.ClickHistory.timestamp.desc()) # Ambil yang terbaru
        .limit(limit)
        .all()
    )

# 🔥 2. TAMBAHKAN FUNGSI BARU (Resep Efisien)
def get_user_history_ids(db: Session, user_id: int) -> List[int]:
    """
    Mengambil list UNIK (DISTINCT) 'item_id' yang pernah diklik user.
    Query ini dioptimalkan untuk feed rekomendasi.
    """
    logger.info(f"Querying unique history IDs for User ID {user_id}")
    
    # Query: SELECT DISTINCT item_id 
    #        FROM click_history 
    #        WHERE user_id = :user_id
    #        GROUP BY item_id 
    #        ORDER BY MAX(timestamp) DESC;
    # (Ini query canggih: Ambil ID unik, urutkan berdasarkan kapan ID itu 
    #  TERAKHIR diklik. Jadi riwayat lo paling relevan/baru).
    query_result = (
        db.query(models.ClickHistory.item_id)
        .filter(models.ClickHistory.user_id == user_id)
        .group_by(models.ClickHistory.item_id)
        .order_by(func.max(models.ClickHistory.timestamp).desc())
        .all()
    )
    
    # Hasil 'query_result' itu kayak gini: [(11,), (4,), (22,)]
    # Kita harus "ratain" (flatten) jadi: [11, 4, 22]
    id_list = [item_id for (item_id,) in query_result]
    
    return id_list

def delete_user_history(db: Session, user_id: int) -> int:
    """
    Menghapus SEMUA riwayat klik untuk satu user.
    (Diambil dari Review Poin c)
    """
    num_deleted = (
        db.query(models.ClickHistory)
        .filter(models.ClickHistory.user_id == user_id)
        .delete(synchronize_session=False) # 'synchronize_session=False' lebih efisien
    )
    db.commit()
    
    if num_deleted > 0:
        logger.info(f"🧹 {num_deleted} riwayat klik dihapus untuk User ID {user_id}")
    
    return num_deleted
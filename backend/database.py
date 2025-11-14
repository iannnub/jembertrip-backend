# backend/database.py

import os
import logging
from pathlib import Path
from typing import Generator
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- Poin 2: Profesionalisasi dengan .env ---
# Memuat variabel dari file .env di root proyek
# (Path().resolve().parent.parent -> .../backend/ -> .../WISATA-RECOMMENDER/)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# --- Poin 1: Path Safety (Menggunakan Pathlib) ---
# Tentukan BASE_DIR (folder 'backend/')
BASE_DIR = Path(__file__).resolve().parent
# Tentukan URL default jika di .env tidak ada
DEFAULT_SQLITE_URL = f"sqlite:///{BASE_DIR}/jembertrip.db"

# Ambil DATABASE_URL dari .env, atau gunakan default SQLite
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)
IS_SQLITE = DATABASE_URL.startswith("sqlite")

logger = logging.getLogger(__name__)

# --- Poin 4: Tambahkan Pooling (Scalability) ---
connect_args = {"check_same_thread": False} if IS_SQLITE else {}

try:
    engine = create_engine(
        DATABASE_URL, 
        connect_args=connect_args,
        pool_size=10,
        max_overflow=20
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base = declarative_base()

    logger.info(f"✅ Koneksi database (Engine, SessionLocal, Base) berhasil dikonfigurasi ke {DATABASE_URL}.")

except Exception as e:
    logger.critical(f"❌ Gagal mengkonfigurasi database di {DATABASE_URL}: {e}", exc_info=True)
    raise

# --- Poin 5: Type Hint dan Docstring ---
def get_db() -> Generator[Session, None, None]:
    """
    Dependency FastAPI untuk mendapatkan sesi database.
    Ini memastikan sesi database (db) selalu ditutup setelah request selesai.

    Contoh penggunaan di endpoint:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Poin 3: Fungsi Utility init_db() ---
def init_db():
    """
    Membuat semua tabel di database berdasarkan 'Base' dari models.py.
    Fungsi ini aman untuk dijalankan berulang kali.
    """
    try:
        # 🔥 PERBAIKAN: Gunakan import absolut (import models)
        # BUKAN import relatif (from . import models)
        import models 
        
        Base.metadata.create_all(bind=engine)
        logger.info("📦 Semua tabel berhasil dibuat (jika belum ada).")
    except Exception as e:
        logger.error(f"❌ Gagal membuat tabel: {e}", exc_info=True)
        raise
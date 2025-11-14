# backend/main.py

import logging
import sys
import time
import auth
import history
from contextlib import asynccontextmanager
from pathlib import Path
# 🔥 1. PERBAIKAN: Tambahkan 'Request' di import ini
from fastapi import FastAPI, Request 
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer

# --- Import file router & database ---
import recommender_api 
# (Nanti kita tambah: import auth, import history)

# 🔥 1. IMPORT FUNGSI DATABASE
from database import init_db # <-- TAMBAHKAN IMPORT INI

# ======================================================
# 2. KONFIGURASI PATH & IMPORT (KRITICAL FIX)
# ======================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent 
SRC_PATH = PROJECT_ROOT / "src"
if not SRC_PATH.is_dir(): 
    logging.critical(f"FATAL: Folder 'src' tidak ditemukan di {SRC_PATH}")
    sys.exit(f"Folder 'src' tidak ditemukan. Pastikan struktur folder benar.")
    
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

try:
    from src.recommender import Recommender 
except ImportError as e:
    logging.critical(f"FATAL: Gagal mengimpor 'src.recommender.Recommender'. Error: {e}")
    sys.exit("Gagal memuat modul 'Recommender'.")

# --- Konfigurasi Lainnya ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

ASSETS_DIR_PATH = PROJECT_ROOT / "assets" / "images"

model_cache = {} 

# ======================================================
# 3. LOGIKA LOADING MODEL (Dengan Pemonitoran Waktu)
# ======================================================
def load_recommender():
    logger.info("⏳ Memuat Recommender (dari src.recommender)...")
    start_time = time.time()
    try:
        rec = Recommender() 
        assert not rec.df.empty, "Dataset (df) di dalam Recommender kosong"
        logger.info(f"✅ Berhasil memuat Recommender (data & embeddings) dalam {time.time() - start_time:.2f} detik.")
        return rec
    except Exception as e:
        logger.critical(f"❌ Gagal memuat Recommender: {e}", exc_info=True)
        return None

def load_bert_model():
    logger.info("⏳ Memuat model S-BERT (paraphrase-multilingual-MiniLM-L12-v2)...")
    start_time = time.time()
    try:
        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        logger.info(f"✅ Berhasil memuat model SentenceTransformer dalam {time.time() - start_time:.2f} detik.")
        return model
    except Exception as e:
        logger.critical(f"❌ Gagal memuat model BERT: {e}", exc_info=True)
        return None

# ======================================================
# 4. LIFESPAN (Menambahkan Config & init_db)
# ======================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Server startup...")
    
    # 🔥 2. BUAT TABEL DATABASE SAAT STARTUP
    # (Memanggil fungsi init_db() dari database.py)
    try:
        init_db()
    except Exception as e:
        logger.critical(f"❌ GAGAL MENGINISIALISASI DATABASE: {e}", exc_info=True)
        # (Opsional: sys.exit("Gagal init DB") jika DB wajib ada)
    
    # --- Load model AI ---
    model_cache["bert_model"] = load_bert_model()
    model_cache["recommender"] = load_recommender()
    
    model_cache["CATEGORY_BOOST"] = 0.5 
    
    app.state.model_cache = model_cache
    
    if not model_cache["bert_model"] or not model_cache["recommender"]:
        logger.critical("❌ Gagal memuat model atau data AI. Server mungkin tidak berfungsi.")
    else:
        logger.info("✅ Model AI & data berhasil dimuat ke 'app.state.model_cache'. Server siap!")
    
    yield
    
    logger.info("🛑 Server shutdown...")
    model_cache.clear()
    logger.info("🧹 Cache model dibersihkan.")

# ======================================================
# 5. INISIALISASI APLIKASI FASTAPI
# ======================================================
app = FastAPI(
    title="JemberTrip API (v2.0)",
    description="API untuk JemberTrip: Sistem Rekomendasi Wisata Jember Berbasis AI.",
    version="2.0.0",
    lifespan=lifespan,
    contact={
        "name": "iann (Developer)",
        "url": "https://github.com/iann", # (Ganti dengan URL kamu)
    },
)

# Pasang CORS Middleware
origins = [ 
    "http://localhost:3000",
    "http://localhost:5173",
    "https://jembertrip.vercel.app", 
    "https://jembertrip.netlify.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sajikan Gambar Statis
if ASSETS_DIR_PATH.is_dir():
    app.mount("/images", StaticFiles(directory=ASSETS_DIR_PATH), name="images")
    logger.info(f"✅ Berhasil me-mount folder statis '/images' dari {ASSETS_DIR_PATH}")
else:
    logger.warning(f"⚠️ Folder assets tidak ditemukan di {ASSETS_DIR_PATH}. Rute '/images' tidak akan aktif.")


# ======================================================
# 6. PASANG ROUTER (Modular)
# ======================================================
app.include_router(recommender_api.router)
app.include_router(auth.router)     # <-- Kode kamu sudah ada
app.include_router(history.router)  # <-- Kode kamu sudah ada
# (Komentar placeholder di bawah ini sekarang bisa dihapus)
# (Nanti kita tambah: import auth, import history)
# (Nanti kita tambah: app.include_router(auth.router))
# (Nanti kita tambah: app.include_router(history.router))

# ======================================================
# 7. ROOT ENDPOINT (Informatif)
# ======================================================
@app.get("/", tags=["Root"])
async def get_root(request: Request): # <-- 'Request' sudah di-import
    """
    Endpoint root untuk cek status API dan rute yang tersedia.
    """
    available_routes = [
        {
            "path": route.path, 
            "name": route.name,
            "methods": ", ".join(route.methods)
        } 
        for route in request.app.routes 
        if route.path.startswith("/api") or route.path.startswith("/auth") # Perbarui ini
    ]
    
    return {
        "message": "Welcome to JemberTrip API 🌴",
        "version": "2.0.0",
        "docs_url": "/docs",
        "status": "ok",
        "available_api_routes": available_routes
    }

# ======================================================
# 8. MENJALANKAN SERVER
# ======================================================
if __name__ == "__main__":
    import uvicorn
    # Jalankan uvicorn dari dalam folder backend
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
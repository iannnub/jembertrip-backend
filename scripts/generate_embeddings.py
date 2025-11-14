"""
======================================================
scripts/generate_embeddings.py
======================================================
MEMBUAT "OTAK" SEMANTIK V3.0

Tugas:
1. Memuat data yang sudah bersih dari 'data/processed/'.
2. Memuat model SentenceTransformer (dioptimalkan untuk kemiripan).
3. Mengubah 'fitur_bersih' dari setiap destinasi menjadi vektor embedding.
4. Menyimpan array embeddings ke 'models/bert_embeddings.pkl'.
======================================================
"""

import pandas as pd
import pickle
import logging
import time
from pathlib import Path
import sys

# Tambahkan path root proyek agar bisa impor 'src.utils'
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("="*50)
    print("ERROR: Library 'sentence-transformers' belum terinstal.")
    print("Silakan jalankan: pip install sentence-transformers")
    print("="*50)
    sys.exit(1)

# Mengimpor helper dari utils
from src.utils import save_pickle

# ===============================================
# 1️⃣ Konfigurasi Path & Logging
# ===============================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")

# ⭐ PERBAIKAN: Gunakan data yang sudah diproses
DATA_PATH = BASE_DIR / "data" / "processed" / "destinasi_processed.csv"
# ⭐ PERBAIKAN: Simpan model di folder 'models'
OUTPUT_PATH = BASE_DIR / "models" / "bert_embeddings.pkl"

# ⭐ PERBAIKAN: Gunakan model yang dioptimalkan untuk Sentence Similarity
MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'
# (Model ini akan diunduh otomatis ~471MB saat pertama kali dijalankan)

# ===============================================
# 2️⃣ Load Dataset Bersih
# ===============================================
logging.info(f"📦 Memuat dataset bersih dari: {DATA_PATH.name}")
try:
    df = pd.read_csv(DATA_PATH)
except FileNotFoundError:
    logging.error(f"❌ File tidak ditemukan di {DATA_PATH}.")
    logging.error("Pastikan Anda sudah menjalankan notebook '1_Data_Exploration.ipynb' terlebih dahulu.")
    sys.exit(1)

# Pastikan kolom 'fitur_bersih' ada dan tidak kosong
if "fitur_bersih" not in df.columns:
    raise ValueError("❌ Kolom 'fitur_bersih' tidak ditemukan di dataset!")
df['fitur_bersih'] = df['fitur_bersih'].fillna('')
logging.info(f"✅ Dataset berhasil dimuat. Jumlah data: {len(df)}")

# ===============================================
# 3️⃣ Load Model SentenceTransformer
# ===============================================
logging.info(f"🤖 Memuat model SentenceTransformer: '{MODEL_NAME}'...")
try:
    start_time = time.time()
    model = SentenceTransformer(MODEL_NAME)
    logging.info(f"✅ Model berhasil dimuat dalam {time.time() - start_time:.2f} detik")
except Exception as e:
    logging.error(f"❌ Gagal mengunduh/memuat model: {e}")
    logging.error("Pastikan Anda memiliki koneksi internet untuk mengunduh model.")
    sys.exit(1)

# ===============================================
# 4️⃣ Generate Embeddings
# ===============================================
logging.info("🧠 Mengonversi 'fitur_bersih' menjadi vektor embeddings...")

# ⭐ PERBAIKAN: Gunakan 'fitur_bersih' untuk mendapatkan makna semantik terkaya
corpus = df["fitur_bersih"].astype(str).tolist()

embeddings = model.encode(
    corpus,
    show_progress_bar=True,
    convert_to_numpy=True
)
logging.info(f"✅ Embedding selesai. Shape: {embeddings.shape}")

# ===============================================
# 5️⃣ Simpan Embeddings (Hanya Vektornya)
# ===============================================
# ⭐ PERBAIKAN: Kita hanya perlu menyimpan array numpy-nya.
# Data 'nama_wisata' akan kita dapatkan dari file CSV di recommender.py
save_pickle(embeddings, OUTPUT_PATH)
logging.info("🎉 Proses selesai — Embeddings V3.0 siap digunakan!")
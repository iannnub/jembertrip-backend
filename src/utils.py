# src/utils.py (Final Professional Version with Centralized Path)

import re
import pickle
import logging
import os
from pathlib import Path
from typing import Any

# ======================================================
# 1️⃣ KONFIGURASI LOGGING
# ======================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s"
)

# ======================================================
# 2️⃣ FUNGSI PATH HELPER
# ======================================================
def get_base_dir() -> Path:
    """
    Mengembalikan path direktori utama (root) proyek.
    Digunakan agar path tetap konsisten di semua modul.
    """
    # Path(__file__) adalah path ke file ini (src/utils.py)
    # .parent adalah folder 'src'
    # .parent lagi adalah folder utama proyek
    return Path(__file__).resolve().parent.parent

# ======================================================
# 3️⃣ FUNGSI PEMROSESAN TEKS
# ======================================================
def clean_text(text: str) -> str:
    """
    Membersihkan teks: mengubah ke huruf kecil, menghapus karakter
    non-alfabet, dan spasi berlebih.
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def truncate_text(text: str, max_length: int = 200) -> str:
    """
    Memotong teks agar tidak terlalu panjang untuk ditampilkan di UI,
    dan memastikan tidak memotong di tengah kata.
    """
    if not isinstance(text, str) or len(text) <= max_length:
        return text
    truncated = text[:max_length].rsplit(' ', 1)[0]
    logging.debug(f"✂️ Teks dipotong menjadi {len(truncated)} karakter.")
    return truncated + "..."

# ======================================================
# 4️⃣ FUNGSI PENANGANAN FILE (MODEL I/O)
# ======================================================
def save_pickle(data: Any, file_path: Path) -> None:
    """
    Menyimpan objek Python ke dalam file pickle.
    Secara otomatis akan membuat direktori jika belum ada.
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            pickle.dump(data, f)
        logging.info(f"💾 Objek berhasil disimpan ke: {file_path}")
    except Exception as e:
        logging.error(f"❌ Gagal menyimpan file pickle di {file_path}: {e}")
        raise

def load_pickle(file_path: Path) -> Any:
    """
    Memuat objek Python dari file pickle.
    """
    try:
        if not file_path.exists():
            raise FileNotFoundError(f"File tidak ditemukan di {file_path}")
        with open(file_path, "rb") as f:
            data = pickle.load(f)
            logging.info(f"✅ Objek berhasil dimuat dari: {file_path}")
            return data
    except FileNotFoundError as e:
        logging.error(f"❌ {e}. Pastikan path sudah benar dan model sudah dibuat.")
        raise
    except Exception as e:
        logging.error(f"❌ Gagal memuat file pickle dari {file_path}: {e}")
        raise

# ======================================================
# 5️⃣ FUNGSI UTAMA (UNTUK PENGUJIAN CEPAT)
# ======================================================
if __name__ == "__main__":
    """
    Blok ini hanya akan berjalan jika file ini dieksekusi secara langsung.
    Berguna untuk menguji semua fungsi di atas.
    """
    print("--- Menguji fungsi get_base_dir ---")
    BASE_DIR = get_base_dir()
    print(f"Direktori utama proyek: {BASE_DIR}")
    
    print("\n--- Menguji fungsi clean_text ---")
    sample_text = "Ini adalah Contoh Teks, dengan Tanda Baca! & Angka 123."
    print(f"Asli: '{sample_text}'")
    print(f"Bersih: '{clean_text(sample_text)}'")
    
    print("\n--- Menguji fungsi truncate_text ---")
    long_text = "Ini adalah deskripsi yang sangat panjang tentang sebuah tempat wisata yang indah dan menawan."
    print(f"Asli: '{long_text}'")
    print(f"Dipotong (30 karakter): '{truncate_text(long_text, 30)}'")
    
    print("\n--- Menguji fungsi save_pickle dan load_pickle ---")
    dummy_data = {"project": "wisata-recommender"}
    dummy_path = BASE_DIR / "temp_test_object.pkl"
    save_pickle(dummy_data, dummy_path)
    loaded_data = load_pickle(dummy_path)
    print(f"Data asli: {dummy_data}")
    print(f"Data yang dimuat: {loaded_data}")
    
    if dummy_path.exists():
        os.remove(dummy_path)
        print("\nFile tes sementara telah dihapus.")
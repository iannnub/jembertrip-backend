import pandas as pd
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
import time
import logging
from pathlib import Path # <-- 1. IMPORT LIBRARY PATHING

# --- 1. KONFIGURASI ---
# Kredensial ini sudah diisi sesuai data kamu
SUPABASE_URL = "https://jhfdnlemlkqrjfvgginc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpoZmRubGVtbGtxcmpmdmdnaW5jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzExMTE2NiwiZXhwIjoyMDc4Njg3MTY2fQ.Xg3owL48zkNGAhDQZY36eLkZyDnA8uJJy8yDEJ-86io" 

# --- Pathing Cerdas (PERUBAHAN DI SINI) ---
# Mendeteksi lokasi folder tempat script 'ingest.py' ini berada
SCRIPT_DIR = Path(__file__).resolve().parent
# Membuat path absolut ke file CSV kamu berdasarkan struktur folder kamu
CSV_FILE_PATH = SCRIPT_DIR / "data" / "processed" / "destinasi_processed.csv"

TABLE_NAME = "destinasi"
MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2' # Model S-BERT 384-dimensi

# Setup logging dasar
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 2. FUNGSI UTAMA ---

def load_model():
    """Memuat model Sentence Transformer dari cache atau men-download-nya."""
    logger.info(f"⏳ Memuat model AI: {MODEL_NAME}...")
    try:
        model = SentenceTransformer(MODEL_NAME)
        logger.info("✅ Model AI berhasil dimuat.")
        return model
    except Exception as e:
        logger.critical(f"❌ Gagal memuat model AI: {e}", exc_info=True)
        return None

def connect_supabase():
    """Membuat koneksi ke Supabase."""
    logger.info("Menghubungkan ke Supabase...")
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Berhasil terhubung ke Supabase.")
        return supabase
    except Exception as e:
        logger.critical(f"❌ Gagal terhubung ke Supabase: {e}", exc_info=True)
        return None

def load_and_process_data(model, file_path):
    """Membaca CSV, membuat embedding, dan menyiapkan data."""
    logger.info(f"Membaca file CSV dari: {file_path}") # Path ini sekarang sudah absolut
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Ditemukan {len(df)} baris data.")
        
        columns_to_keep = ['id', 'nama_wisata', 'kategori', 'kota', 'alamat', 'deskripsi', 'gambar']
        
        if 'fitur_bersih' not in df.columns or not all(col in df.columns for col in columns_to_keep):
            logger.critical("❌ CSV tidak memiliki kolom 'fitur_bersih' atau kolom wajib lainnya.")
            return None

        logger.info("Memulai proses encoding (vectorizing)... Ini mungkin butuh waktu.")
        
        df['embedding'] = df['fitur_bersih'].apply(lambda x: model.encode(x).tolist())
        
        logger.info("✅ Encoding selesai.")
        
        data_to_upload = df[columns_to_keep + ['embedding']].to_dict(orient='records')
        
        for item in data_to_upload:
            item['id'] = int(item['id'])
        
        return data_to_upload

    except FileNotFoundError:
        logger.critical(f"❌ File CSV tidak ditemukan di: {file_path}. Cek struktur folder!")
        return None
    except Exception as e:
        logger.critical(f"❌ Gagal memproses data CSV: {e}", exc_info=True)
        return None

def ingest_data(supabase, data):
    """Meng-upload data ke tabel Supabase."""
    if not data:
        logger.warning("Tidak ada data untuk di-upload.")
        return

    logger.info(f"Mulai meng-upload {len(data)} baris ke tabel '{TABLE_NAME}'...")
    
    try:
        response = supabase.table(TABLE_NAME).insert(data).execute()
        
        if response.data:
            logger.info(f"✅ Berhasil meng-upload {len(response.data)} baris data.")
        else:
            logger.error(f"⚠️ Respon Supabase kosong. Cek error (jika ada): {response.error}")

    except Exception as e:
        logger.critical(f"❌ Gagal meng-upload data ke Supabase: {e}", exc_info=True)

# --- 3. EKSEKUSI SCRIPT ---
if __name__ == "__main__":
    start_time = time.time()
    logger.info("🚀 Memulai script ingesti JemberTrip...")
    
    model = load_model()
    supabase = connect_supabase()
    
    if model and supabase:
        # Gunakan variabel CSV_FILE_PATH yang sudah 'pintar'
        data_to_upload = load_and_process_data(model, CSV_FILE_PATH) 
        if data_to_upload:
            ingest_data(supabase, data_to_upload)
            
    end_time = time.time()
    logger.info(f"🏁 Script selesai dalam {end_time - start_time:.2f} detik.")
"""
======================================================
RECOMMENDER ENGINE — Sistem Rekomendasi Wisata Jember
======================================================

Versi: 5.0 (Professional Refactor)
- Menggunakan dataclass untuk manajemen path yang bersih.
- Peningkatan pada type hinting dan struktur error handling.
- Menambahkan konstanta untuk kolom DataFrame (best practice).
- Logika komputasi on-the-fly untuk matriks BERT dipertahankan
  dengan logging yang lebih jelas.
"""

# ======================================================
# 1️⃣ IMPORT LIBRARY
# ======================================================
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Literal, Dict, List
from dataclasses import dataclass, field
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

# Mengimpor fungsi helper dari modul utils
from .utils import load_pickle, get_base_dir, save_pickle

# ======================================================
# 2️⃣ KONFIGURASI & SETUP
# ======================================================

# Inisialisasi logger untuk modul ini
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class ModelPaths:
    """
    Dataclass untuk mengelola semua path file model.
    Membuat konfigurasi menjadi terpusat dan mudah diubah.
    """
    base_dir: Path = field(default_factory=get_base_dir)
    data: Path = field(init=False)
    tfidf_sim: Path = field(init=False)
    hybrid_sim: Path = field(init=False)
    bert_embed: Path = field(init=False)
    bert_sim: Path = field(init=False)

    def __post_init__(self):
        # Menggunakan object mutation karena frozen=True
        object.__setattr__(self, 'data', self.base_dir / "data" / "processed" / "destinasi_processed.csv")
        object.__setattr__(self, 'tfidf_sim', self.base_dir / "models" / "similarity_matrix.pkl")
        object.__setattr__(self, 'hybrid_sim', self.base_dir / "models" / "hybrid_similarity.pkl")
        object.__setattr__(self, 'bert_embed', self.base_dir / "models" / "bert_embeddings.pkl")
        object.__setattr__(self, 'bert_sim', self.base_dir / "models" / "bert_similarity.pkl")


class Recommender:
    """
    Engine rekomendasi yang memuat data dan matriks kemiripan
    saat inisialisasi untuk penyajian rekomendasi yang cepat dan efisien.
    """
    # Konstanta untuk kolom yang sering digunakan
    RECOMMENDATION_COLS = ['id', 'nama_wisata', 'kategori', 'alamat', 'deskripsi', 'gambar']
    SEARCH_COLS = ['id', 'nama_wisata', 'kategori']

    def __init__(self, paths: ModelPaths = ModelPaths()):
        self.paths = paths
        self.df: pd.DataFrame | None = None
        self.embeddings: np.ndarray | None = None
        self.similarity_matrices: Dict[str, np.ndarray | None] = {
            "tfidf": None, "hybrid": None, "bert": None
        }
        self.is_loaded = False
        self.load()

    def load(self) -> None:
        """
        Memuat dataset utama dan semua matriks kemiripan ke dalam memori.
        Jika matriks kemiripan BERT tidak ada, akan dihitung secara on-the-fly.
        """
        if self.is_loaded:
            logger.info("Recommender sudah dimuat sebelumnya.")
            return
        
        try:
            logger.info("📦 Memulai pemuatan semua artefak model...")
            self._load_dataset()
            self._load_similarity_matrices()
            self._load_or_compute_bert_artifacts()
            
            self.is_loaded = True
            logger.info("🎉 Semua artefak model berhasil dimuat ke memori.")

        except FileNotFoundError as e:
            logger.error(f"❌ File tidak ditemukan: {e}", exc_info=True)
            raise  # Re-raise error untuk menghentikan aplikasi jika file kritis hilang
        except Exception as e:
            logger.error(f"❌ Gagal memuat artefak secara keseluruhan: {e}", exc_info=True)
            raise

    def _load_dataset(self):
        """Memuat dan memproses dataset destinasi."""
        if not self.paths.data.exists():
            raise FileNotFoundError(f"Dataset tidak ditemukan di {self.paths.data}")
        self.df = pd.read_csv(self.paths.data)
        self.df['fitur_bersih'] = self.df['fitur_bersih'].fillna('')
        logger.info(f"✅ Dataset berhasil dimuat ({len(self.df)} baris).")

    def _load_similarity_matrices(self):
        """Memuat matriks kemiripan TF-IDF dan Hybrid."""
        self.similarity_matrices["tfidf"] = load_pickle(self.paths.tfidf_sim)
        self.similarity_matrices["hybrid"] = load_pickle(self.paths.hybrid_sim)
        if self.similarity_matrices["tfidf"] is None or self.similarity_matrices["hybrid"] is None:
            raise FileNotFoundError("Matriks TF-IDF atau Hybrid gagal dimuat.")
        logger.info("✅ Matriks TF-IDF (V1) & Hybrid (V2) berhasil dimuat.")

    def _load_or_compute_bert_artifacts(self):
        """Memuat matriks BERT atau menghitungnya jika tidak ada."""
        if self.paths.bert_sim.exists():
            self.similarity_matrices["bert"] = load_pickle(self.paths.bert_sim)
            logger.info("✅ Matriks kemiripan BERT (V3) berhasil dimuat dari cache.")
            # Load embeddings juga untuk app.py
            if self.paths.bert_embed.exists():
                self.embeddings = load_pickle(self.paths.bert_embed)
            else:
                 logger.warning("File embedding BERT tidak ada, pencarian semantik mungkin tidak akurat.")

        elif self.paths.bert_embed.exists():
            logger.warning(f"⚠️ Matriks '{self.paths.bert_sim.name}' tidak ditemukan. Menghitung dari embeddings...")
            self.embeddings = load_pickle(self.paths.bert_embed)
            if self.embeddings is None:
                 raise ValueError("Gagal memuat file embeddings BERT.")
            
            # Normalisasi penting sebelum cosine similarity untuk efisiensi & akurasi
            normalized_embeddings = normalize(self.embeddings)
            self.similarity_matrices["bert"] = cosine_similarity(normalized_embeddings)
            
            save_pickle(self.similarity_matrices["bert"], self.paths.bert_sim)
            logger.info(f"✅ Matriks kemiripan BERT (V3) berhasil dibuat dan disimpan di {self.paths.bert_sim}")
        else:
            logger.warning("⚠️ Embeddings & similarity matrix BERT tidak ditemukan. Mode 'bert' tidak akan tersedia.")
    
    @property
    def destinations(self) -> List[str]:
        """Properti untuk mendapatkan daftar semua nama destinasi."""
        if not self.is_loaded or self.df is None:
            return []
        return self.df['nama_wisata'].tolist()
        
    def get_recommendations(self, nama_wisata: str, top_n: int = 5, mode: Literal["tfidf", "hybrid", "bert"] = "bert") -> pd.DataFrame:
        """
        Mengambil N rekomendasi destinasi wisata paling mirip.

        Args:
            nama_wisata: Nama wisata referensi.
            top_n: Jumlah rekomendasi yang diinginkan.
            mode: Tipe model ('tfidf', 'hybrid', 'bert'). Default ke 'bert'.

        Returns:
            DataFrame pandas berisi rekomendasi.
        """
        if not self.is_loaded or self.df is None:
            raise RuntimeError("Recommender belum dimuat. Jalankan .load() terlebih dahulu.")
        
        mode = mode.lower()
        if nama_wisata not in self.df['nama_wisata'].values:
            raise ValueError(f"Wisata '{nama_wisata}' tidak ditemukan dalam dataset.")
        
        matrix = self.similarity_matrices.get(mode)
        if matrix is None:
            raise ValueError(f"Mode '{mode}' tidak valid atau matriksnya gagal dimuat.")
            
        idx_ref = self.df.index[self.df['nama_wisata'] == nama_wisata].item()
        sim_scores = list(enumerate(matrix[idx_ref]))
        
        # Mengurutkan berdasarkan skor kemiripan
        sorted_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        # Mengambil top_n+1 untuk mengabaikan item itu sendiri
        top_indices = [i[0] for i in sorted_scores[1:top_n + 1]]
        top_scores = [i[1] for i in sorted_scores[1:top_n + 1]]
        
        rekomendasi_df = self.df.iloc[top_indices][self.RECOMMENDATION_COLS].copy()
        rekomendasi_df['skor_kemiripan'] = np.round(top_scores, 3)
        rekomendasi_df['mode_rekomendasi'] = mode.upper()
        
        return rekomendasi_df

# ======================================================
# 4️⃣ FUNGSI TEST MANDIRI
# ======================================================
if __name__ == "__main__":
    """
    Blok ini hanya akan berjalan jika file ini dieksekusi secara langsung.
    Cara menjalankan dari root folder: python -m src.recommender
    """
    logging.basicConfig(level=logging.INFO)
    try:
        recommender = Recommender()
        nama_ref = "Pantai Papuma" # Pastikan nama ini ada di CSV Anda

        if nama_ref not in recommender.destinations:
            print(f"Nama referensi '{nama_ref}' tidak ada. Menggunakan item pertama: '{recommender.destinations[0]}'")
            nama_ref = recommender.destinations[0]

        logging.info(f"\n🎯 V1.0 TF-IDF Recommendations for '{nama_ref}':")
        tfidf_recs = recommender.get_recommendations(nama_ref, 3, mode="tfidf")
        print(tfidf_recs[['nama_wisata', 'skor_kemiripan']].to_string(index=False))

        logging.info(f"\n🎯 V2.0 HYBRID Recommendations for '{nama_ref}':")
        hybrid_recs = recommender.get_recommendations(nama_ref, 3, mode="hybrid")
        print(hybrid_recs[['nama_wisata', 'skor_kemiripan']].to_string(index=False))

        if recommender.similarity_matrices["bert"] is not None:
            logging.info(f"\n🎯 V3.0 BERT Recommendations for '{nama_ref}':")
            bert_recs = recommender.get_recommendations(nama_ref, 3, mode="bert")
            print(bert_recs[['nama_wisata', 'skor_kemiripan']].to_string(index=False))
        else:
            logging.warning("\n⚠️ Mode BERT dilewati karena model tidak tersedia.")

    except Exception as e:
        logging.error(f"❌ Terjadi kesalahan saat pengujian: {e}", exc_info=True)

# backend/recommender_api.py

import logging
from fastapi import APIRouter, Request, HTTPException
from typing import List
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np

# 1. Import 'cetakan' Pydantic dari file schemas.py
# (Kita juga butuh 'List' dari typing untuk response_model)
from schemas import RecommendationRequest 

# 2. Buat 'Router'. Ini seperti 'mini-FastAPI'
router = APIRouter(
    prefix="/api/v1",  # Tambahkan prefix di sini agar endpoint lebih rapi
    tags=["Recommender"] # Kelompokkan di /docs
)
logger = logging.getLogger(__name__)

# ======================================================
# LOGIKA INTI (Dipindah dari main.py)
# ======================================================

def get_semantic_search_logic(query: str, recommender: object, bert_model: SentenceTransformer, top_k: int = None):
    """
    Logika murni untuk semantic search.
    (Review Poin 2: Normalisasi opsional bisa ditambah di sini jika perlu)
    """
    if not query: return pd.DataFrame() # Defensive check awal
    
    query_vec = bert_model.encode([query], show_progress_bar=False)
    sim_scores = cosine_similarity(query_vec, recommender.embeddings)[0]

    # (Opsional: Normalisasi skor 0-1)
    # sim_scores = (sim_scores - sim_scores.min()) / (sim_scores.max() - sim_scores.min() + 1e-9)

    if top_k is None: top_k = len(recommender.df)
    
    idx = np.argsort(sim_scores)[::-1][:top_k]
    df_results = recommender.df.iloc[idx].copy()
    df_results["skor_kemiripan"] = np.round(sim_scores[idx], 3)
    return df_results

def get_personalized_feed_logic(
    history: List[str], 
    recommender: object, 
    request: Request, # 🔥 1. Terima 'request'
    top_n: int = 9
):
    """
    Logika murni untuk feed personalisasi dengan category boost.
    """
    df = recommender.df
    
    # 🔥 2. Ambil 'BOOST' dari config di app.state (Review Poin 3)
    # (Kita akan set 'CATEGORY_BOOST' di main.py nanti)
    try:
        BOOST = float(request.app.state.model_cache.get("CATEGORY_BOOST", 0.5))
    except Exception:
        BOOST = 0.5
    
    if not history:
        results = df.sample(top_n, random_state=42)
        title = "✨ Jelajahi Destinasi Populer di Jember"
        return results, title
    try:
        idx_hist = [df.index[df["nama_wisata"] == nama].item() for nama in history if nama in df['nama_wisata'].values]
        if not idx_hist:
            logger.warning("Riwayat klik tidak valid, kembali ke cold start.")
            return get_personalized_feed_logic([], recommender, request, top_n) # Pass 'request'
        
        hist_vec = recommender.embeddings[idx_hist]
        user_vec = np.mean(hist_vec, axis=0).reshape(1, -1)
        sim_scores = cosine_similarity(user_vec, recommender.embeddings)[0]
        
        clicked_cats = df.loc[idx_hist, "kategori"]
        top_cat = clicked_cats.value_counts().idxmax()
        
        # Gunakan BOOST yang sudah configurable
        mask = (df["kategori"] == top_cat)
        sim_scores[mask] += BOOST 
        
        idx = sim_scores.argsort()[::-1]
        df_sorted = df.iloc[idx]
        final_df = df_sorted[~df_sorted["nama_wisata"].isin(history)]
        results = final_df.head(top_n)
        title = f"🔥 Karena Anda Suka Kategori '{top_cat}'"
        return results, title
    except Exception as e:
        logger.error(f"Gagal memproses feed personalisasi: {e}", exc_info=True)
        results = df.sample(top_n, random_state=42)
        title = "✨ Jelajahi Destinasi Populer di Jember"
        return results, title

# ======================================================
# API ENDPOINTS (Di-upgrade dengan Review Profesional)
# ======================================================

# 🔥 3. Tambahkan response_model, summary, dll. (Review Poin 4 & 6)
@router.get(
    "/destinations/all", 
    response_model=List[dict], # Tentukan tipe data balikan
    summary="Dapatkan Semua Destinasi",
    description="Mengambil *seluruh* daftar destinasi wisata yang ada di database."
)
async def get_all_destinations(request: Request):
    recommender = request.app.state.model_cache.get("recommender")
    if not recommender:
        raise HTTPException(status_code=503, detail="Server sedang inisialisasi, data belum siap.")
    
    # .to_dict('records') sudah mengembalikan List[dict]
    all_data = recommender.df.to_dict('records') 
    return all_data

# 🔥 4. Tambahkan summary & defensive check (Review Poin 5 & 6)
@router.post(
    "/recommendations", 
    summary="Dapatkan Rekomendasi (Search / Personalized)",
    description="Endpoint utama. Memberikan rekomendasi personal (jika `history_ids` diisi) atau hasil pencarian (jika `query` diisi)."
)
async def get_recommendations(request: Request, body: RecommendationRequest):
    recommender = request.app.state.model_cache.get("recommender")
    bert_model = request.app.state.model_cache.get("bert_model")

    if not recommender or not bert_model:
        raise HTTPException(status_code=503, detail="Server sedang inisialisasi, model belum siap.")

    # 🔥 5. Defensive Check .strip() (Review Poin 5)
    # Hanya jalankan search jika query ada isinya (bukan spasi doang)
    if body.query and body.query.strip():
        logger.info(f"Mencari query: '{body.query}'")
        df_results = get_semantic_search_logic(body.query.strip(), recommender, bert_model)
        return {
            "title": f"Hasil Pencarian untuk '{body.query}'",
            "data": df_results.to_dict('records')
        }
    
    logger.info(f"Membuat feed personalisasi untuk riwayat ID: {body.history_ids}")
    history_names = []
    if body.history_ids:
        try:
            history_names = recommender.df[recommender.df['id'].isin(body.history_ids)]['nama_wisata'].tolist()
        except Exception as e:
            logger.warning(f"Gagal konversi history_ids ke nama: {e}")
            
    # 🔥 6. Kirim 'request' ke helper (Review Poin 3)
    df_results, title = get_personalized_feed_logic(history_names, recommender, request)
    return {
        "title": title,
        "data": df_results.to_dict('records')
    }

# 🔥 7. Tambahkan summary & deskripsi (Review Poin 6)
@router.get(
    "/similar/{nama_wisata}", 
    response_model=dict, # Balikannya {title: ..., data: [...]}
    summary="Dapatkan Destinasi Serupa",
    description="Mengembalikan 3 (atau `top_k`) destinasi yang paling mirip berdasarkan *nama wisata* yang dipilih."
)
async def get_similar_destinations(request: Request, nama_wisata: str, top_k: int = 3):
    recommender = request.app.state.model_cache.get("recommender")
    if not recommender:
        raise HTTPException(status_code=503, detail="Server sedang inisialisasi, data belum siap.")
    try:
        df_similar = recommender.get_recommendations(nama_wisata, top_k)
        return {
            "title": f"Mirip dengan {nama_wisata}",
            "data": df_similar.to_dict('records')
        }
    except ValueError as e: 
        logger.warning(f"Nama wisata tidak ditemukan: {nama_wisata}. Error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Gagal mencari similar: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal memproses: {e}")
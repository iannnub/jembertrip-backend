"""
======================================================
STREAMLIT APP — Sistem Rekomendasi Wisata Jember
======================================================
Versi: 7.0 (Final Presentation Version)
------------------------------------------------------
✅ HIDE: Skor kemiripan dihilangkan dari tampilan kartu.
✅ HIDE: Riwayat aktivitas dan tombol reset disembunyikan dari sidebar.
✅ FIX: Panggilan st.rerun() yang berlebihan dihapus untuk mencegah notifikasi.
✅ Aplikasi siap untuk presentasi akhir.
======================================================
"""

# ======================================================
# 1️⃣ IMPORT LIBRARY
# ======================================================
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import sys
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# ======================================================
# 🚀 KONFIGURASI HALAMAN (HARUS MENJADI PERINTAH PERTAMA)
# ======================================================
st.set_page_config(
    page_title="Rekomendasi Wisata Jember",
    page_icon="🌴",
    layout="wide"
)

# ======================================================
# 2️⃣ KONFIGURASI DASAR
# ======================================================
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

try:
    from src.recommender import Recommender
except ImportError as e:
    st.error(f"❌ Gagal mengimpor Recommender: {e}")
    st.stop()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
logger = logging.getLogger(__name__)

# ======================================================
# 3️⃣ KONSTANTA SESSION STATE
# ======================================================
STATE_VIEW_MODE = "view_mode"
STATE_CLICKED_HISTORY = "clicked_history"
STATE_SELECTED_WISATA = "selected_wisata"
STATE_SHOW_ALL = "show_all_mode"

# ======================================================
# 4️⃣ CLASS APLIKASI
# ======================================================
class TourismApp:
    def __init__(self):
        self.recommender = self._load_recommender()
        self.bert_model = self._load_bert_model()
        self._init_session_state()

    # ------------------------------------------------------
    # 🔹 LOAD MODEL
    # ------------------------------------------------------
    @staticmethod
    @st.cache_resource
    def _load_recommender():
        try:
            rec = Recommender()
            assert not rec.df.empty, "Dataset kosong"
            return rec
        except Exception as e:
            st.error(f"❌ Gagal memuat Recommender: {e}")
            return None

    @staticmethod
    @st.cache_resource
    def _load_bert_model():
        try:
            model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            return model
        except Exception as e:
            st.error(f"❌ Gagal memuat model BERT: {e}")
            return None

    # ------------------------------------------------------
    # 🔹 STATE MANAGEMENT
    # ------------------------------------------------------
    @staticmethod
    def _init_session_state():
        defaults = {
            STATE_VIEW_MODE: "home",
            STATE_CLICKED_HISTORY: [],
            STATE_SELECTED_WISATA: None,
            STATE_SHOW_ALL: False
        }
        for key, val in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = val

    def _go_home(self):
        st.session_state[STATE_VIEW_MODE] = "home"
        # st.rerun() tidak diperlukan di dalam callback

    def _go_detail(self, nama_wisata: str):
        st.session_state[STATE_VIEW_MODE] = "detail"
        st.session_state[STATE_SELECTED_WISATA] = nama_wisata
        st.session_state[STATE_SHOW_ALL] = False

        history = st.session_state[STATE_CLICKED_HISTORY]
        if nama_wisata in history:
            history.remove(nama_wisata)
        history.insert(0, nama_wisata)
        st.session_state[STATE_CLICKED_HISTORY] = history[:5]
        # st.rerun() tidak diperlukan di dalam callback

    def _toggle_show_all(self):
        st.session_state[STATE_SHOW_ALL] = not st.session_state[STATE_SHOW_ALL]
        # st.rerun() tidak diperlukan di dalam callback

    # ------------------------------------------------------
    # 🔹 LOGIKA REKOMENDASI
    # ------------------------------------------------------
    @st.cache_data(show_spinner=False)
    def _get_semantic_search_results(_self, query: str, top_k: int = None):
        if not query:
            return pd.DataFrame()

        query_vec = _self.bert_model.encode([query], show_progress_bar=False)
        sim_scores = cosine_similarity(query_vec, _self.recommender.embeddings)[0]

        if top_k is None:
            top_k = len(_self.recommender.df)

        idx = np.argsort(sim_scores)[::-1][:top_k]
        df = _self.recommender.df.iloc[idx].copy()
        df["skor_kemiripan"] = np.round(sim_scores[idx], 3)
        return df

    def _get_personalized_feed(self, history: list, top_n: int = 9):
        df = self.recommender.df
        if not history:
            return df.sample(top_n, random_state=42), "✨ Jelajahi Destinasi Populer di Jember"

        try:
            idx_hist = [df.index[df["nama_wisata"] == nama].item() for nama in history]
            hist_vec = self.recommender.embeddings[idx_hist]
            user_vec = np.mean(hist_vec, axis=0).reshape(1, -1)

            sim_scores = cosine_similarity(user_vec, self.recommender.embeddings)[0]
            clicked_cats = df.loc[idx_hist, "kategori"]
            top_cat = clicked_cats.value_counts().idxmax()

            BOOST = 0.5
            mask = (df["kategori"] == top_cat)
            sim_scores[mask] += BOOST

            idx = sim_scores.argsort()[::-1]
            df_sorted = df.iloc[idx]
            final_df = df_sorted[~df_sorted["nama_wisata"].isin(history)]
            return final_df.head(top_n), f"🔥 Karena Anda Suka Kategori '{top_cat}'"
        except Exception as e:
            logger.error(f"Feed personalization failed: {e}")
            return df.sample(top_n, random_state=42), "✨ Jelajahi Destinasi Populer di Jember"

    # ------------------------------------------------------
    # 🔹 UI KOMPONEN
    # ------------------------------------------------------
    def _display_cards(self, df, key_prefix, title=None, max_items=9):
        if title:
            st.header(title)

        if df is None or df.empty:
            st.warning("😅 Tidak ditemukan destinasi yang sesuai dengan kategori atau pencarian Anda.")
            return

        cols = st.columns([1, 1, 1])
        for i, row in enumerate(df.head(max_items).itertuples()):
            col = cols[i % 3]
            with col:
                with st.container(border=True):
                    img_path = BASE_DIR / getattr(row, "gambar", "assets/images/default.png")
                    if not img_path.is_file():
                        img_path = BASE_DIR / "assets/images/default.png"

                    st.image(str(img_path), use_container_width=True)
                    st.subheader(getattr(row, "nama_wisata"))
                    st.caption(f"📌 {getattr(row, 'kategori')}")
                    # --- SKOR KEMIRIPAN DIHILANGKAN ---
                    # if "skor_kemiripan" in df.columns:
                    #     st.markdown(f"**Skor:** `{getattr(row, 'skor_kemiripan', 0.0):.3f}`")
                    st.button(
                        "👀 Lihat Detail",
                        key=f"{key_prefix}_{getattr(row, 'id')}",
                        on_click=self._go_detail,
                        args=(getattr(row, "nama_wisata"),),
                        use_container_width=True
                    )

    def _render_sidebar(self):
        with st.sidebar:
            st.header("🔍 Pencarian & Filter")
            query = st.text_input("Cari berdasarkan makna:", placeholder="contoh: pantai untuk keluarga...")

            kategori_unik = sorted(self.recommender.df["kategori"].dropna().unique())
            selected_cats = st.multiselect("Filter kategori:", kategori_unik)

            # --- RIWAYAT DAN TOMBOL RESET DIHILANGKAN ---
            # st.markdown("---")
            # st.header("👤 Riwayat Anda")
            # if st.session_state[STATE_CLICKED_HISTORY]:
            #     for nama in st.session_state[STATE_CLICKED_HISTORY]:
            #         if st.button(f"➡️ {nama}", key=f"hist_{nama}", use_container_width=True):
            #             self._go_detail(nama)
            # else:
            #     st.caption("Belum ada aktivitas.")
            #
            # st.markdown("---")
            # if st.button("🔄 Reset Riwayat", use_container_width=True, type="secondary"):
            #     self._init_session_state()
            #     st.rerun()

            st.markdown("---")
            st.info("📚 Proyek oleh **iann** (2025)")
            return query, selected_cats

    def _render_home(self, query, selected_cats):
        history = st.session_state[STATE_CLICKED_HISTORY]

        # Mode pencarian
        if query:
            title = "🔍 Hasil Pencarian Semantik"
            df_candidates = self._get_semantic_search_results(query)
            if selected_cats:
                title = f"🔍 Hasil Pencarian untuk Kategori '{', '.join(selected_cats)}'"
                filtered_df = df_candidates[df_candidates["kategori"].isin(selected_cats)]
                if filtered_df.empty:
                    st.info("🤔 Tidak ada hasil untuk kategori yang dipilih. Menampilkan semua hasil pencarian.")
                else:
                    df_candidates = filtered_df
            self._display_cards(df_candidates, "search", title=title, max_items=12)
            return

        # Mode lihat semua
        if st.session_state[STATE_SHOW_ALL]:
            title = "🖼️ Semua Destinasi Wisata Jember"
            st.button("⬅️ Kembali ke Rekomendasi", on_click=self._toggle_show_all)
            df = self.recommender.df.sort_values("nama_wisata")
            if selected_cats:
                title = f"🖼️ Semua Wisata Kategori '{', '.join(selected_cats)}'"
                filtered_df = df[df["kategori"].isin(selected_cats)]
                if filtered_df.empty:
                    st.info("🤔 Tidak ada wisata dalam kategori yang dipilih.")
                else:
                    df = filtered_df
            self._display_cards(df, "all", title=title, max_items=len(df))
            return

        # Mode Beranda (Personalisasi / Cold Start)
        if history:
            p_df_candidates, p_title = self._get_personalized_feed(history, top_n=len(self.recommender.df))
            final_title = p_title 

            if selected_cats:
                final_title = f"Rekomendasi Kategori '{', '.join(selected_cats)}' Untuk Anda"
                filtered_df = p_df_candidates[p_df_candidates["kategori"].isin(selected_cats)]
                if filtered_df.empty:
                    st.info("🤔 Tidak ada destinasi dengan kategori tersebut, menampilkan feed umum.")
                else:
                    p_df_candidates = filtered_df
            self._display_cards(p_df_candidates, "personalized", title=final_title, max_items=6)

            st.markdown("---")
            st.header("✨ Jelajahi Destinasi Lainnya")
            shown_items = set(p_df_candidates['nama_wisata'].head(6))
            explore_df = self.recommender.df[~self.recommender.df['nama_wisata'].isin(shown_items)]
            if selected_cats:
                filtered_df = explore_df[explore_df['kategori'].isin(selected_cats)]
                if not filtered_df.empty:
                    explore_df = filtered_df
            
            sample_size = min(6, len(explore_df))
            if sample_size > 0:
                self._display_cards(explore_df.sample(n=sample_size, random_state=42), "explore_p", max_items=6)

        else:
            # Pengguna baru
            title = "✨ Jelajahi Destinasi Populer di Jember"
            df_candidates = self.recommender.df
            if selected_cats:
                title = f"✨ Destinasi Populer Kategori '{', '.join(selected_cats)}'"
                filtered_df = df_candidates[df_candidates["kategori"].isin(selected_cats)]
                if filtered_df.empty:
                    st.info("🤔 Tidak ada destinasi dengan kategori tersebut, menampilkan semua wisata.")
                else:
                    df_candidates = filtered_df
            
            sample_size = min(6, len(df_candidates))
            if sample_size > 0:
                self._display_cards(df_candidates.sample(n=sample_size, random_state=42), "feed", title=title, max_items=6)

        st.markdown("---")
        st.button("Tampilkan Semua Wisata 🗺️", on_click=self._toggle_show_all, use_container_width=True, type="secondary")

    def _render_detail(self):
        nama = st.session_state[STATE_SELECTED_WISATA]
        df = self.recommender.df
        try:
            wisata = df[df["nama_wisata"] == nama].iloc[0]
        except IndexError:
            st.error("Wisata tidak ditemukan.")
            self._go_home()
            return

        st.button("⬅️ Kembali", on_click=self._go_home)
        st.title(f"🏖️ {wisata['nama_wisata']}")
        st.caption(f"📍 {wisata['alamat']} | 🏷️ {wisata['kategori']}")
        st.markdown("---")

        col1, col2 = st.columns([1, 1.5])
        with col1:
            img_path = BASE_DIR / wisata["gambar"]
            if not img_path.is_file():
                img_path = BASE_DIR / "assets/images/default.png"
            st.image(str(img_path), use_container_width=True)
        with col2:
            st.markdown("**Deskripsi:**")
            st.write(wisata["deskripsi"])

        st.markdown("---")
        st.subheader("🌟 Destinasi Serupa")
        rekom_df = self.recommender.get_recommendations(nama, 3)
        self._display_cards(rekom_df, "rec_detail", max_items=3)

    # ------------------------------------------------------
    # 🔹 MAIN
    # ------------------------------------------------------
    def run(self):
        # st.set_page_config() dipindahkan ke atas
        st.title("🌴 Sistem Rekomendasi Wisata Jember")
        st.caption("Temukan surga tersembunyi di Jember dengan AI ✨")

        if not self.recommender or not self.bert_model:
            st.error("❌ Komponen AI gagal dimuat.")
            st.stop()

        query, selected_cats = self._render_sidebar()

        if st.session_state[STATE_VIEW_MODE] == "home":
            self._render_home(query, selected_cats)
        elif st.session_state[STATE_VIEW_MODE] == "detail":
            self._render_detail()


# ======================================================
# ENTRY POINT
# ======================================================
if __name__ == "__main__":
    with st.spinner("Mempersiapkan mesin rekomendasi... Ini hanya butuh sesaat saat pertama kali dijalankan."):
        app = TourismApp()
    app.run()
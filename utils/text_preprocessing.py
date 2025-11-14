# utils/text_preprocessing.py

import re

# ⭐ PERBAIKAN 1: Menggunakan daftar stopwords Bahasa Indonesia yang kustom dan ringan.
# Ini menghilangkan ketergantungan pada NLTK dan jauh lebih cepat.
STOPWORDS_INDONESIA = set([
    'ada', 'adalah', 'adanya', 'adapun', 'agak', 'agaknya', 'agar', 'akan', 'akankah', 'akhir',
    'akhiri', 'akhirnya', 'aku', 'akulah', 'amat', 'amatlah', 'anda', 'andalah', 'antar',
    'antara', 'antaranya', 'apa', 'apaan', 'apabila', 'apakah', 'apalagi', 'apatah', 'atau',
    'ataukah', 'ataupun', 'atas', 'awal', 'awalnya', 'bagaimana', 'bagaimanakah', 'bagaimanapun',
    'bagi', 'bagian', 'bahkan', 'bahwa', 'bahwasanya', 'baik', 'bakal', 'bakalan', 'balik',
    'banyak', 'bapak', 'baru', 'bawah', 'beberapa', 'begini', 'beginian', 'beginikah',
    'beginilah', 'begitu', 'begitukah', 'begitulah', 'begitupun', 'bekerja', 'belakang',
    'belakangan', 'belum', 'belumlah', 'benar', 'benarkah', 'benarlah', 'berada', 'berakhir',
    'berakhirlah', 'berakhirnya', 'berapa', 'berapakah', 'berapalah', 'berapapun', 'berarti',
    'berawal', 'berbagai', 'dari', 'dan', 'dapat', 'dengan', 'di', 'ia', 'ini', 'itu', 'juga',
    'jika', 'jadi', 'jangan', 'kami', 'kamu', 'kalian', 'kita', 'ke', 'karena', 'kepada',
    'ketika', 'kok', 'lagi', 'lain', 'lalu', 'mau', 'maka', 'masih', 'saya', 'saja', 'saat',
    'seperti', 'sekarang', 'sementara', 'serta', 'sudah', 'tapi', 'telah', 'tentang', 'tersebut',
    'tidak', 'untuk', 'wah', 'yakni', 'yang'
])

def clean_text(text: str) -> str:
    """
    Membersihkan teks dengan tahapan yang dioptimalkan:
    1. Mengubah menjadi huruf kecil (lowercase).
    2. Menghapus semua karakter kecuali huruf alfabet dan spasi.
    3. Memecah teks menjadi kata-kata (tokenisasi).
    4. Menghapus stopwords Bahasa Indonesia.
    5. Menggabungkan kembali kata-kata menjadi kalimat bersih.
    
    Args:
        text (str): Teks mentah dari dataset.
    
    Returns:
        str: Hasil teks yang sudah dibersihkan dan siap untuk TF-IDF.
    """
    if not isinstance(text, str):
        return ""

    # 1. Lowercase
    text = text.lower()

    # 2. Hapus semua karakter kecuali huruf dan spasi
    # ⭐ PERBAIKAN 2: Regex yang lebih sederhana dan efektif
    text = re.sub(r'[^a-z\s]', ' ', text)

    # 3 & 4. Tokenisasi dan penghapusan stopwords dalam satu langkah efisien
    # ⭐ PERBAIKAN 3: Alur yang lebih logis dan cepat
    words = [word for word in text.split() if word not in STOPWORDS_INDONESIA and len(word) > 1]
    
    # 5. Gabungkan kembali
    cleaned_text = " ".join(words)
    
    # ⭐ PERBAIKAN 4: Stemming dihapus karena PorterStemmer tidak cocok.
    # Jika stemming diperlukan untuk Bahasa Indonesia, gunakan library Sastrawi.
    # from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
    # factory = StemmerFactory()
    # stemmer = factory.create_stemmer()
    # cleaned_text = stemmer.stem(cleaned_text)
    
    return cleaned_text

if __name__ == "__main__":
    # Contoh pengujian cepat
    sample_text = "Puncak Rembangan adalah destinasi wisata pegunungan di Jember yang menawarkan udara sejuk & panorama alam memesona!"
    cleaned = clean_text(sample_text)
    
    print("--- Contoh Pengujian clean_text ---")
    print(f"Teks Asli:\n'{sample_text}'")
    print(f"\nHasil Teks Bersih:\n'{cleaned}'")
    print("\n--- Selesai ---")
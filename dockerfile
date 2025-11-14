# 1. Mulai dari "OS" Python yang ringan
# (Saya asumsikan kita pakai Python 3.11, sesuaikan jika beda)
FROM python:3.11-slim

# 2. Buat "folder kerja" di dalam server
WORKDIR /app

# 3. Salin SEMUA file project kita ke "folder kerja" itu
# (Termasuk folder 'backend', 'data', 'models', dll.)
COPY . .

# 4. Jalankan "Build Command" (Install semua 'requirements.txt')
RUN pip install -r requirements.txt

# 5. Beri tahu HF, "Server saya akan jalan di port ini"
# (7860 adalah port default yang disukai HF Spaces)
EXPOSE 7860

# 6. Ini adalah "Start Command" kita!
# (Jalankan Uvicorn, tapi di port 7860)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]

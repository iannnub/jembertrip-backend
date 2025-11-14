# backend/models.py

import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
# 1. Import 'func' untuk timestamp di level DB (Review Poin 4)
from sqlalchemy.sql import func 

# Import 'Base' dari file database.py kita
from database import Base 

# ======================================================
# Definisi Tabel 'User'
# ======================================================
class User(Base):
    # 2. Docstring (Review Poin 8)
    """Model pengguna aplikasi JemberTrip."""
    
    __tablename__ = "users" 

    id = Column(Integer, primary_key=True, index=True)
    # Tambahkan panjang max untuk String (Best Practice)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # --- Relasi (Profesional Practice) ---
    history = relationship(
        "ClickHistory", 
        back_populates="owner",
        # 3. Cascade Delete (Review Poin 3)
        # Jika User dihapus, semua history-nya ikut terhapus.
        cascade="all, delete-orphan"
    )

    # 4. __repr__ untuk debugging (Review Poin 2)
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

# ======================================================
# Definisi Tabel 'ClickHistory'
# ======================================================
class ClickHistory(Base):
    # 2. Docstring (Review Poin 8)
    """Model log riwayat klik pengguna."""

    __tablename__ = "click_history"

    id = Column(Integer, primary_key=True, index=True)
    
    item_id = Column(Integer, nullable=False, index=True) 
    
    # 5. Timestamp di DB-side (Review Poin 4)
    # Menggantikan default=datetime.datetime.now(datetime.timezone.utc)
    timestamp = Column(
        DateTime(timezone=True), # Memastikan timezone disimpan
        server_default=func.now()  # Dibuat oleh server DB, bukan Python
    )

    # --- Foreign Key (Kunci Tamu) ---
    # 6. Indexing di Foreign Key (Review Poin 6)
    # Mempercepat query pencarian history berdasarkan user_id
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    # --- Relasi (Profesional Practice) ---
    owner = relationship("User", back_populates="history")

    # 4. __repr__ untuk debugging (Review Poin 2)
    def __repr__(self):
        return f"<ClickHistory(user_id={self.user_id}, item_id={self.item_id})>"
# Multi-stage Python Dockerfile
FROM python:3.11-slim

# Metadatalar va ish rejimi
WORKDIR /app

# Tizim paketlarini yangilash va kerakli vositalarni o'rnatish
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt-get/lists/*

# Kutubxona talablarini nusxalash va o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyiha fayllarini nusxalash
COPY . .

# Yuklanadigan fayllar uchun papka yaratish
RUN mkdir -p /app/uploads

# Admin panel portini ochish
EXPOSE 8000

# Standart ishga tushirish buyrug'i (Bot va FastAPI birgalikda runs or custom start script)
CMD ["python", "bot.py"]

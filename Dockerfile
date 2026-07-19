FROM python:3.11-slim

WORKDIR /app

# System bog'liqliklar
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Requirements o'rnatish
COPY shopmaker/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Bot fayllarini ko'chirish
COPY shopmaker/ .

# Logs papkasini yaratish
RUN mkdir -p logs

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["python", "main.py"]

FROM python:3.11-slim

WORKDIR /app

# Build uchun kerakli tizim kutubxonalari
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# pip ni eng yangi versiyaga yangilash (wheel topish uchun muhim)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# pydantic-core ni alohida binary wheel sifatida o'rnatish
RUN pip install --no-cache-dir --only-binary=pydantic-core \
    "pydantic-core==2.27.2" \
    "pydantic==2.10.6"

# Qolgan paketlarni o'rnatish
COPY shopmaker/requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Bot fayllarini ko'chirish
COPY shopmaker/ .
RUN mkdir -p logs

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["python", "main.py"]

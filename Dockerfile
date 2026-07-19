FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# uv — pip'dan tezroq, binary wheel'ni Rust'siz o'rnatadi
RUN pip install --no-cache-dir uv

COPY shopmaker/requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY shopmaker/ .
RUN mkdir -p logs

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["python", "main.py"]

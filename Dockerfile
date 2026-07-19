FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make \
    && rm -rf /var/lib/apt/lists/*

COPY shopmaker/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --prefer-binary \
        pydantic-core==2.27.2 \
        pydantic==2.10.6 && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY shopmaker/ .

RUN mkdir -p logs

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["python", "main.py"]

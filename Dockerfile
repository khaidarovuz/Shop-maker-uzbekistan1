FROM python:3.11-slim

WORKDIR /app

# System kutubxonalari va Rust (pydantic-core uchun shart)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make curl ca-certificates pkg-config \
    libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
    | sh -s -- -y --profile minimal --no-modify-path

ENV PATH="/root/.cargo/bin:${PATH}"

COPY shopmaker/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY shopmaker/ .
RUN mkdir -p logs

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["python", "main.py"]

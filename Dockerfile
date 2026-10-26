FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema necesarias para psycopg y Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu --no-deps \
    torch==2.14.0 torchvision==0.29.0 \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads models

EXPOSE 10000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]

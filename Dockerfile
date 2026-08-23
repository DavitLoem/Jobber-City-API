# ប្រើប្រាស់ Python 3.13 ដែលលោកអ្នកកំពុងប្រើ
FROM python:3.13-slim

WORKDIR /app

# 🎯 ដំឡើង System Libraries ដោយប្រើប្រាស់ឈ្មោះ Package ថ្មី (libgdk-pixbuf-2.0-0)
RUN apt-get update && apt-get install -y \
    build-essential \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    libglib2.0-0 \
    fontconfig \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
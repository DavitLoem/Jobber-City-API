# ប្រើប្រាស់ Python 3.13 ដែលលោកអ្នកកំពុងប្រើ
FROM python:3.13-slim

# កំណត់ទីតាំងធ្វើការ
WORKDIR /app

# 🎯 ដំឡើង System Libraries និង Fonts ទាំងអស់ដែល WeasyPrint ត្រូវការជាចាំបាច់
RUN apt-get update && apt-get install -y \
    build-essential \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    libglib2.0-0 \
    fontconfig \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# ចម្លងឯកសារ requirements.txt និងដំឡើង Python Packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ចម្លងកូដទាំងអស់ចូលទៅក្នុង Docker
COPY . .

# បញ្ជាឱ្យ Run FastAPI Server (ប្រើ Port របស់ Railway)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
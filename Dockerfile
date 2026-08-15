FROM python:3.12-slim

# System dependencies: Tesseract (the actual OCR engine, not just the Python wrapper)
# and OpenCV's runtime libraries (libgl1, libglib2.0-0 — OpenCV needs these even
# though we only use it for image processing, not display)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first, install, THEN copy the rest of the code.
# This ordering matters for Docker's build cache.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
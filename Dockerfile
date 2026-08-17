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

# --timeout raised well above gunicorn's 30s default: each upload request runs
# OpenCV preprocessing + Tesseract OCR synchronously per photo, in a loop for
# multi-file uploads, and full-res phone camera photos over a mobile connection
# can push a multi-photo request past 30s — gunicorn silently kills the worker
# and the client sees no response at all, which looks like the upload button
# doing nothing.
CMD python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120
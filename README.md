# InBody Tracker

A Django web app that OCRs photos of InBody 270 body composition receipts and tracks metrics (weight, muscle mass, body fat, etc.) over time with charts. Supports multiple user accounts.

## Requirements

- Python 3.11+ (developed against 3.12)
- **Tesseract OCR** — this is a system-level binary, not a Python package. `pytesseract` is just a wrapper around it, so it won't work without this installed separately:
  - **Mac:** `brew install tesseract`
  - **Ubuntu/Debian/WSL:** `sudo apt install tesseract-ocr`
  - **Windows:** install from the [UB-Mannheim build](https://github.com/UB-Mannheim/tesseract/wiki), then make sure the install location is on your PATH (or set `pytesseract.pytesseract.tesseract_cmd` to the full path in `scans/ocr.py` if Python can't find it automatically)

## Setup

1. **Clone the repo:**
   ```bash
   git clone https://github.com/LandonGeorge/inbody-tracker.git
   cd inbody-tracker
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser** (for accessing `/admin/` and testing):
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the dev server:**
   ```bash
   python manage.py runserver
   ```
   Visit `http://127.0.0.1:8000/accounts/signup/` to create an account, or `http://127.0.0.1:8000/admin/` to log in as the superuser.

## Usage

- **Sign up / log in:** `/accounts/signup/` and `/accounts/login/`
- **Upload a scan:** `/scans/upload/` — take a clear, well-lit photo of your InBody 270 receipt
- **View your scans:** `/scans/` — edit or delete any scan, and compare the parsed values against the original photo
- **Dashboard:** `/scans/dashboard/` — charts of your metrics over time

## Notes on OCR accuracy

OCR works best on clear, well-lit, non-creased receipts. Faded thermal paper or heavy creases can cause some fields (especially the scan date) to misread. If a scan's date wasn't read correctly, the list view will flag it in red — you can manually correct any field from the Edit page, which shows the original photo alongside the form for easy comparison.

## Deployment

The app is deployed on [Railway](https://railway.app) using the included `Dockerfile` (Railway builds and runs it automatically — no separate config needed beyond environment variables).

The Dockerfile installs Tesseract and OpenCV's runtime libraries alongside the Python dependencies, then runs migrations and starts `gunicorn` on container startup, binding to Railway's `$PORT`.

Required environment variables in production:

- `SECRET_KEY` — a unique, secret value (don't reuse the dev default baked into `settings.py`)
- `DEBUG` — set to `False`
- `ALLOWED_HOSTS` — comma-separated hostnames, e.g. your `*.up.railway.app` domain or custom domain
- `CSRF_TRUSTED_ORIGINS` — comma-separated origins including scheme, e.g. `https://yourapp.up.railway.app`
- `DATA_DIR` — path to a persistent volume for the SQLite database and uploaded media (without a mounted volume, both are wiped on every redeploy)

Media files (uploaded receipt photos) are served directly by Django, even with `DEBUG=False` — there's no CDN/S3 in front of them, which is fine at this app's scale but worth knowing if usage grows.

## Tech stack

- Django (backend, auth, templates)
- Tesseract + pytesseract (OCR)
- OpenCV (image preprocessing — adaptive thresholding for uneven lighting/fading)
- Pillow (image handling)
- Chart.js (dashboard charts, via CDN)
- SQLite (default dev database — fine for personal/small-scale use)
- Docker + gunicorn (production, deployed on Railway)

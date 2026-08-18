# InBody Tracker

Django web app that OCRs photos of InBody 270 body composition receipts and tracks metrics (weight, muscle mass, body fat, etc.) over time with charts. Multi-user, each with their own accounts and data.

## Tech stack

- Django (backend, auth, templates — server-rendered, no separate frontend/API split)
- Tesseract (via pytesseract) for OCR — local/free, not a cloud API
- OpenCV for image preprocessing (adaptive thresholding — handles uneven lighting/fading better than simple contrast adjustment)
- Bootstrap 5 (via CDN, no build step) for styling — chosen over Tailwind/plain CSS for fastest effort-to-result given no existing npm/build pipeline
- Chart.js (via CDN) for the dashboard charts
- SQLite for now (fine for personal/small-scale use)

## Styling conventions

- Bootstrap loaded via CDN in `base.html` (both CSS and JS bundle) — no npm, no build step
- Dark navbar (`navbar-dark bg-dark`) with nav links for Dashboard / Your Scans / Upload Scan, plus a logout form styled as a button
- Content wrapped in `class="container"` in `base.html`
- Design direction: whitespace-forward, cards for grouped/bounded content (metric summaries, scan rows), restrained color (one accent + neutral grays, red reserved for the OCR-date-mismatch warning), consistent spacing via Bootstrap's utility classes rather than custom margins/padding
- Chart.js colors are NOT automatically styled by Bootstrap (canvas-rendered, not real DOM) — if updating chart appearance, match Bootstrap's palette manually (e.g. `#0d6efd` for its default blue) rather than Chart.js's own default colors

## Project structure

- `accounts/` — signup/login/logout (mostly Django's built-in auth views)
- `scans/` — the core app: `ScanUpload` (raw image) and `ScanResult` (parsed metrics), OCR pipeline in `ocr.py`, upload/edit/delete/dashboard views
- `config/` — Django project settings/urls

## Key decisions / conventions

- Views stay thin — OCR/parsing logic lives in `scans/ocr.py`, not in `views.py`
- Every `ScanResult` numeric field is nullable — OCR won't always get every field, and a partial result should still save
- `raw_ocr_text` is stored permanently on `ScanUpload` for debugging bad parses
- Removed `basal_metabolic_rate_kcal` field; kept `bmi`
- All user-owned data lookups are scoped by user (e.g. `get_object_or_404(ScanResult, pk=pk, upload__user=request.user)`) — never trust a URL pk alone
- List view flags scans where `scan_date == uploaded_at.date()` in red, since that usually means OCR failed to read the date and it fell back to upload date
- Edit page shows the original receipt photo next to the edit form for easy comparison; list view intentionally does NOT show thumbnails (removed by choice)
- Upload accepts multiple files at once (`MultipleFileField` in `scans/forms.py`, Django's documented pattern for `<input multiple>`); each file becomes its own `ScanUpload`/`ScanResult` pair, processed and saved in a loop

## OCR notes

- Receipt fields print with exactly one digit after the decimal — regex patterns rely on this
- Common OCR misreads handled in `ocr.py`: `/` misread for `7` (converted back), stray space inserted around decimal points, `Weight`/`Welght` label i/l confusion, case variation in `InBody270`/`inBody270`/`INBody270`
- Tuned preprocessing (grayscale + adaptive threshold + `--psm 4`, no upscaling since photos are already high-res) improved tested field accuracy from ~54% to ~76% against a batch of real receipts
- Remaining failures are genuine character-level misreads (OCR reading the wrong digit/letter entirely) on faded or creased receipts — not fixable via regex, would need a different OCR engine to improve further

## Testing

- `pytest` (via `pytest-django`), not Django's built-in test runner — config in `pytest.ini`, dev-only deps in `requirements-dev.txt`
- Root `conftest.py` autouse-overrides `MEDIA_ROOT` to a tmp dir so uploaded test files don't land in the real media directory
- View tests live in each app's `tests.py` (`scans/tests.py`, `accounts/tests.py`); OCR calls (`extract_text`/`parse_inbody_text`) are mocked in view tests rather than exercising real Tesseract

## Deployment

- Deployed on Railway using the `Dockerfile` (gunicorn, migrations run automatically on container start) — see README.md's Deployment section for required env vars
- gunicorn started with `--timeout 120` (default is 30s) — uploads run OpenCV + Tesseract synchronously per photo, looped for multi-file uploads, and a multi-photo request over a mobile connection can exceed the default before OCR finishes
- Every page footer shows a version string like `v1.0.0 (3db0f55)` (`scans/context_processors.py`'s `version`, wired into `TEMPLATES` in `settings.py`), so it's obvious whether you're on a freshly deployed build without checking Railway:
  - `v1.0.0` is read from the root `VERSION` file — bump it by hand (semver) as part of any change worth calling a release
  - `(3db0f55)` is the deployed commit's short SHA, read from Railway's auto-populated `RAILWAY_GIT_COMMIT_SHA` env var; shows `(dev)` when that env var isn't set (i.e. locally) — this changes on every deploy even between version bumps

## Still open / deferred

- Styling/polish (currently bare HTML, no CSS)

## Setup

See README.md for install steps. Requires Tesseract OCR installed as a system binary (not just the pip package) and `opencv-python-headless`.

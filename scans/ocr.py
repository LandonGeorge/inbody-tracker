import re
from decimal import Decimal, InvalidOperation

import pytesseract
from PIL import Image, ImageOps

# Words we expect to find on a correctly-oriented InBody receipt.
# Used to score which rotation produced readable text.
_EXPECTED_KEYWORDS = ["Weight", "Muscle", "Body Fat", "InBody"]


def _score_text(text):
    """Count how many expected keywords appear — higher score = more likely correct orientation."""
    return sum(1 for keyword in _EXPECTED_KEYWORDS if keyword.lower() in text.lower())


def extract_text(image_path):
    """Run OCR at each of 4 rotations, return the text with the highest keyword match score."""
    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img)
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)

    best_text = ""
    best_score = -1

    for angle in [0, 90, 180, 270]:
        rotated = img.rotate(angle, expand=True)
        text = pytesseract.image_to_string(rotated)
        score = _score_text(text)

        if score > best_score:
            best_score = score
            best_text = text

    return best_text


def _extract_number(pattern, text):
    """Find first regex match and return it as Decimal, or None if not found/invalid."""
    match = re.search(pattern, text)
    if not match:
        return None
    try:
        return Decimal(match.group(1))
    except InvalidOperation:
        return None


def parse_inbody_text(text):
    """Extract known InBody 270 fields from raw OCR text. Returns a dict."""
    return {
        "weight_lb": _extract_number(r"Weight\s+(\d{1,3}\.\d)", text),
        "skeletal_muscle_mass_lb": _extract_number(r"Muscle Mass\s+(\d+\.?\d*)", text),
        "body_fat_mass_lb": _extract_number(r"Body Fat Mass\s+(\d+\.?\d*)", text),
        "total_body_water_lb": _extract_number(r"Total Body Water\s+(\d+\.?\d*)", text),
        "lean_body_mass_lb": _extract_number(r"Lean Body Mass\s+(\d+\.?\d*)", text),
        "percent_body_fat": _extract_number(r"Percent Body Fat\s+(\d+\.?\d*)", text),
        "bmi": _extract_number(r"BMI\s+(\d+\.?\d*)", text),
        "basal_metabolic_rate_kcal": _extract_number(
            r"Basal Metabolic Rate\s+(\d+)", text
        ),
    }

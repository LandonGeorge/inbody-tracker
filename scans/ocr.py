"""OCR pipeline for InBody 270 receipts: image preprocessing, text extraction
via Tesseract, and regex-based parsing of the known receipt fields.
"""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageOps

_EXPECTED_KEYWORDS = ["Weight", "Muscle", "Body Fat", "InBody"]
_TESSERACT_CONFIG = "--psm 4"


def _score_text(text):
    """Count how many expected receipt keywords appear in `text`.

    Used to pick the best OCR result across rotation attempts in
    extract_text(), since a correctly-oriented pass reads the labels
    (Weight, Muscle, etc.) while a sideways/upside-down pass mostly won't.
    """
    return sum(1 for keyword in _EXPECTED_KEYWORDS if keyword.lower() in text.lower())


def _preprocess_for_ocr(pil_image):
    """Grayscale + adaptive thresholding.

    Adaptive thresholding (vs. simple global contrast) handles receipts
    where fading/lighting is uneven across the page — it evaluates each
    pixel relative to its local neighborhood rather than one global curve.
    Tested against 10 real receipts: this step alone took field-level
    parsing accuracy from ~64% to ~76% versus plain grayscale+autocontrast.
    """
    img = ImageOps.exif_transpose(pil_image)
    img = ImageOps.grayscale(img)
    img_array = np.array(img)
    thresholded = cv2.adaptiveThreshold(
        img_array,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=25,
        C=15,
    )
    return Image.fromarray(thresholded)


def extract_text(image_path):
    """Run OCR at each of 4 rotations, return the text with the highest keyword match score."""
    raw_img = Image.open(image_path)
    preprocessed = _preprocess_for_ocr(raw_img)

    best_text = ""
    best_score = -1

    for angle in [0, 90, 180, 270]:
        rotated = preprocessed.rotate(angle, expand=True)
        text = pytesseract.image_to_string(rotated, config=_TESSERACT_CONFIG)
        score = _score_text(text)

        if score > best_score:
            best_score = score
            best_text = text

    return best_text


def _extract_number(pattern, text, fix_slash=False):
    """Find first regex match and return it as Decimal, or None if not found/invalid."""
    match = re.search(pattern, text)
    if not match:
        return None
    raw_value = match.group(1)
    raw_value = raw_value.replace(
        " ", ""
    )  # OCR sometimes inserts a stray space around the decimal
    if fix_slash:
        raw_value = raw_value.replace("/", "7")
    try:
        value = Decimal(raw_value)
    except InvalidOperation:
        return None
    return abs(value)


def _extract_scan_date(text):
    """Extract the scan date, preferring the receipt header but falling back
    to the Body Composition History row, which sometimes reads correctly
    even when the header line itself is too garbled to match.
    """
    match = re.search(r"[Ii][NnMm][Bb]ody\s*270\D{0,10}?(\d{2}/\d{2}/\d{2})", text)
    if match:
        try:
            return datetime.strptime(match.group(1), "%m/%d/%y").date()  # noqa: DTZ007
        except ValueError:
            pass

    match = re.search(r"Test Date\D{0,40}?(\d{2}/\d{2}/\d{2})", text)
    if match:
        try:
            return datetime.strptime(match.group(1), "%m/%d/%y").date()  # noqa: DTZ007
        except ValueError:
            pass

    return None


def parse_inbody_text(text):
    """Extract known InBody 270 fields from raw OCR text. Returns a dict.

    Every field on this receipt prints with exactly one digit after the
    decimal point. Constraining the pattern to exactly one digit (rather
    than a greedy \\d*) avoids swallowing a misread unit suffix like "lb"
    -> "1b", which would otherwise get pulled into the number as extra
    trailing digits. '/' is allowed as an alternate digit character and
    converted to '7', since a low-contrast "7" is frequently misread as
    "/" in this receipt's thermal print font.
    """
    one_decimal = r"(-?[\d/]{1,3}\.\s?[\d/])"
    return {
        "scan_date": _extract_scan_date(text),
        "weight_lb": _extract_number(
            r"We[il]ght\D{0,15}?" + one_decimal, text, fix_slash=True
        ),
        "skeletal_muscle_mass_lb": _extract_number(
            r"Muscle Mass\D{0,15}?" + one_decimal, text, fix_slash=True
        ),
        "body_fat_mass_lb": _extract_number(
            r"Body Fat Mass\D{0,15}?" + one_decimal, text, fix_slash=True
        ),
        "total_body_water_lb": _extract_number(
            r"Total Body Water\D{0,15}?" + one_decimal, text, fix_slash=True
        ),
        "lean_body_mass_lb": _extract_number(
            r"Lean Body Mass\D{0,15}?" + one_decimal, text, fix_slash=True
        ),
        "percent_body_fat": _extract_number(
            r"Per[c]?ent Body Fat\D{0,15}?" + one_decimal, text, fix_slash=True
        ),
        "bmi": _extract_number(r"BMI\D{0,15}?" + one_decimal, text, fix_slash=True),
    }

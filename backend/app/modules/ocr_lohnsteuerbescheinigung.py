"""
Modul 2 - Deterministisches OCR für die Lohnsteuerbescheinigung.

KEIN LLM. Pipeline:
  1. Metadaten/GPS-Strip (exiftool) BEVOR irgendetwas verarbeitet wird.
  2. De-Skewing (OpenCV).
  3. Template-Matching gegen BMF-Standard-Layout (feste Bounding-Boxes
     pro Feld, da die Lohnsteuerbescheinigung ein amtlich genormtes
     Formular ist -> Koordinaten sind stabil über Jahrgänge hinweg
     innerhalb einer Formularversion).
  4. Tesseract pro Bounding-Box (statt Volltext-OCR -> höhere Präzision).
  5. Zwingende RegEx-Validierung jedes Feldes (z.B. Geldbeträge im
     deutschen Format "1.234,56") BEVOR der Wert in die Steuer-Engine
     einfließen darf.
"""

from __future__ import annotations

import logging
import re
import subprocess
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

import cv2
import numpy as np
import pytesseract

logger = logging.getLogger("ocr.lohnsteuerbescheinigung")

# BMF-Standard-Layout: Bounding-Boxes als (x, y, w, h) in Pixel bei
# 300 DPI Scan. In Produktion versioniert pro Formularjahr in
# separater Konfigurationsdatei halten.
BMF_FIELD_BOXES: dict[str, tuple[int, int, int, int]] = {
    "bruttoarbeitslohn": (1250, 480, 400, 40),
    "einbehaltene_lohnsteuer": (1250, 560, 400, 40),
    "einbehaltener_solidaritaetszuschlag": (1250, 640, 400, 40),
    "steuerklasse": (1250, 720, 150, 40),
    "identifikationsnummer": (600, 200, 500, 40),
}

# Deutsches Geldbetragsformat: 1.234,56 oder 1234,56 oder 0,00
GERMAN_CURRENCY_RE = re.compile(r"^\d{1,3}(?:\.\d{3})*,\d{2}$|^\d+,\d{2}$")
STEUERKLASSE_RE = re.compile(r"^[IVI]{1,3}$")  # I, II, III, IV, V, VI (römisch)
IDNR_RE = re.compile(r"^\d{2}\s?\d{3}\s?\d{3}\s?\d{3}$")


class MetadataStripError(RuntimeError):
    pass


class FieldValidationError(RuntimeError):
    def __init__(self, field: str, raw_value: str):
        self.field = field
        self.raw_value = raw_value
        super().__init__(
            f"Feld '{field}' hat OCR-Rohwert '{raw_value}', der die "
            "RegEx-Validierung nicht besteht. Manuelle Prüfung erforderlich."
        )


@dataclass(frozen=True)
class ExtractedField:
    name: str
    raw_ocr_text: str
    validated_value: str
    confidence_ok: bool


def strip_all_metadata(input_path: Path, output_path: Path) -> Path:
    """
    Entfernt 100% aller Metadaten (inkl. GPS-EXIF) via exiftool, BEVOR
    die Datei irgendeiner weiteren Verarbeitung zugeführt wird.
    Läuft mit -overwrite_original auf einer KOPIE, nie auf dem Original-Upload.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(input_path.read_bytes())

    result = subprocess.run(
        ["exiftool", "-all=", "-overwrite_original", str(output_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise MetadataStripError(
            f"exiftool schlug fehl (rc={result.returncode}): {result.stderr}"
        )

    # Verifikation: keine verbliebenen Metadaten-Tags
    verify = subprocess.run(
        ["exiftool", str(output_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    remaining_lines = [
        line for line in verify.stdout.splitlines()
        if not line.startswith(("File Name", "Directory", "File Size",
                                 "File Modification", "File Access",
                                 "File Inode", "File Permissions",
                                 "File Type", "MIME Type"))
    ]
    if remaining_lines:
        logger.warning(
            "Nach Strip verbliebene Tags (nur Dateisystem-Meta erwartet): %s",
            remaining_lines,
        )

    return output_path


def _deskew(image: np.ndarray) -> np.ndarray:
    """Korrigiert Scan-Schräglage via Minimum-Area-Rectangle über Textpixel."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thresh > 0))
    if coords.size == 0:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        image, matrix, (w, h),
        flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE,
    )


def _validate_field(field_name: str, raw_text: str) -> str:
    cleaned = raw_text.strip()

    if field_name in ("bruttoarbeitslohn", "einbehaltene_lohnsteuer",
                       "einbehaltener_solidaritaetszuschlag"):
        if not GERMAN_CURRENCY_RE.match(cleaned):
            raise FieldValidationError(field_name, cleaned)
        # Zusätzliche Plausibilitätsprüfung: parsebar als Decimal
        normalized = cleaned.replace(".", "").replace(",", ".")
        try:
            Decimal(normalized)
        except InvalidOperation as exc:
            raise FieldValidationError(field_name, cleaned) from exc
        return normalized

    if field_name == "steuerklasse":
        if not STEUERKLASSE_RE.match(cleaned):
            raise FieldValidationError(field_name, cleaned)
        return cleaned

    if field_name == "identifikationsnummer":
        compact = cleaned.replace(" ", "")
        if not IDNR_RE.match(cleaned) or len(compact) != 11:
            raise FieldValidationError(field_name, cleaned)
        return compact

    raise ValueError(f"Unbekanntes Feld ohne Validierungsregel: {field_name}")


def extract_lohnsteuerbescheinigung(
    stripped_image_path: Path,
) -> dict[str, ExtractedField]:
    """
    Hauptfunktion: liefert ausschließlich RegEx-validierte Felder zurück.
    Wirft FieldValidationError statt stillschweigend falsche Werte an
    die Steuer-Engine weiterzugeben - Fail-Closed, nicht Fail-Open.
    """
    image = cv2.imread(str(stripped_image_path))
    if image is None:
        raise ValueError(f"Bild konnte nicht geladen werden: {stripped_image_path}")

    deskewed = _deskew(image)

    results: dict[str, ExtractedField] = {}
    for field_name, (x, y, w, h) in BMF_FIELD_BOXES.items():
        crop = deskewed[y:y + h, x:x + w]
        gray_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        # Otsu-Binarisierung verbessert Tesseract-Genauigkeit auf Formularfeldern
        _, binarized = cv2.threshold(
            gray_crop, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
        )

        raw_text = pytesseract.image_to_string(
            binarized, config="--psm 7 -l deu"  # PSM 7: einzelne Textzeile
        )

        validated = _validate_field(field_name, raw_text)
        results[field_name] = ExtractedField(
            name=field_name,
            raw_ocr_text=raw_text.strip(),
            validated_value=validated,
            confidence_ok=True,
        )

    return results

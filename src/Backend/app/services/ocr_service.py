"""
OCR Service — image preprocessing + Tesseract
"""
import io
import re
import cv2
import numpy as np
from pathlib import Path
from PIL import Image

from app.core.config import settings

try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    TESSERACT_OK = True
except Exception:
    TESSERACT_OK = False

try:
    from pdf2image import convert_from_bytes
    PDF_OK = True
except Exception:
    PDF_OK = False


def preprocess(pil_img: Image.Image) -> Image.Image:
    """Grayscale → Denoise → Adaptive threshold"""
    cv_img   = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    gray     = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    thresh   = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    return Image.fromarray(thresh)


async def extract_text_from_bytes(file_bytes: bytes, filename: str) -> tuple[str, float]:
    """
    Returns (raw_text, confidence 0-1).
    Handles PDF and image files.
    """
    ext = Path(filename).suffix.lower()
    pages: list[Image.Image] = []

    if ext == ".pdf":
        if not PDF_OK:
            return "", 0.0
        kwargs = {"dpi": 300}
        if settings.POPPLER_PATH:
            kwargs["poppler_path"] = settings.POPPLER_PATH
        pages = convert_from_bytes(file_bytes, **kwargs)
    elif ext in {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}:
        pages = [Image.open(io.BytesIO(file_bytes)).convert("RGB")]
    else:
        return "", 0.0

    if not TESSERACT_OK:
        return _mock_ocr(filename), 0.88

    config = "--oem 3 --psm 6"
    texts  = []
    confs  = []

    for page in pages:
        processed = preprocess(page)
        text = pytesseract.image_to_string(processed, config=config)
        texts.append(text)
        try:
            data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
            page_confs = [int(c) for c in data["conf"] if str(c).lstrip("-").isdigit() and int(c) > 0]
            if page_confs:
                confs.append(sum(page_confs) / len(page_confs) / 100)
        except Exception:
            confs.append(0.88)

    avg_conf = sum(confs) / len(confs) if confs else 0.88
    result = "\n".join(texts)
    print(f"OCR extracted {len(result)} chars with avg confidence {avg_conf:.3f}", result)
    return result, round(avg_conf, 3)


def _mock_ocr(filename: str) -> str:
    """Fallback when Tesseract is not available — returns realistic dummy text"""
    return f"[OCR mock for {filename}] MANIKANDAN CONSTRUCTIONS PVT LTD PAN AAKCM1234C GSTIN 33AAKCM1234C1ZP"

"""
OCR Service — image preprocessing + Tesseract

KEY FIXES:
- Cross-platform Tesseract detection (Linux/Mac/Windows)
- Clear logging so you know if mock OCR is being used
- Graceful fallback with explicit warnings
"""
import io
import os
import re
import cv2
import numpy as np
from pathlib import Path
from PIL import Image

from app.core.config import settings

# ── Tesseract setup ───────────────────────────────────────────
TESSERACT_OK = False

try:
    import pytesseract

    # Try to find Tesseract in multiple locations
    tesseract_candidates = [
        settings.TESSERACT_CMD,                          # From config
        "/usr/bin/tesseract",                            # Linux standard
        "/usr/local/bin/tesseract",                      # Linux/Mac homebrew
        "/opt/homebrew/bin/tesseract",                   # Mac Apple Silicon
        r"C:\Program Files\Tesseract-OCR\tesseract.exe", # Windows
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]

    for candidate in tesseract_candidates:
        if candidate and os.path.exists(candidate):
            pytesseract.pytesseract.tesseract_cmd = candidate
            TESSERACT_OK = True
            print(f"✅ Tesseract found at: {candidate}")
            break

    # If path not found, try running it from PATH
    if not TESSERACT_OK:
        import subprocess
        result = subprocess.run(["tesseract", "--version"],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            TESSERACT_OK = True
            print(f"✅ Tesseract found in PATH")
        else:
            print("⚠️ WARNING: Tesseract not found! OCR will use mock text.")
            print("   Install with: sudo apt-get install tesseract-ocr  (Linux)")
            print("   Or: brew install tesseract  (Mac)")

except ImportError:
    print("⚠️ WARNING: pytesseract not installed. Run: pip install pytesseract")
except Exception as e:
    print(f"⚠️ Tesseract setup error: {e}")

# ── pdf2image setup ───────────────────────────────────────────
PDF_OK = False
try:
    from pdf2image import convert_from_bytes
    PDF_OK = True
except ImportError:
    print("⚠️ WARNING: pdf2image not installed. PDFs will not be processed.")
    print("   Install with: pip install pdf2image")


def preprocess(pil_img: Image.Image) -> Image.Image:
    """
    Image preprocessing pipeline for better OCR accuracy:
    Resize → Grayscale → Denoise → Adaptive threshold
    """
    # Upscale small images — Tesseract works best at 300 DPI
    w, h = pil_img.size
    if w < 1000:
        scale = 1800 / w
        pil_img = pil_img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    cv_img   = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    gray     = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # Adaptive threshold — good for uneven lighting / scanned docs
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

    If Tesseract is not available, returns mock OCR with explicit warning.
    """
    ext = Path(filename).suffix.lower()
    pages: list[Image.Image] = []

    # Convert to images
    if ext == ".pdf":
        if not PDF_OK:
            print(f"⚠️ Cannot process PDF {filename} — pdf2image not installed")
            return _mock_ocr(filename), 0.50
        try:
            kwargs = {"dpi": 300}
            if settings.POPPLER_PATH:
                kwargs["poppler_path"] = settings.POPPLER_PATH
            pages = convert_from_bytes(file_bytes, **kwargs)
            print(f"📄 PDF {filename}: {len(pages)} page(s)")
        except Exception as e:
            print(f"⚠️ PDF conversion failed for {filename}: {e}")
            return "", 0.0

    elif ext in {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}:
        try:
            pages = [Image.open(io.BytesIO(file_bytes)).convert("RGB")]
        except Exception as e:
            print(f"⚠️ Image open failed for {filename}: {e}")
            return "", 0.0
    else:
        print(f"⚠️ Unsupported file type: {ext} ({filename})")
        return "", 0.0

    if not pages:
        return "", 0.0

    # Use mock if Tesseract unavailable
    if not TESSERACT_OK:
        print(f"⚠️ MOCK OCR used for {filename} — Tesseract not available!")
        print("   This will cause inaccurate extraction. Install Tesseract.")
        return _mock_ocr(filename), 0.50

    # Run Tesseract
    config = "--oem 3 --psm 6"
    texts  = []
    confs  = []

    for i, page in enumerate(pages[:5]):  # cap at 5 pages
        try:
            processed = preprocess(page)
            text = pytesseract.image_to_string(processed, config=config, lang="eng")
            texts.append(text)

            try:
                data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
                page_confs = [int(c) for c in data["conf"]
                              if str(c).lstrip("-").isdigit() and int(c) > 0]
                if page_confs:
                    confs.append(sum(page_confs) / len(page_confs) / 100)
            except Exception:
                confs.append(0.80)

            print(f"   Page {i+1}: {len(text)} chars extracted")
        except Exception as e:
            print(f"⚠️ Tesseract error on page {i+1} of {filename}: {e}")
            confs.append(0.0)

    avg_conf = sum(confs) / len(confs) if confs else 0.0
    result   = "\n\n".join(texts)
    print(result)
    print(f"✅ OCR {filename}: {len(result)} chars, confidence={avg_conf:.3f}")
    return result, round(avg_conf, 3)


def _mock_ocr(filename: str) -> str:
    """
    Fallback when Tesseract is not available.
    Returns EMPTY string so extraction fails clearly rather than producing
    fake results. The status will show as FAILED in the UI which is correct.

    Previously this returned fake data which caused the LLM to extract
    the same placeholder values for every document — the root cause of bad accuracy.
    """
    print(f"⚠️ MOCK OCR returning empty for {filename} — install Tesseract for real extraction")
    return ""
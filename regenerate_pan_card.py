"""
Regenerated PAN Card Document
=============================
Improved styling, larger text sizes, clearer company name.
Fixed font paths for Windows OS.
"""

from PIL import Image, ImageDraw, ImageFont
import math
import os

OUT = "fake_docs_v2"
os.makedirs(OUT, exist_ok=True)

E = {
    "company":        "NEXA URBAN DEVELOPERS PRIVATE LIMITED",
    "company_pan":    "AACCN4587K",
    "incorp_date":    "11/07/2019",
}

def make_pan_card():
    path = f"{OUT}/01_Company_PAN_Card_Regenerated.png"

    CW, CH = 1012, 638   # standard card ratio at high res
    img  = Image.new("RGB", (CW, CH), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # ── Background gradient simulation (light blue strips) ──────
    for i in range(CH):
        t = i / CH
        r = int(230 + (245 - 230) * t)
        g = int(240 + (250 - 240) * t)
        b = int(255)
        draw.line([(0, i), (CW, i)], fill=(r, g, b))

    # ── Top orange stripe (Income Tax dept color) ────────────────
    draw.rectangle([0, 0, CW, 90], fill=(255, 153, 0))

    # ── Ashoka chakra placeholder (circle with spokes) ───────────
    cx, cy, cr = 80, 45, 30
    draw.ellipse([cx-cr, cy-cr, cx+cr, cy+cr], outline=(255,255,255), width=3)
    for i in range(24):
        angle = math.radians(i * 15)
        x1 = cx + int((cr-8) * math.cos(angle))
        y1 = cy + int((cr-8) * math.sin(angle))
        x2 = cx + int(cr * math.cos(angle))
        y2 = cy + int(cr * math.sin(angle))
        draw.line([x1, y1, x2, y2], fill=(255, 255, 255), width=1)

    # ── Header text ──────────────────────────────────────────────
    try:
        # Better font paths for Windows
        font_hdr   = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 28)
        font_sub   = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
        font_label = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)
        font_value = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 24)
        font_pan   = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 52)
        font_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
        
        # Mangal or Nirmala UI for Hindi/Devanagari text
        try:
            font_hindi = ImageFont.truetype("C:/Windows/Fonts/mangal.ttf", 28)
        except:
            font_hindi = ImageFont.truetype("C:/Windows/Fonts/Nirmala.ttf", 28)
    except:
        font_hdr = font_sub = font_label = font_value = font_pan = font_small = font_hindi = ImageFont.load_default()

    # Hindi + English header
    draw.text((120, 10), "आयकर विभाग", font=font_hindi, fill=(255, 255, 255))
    draw.text((120, 48), "INCOME TAX DEPARTMENT", font=font_sub, fill=(255, 255, 255))
    draw.text((650, 10), "भारत सरकार", font=font_hindi, fill=(255, 255, 255))
    draw.text((650, 48), "GOVT. OF INDIA", font=font_sub, fill=(255, 255, 255))

    # ── Horizontal divider ───────────────────────────────────────
    draw.rectangle([0, 90, CW, 95], fill=(0, 80, 160))

    # ── Company name ─────────────────────────────────────────────
    draw.text((50, 115), "Name", font=font_label, fill=(80, 80, 80))
    draw.text((50, 145), E["company"], font=font_value, fill=(0, 0, 0))

    # ── Date of Registration ─────────────────────────────────────
    draw.text((50, 210), "Date of Registration / Incorporation", font=font_label, fill=(80, 80, 80))
    draw.text((50, 240), E["incorp_date"], font=font_value, fill=(0, 0, 0))

    # ── Divider line ─────────────────────────────────────────────
    draw.rectangle([40, 300, CW - 40, 303], fill=(200, 200, 200))

    # ── PAN label ────────────────────────────────────────────────
    draw.text((50, 315), "Permanent Account Number", font=font_label, fill=(80, 80, 80))

    # ── PAN number (bold, large, prominent) ──────────────────────
    draw.text((50, 348), E["company_pan"], font=font_pan, fill=(0, 60, 160))

    # ── 4th character annotation ─────────────────────────────────
    draw.text((50, 420), "4th character 'C' denotes — Company", font=font_small, fill=(120, 120, 120))

    # ── IT Dept seal (circle) ────────────────────────────────────
    sx, sy, sr = 860, 420, 80
    draw.ellipse([sx-sr, sy-sr, sx+sr, sy+sr], outline=(0, 80, 160), width=4)
    draw.ellipse([sx-sr+8, sy-sr+8, sx+sr-8, sy+sr-8], outline=(0, 80, 160), width=2)
    draw.text((sx-55, sy-18), "INCOME TAX", font=font_small, fill=(0, 80, 160))
    draw.text((sx-46, sy+6), "DEPARTMENT", font=font_small, fill=(0, 80, 160))

    # ── Bottom strip ─────────────────────────────────────────────
    draw.rectangle([0, CH - 70, CW, CH], fill=(0, 80, 160))
    draw.text((50, CH - 52), "This card is issued under section 139A of the Income Tax Act, 1961",
              font=font_small, fill=(255, 255, 255))
    draw.text((50, CH - 30), "FAKE DOCUMENT — FOR OCR TESTING PURPOSES ONLY",
              font=font_small, fill=(255, 200, 0))

    # ── Microprint border ────────────────────────────────────────
    draw.rectangle([0, 0, CW-1, CH-1], outline=(0, 80, 160), width=6)
    draw.rectangle([6, 6, CW-7, CH-7], outline=(255, 153, 0), width=2)

    img.save(path, dpi=(300, 300))
    print(f"✅ Company PAN Card Regenerated: {path}")
    return path

if __name__ == '__main__':
    make_pan_card()

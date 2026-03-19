"""
NBFC Compliance — Complete Fake Document Generator
====================================================
Generates all 7 KYC compliance documents for OCR testing:

  1.  Company PAN Card           (PNG image — real card look)
  2.  GST Certificate            (PDF)
  3.  LEI Certificate            (PDF)
  4.  Certificate of Incorporation (PDF)
  5.  MOA                        (PDF)
  6.  AOA                        (PDF)
  7.  Registered Address INC-22  (PDF)
  8.  Electricity Bill           (PDF)
  9.  Telephone / Landline Bill  (PDF)

Entity: MANIKANDAN CONSTRUCTIONS PVT LTD
All data is 100% fake — for OCR testing only.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFont
import os, math

OUT = "fake_docs_v2"
os.makedirs(OUT, exist_ok=True)

W, H = A4  # 595 x 842 pts

# ── Shared entity ─────────────────────────────────────────────
E = {
    "company":        "MANIKANDAN CONSTRUCTIONS PVT LTD",
    "company_pan":    "AAKCM1234C",
    "company_gstin":  "33AAKCM1234C1ZP",
    "company_lei":    "335800AAKCM12345678X",
    "cin":            "U45200TN2015PTC123456",
    "incorp_date":    "15/04/2015",
    "director":       "D MANIKANDAN",
    "director_pan":   "BNZPM2501F",
    "director2":      "S RAJESHWARI",
    "addr1":          "No. 14, Second Floor, Anna Salai",
    "addr2":          "Teynampet, Chennai - 600018",
    "state":          "Tamil Nadu",
    "state_code":     "33",
    "pincode":        "600018",
    "auth_capital":   "25,00,000",
    "email":          "info@manikandanconstructions.in",
    "phone":          "044-28140055",
    "mobile":         "9884012345",
    "roc":            "Registrar of Companies, Tamil Nadu, Chennai",
}


# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════
def hdr(c, title, subtitle, bg="#1a3c6e", h=75):
    c.setFillColor(colors.HexColor(bg))
    c.rect(0, H - h, W, h, fill=1, stroke=0)
    # emblem circle
    c.setFillColor(colors.HexColor("#c0a020"))
    c.circle(W / 2, H - h / 2, 24, fill=1, stroke=0)
    c.setFillColor(colors.HexColor(bg))
    c.setFont("Helvetica-Bold", 5.5)
    c.drawCentredString(W / 2, H - h / 2 + 4, "GOVT.")
    c.drawCentredString(W / 2, H - h / 2 - 4, "OF INDIA")
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W / 2, H - h + 28, title)
    c.setFont("Helvetica", 8.5)
    c.drawCentredString(W / 2, H - h + 14, subtitle)

def band(c, y, text, bg="#1a3c6e"):
    c.setFillColor(colors.HexColor(bg))
    c.rect(40, y - 5, W - 80, 17, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(48, y, text)
    return y - 24

def row(c, y, label, value, lx=48, vx=265, size=8.5):
    c.setFont("Helvetica-Bold", size)
    c.setFillColor(colors.HexColor("#333333"))
    c.drawString(lx, y, label)
    c.setFont("Helvetica", size)
    c.setFillColor(colors.black)
    c.drawString(vx, y, f":  {value}")
    c.setStrokeColor(colors.HexColor("#eeeeee"))
    c.setLineWidth(0.3)
    c.line(lx, y - 4, W - lx, y - 4)
    return y - 16

def ftr(c, text, bg="#1a3c6e"):
    c.setFillColor(colors.HexColor(bg))
    c.rect(0, 0, W, 22, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 7)
    c.drawCentredString(W / 2, 8, text)

def border(c, color="#c0a020"):
    c.setStrokeColor(colors.HexColor(color))
    c.setLineWidth(1.2)
    c.rect(25, 25, W - 50, H - 110, fill=0, stroke=1)


# ═══════════════════════════════════════════════════════════════════════
# 1. COMPANY PAN CARD  (PNG — real card look)
# ═══════════════════════════════════════════════════════════════════════
def make_pan_card():
    path = f"{OUT}/01_Company_PAN_Card.png"

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
        font_hdr   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_sub   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        font_value = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_pan   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        font_hindi = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        font_hdr = font_sub = font_label = font_value = font_pan = font_small = font_hindi = ImageFont.load_default()

    # Hindi + English header
    draw.text((120, 10), "आयकर विभाग", font=font_hdr, fill=(255, 255, 255))
    draw.text((120, 48), "INCOME TAX DEPARTMENT", font=font_sub, fill=(255, 255, 255))
    draw.text((650, 10), "भारत सरकार", font=font_hdr, fill=(255, 255, 255))
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
    draw.text((50, 415), "4th character 'C' denotes — Company", font=font_small, fill=(120, 120, 120))

    # ── IT Dept seal (circle) ────────────────────────────────────
    sx, sy, sr = 860, 420, 80
    draw.ellipse([sx-sr, sy-sr, sx+sr, sy+sr], outline=(0, 80, 160), width=4)
    draw.ellipse([sx-sr+8, sy-sr+8, sx+sr-8, sy+sr-8], outline=(0, 80, 160), width=2)
    draw.text((sx-55, sy-18), "INCOME TAX", font=font_small, fill=(0, 80, 160))
    draw.text((sx-42, sy+2), "DEPARTMENT", font=font_small, fill=(0, 80, 160))

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
    print(f"✅ Company PAN Card: {path}")
    return path


# ═══════════════════════════════════════════════════════════════════════
# 2. GST CERTIFICATE
# ═══════════════════════════════════════════════════════════════════════
def make_gst():
    path = f"{OUT}/02_GST_Certificate.pdf"
    c = canvas.Canvas(path, pagesize=A4)
    bg = "#1a3c6e"

    hdr(c, "GOODS AND SERVICES TAX — REGISTRATION CERTIFICATE",
        "Government of India  |  Ministry of Finance  |  FORM GST REG-06", bg=bg)
    border(c)

    y = H - 100
    c.setFillColor(colors.HexColor(bg))
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W/2, y, "CERTIFICATE OF REGISTRATION")
    y -= 14
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawCentredString(W/2, y, "[See Rule 10(1) of the CGST Rules, 2017]")
    y -= 18

    # GSTIN highlight box
    c.setFillColor(colors.HexColor("#eef2fa"))
    c.roundRect(40, y-32, W-80, 36, 5, fill=1, stroke=0)
    c.setFillColor(colors.HexColor(bg))
    c.setFont("Helvetica-Bold", 8.5)
    c.drawCentredString(W/2, y-8, "GSTIN  (Goods and Services Tax Identification Number)")
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(W/2, y-26, E["company_gstin"])
    y -= 48

    y = band(c, y, "REGISTRATION DETAILS", bg=bg)
    fields = [
        ("Legal Name of Business",       E["company"]),
        ("Trade Name",                   E["company"]),
        ("Constitution of Business",     "Private Limited Company"),
        ("PAN",                          E["company_pan"]),
        ("Date of Liability",            "15/04/2015"),
        ("Type of Registration",         "Regular"),
        ("Period of Validity",           "15/04/2015  to  Till Cancelled"),
        ("Nature of Business Activity",  "Construction of Buildings / Civil Engineering"),
        ("Status",                       "ACTIVE"),
    ]
    for lbl, val in fields:
        y = row(c, y, lbl, val)
    y -= 6

    y = band(c, y, "PRINCIPAL PLACE OF BUSINESS", bg=bg)
    for lbl, val in [
        ("Address Line 1", E["addr1"]),
        ("Address Line 2", E["addr2"]),
        ("PIN Code",       E["pincode"]),
        ("State",          f"{E['state']}  |  State Code: {E['state_code']}"),
    ]:
        y = row(c, y, lbl, val)
    y -= 6

    y = band(c, y, "APPROVING AUTHORITY", bg=bg)
    for lbl, val in [
        ("Designation",           "Assistant Commissioner, CGST, Chennai South"),
        ("Centre Jurisdiction",   "Range: Anna Salai, Division: Chennai South"),
        ("State Jurisdiction",    "State: Tamil Nadu, Zone: Chennai"),
        ("Date of Issue",         "20/04/2015"),
    ]:
        y = row(c, y, lbl, val)
    y -= 10

    c.setFillColor(colors.HexColor("#888888"))
    c.setFont("Helvetica-Oblique", 7.5)
    c.drawString(40, y, "This is a system generated certificate. Verify at: https://www.gst.gov.in")
    c.drawString(40, y-12, "FAKE DOCUMENT — FOR OCR TESTING PURPOSES ONLY")

    ftr(c, f"GSTN  |  East Wing, World Mark-1, Aerocity, New Delhi  |  {E['company_gstin']}", bg=bg)
    c.save()
    print(f"✅ GST Certificate: {path}")
    return path


# ═══════════════════════════════════════════════════════════════════════
# 3. LEI CERTIFICATE
# ═══════════════════════════════════════════════════════════════════════
def make_lei():
    path = f"{OUT}/03_LEI_Certificate.pdf"
    c = canvas.Canvas(path, pagesize=A4)
    bg = "#00467f"

    hdr(c, "LEGAL ENTITY IDENTIFIER — CERTIFICATE OF REGISTRATION",
        "Global Legal Entity Identifier Foundation (GLEIF)  |  India LEI Issuer: CRISIL", bg=bg)
    border(c, color="#00467f")

    y = H - 100
    c.setFillColor(colors.HexColor(bg))
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W/2, y, "LEI REGISTRATION CERTIFICATE")
    y -= 14
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawCentredString(W/2, y, "[Issued under ISO 17442 Standard  |  Endorsed by Financial Stability Board]")
    y -= 18

    # LEI highlight
    c.setFillColor(colors.HexColor("#e8f4fd"))
    c.roundRect(40, y-32, W-80, 36, 5, fill=1, stroke=0)
    c.setFillColor(colors.HexColor(bg))
    c.setFont("Helvetica-Bold", 8.5)
    c.drawCentredString(W/2, y-8, "LEI CODE  (Legal Entity Identifier — 20 Characters)")
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(W/2, y-26, E["company_lei"])
    y -= 48

    y = band(c, y, "ENTITY DETAILS", bg=bg)
    for lbl, val in [
        ("Legal Name",                E["company"]),
        ("Legal Form",                "Private Limited Company"),
        ("Jurisdiction",              "India"),
        ("Registration Authority",    "Registrar of Companies, Tamil Nadu"),
        ("Registration Number (CIN)", E["cin"]),
        ("PAN",                       E["company_pan"]),
        ("GSTIN",                     E["company_gstin"]),
    ]:
        y = row(c, y, lbl, val)
    y -= 6

    y = band(c, y, "REGISTERED ADDRESS", bg=bg)
    for lbl, val in [
        ("Address",  f"{E['addr1']}, {E['addr2']}"),
        ("City",     "Chennai"),
        ("State",    E["state"]),
        ("Country",  "India"),
        ("PIN Code", E["pincode"]),
    ]:
        y = row(c, y, lbl, val)
    y -= 6

    y = band(c, y, "LEI REGISTRATION STATUS", bg=bg)
    for lbl, val in [
        ("LEI Status",             "ACTIVE"),
        ("Initial Registration",   "20/04/2015"),
        ("Last Update",            "01/04/2024"),
        ("Next Renewal Date",      "01/04/2025"),
        ("Issuing LOU",            "CRISIL Limited — LEI Issuer, India"),
        ("Corroboration Level",    "FULLY_CORROBORATED"),
    ]:
        y = row(c, y, lbl, val)
    y -= 12

    # Status badge
    c.setFillColor(colors.HexColor("#e8f5e9"))
    c.roundRect(40, y-16, 180, 22, 4, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#2e7d32"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(55, y-8, "STATUS :  ACTIVE")
    y -= 30

    c.setFillColor(colors.HexColor("#888888"))
    c.setFont("Helvetica-Oblique", 7.5)
    c.drawString(40, y, "Verify at: https://www.gleif.org/lei  |  FAKE DOCUMENT — FOR OCR TESTING ONLY")

    ftr(c, f"GLEIF  |  Winterthur, Switzerland  |  LEI: {E['company_lei']}", bg=bg)
    c.save()
    print(f"✅ LEI Certificate: {path}")
    return path


# ═══════════════════════════════════════════════════════════════════════
# 4. CERTIFICATE OF INCORPORATION
# ═══════════════════════════════════════════════════════════════════════
def make_incorporation():
    path = f"{OUT}/04_Certificate_of_Incorporation.pdf"
    c = canvas.Canvas(path, pagesize=A4)
    bg = "#1a3c6e"

    c.setStrokeColor(colors.HexColor(bg))
    c.setLineWidth(4)
    c.rect(12, 12, W-24, H-24, fill=0, stroke=1)
    c.setStrokeColor(colors.HexColor("#c0a020"))
    c.setLineWidth(1.5)
    c.rect(18, 18, W-36, H-36, fill=0, stroke=1)

    # Emblem
    c.setFillColor(colors.HexColor(bg))
    c.circle(W/2, H-65, 35, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#c0a020"))
    c.circle(W/2, H-65, 32, fill=1, stroke=0)
    c.setFillColor(colors.HexColor(bg))
    c.setFont("Helvetica-Bold", 6.5)
    c.drawCentredString(W/2, H-61, "MINISTRY OF")
    c.drawCentredString(W/2, H-71, "CORP AFFAIRS")

    y = H - 112
    c.setFillColor(colors.HexColor(bg))
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W/2, y, "MINISTRY OF CORPORATE AFFAIRS — GOVERNMENT OF INDIA")
    y -= 15
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#444444"))
    c.drawCentredString(W/2, y, "REGISTRAR OF COMPANIES, TAMIL NADU, CHENNAI")
    y -= 20
    c.setStrokeColor(colors.HexColor("#c0a020"))
    c.setLineWidth(1.5)
    c.line(50, y, W-50, y)
    y -= 22

    c.setFillColor(colors.HexColor(bg))
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(W/2, y, "CERTIFICATE OF INCORPORATION")
    y -= 16
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawCentredString(W/2, y, "[Pursuant to Section 7(2) of the Companies Act, 2013]")
    y -= 28

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    c.drawCentredString(W/2, y, "I hereby certify that")
    y -= 28

    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor(bg))
    c.drawCentredString(W/2, y, E["company"])
    y -= 22
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawCentredString(W/2, y, "is this day incorporated under the Companies Act, 2013")
    y -= 15
    c.drawCentredString(W/2, y, "and that the company is LIMITED.")
    y -= 30

    c.setFillColor(colors.HexColor("#eef2fa"))
    c.roundRect(50, y-130, W-100, 135, 6, fill=1, stroke=0)

    for lbl, val in [
        ("Corporate Identity Number (CIN)", E["cin"]),
        ("PAN of Company",                 E["company_pan"]),
        ("Date of Incorporation",          E["incorp_date"]),
        ("Type of Company",                "Company Limited by Shares"),
        ("Sub Category",                   "Non-Government Company"),
        ("Authorized Capital",             f"Rs. {E['auth_capital']}/- (Twenty Five Lakhs)"),
        ("Registered State",               E["state"]),
        ("ROC",                            "Chennai"),
    ]:
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(colors.HexColor(bg))
        c.drawString(65, y-10, lbl)
        c.setFont("Helvetica", 8.5)
        c.setFillColor(colors.black)
        c.drawString(310, y-10, f":  {val}")
        y -= 16

    y -= 20
    c.setFont("Helvetica", 9.5)
    c.drawCentredString(W/2, y,
        "Given under my hand at Chennai this Fifteenth day of April, Two Thousand Fifteen.")
    y -= 40

    # Sig
    c.setLineWidth(0.8)
    c.setStrokeColor(colors.black)
    c.line(340, y, 530, y)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(340, y-14, "For Registrar of Companies")
    c.drawString(340, y-28, "Tamil Nadu, Chennai")

    # Seal
    c.setStrokeColor(colors.HexColor(bg))
    c.setLineWidth(2)
    c.circle(110, y-15, 38, fill=0, stroke=1)
    c.setLineWidth(1)
    c.circle(110, y-15, 32, fill=0, stroke=1)
    c.setFillColor(colors.HexColor(bg))
    c.setFont("Helvetica-Bold", 6.5)
    c.drawCentredString(110, y-10, "OFFICE SEAL")
    c.drawCentredString(110, y-22, "ROC — CHENNAI")

    y -= 60
    c.setStrokeColor(colors.HexColor("#c0a020"))
    c.setLineWidth(1)
    c.line(50, y, W-50, y)
    y -= 14
    c.setFillColor(colors.HexColor("#888888"))
    c.setFont("Helvetica-Oblique", 7.5)
    c.drawCentredString(W/2, y, "Verify at: www.mca.gov.in  |  FAKE DOCUMENT — FOR OCR TESTING ONLY")

    c.setFillColor(colors.HexColor(bg))
    c.rect(12, 12, W-24, 20, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 7)
    c.drawCentredString(W/2, 19, f"MCA  |  CIN: {E['cin']}  |  www.mca.gov.in")

    c.save()
    print(f"✅ Certificate of Incorporation: {path}")
    return path


# ═══════════════════════════════════════════════════════════════════════
# 5. MOA
# ═══════════════════════════════════════════════════════════════════════
def make_moa():
    path = f"{OUT}/05_MOA.pdf"
    c = canvas.Canvas(path, pagesize=A4)
    bg = "#1a3c6e"

    hdr(c, "MEMORANDUM OF ASSOCIATION — COMPANIES ACT, 2013",
        f"CIN: {E['cin']}  |  {E['company']}", bg=bg)
    border(c)

    y = H - 100
    c.setFillColor(colors.HexColor(bg))
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W/2, y, "MEMORANDUM OF ASSOCIATION")
    y -= 13
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawCentredString(W/2, y, "[Section 4, Companies Act 2013  |  Rule 13, Companies (Incorporation) Rules 2014]")
    y -= 20

    def clause(y, num, title, lines):
        y = band(c, y, f"CLAUSE {num} — {title}", bg=bg)
        c.setFont("Helvetica", 8.5)
        c.setFillColor(colors.black)
        for l in lines:
            c.drawString(48, y, l)
            y -= 13
        return y - 6

    y = clause(y, "I", "NAME", [
        f"The name of the Company is  {E['company']}",
    ])
    y = clause(y, "II", "REGISTERED OFFICE", [
        f"The Registered Office of the Company will be situated in the State of {E['state']}.",
        f"Address: {E['addr1']}, {E['addr2']}",
        f"PIN: {E['pincode']}  |  ROC: Registrar of Companies, Tamil Nadu, Chennai",
    ])
    y = clause(y, "III", "OBJECTS OF THE COMPANY", [
        "MAIN OBJECTS:",
        "1. To carry on the business of civil engineering, construction and contracting of all kinds,",
        "   including residential, commercial buildings, roads, bridges, dams and infrastructure.",
        "2. To purchase, take on lease or otherwise acquire lands, buildings and property.",
        "3. To carry on the business of real estate developers and builders.",
        "4. To undertake development of townships, housing colonies and residential complexes.",
        "5. To act as project management consultants for construction projects.",
    ])
    y = clause(y, "IV", "LIABILITY", [
        "The liability of the members is LIMITED to the amount unpaid on shares held by them.",
    ])
    y = clause(y, "V", "SHARE CAPITAL", [
        f"Authorized Capital: Rs. {E['auth_capital']}/- (Twenty Five Lakhs Only)",
        "Divided into 2,50,000 Equity Shares of Rs. 10/- (Ten) each.",
    ])

    y = band(c, y, "CLAUSE VI — SUBSCRIBERS", bg=bg)
    # Table
    c.setFillColor(colors.HexColor("#dce6f4"))
    c.rect(40, y-4, W-80, 16, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.HexColor(bg))
    for x, t in [(48,"Name"),(200,"Father's Name"),(350,"Address"),(490,"Shares")]:
        c.drawString(x, y, t)
    y -= 18
    for name, father, shares in [
        (E["director"],  "DURAISAMY",    "50,000"),
        (E["director2"], "K SELVAKUMAR", "50,000"),
    ]:
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.black)
        c.drawString(48,  y, name)
        c.drawString(200, y, father)
        c.drawString(350, y, E["addr1"][:22])
        c.drawString(490, y, shares)
        y -= 15
    y -= 10

    # Sig
    c.setLineWidth(0.5)
    c.setStrokeColor(colors.HexColor("#aaaaaa"))
    c.line(40, y, W-40, y)
    y -= 16
    for name in [E["director"], E["director2"]]:
        c.setLineWidth(0.6)
        c.setStrokeColor(colors.black)
        c.line(48, y, 220, y)
        c.line(320, y, 500, y)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(colors.HexColor("#666666"))
        c.drawString(48,  y-11, f"Signature: {name}")
        c.drawString(320, y-11, "Witness Signature")
        y -= 28

    c.setFont("Helvetica-Oblique", 7.5)
    c.setFillColor(colors.HexColor("#888888"))
    c.drawString(40, y-8, "FAKE DOCUMENT — FOR OCR TESTING PURPOSES ONLY")

    ftr(c, f"MOA  |  {E['company']}  |  CIN: {E['cin']}", bg=bg)
    c.save()
    print(f"✅ MOA: {path}")
    return path


# ═══════════════════════════════════════════════════════════════════════
# 6. AOA
# ═══════════════════════════════════════════════════════════════════════
def make_aoa():
    path = f"{OUT}/06_AOA.pdf"
    c = canvas.Canvas(path, pagesize=A4)
    bg = "#2e5900"

    hdr(c, "ARTICLES OF ASSOCIATION — COMPANIES ACT, 2013",
        f"CIN: {E['cin']}  |  {E['company']}", bg=bg)
    border(c, color="#4caf50")

    y = H - 100
    c.setFillColor(colors.HexColor(bg))
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W/2, y, "ARTICLES OF ASSOCIATION")
    y -= 13
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawCentredString(W/2, y, "[Section 5, Companies Act 2013  |  Table F of Schedule I]")
    y -= 14
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.black)
    c.drawCentredString(W/2, y, f"OF  {E['company']}")
    y -= 20

    def article(y, num, title, clauses):
        y = band(c, y, f"ARTICLE {num} — {title}", bg=bg)
        for cn, text in clauses:
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(colors.HexColor("#333333"))
            c.drawString(48, y, f"{cn}.")
            c.setFont("Helvetica", 8)
            c.setFillColor(colors.black)
            # wrap
            words = text.split()
            line, lines = "", []
            for w in words:
                test = (line + " " + w).strip()
                if len(test) < 90:
                    line = test
                else:
                    lines.append(line)
                    line = w
            lines.append(line)
            for i, l in enumerate(lines):
                c.drawString(62, y - i*12, l)
            y -= len(lines)*12 + 6
        return y - 4

    y = article(y, "1", "INTERPRETATION", [
        ("1.1", f"'Act' means the Companies Act, 2013. 'Company' means {E['company']}."),
        ("1.2", "'Directors' means the Directors for the time being of the Company."),
    ])
    y = article(y, "2", "SHARE CAPITAL", [
        ("2.1", f"Authorized Capital: Rs. {E['auth_capital']}/- divided into 2,50,000 Equity Shares of Rs. 10/- each."),
        ("2.2", "The Company may issue shares at par, at a premium, or at a discount as per the Act."),
        ("2.3", "Every share shall be distinguished by its appropriate number."),
    ])
    y = article(y, "3", "TRANSFER OF SHARES", [
        ("3.1", "Transfer shall be executed by or on behalf of both the transferor and transferee in writing."),
        ("3.2", "The Board may, in its absolute discretion, refuse to register any proposed transfer."),
        ("3.3", "No transfer shall be made to a minor or person of unsound mind."),
    ])
    y = article(y, "4", "BOARD OF DIRECTORS", [
        ("4.1", f"First Directors: (i) {E['director']}  DIN: 06712345  (ii) {E['director2']}  DIN: 07823456"),
        ("4.2", "Minimum 2 (two) and maximum 15 (fifteen) Directors at any time."),
        ("4.3", "Directors shall manage the business and affairs of the Company."),
    ])
    y = article(y, "5", "GENERAL MEETINGS", [
        ("5.1", "Annual General Meeting shall be held each year as per Section 96 of the Act."),
        ("5.2", "Minimum 21 days notice shall be given for any General Meeting."),
    ])
    y = article(y, "6", "DIVIDENDS & WINDING UP", [
        ("6.1", "No dividend shall be paid otherwise than out of profits of the Company."),
        ("6.2", "On winding up, assets shall be distributed among members in proportion to paid-up capital."),
    ])

    # Sig
    c.setLineWidth(0.5)
    c.setStrokeColor(colors.HexColor("#aaaaaa"))
    c.line(40, y, W-40, y)
    y -= 14
    c.setFont("Helvetica", 8.5)
    c.setFillColor(colors.black)
    c.drawString(48, y, "We, the subscribers, wish to be formed into a company in pursuance of these Articles.")
    y -= 22
    for name in [E["director"], E["director2"]]:
        c.setLineWidth(0.6)
        c.setStrokeColor(colors.black)
        c.line(48, y, 220, y)
        c.line(320, y, 500, y)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(colors.HexColor("#666666"))
        c.drawString(48,  y-11, f"Signature: {name}")
        c.drawString(320, y-11, "Witness Signature & Name")
        y -= 28

    c.setFont("Helvetica-Oblique", 7.5)
    c.setFillColor(colors.HexColor("#888888"))
    c.drawString(40, y-8, "FAKE DOCUMENT — FOR OCR TESTING PURPOSES ONLY")

    ftr(c, f"AOA  |  {E['company']}  |  CIN: {E['cin']}", bg=bg)
    c.save()
    print(f"✅ AOA: {path}")
    return path


# ═══════════════════════════════════════════════════════════════════════
# 7. REGISTERED ADDRESS (INC-22)
# ═══════════════════════════════════════════════════════════════════════
def make_address():
    path = f"{OUT}/07_Registered_Address_INC22.pdf"
    c = canvas.Canvas(path, pagesize=A4)
    bg = "#4a0072"

    hdr(c, "MINISTRY OF CORPORATE AFFAIRS  |  FORM INC-22",
        "Notice of Situation / Change of Registered Office", bg=bg)
    border(c, color="#9c27b0")

    y = H - 100
    c.setFillColor(colors.HexColor(bg))
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W/2, y, "CERTIFICATE OF REGISTERED OFFICE ADDRESS")
    y -= 13
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawCentredString(W/2, y, "[Section 12(2), Companies Act 2013  |  Form INC-22]")
    y -= 22

    y = band(c, y, "SECTION A — COMPANY PARTICULARS", bg=bg)
    for lbl, val in [
        ("Corporate Identity Number (CIN)",  E["cin"]),
        ("Name of the Company",              E["company"]),
        ("PAN of Company",                   E["company_pan"]),
        ("GSTIN",                            E["company_gstin"]),
        ("LEI",                              E["company_lei"]),
        ("Date of Incorporation",            E["incorp_date"]),
        ("Registrar of Companies",           E["roc"]),
        ("Email Address",                    E["email"]),
        ("Phone Number",                     E["phone"]),
    ]:
        y = row(c, y, lbl, val, vx=270)
    y -= 6

    y = band(c, y, "SECTION B — REGISTERED OFFICE ADDRESS", bg=bg)
    c.setFillColor(colors.HexColor("#f3e5f5"))
    c.roundRect(40, y-96, W-80, 100, 5, fill=1, stroke=0)
    for lbl, val in [
        ("Building / Flat No.", "No. 14, Second Floor"),
        ("Street / Road",       "Anna Salai (Mount Road)"),
        ("Area / Locality",     "Teynampet"),
        ("City / Town",         "Chennai"),
        ("District",            "Chennai"),
        ("State",               E["state"]),
        ("PIN Code",            E["pincode"]),
        ("Country",             "India"),
    ]:
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(colors.HexColor(bg))
        c.drawString(55, y-8, lbl)
        c.setFont("Helvetica", 8.5)
        c.setFillColor(colors.black)
        c.drawString(220, y-8, f":  {val}")
        y -= 12
    y -= 10

    y = band(c, y, "SECTION C — PROOF OF ADDRESS SUBMITTED", bg=bg)
    for lbl, val in [
        ("Document Type",    "Electricity Bill (TANGEDCO)"),
        ("Consumer Number",  "33-4892-0045-001"),
        ("Bill Date",        "20/11/2024"),
        ("Name on Bill",     E["company"]),
        ("Address on Bill",  f"{E['addr1']}, {E['addr2']}"),
        ("Bill Validity",    "Within 3 months — VALID"),
    ]:
        y = row(c, y, lbl, val, vx=270)
    y -= 6

    y = band(c, y, "SECTION D — DIRECTOR DECLARATION", bg=bg)
    c.setFont("Helvetica", 8.5)
    c.setFillColor(colors.black)
    for line in [
        f"I, {E['director']}, Director of {E['company']},",
        "hereby confirm that the above mentioned address is the Registered Office of the Company.",
        "All communications and notices may be served at the above address.",
        f"Declaration Date: {E['incorp_date']}",
    ]:
        c.drawString(48, y, line)
        y -= 13
    y -= 8
    c.setLineWidth(0.7)
    c.setStrokeColor(colors.black)
    c.line(48, y, 230, y)
    c.line(330, y, 520, y)
    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawString(48,  y-12, f"Signature: {E['director']}")
    c.drawString(330, y-12, "DIN: 06712345")
    y -= 28

    y = band(c, y, "SECTION E — ROC ACKNOWLEDGEMENT", bg=bg)
    c.setFillColor(colors.HexColor("#e8f5e9"))
    c.roundRect(40, y-38, W-80, 42, 4, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(colors.HexColor("#1b5e20"))
    c.drawString(55, y-10, "SRN: A12345678  |  Filing Date: 15/04/2015  |  Approved: 18/04/2015  |  STATUS: APPROVED")
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#888888"))
    c.drawString(55, y-26, "FAKE DOCUMENT — FOR OCR TESTING PURPOSES ONLY")

    ftr(c, f"MCA INC-22  |  CIN: {E['cin']}  |  www.mca.gov.in", bg=bg)
    c.save()
    print(f"✅ Registered Address INC-22: {path}")
    return path


# ═══════════════════════════════════════════════════════════════════════
# 8. ELECTRICITY BILL
# ═══════════════════════════════════════════════════════════════════════
def make_electricity():
    path = f"{OUT}/08_Electricity_Bill.pdf"
    c = canvas.Canvas(path, pagesize=A4)
    bg = "#c62828"

    hdr(c, "TAMIL NADU GENERATION AND DISTRIBUTION CORPORATION LTD (TANGEDCO)",
        "ELECTRICITY BILL  —  COMMERCIAL CONNECTION  |  Chennai South Division", bg=bg)

    y = H - 85
    # Bill ref bar
    c.setFillColor(colors.HexColor("#fff3e0"))
    c.rect(0, y-18, W, 18, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.black)
    for x, t in [(30,"Bill No: TNEB/CHN/2024/NOV/88234"),
                 (210,"Bill Date: 20/11/2024"),
                 (330,"Due Date: 05/12/2024"),
                 (450,"Period: NOV 2024")]:
        c.drawString(x, y-12, t)
    y -= 28

    # Consumer + meter split
    c.setFillColor(colors.HexColor("#e3f2fd"))
    c.roundRect(20, y-95, W/2-30, 98, 5, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#1565c0"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(30, y-10, "CONSUMER DETAILS")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)
    for lbl, val in [
        ("Consumer No",     "33-4892-0045-001"),
        ("Name",            E["company"]),
        ("Address",         E["addr1"]),
        ("",                E["addr2"]),
        ("Connection",      "Commercial LT-IIB"),
        ("Sanctioned Load", "15 KW"),
        ("Meter No",        "MTR-CHN-20240331"),
    ]:
        if lbl:
            c.setFont("Helvetica-Bold", 8)
            c.drawString(30, y-24, f"{lbl}:")
            c.setFont("Helvetica", 8)
            c.drawString(140, y-24, val)
        else:
            c.drawString(140, y-24, val)
        y -= 13
    y += 13*7   # reset y to top of box

    c.setFillColor(colors.HexColor("#f3e5f5"))
    c.roundRect(W/2+10, y-95, W/2-30, 98, 5, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#6a1b9a"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(W/2+20, y-10, "METER READING")
    c.setFillColor(colors.black)
    for lbl, val in [
        ("Previous Reading", "12,340 Units (20/10/2024)"),
        ("Present Reading",  "12,892 Units (20/11/2024)"),
        ("Units Consumed",   "552 Units"),
        ("Multiplying Factor", "1"),
        ("Adjusted Units",   "552 Units"),
    ]:
        c.setFont("Helvetica-Bold", 8)
        c.drawString(W/2+20, y-24, f"{lbl}:")
        c.setFont("Helvetica", 8)
        c.drawString(W/2+155, y-24, val)
        y -= 13

    y -= 22
    # Bill table
    c.setFillColor(colors.HexColor("#1565c0"))
    c.rect(20, y, W-40, 18, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(30, y+5, "BILL DESCRIPTION")
    c.drawRightString(390, y+5, "Amount (Rs.)")

    bill_rows = [
        ("Energy Charges (552 units @ Rs. 6.50/unit)", "3,588.00"),
        ("Fixed Charges (Commercial 15KW)",             "  450.00"),
        ("Electricity Duty @ 15%",                      "  605.70"),
        ("Meter Rent",                                   "   50.00"),
        ("Previous Arrears",                             "    0.00"),
        ("Surcharge",                                    "    0.00"),
    ]
    for i, (desc, amt) in enumerate(bill_rows):
        c.setFillColor(colors.HexColor("#f5f5f5") if i%2==0 else colors.white)
        c.rect(20, y-16, W-40, 15, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 8.5)
        c.drawString(30, y-10, desc)
        c.drawRightString(390, y-10, amt)
        y -= 15

    # Total
    c.setFillColor(colors.HexColor(bg))
    c.rect(20, y-18, W-40, 20, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(30, y-10, "TOTAL AMOUNT DUE")
    c.drawRightString(390, y-10, "Rs.  4,693.70")
    y -= 30

    c.setFont("Helvetica-Oblique", 8.5)
    c.setFillColor(colors.black)
    c.drawString(30, y, "Amount in words: Rupees Four Thousand Six Hundred Ninety Three and Seventy Paise Only")
    y -= 22

    # Payment
    c.setFillColor(colors.HexColor("#e8f5e9"))
    c.roundRect(20, y-42, W-40, 46, 5, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#1b5e20"))
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(30, y-8, "PAYMENT OPTIONS")
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.black)
    c.drawString(30, y-22, "Online: www.tangedco.gov.in  |  NEFT/RTGS  |  TANGEDCO Customer Service Centre")
    c.drawString(30, y-34, f"Phone: 1912 (Helpline)  |  Email: helpdesk@tangedco.gov.in")

    y -= 55
    c.setFont("Helvetica-Oblique", 7.5)
    c.setFillColor(colors.HexColor("#888888"))
    c.drawString(30, y, "FAKE DOCUMENT — FOR OCR TESTING PURPOSES ONLY")

    ftr(c, "TANGEDCO  |  144, Anna Salai, Chennai - 600002  |  1912 (Helpline)", bg=bg)
    c.save()
    print(f"✅ Electricity Bill: {path}")
    return path


# ═══════════════════════════════════════════════════════════════════════
# 9. TELEPHONE / LANDLINE BILL
# ═══════════════════════════════════════════════════════════════════════
def make_telephone():
    path = f"{OUT}/09_Telephone_Landline_Bill.pdf"
    c = canvas.Canvas(path, pagesize=A4)
    bg = "#01579b"

    hdr(c, "BHARAT SANCHAR NIGAM LIMITED (BSNL)",
        "TELEPHONE BILL  —  LANDLINE CONNECTION  |  Chennai Telephones", bg=bg)

    y = H - 85
    c.setFillColor(colors.HexColor("#e1f5fe"))
    c.rect(0, y-18, W, 18, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.black)
    for x, t in [(30, "Bill No: BSNL/CHN/LL/2024/NOV/44512"),
                 (220,"Bill Date: 25/11/2024"),
                 (340,"Due Date: 10/12/2024"),
                 (450,"Period: NOV 2024")]:
        c.drawString(x, y-12, t)
    y -= 30

    # Account details
    c.setFillColor(colors.HexColor("#e3f2fd"))
    c.roundRect(20, y-110, W-40, 112, 5, fill=1, stroke=0)
    c.setFillColor(colors.HexColor(bg))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(30, y-12, "ACCOUNT & CONNECTION DETAILS")
    c.setFillColor(colors.black)

    acc_fields = [
        ("Account Number",      "TN-CHN-044-28140055"),
        ("Telephone Number",    "044-28140055"),
        ("Connection Type",     "Landline — Commercial (BT Basic)"),
        ("Account Name",        E["company"]),
        ("Billing Address",     E["addr1"]),
        ("",                    E["addr2"]),
        ("PIN Code",            E["pincode"]),
        ("Circle",              "Chennai Telephones"),
        ("Customer ID",         "BSNL-CID-20150420-8812"),
        ("Connection Date",     "20/04/2015"),
        ("Plan",                "BT Combo ULD 599"),
    ]
    ay = y - 28
    for lbl, val in acc_fields:
        if lbl:
            c.setFont("Helvetica-Bold", 8)
            c.drawString(30, ay, f"{lbl}:")
            c.setFont("Helvetica", 8)
            c.drawString(180, ay, val)
        else:
            c.setFont("Helvetica", 8)
            c.drawString(180, ay, val)
        ay -= 11

    y = ay - 16

    # Bill breakdown
    c.setFillColor(colors.HexColor(bg))
    c.rect(20, y, W-40, 18, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(30, y+5, "CHARGE DESCRIPTION")
    c.drawString(320, y+5, "Units / Mins")
    c.drawRightString(555, y+5, "Amount (Rs.)")

    tel_rows = [
        ("Monthly Rental — BT Combo ULD 599",    "—",        "599.00"),
        ("Local Calls (included in plan)",        "0 Mins",   "  0.00"),
        ("STD Calls",                             "45 Mins",  " 67.50"),
        ("ISD Calls",                             "0 Mins",   "  0.00"),
        ("Broadband Charges (if bundled)",         "—",        "  0.00"),
        ("GST @ 18%",                             "—",        "120.15"),
        ("Previous Arrears",                      "—",        "  0.00"),
        ("Late Payment Surcharge",                "—",        "  0.00"),
    ]
    for i, (desc, units, amt) in enumerate(tel_rows):
        c.setFillColor(colors.HexColor("#f5f5f5") if i%2==0 else colors.white)
        c.rect(20, y-15, W-40, 15, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 8.5)
        c.drawString(30, y-9, desc)
        c.drawString(320, y-9, units)
        c.drawRightString(555, y-9, amt)
        y -= 15

    # Total
    c.setFillColor(colors.HexColor(bg))
    c.rect(20, y-18, W-40, 20, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(30, y-10, "TOTAL AMOUNT DUE")
    c.drawRightString(555, y-10, "Rs.  786.65")
    y -= 32

    c.setFont("Helvetica-Oblique", 8.5)
    c.setFillColor(colors.black)
    c.drawString(30, y, "Amount in words: Rupees Seven Hundred Eighty Six and Sixty Five Paise Only")
    y -= 20

    # Call detail
    c.setFillColor(colors.HexColor("#e8f5e9"))
    c.roundRect(20, y-55, W-40, 58, 5, fill=1, stroke=0)
    c.setFillColor(colors.HexColor(bg))
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(30, y-10, "CALL DETAIL SUMMARY")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8.5)
    for line in [
        "Local Calls: 0 chargeable mins (unlimited included in plan)",
        "STD Calls: 45 mins @ Rs. 1.50/min = Rs. 67.50",
        "ISD Calls: 0 mins",
        "Free SMS: Included in plan",
    ]:
        y -= 13
        c.drawString(30, y, line)
    y -= 20

    # Payment
    c.setFillColor(colors.HexColor("#fff8e1"))
    c.roundRect(20, y-38, W-40, 42, 5, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#e65100"))
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(30, y-10, "PAYMENT OPTIONS")
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.black)
    c.drawString(30, y-23, "Online: www.bsnl.co.in  |  NACH/Auto-debit  |  Nearest BSNL Customer Service Centre")
    c.drawString(30, y-35, "Helpline: 1800-345-1500 (Toll Free)  |  Email: chennai.pgm@bsnl.co.in")
    y -= 50

    c.setFont("Helvetica-Oblique", 7.5)
    c.setFillColor(colors.HexColor("#888888"))
    c.drawString(30, y, "FAKE DOCUMENT — FOR OCR TESTING PURPOSES ONLY")

    ftr(c, "BSNL Chennai Telephones  |  9th Floor, BSNL House, Greams Road, Chennai - 600006  |  1800-345-1500",
        bg=bg)
    c.save()
    print(f"✅ Telephone Bill: {path}")
    return path


# ═══════════════════════════════════════════════════════════════════════
# RUN ALL
# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  NBFC Compliance — Complete Fake Document Generator")
    print("="*60 + "\n")

    paths = []
    paths.append(make_pan_card())
    paths.append(make_gst())
    paths.append(make_lei())
    paths.append(make_incorporation())
    paths.append(make_moa())
    paths.append(make_aoa())
    paths.append(make_address())
    paths.append(make_electricity())
    paths.append(make_telephone())

    print(f"\n{'='*60}")
    print(f"  ✅ All 9 documents saved to ./{OUT}/")
    print(f"{'='*60}")
    print("""
  Document Index:
  ───────────────────────────────────────────────────
  01  Company PAN Card          (PNG)
  02  GST Certificate           (PDF)
  03  LEI Certificate           (PDF)
  04  Certificate of Incorp.    (PDF)
  05  MOA                       (PDF)
  06  AOA                       (PDF)
  07  Registered Address INC-22 (PDF)
  08  Electricity Bill          (PDF)
  09  Telephone / Landline Bill (PDF)
  ───────────────────────────────────────────────────
  Entity   : MANIKANDAN CONSTRUCTIONS PVT LTD
  PAN      : AAKCM1234C  (Company — 4th char C)
  GSTIN    : 33AAKCM1234C1ZP
  CIN      : U45200TN2015PTC123456
  LEI      : 335800AAKCM12345678X
  Director : D MANIKANDAN  (PAN: BNZPM2501F)
  ───────────────────────────────────────────────────
  Ready for OCR pipeline testing.
""")

import os
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas as rl_canvas

# ═══════════════════════════════════════════════════════════
# CONFIGURATION & DIRECTORY SETUP
# ═══════════════════════════════════════════════════════════
FRAUD_DIR = Path('ocr_test_docs_v2')
FRAUD_DIR.mkdir(exist_ok=True)
W, H = A4

# ── HELPER FUNCTIONS ────────────────────────────────────────

def _hdr(c, title, bg='#004d40'):
    """Generates the document header with company name."""
    c.setFillColor(colors.HexColor(bg))
    c.rect(0, H-52, W, 52, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 12)
    c.drawCentredString(W/2, H-24, title)
    c.setFont('Helvetica', 8.5)
    c.drawCentredString(W/2, H-40, 'VIGNESHWARA TECH-LOGISTICS SOLUTIONS PVT LTD  |  SYNTHETIC TEST DATA')

def _row(c, y, label, value):
    """Generates a formatted data row for OCR extraction."""
    c.setFont('Helvetica-Bold', 8.5)
    c.setFillColor(colors.black)
    c.drawString(50, y, label)
    c.setFont('Helvetica', 8.5)
    c.drawString(210, y, f': {value}')
    c.setStrokeColor(colors.HexColor('#dddddd'))
    c.setLineWidth(0.3)
    c.line(50, y-4, W-50, y-4)
    return y - 15

def _section(c, y, title, bg='#004d40'):
    """Generates a colored section sub-header."""
    c.setFillColor(colors.HexColor(bg))
    c.rect(40, y-5, W-80, 17, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 8.5)
    c.drawString(48, y, title)
    return y - 22

# ── DOCUMENT GENERATORS ──────────────────────────────────────

def make_board_of_directors():
    path = str(FRAUD_DIR / '10_Board_of_Directors.pdf')
    c = rl_canvas.Canvas(path, pagesize=A4)
    _hdr(c, 'ANNEXURE: BOARD OF DIRECTORS LIST')
    y = H - 68
    c.setFont('Helvetica-Bold', 10)
    c.setFillColor(colors.HexColor('#004d40'))
    c.drawString(50, y, 'Entity: VIGNESHWARA TECH-LOGISTICS SOLUTIONS PVT LTD')
    y -= 14
    c.setFont('Helvetica', 9)
    # CIN Pattern: U + Industry Code + State + Year + PTC + ID
    c.drawString(50, y, 'CIN: U72900MH2018PTC315689  |  PAN: AAFCV0982E  |  Valid as of: 10/01/2026')
    y -= 28
    
    directors = [
        {'name': 'KARTIK VIGNESH', 'din': '08124567', 'pan': 'BOPPK4412Q', 'dob': '05/11/1982',
         'designation': 'Executive Director', 'shareholding': '65%',
         'address': 'Flat 402, Sai Enclave, Powai, Mumbai - 400076',
         'nationality': 'Indian', 'other': 'OMNI-CARGO SOLUTIONS (Since 2021)'},
        {'name': 'ANANYA IYER', 'din': '09235678', 'pan': 'AZZPI1109L', 'dob': '12/01/1990',
         'designation': 'Non-Executive Director', 'shareholding': '35%',
         'address': 'Plot 88, Jubilee Hills, Hyderabad - 500033',
         'nationality': 'Indian', 'other': 'NIL'},
    ]
    
    for i, d in enumerate(directors):
        c.setFillColor(colors.HexColor('#f1f8e9'))
        c.rect(40, y-118, W-80, 122, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#004d40'))
        c.setFont('Helvetica-Bold', 10)
        c.drawString(50, y-10, f'ID: {i+1} | {d["name"]}')
        y2 = y - 26
        for label, key in [
            ('DIN','din'),('PAN','pan'),('DOB','dob'),
            ('Role','designation'),('Equity','shareholding'),
            ('Residential Address','address'),('Citizenship','nationality'),
            ('External Boards','other')
        ]:
            y2 = _row(c, y2, label, d[key])
        y = y2 - 18
    c.save()
    return path

def make_kmp_list():
    path = str(FRAUD_DIR / '11_KMP_List.pdf')
    c = rl_canvas.Canvas(path, pagesize=A4)
    _hdr(c, 'REGISTER OF KEY MANAGERIAL PERSONNEL', bg='#1565c0')
    y = H - 68
    kmps = [
        {'name': 'KARTIK VIGNESH', 'role': 'CEO & MD',
         'ids': 'DIN: 08124567 | PAN: BOPPK4412Q',
         'email': 'kv@vigneshwara.tech', 'mob': '+91 90000 11223'},
        {'name': 'RAHUL DESHMUKH', 'role': 'Chief Financial Officer',
         'ids': 'PAN: AFSPD9081G',
         'email': 'rahul.d@vigneshwara.tech', 'mob': '+91 98220 33445'},
    ]
    for k in kmps:
        c.setFillColor(colors.HexColor('#e3f2fd'))
        c.rect(40, y-72, W-80, 76, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#1565c0'))
        c.setFont('Helvetica-Bold', 10)
        c.drawString(50, y-10, f"{k['name']} - {k['role']}")
        y2 = y - 26
        for label, key in [('Identification','ids'),('Corporate Email','email'),('Mobile','mob')]:
            y2 = _row(c, y2, label, k[key])
        y = y2 - 18
    c.save()
    return path

def make_beneficial_owners():
    path = str(FRAUD_DIR / '12_Beneficial_Owners.pdf')
    c = rl_canvas.Canvas(path, pagesize=A4)
    _hdr(c, 'SIGNIFICANT BENEFICIAL OWNERSHIP (SBO) DECLARATION', bg='#4527a0')
    y = H - 68
    c.setFont('Helvetica', 9)
    c.setFillColor(colors.black)
    c.drawString(50, y, 'Form No. BEN-2: Return to the Registrar in respect of declaration under Section 90')
    y -= 22
    y = _section(c, y, 'PART A: INDIVIDUAL BENEFICIAL OWNERS', bg='#4527a0')
    
    ubos = [
        {'name': 'KARTIK VIGNESH', 'pan': 'BOPPK4412Q',
         'direct': '65%', 'indirect': '15% via KV FAMILY TRUST',
         'total': '80%', 'nature': 'Owner with Majority Voting Rights',
         'date': '12/01/2026'},
        {'name': 'SIVARAMAN IYER', 'pan': 'AIXPI5521M',
         'direct': '5%', 'indirect': '15% via IYER HOLDINGS',
         'total': '20%', 'nature': 'Significant Influence via Associate',
         'date': '15/01/2026'},
    ]
    for o in ubos:
        c.setFillColor(colors.HexColor('#ede7f6'))
        c.rect(40, y-86, W-80, 90, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#4527a0'))
        c.setFont('Helvetica-Bold', 10)
        c.drawString(50, y-10, f"UBO Name: {o['name']}  |  Tax ID: {o['pan']}")
        y2 = y - 26
        for label, key in [('Direct Stake','direct'),('Indirect Stake','indirect'),('Total','total'),('Control Nature','nature'),('Date','date')]:
            y2 = _row(c, y2, label, o[key])
        y = y2 - 18
    c.save()
    return path

def make_pep_declaration():
    path = str(FRAUD_DIR / '13_PEP_Declaration.pdf')
    c = rl_canvas.Canvas(path, pagesize=A4)
    _hdr(c, 'POLITICALLY EXPOSED PERSONS (PEP) CLEARANCE', bg='#c62828')
    y = H - 68
    c.setFont('Helvetica', 9)
    c.setFillColor(colors.black)
    c.drawString(50, y, 'Compliance Check: Prevention of Money Laundering Act (PMLA), 2002')
    y -= 36
    persons = [
        {'name': 'KARTIK VIGNESH', 'role': 'Managing Director', 'status': 'NEGATIVE (NOT A PEP)',
         'sign': 'Digital Signature Verified - KV 2026'},
        {'name': 'ANANYA IYER', 'role': 'Non-Executive Director', 'status': 'NEGATIVE (NOT A PEP)',
         'sign': 'Digital Signature Verified - AI 2026'},
    ]
    for p in persons:
        c.setFillColor(colors.HexColor('#ffebee'))
        c.rect(40, y-60, W-80, 64, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#c62828'))
        c.setFont('Helvetica-Bold', 10)
        c.drawString(50, y-10, f"Person: {p['name']} ({p['role']})")
        y2 = y - 26
        for label, key in [('PEP Status','status'),('Validation','sign')]:
            y2 = _row(c, y2, label, p[key])
        y = y2 - 18
    c.save()
    return path

def make_rpt_document():
    path = str(FRAUD_DIR / '14_RPT_Disclosure.pdf')
    c = rl_canvas.Canvas(path, pagesize=A4)
    _hdr(c, 'RELATED PARTY TRANSACTIONS (RPT) DISCLOSURE', bg='#0277bd')
    y = H - 68
    c.setFont('Helvetica', 9)
    c.drawString(50, y, 'Disclosures as per Ind AS 24 and Section 188 of the Companies Act')
    y -= 24
    rpts = [
        {'party': 'OMNI-CARGO SOLUTIONS LTD', 'rel': 'Common Directorship',
         'type': 'Lease of Equipment', 'val': 'INR 1,25,00,000', 'risk': 'STABLE'},
        {'party': 'KV FAMILY TRUST', 'rel': 'Majority Shareholder',
         'type': 'Unsecured Loan', 'val': 'INR 50,00,000', 'risk': 'LOW RISK'},
    ]
    for rpt in rpts:
        c.setFillColor(colors.HexColor('#e1f5fe'))
        c.rect(40, y-90, W-80, 94, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#0277bd'))
        c.setFont('Helvetica-Bold', 10)
        c.drawString(50, y-10, f"Related Entity: {rpt['party']}")
        y2 = y - 26
        for label, key in [('Relationship','rel'),('Transaction','type'),('Value','val'),('Risk','risk')]:
            y2 = _row(c, y2, label, rpt[key])
        y = y2 - 18
    c.save()
    return path

# ── EXECUTION ───────────────────────────────────────────────

if __name__ == "__main__":
    print(f'Starting generation in directory: {FRAUD_DIR}...')
    docs = [
        make_board_of_directors(),
        make_kmp_list(),
        make_beneficial_owners(),
        make_pep_declaration(),
        make_rpt_document()
    ]
    for d in docs:
        print(f' SUCCESS: {os.path.basename(d)}')
    print('\nAll 5 synthetic test documents are ready for your OCR pipeline.')
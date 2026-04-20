"""
PDF Export Service — generates compliance and fraud reports using reportlab
LLM narrative via qwen2.5:3b
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Color palette ─────────────────────────────────────────────
BRAND_DARK = colors.HexColor("#0f172a")  # Slate 900
BRAND_MID  = colors.HexColor("#334155")  # Slate 700
BRAND_LIGHT= colors.HexColor("#f8fafc")  # Slate 50
GREEN      = colors.HexColor("#166534")  # Green 800
RED        = colors.HexColor("#991b1b")  # Red 800
AMBER      = colors.HexColor("#9a3412")  # Orange 800
GREY       = colors.HexColor("#475569")  # Slate 600
LIGHT      = colors.HexColor("#f1f5f9")  # Slate 100
WHITE      = colors.white


def _styles():
    base = getSampleStyleSheet()
    return {
        "title":    ParagraphStyle("title",   fontSize=18, fontName="Helvetica-Bold", textColor=BRAND_DARK,  spaceAfter=6),
        "h2":       ParagraphStyle("h2",      fontSize=12, fontName="Helvetica-Bold", textColor=BRAND_DARK,  spaceAfter=6, spaceBefore=16),
        "h3":       ParagraphStyle("h3",      fontSize=10, fontName="Helvetica-Bold", textColor=BRAND_MID,   spaceAfter=4, spaceBefore=12),
        "body":     ParagraphStyle("body",    fontSize=9,  fontName="Helvetica",      textColor=GREY,        spaceAfter=5, leading=13),
        "mono":     ParagraphStyle("mono",    fontSize=8,  fontName="Courier",        textColor=BRAND_DARK),
        "center":   ParagraphStyle("center",  fontSize=9,  fontName="Helvetica",      alignment=TA_CENTER,   textColor=GREY),
        "left":     ParagraphStyle("left",    fontSize=9,  fontName="Helvetica",      alignment=TA_LEFT,     textColor=BRAND_DARK),
        "right":    ParagraphStyle("right",   fontSize=9,  fontName="Helvetica",      alignment=TA_RIGHT,    textColor=BRAND_DARK),
        "pass":     ParagraphStyle("pass",    fontSize=9,  fontName="Helvetica-Bold", textColor=GREEN),
        "fail":     ParagraphStyle("fail",    fontSize=9,  fontName="Helvetica-Bold", textColor=RED),
        "warn":     ParagraphStyle("warn",    fontSize=9,  fontName="Helvetica-Bold", textColor=AMBER),
        "small":    ParagraphStyle("small",   fontSize=7,  fontName="Helvetica",      textColor=GREY),
        "banner":   ParagraphStyle("banner",  fontSize=10, fontName="Helvetica-Bold", alignment=TA_CENTER,   textColor=WHITE),
    }


def _header_table(company: str, pan: str, report_type: str, date_str: str, analyst: str) -> Table:
    data = [[
        Paragraph(f"<b>PRAMANIK REGTECH</b><br/><font size='8' color='#475569'>NBFC Compliance Platform</font>", _styles()["left"]),
        Paragraph(f"<b>{report_type.upper()} REPORT</b><br/><font size='8' color='#475569'>{date_str}</font>", _styles()["center"]),
        Paragraph(f"<b>{company}</b><br/><font size='8' color='#475569'>PAN: {pan} · Analyst: {analyst}</font>", _styles()["right"]),
    ]]
    t = Table(data, colWidths=[6*cm, 7*cm, 6*cm])
    t.setStyle(TableStyle([
        ("VALIGN",      (0,0), (-1,0), "MIDDLE"),
        ("LINEBELOW",   (0,0), (-1,0), 0.5, BRAND_MID),
        ("BOTTOMPADDING",(0,0), (-1,0), 8),
    ]))
    return t


def _kv_table(rows: list, col_widths=None) -> Table:
    """Key-value two-column table"""
    data = [[Paragraph(f"<b>{k}</b>", _styles()["small"]),
             Paragraph(str(v), _styles()["body"])] for k, v in rows]
    cw = col_widths or [5*cm, 14*cm]
    t  = Table(data, colWidths=cw)
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (0,-1), BRAND_LIGHT),
        ("FONTNAME",    (0,0), (0,-1), "Helvetica-Bold"),
        ("GRID",        (0,0), (-1,-1), 0.25, colors.HexColor("#cbd5e1")),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    return t


def _status_badge(status: str):
    status = str(status).upper()
    color_map = {
        "PASS": "#166534", "ACTIVE": "#166534", "ISSUED": "#166534",
        "VALID": "#166534", "EXTRACTED": "#166534", "LOW": "#166534",
        "FAIL": "#991b1b", "FAILED": "#991b1b", "NOT_FOUND": "#991b1b", "HIGH": "#991b1b",
        "MEDIUM": "#9a3412", "PARTIAL": "#9a3412",
    }
    c = color_map.get(status, "#475569")
    return Paragraph(f'<font color="{c}"><b>[{status}]</b></font>', _styles()["body"])


# ── Compliance PDF ────────────────────────────────────────────
async def generate_compliance_pdf(session_data: dict, llm_narrative: str = "") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    s  = _styles()
    story = []

    meta      = session_data.get("session", {})
    docs      = session_data.get("documents", [])
    cross     = session_data.get("cross_check", {})
    api_verif = session_data.get("api_verification", {})
    company   = meta.get("company_name") or "N/A"
    pan       = meta.get("pan", "N/A")
    analyst   = session_data.get("analyst_name", "System")
    date_str  = datetime.now().strftime("%d %b %Y %H:%M")
    verdict   = cross.get("verdict", "UNKNOWN")

    # Header
    story.append(_header_table(company, pan, "COMPLIANCE", date_str, analyst))
    story.append(Spacer(1, 10))

    # Overall verdict banner
    v_color = GREEN if verdict == "PASS" else (AMBER if verdict == "PARTIAL" else RED)
    banner_data = [[Paragraph(f"<b>COMPLIANCE VERDICT: {verdict}</b>  |  "
                               f"Consistent: {len(cross.get('passed',[]))}  |  "
                               f"Anomalies: {len(cross.get('failed',[]))}  |  "
                               f"Warnings: {len(cross.get('warnings',[]))}", s["banner"])]]
    banner = Table(banner_data, colWidths=[19.0*cm])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), v_color),
        ("ROWHEIGHT",  (0,0), (-1,-1), 24),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
    ]))
    story.append(banner)
    story.append(Spacer(1, 12))

    # LLM narrative
    if llm_narrative:
        story.append(Paragraph("Executive Summary", s["h2"]))
        for para in llm_narrative.split("\n"):
            para = para.strip()
            if para:
                story.append(Paragraph(para, s["body"]))
                story.append(Spacer(1, 4))
        story.append(Spacer(1, 8))

    # Session info
    story.append(Paragraph("Session Details", s["h2"]))
    story.append(_kv_table([
        ("Company", company),
        ("PAN",     pan),
        ("Session", meta.get("id", "N/A")),
        ("Date",    date_str),
        ("Analyst", analyst),
    ]))
    story.append(Spacer(1, 12))

    # Cross-check results
    story.append(Paragraph("Cross-Check Results", s["h2"]))

    # Passed params
    if cross.get("passed"):
        story.append(Paragraph("Consistent Parameters", s["h3"]))
        table_data = [[
            Paragraph("<b>Parameter</b>", s["banner"]), 
            Paragraph("<b>Value</b>", s["banner"]), 
            Paragraph("<b>Documents</b>", s["banner"])
        ]]
        for p in cross["passed"]:
            doc_list = p.get("docs", [])
            # Cleaner display for many documents
            doc_text = ", ".join(doc_list)
            if len(doc_list) >= 4:
                doc_text = "PRESENT IN ALL RELEVANT DOCUMENTS"

            table_data.append([
                Paragraph(p.get("parameter", ""), s["body"]),
                Paragraph(p.get("value", ""), s["body"]),
                Paragraph(doc_text, s["body"]),
            ])
        t = Table(table_data, colWidths=[4.0*cm, 5.5*cm, 7.9*cm], repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,0), BRAND_MID),
            ("GRID",         (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
            ("BACKGROUND",   (0,1), (-1,-1), colors.HexColor("#f8fafc")),
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING",  (0,0), (-1,-1), 5),
            ("TOPPADDING",   (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

    # Failed params
    if cross.get("failed"):
        story.append(Paragraph("Anomalies Detected", s["h3"]))
        for f in cross["failed"]:
            all_doc_types = list(f.get("all_values", {}).keys())
            bad_docs = f.get("inconsistent_docs", [])
            good_docs = [d for d in all_doc_types if d not in bad_docs]
            
            # User request: "ALL EXCEPT X" or "NONE EXCEPT X"
            if not good_docs:
                consist_text = "NONE (TOTAL MISMATCH)"
            elif len(good_docs) >= len(bad_docs):
                consist_text = f"ALL EXCEPT {', '.join(bad_docs)}"
            else:
                consist_text = f"NONE EXCEPT {', '.join(good_docs)}"

            block_data = [
                [Paragraph(f"<b>Parameter: {f['parameter']}</b>", s["fail"]),
                 Paragraph(f"Expected: <b>{f.get('majority_value','')}</b>", s["body"])],
                [Paragraph(f"<b>IS CONSISTENT:</b> {consist_text}", s["warn"]),
                 Paragraph(f"Found: {', '.join(f.get('inconsistent_values',[]))}", s["body"])],
            ]
            bt = Table(block_data, colWidths=[8.7*cm, 8.7*cm])
            bt.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,-1), colors.HexColor("#fef2f2")),
                ("BOX",         (0,0), (-1,-1), 1, RED),
                ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#fecaca")),
                ("VALIGN",      (0,0), (-1,-1), "TOP"),
                ("TOPPADDING",  (0,0), (-1,-1), 6),
                ("BOTTOMPADDING",(0,0),(-1,-1), 6),
                ("LEFTPADDING", (0,0), (-1,-1), 6),
            ]))
            story.append(KeepTogether(bt))
            story.append(Spacer(1, 6))

    story.append(Spacer(1, 10))

    # API Verification results
    if api_verif:
        story.append(Paragraph("API Verification Results", s["h2"]))
        api_rows = [["Check", "Source", "Status", "Detail"]]
        for key, label, detail_field in [
            ("pan",     "PAN",     "name"),
            ("gst",     "GST",     "legal_name"),
            ("lei",     "LEI",     "corroboration"),
            ("cin",     "CIN",     "roc"),
            ("pincode", "Pincode", "district"),
        ]:
            r = api_verif.get(key, {})
            if r:
                status  = r.get("status", "N/A")
                api_rows.append([
                    Paragraph(label, s["body"]),
                    Paragraph(r.get("source", ""), s["body"]),
                    _status_badge(status),
                    Paragraph(r.get(detail_field, ""), s["body"]),
                ])
        at = Table(api_rows, colWidths=[3*cm, 5*cm, 3.5*cm, 5.9*cm], repeatRows=1)
        at.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), BRAND_MID),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
            ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 5),
            ("TOPPADDING",  (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ]))
        story.append(KeepTogether(at))
        story.append(Spacer(1, 10))

    # Document table
    if docs:
        story.append(Paragraph("Extracted Documents", s["h2"]))
        doc_rows = [["Document", "Status", "Confidence", "File"]]
        for d in docs:
            conf = int((d.get("confidence", 0.9)) * 100)
            doc_rows.append([
                Paragraph(d.get("doc_type", "").replace("_", " "), s["body"]),
                _status_badge(d.get("status", "")),
                Paragraph(f"{conf}%", s["body"]),
                Paragraph(d.get("source_file", ""), s["body"]),
            ])
        dt = Table(doc_rows, colWidths=[5*cm, 3.5*cm, 2.5*cm, 6.4*cm], repeatRows=1)
        dt.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), BRAND_MID),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
            ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 5),
            ("TOPPADDING",  (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ]))
        story.append(KeepTogether(dt))

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1")))
    story.append(Paragraph(
        "CONFIDENTIAL — Generated by Pramanik RegTech Platform. For internal NBFC compliance use only.",
        s["small"],
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ── Fraud PDF ─────────────────────────────────────────────────
async def generate_fraud_pdf(fraud_data: dict, llm_narrative: str = "") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    s     = _styles()
    story = []

    company   = fraud_data.get("company", "N/A")
    pan       = fraud_data.get("pan", "N/A")
    analyst   = fraud_data.get("analyst_name", "System")
    date_str  = datetime.now().strftime("%d %b %Y %H:%M")
    risk_score = fraud_data.get("risk_score", 0)
    risk_level = fraud_data.get("risk_level", "UNKNOWN")
    persons    = fraud_data.get("persons", [])
    rpt        = fraud_data.get("rpt", [])
    nlp        = fraud_data.get("nlp_summary", [])
    graph      = fraud_data.get("entity_graph", {})
    flags      = fraud_data.get("flags", [])

    story.append(_header_table(company, pan, "FRAUD DETECTION", date_str, analyst))
    story.append(Spacer(1, 10))

    # Risk banner
    r_color = GREEN if risk_level == "LOW" else (AMBER if risk_level == "MEDIUM" else RED)
    banner_data = [[Paragraph(
        f"<b>RISK SCORE: {risk_score}/100  |  LEVEL: {risk_level}  |  "
        f"FLAGS: {', '.join(flags) if flags else 'None'}</b>", s["banner"]
    )]]
    banner = Table(banner_data, colWidths=[19.0*cm])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), r_color),
        ("ROWHEIGHT",  (0,0), (-1,-1), 24),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
    ]))
    story.append(banner)
    story.append(Spacer(1, 12))

    # LLM narrative
    if llm_narrative:
        story.append(Paragraph("AI Risk Analysis Summary", s["h2"]))
        for para in llm_narrative.split("\n"):
            para = para.strip()
            if para:
                story.append(Paragraph(para, s["body"]))
                story.append(Spacer(1, 4))
        story.append(Spacer(1, 8))

    # NLP Summary points
    if nlp:
        story.append(Paragraph("Risk Summary Points", s["h2"]))
        for i, pt in enumerate(nlp, 1):
            bg = colors.HexColor("#f8fafc") if i == len(nlp) else LIGHT
            pt_data = [[Paragraph(f"<b>{i}</b>", s["body"]), Paragraph(str(pt), s["body"])]]
            pt_t = Table(pt_data, colWidths=[1*cm, 18*cm])
            pt_t.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,-1), bg),
                ("FONTSIZE",   (0,0), (-1,-1), 8),
                ("TOPPADDING", (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
                ("LEFTPADDING",  (0,0), (-1,-1), 5),
                ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
            ]))
            story.append(pt_t)
            story.append(Spacer(1, 2))
        story.append(Spacer(1, 10))

    # Risk overview
    story.append(Paragraph("Risk Overview", s["h2"]))
    story.append(_kv_table([
        ("Risk Score",      f"{risk_score}/100"),
        ("Risk Level",      risk_level),
        ("Recommendation",  fraud_data.get("recommendation", "")),
        ("Active Flags",    ", ".join(flags) or "None"),
        ("Entity Graph",    f"{len(graph.get('nodes',[]))} nodes, {len(graph.get('edges',[]))} edges"),
        ("PEP Flags",       str(sum(1 for p in persons if p.get("pep")))),
        ("RPT Entities",    str(len(rpt))),
    ]))
    story.append(Spacer(1, 12))

    # Persons table
    if persons:
        story.append(Paragraph("Persons of Interest", s["h2"]))
        p_rows = [["Name", "Role", "DIN", "PAN", "PEP", "Risk"]]
        for p in persons:
            p_rows.append([
                Paragraph(p.get("name", ""), s["body"]),
                Paragraph(p.get("role", ""), s["body"]),
                Paragraph(p.get("din", ""), s["body"]),
                Paragraph(p.get("pan", ""), s["body"]),
                Paragraph("YES" if p.get("pep") else "No", s["body"]),
                Paragraph(str(p.get("riskScore", 0)), s["body"]),
            ])
        pt = Table(p_rows, colWidths=[4.5*cm, 3*cm, 3*cm, 3*cm, 1.5*cm, 2.4*cm], repeatRows=1)
        pt.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), BRAND_MID),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
            ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 5),
            ("TOPPADDING",  (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ]))
        story.append(KeepTogether(pt))
        story.append(Spacer(1, 10))

    # RPT table
    if rpt:
        story.append(Paragraph("Related Party Transactions", s["h2"]))
        r_rows = [["Entity", "Relationship", "Type", "Amount", "Risk", "Flag Reason"]]
        for r in rpt:
            lvl = r.get("riskLevel", "LOW")
            r_rows.append([
                Paragraph(r.get("entity", ""), s["body"]),
                Paragraph(r.get("relationship", ""), s["body"]),
                Paragraph(r.get("transactionType", ""), s["body"]),
                Paragraph(str(r.get("amount", "")), s["body"]),
                _status_badge(lvl),
                Paragraph(r.get("flagReason", ""), s["body"]),
            ])
        rt = Table(r_rows, colWidths=[3*cm, 3*cm, 3*cm, 2*cm, 2*cm, 4.4*cm], repeatRows=1)
        rt.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), BRAND_MID),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
            ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 5),
            ("TOPPADDING",  (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ]))
        story.append(KeepTogether(rt))

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1")))
    story.append(Paragraph(
        "CONFIDENTIAL — Generated by Pramanik RegTech Platform. For internal NBFC use only.",
        s["small"],
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()

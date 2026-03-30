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
BLUE   = colors.HexColor("#1a56db")
GREEN  = colors.HexColor("#057a55")
RED    = colors.HexColor("#c81e1e")
AMBER  = colors.HexColor("#92400e")
GREY   = colors.HexColor("#6b7280")
LIGHT  = colors.HexColor("#f3f4f6")
WHITE  = colors.white
DARK   = colors.HexColor("#111827")


def _styles():
    base = getSampleStyleSheet()
    return {
        "title":    ParagraphStyle("title",   fontSize=18, fontName="Helvetica-Bold", textColor=DARK,  spaceAfter=6),
        "h2":       ParagraphStyle("h2",      fontSize=13, fontName="Helvetica-Bold", textColor=BLUE,  spaceAfter=4, spaceBefore=14),
        "h3":       ParagraphStyle("h3",      fontSize=11, fontName="Helvetica-Bold", textColor=DARK,  spaceAfter=3, spaceBefore=10),
        "body":     ParagraphStyle("body",    fontSize=9,  fontName="Helvetica",      textColor=GREY,  spaceAfter=4, leading=14),
        "mono":     ParagraphStyle("mono",    fontSize=8,  fontName="Courier",        textColor=DARK),
        "center":   ParagraphStyle("center",  fontSize=9,  fontName="Helvetica",      alignment=TA_CENTER, textColor=GREY),
        "pass":     ParagraphStyle("pass",    fontSize=9,  fontName="Helvetica-Bold", textColor=GREEN),
        "fail":     ParagraphStyle("fail",    fontSize=9,  fontName="Helvetica-Bold", textColor=RED),
        "warn":     ParagraphStyle("warn",    fontSize=9,  fontName="Helvetica-Bold", textColor=AMBER),
        "small":    ParagraphStyle("small",   fontSize=7,  fontName="Helvetica",      textColor=GREY),
    }


def _header_table(company: str, pan: str, report_type: str, date_str: str, analyst: str) -> Table:
    data = [[
        Paragraph(f"<b>PRAMANIK REGTECH</b><br/><font size='8'>NBFC Compliance Platform</font>", _styles()["center"]),
        Paragraph(f"<b>{report_type.upper()} REPORT</b><br/><font size='8'>{date_str}</font>", _styles()["center"]),
        Paragraph(f"<b>{company}</b><br/><font size='8'>PAN: {pan} · Analyst: {analyst}</font>", _styles()["center"]),
    ]]
    t = Table(data, colWidths=[5.5*cm, 8*cm, 6.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), BLUE),
        ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,0), 9),
        ("ALIGN",       (0,0), (-1,0), "CENTER"),
        ("VALIGN",      (0,0), (-1,0), "MIDDLE"),
        ("ROWHEIGHT",   (0,0), (-1,0), 30),
        ("GRID",        (0,0), (-1,-1), 0.3, colors.white),
    ]))
    return t


def _kv_table(rows: list, col_widths=None) -> Table:
    """Key-value two-column table"""
    data = [[Paragraph(f"<b>{k}</b>", _styles()["small"]),
             Paragraph(str(v), _styles()["body"])] for k, v in rows]
    cw = col_widths or [5*cm, 14*cm]
    t  = Table(data, colWidths=cw)
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (0,-1), LIGHT),
        ("FONTNAME",    (0,0), (0,-1), "Helvetica-Bold"),
        ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",  (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    return t


def _status_badge(status: str) -> str:
    color_map = {
        "PASS": "#057a55", "ACTIVE": "#057a55", "Active": "#057a55", "ISSUED": "#057a55",
        "Valid": "#057a55", "EXTRACTED": "#057a55",
        "FAIL": "#c81e1e", "FAILED": "#c81e1e", "NOT_FOUND": "#c81e1e",
        "MEDIUM": "#92400e", "PARTIAL": "#92400e",
        "LOW": "#057a55", "HIGH": "#c81e1e",
    }
    c = color_map.get(status, "#6b7280")
    return f'<font color="{c}"><b>[{status}]</b></font>'


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
                               f"Warnings: {len(cross.get('warnings',[]))}", s["center"])]]
    banner = Table(banner_data, colWidths=[19*cm])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), v_color),
        ("TEXTCOLOR",  (0,0), (-1,-1), WHITE),
        ("ROWHEIGHT",  (0,0), (-1,-1), 24),
        ("FONTNAME",   (0,0), (-1,-1), "Helvetica-Bold"),
    ]))
    story.append(banner)
    story.append(Spacer(1, 12))

    # LLM narrative
    if llm_narrative:
        story.append(Paragraph("Executive Summary", s["h2"]))
        story.append(Paragraph(llm_narrative, s["body"]))
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
        table_data = [["Parameter", "Value", "Documents"]]
        for p in cross["passed"]:
            table_data.append([
                p.get("parameter", ""),
                p.get("value", ""),
                ", ".join(p.get("docs", [])),
            ])
        t = Table(table_data, colWidths=[4.5*cm, 5*cm, 9.5*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,0), GREEN),
            ("TEXTCOLOR",    (0,0), (-1,0), WHITE),
            ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,-1), 8),
            ("GRID",         (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
            ("BACKGROUND",   (0,1), (-1,-1), colors.HexColor("#f0fdf4")),
            ("ROWHEIGHT",    (0,0), (-1,-1), 16),
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING",  (0,0), (-1,-1), 5),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

    # Failed params
    if cross.get("failed"):
        story.append(Paragraph("Anomalies Detected", s["h3"]))
        for f in cross["failed"]:
            block_data = [
                [Paragraph(f"<b>Parameter: {f['parameter']}</b>", s["fail"]),
                 Paragraph(f"Expected: <b>{f.get('majority_value','')}</b>", s["body"])],
                [Paragraph(f"Inconsistent in: {', '.join(f.get('inconsistent_docs',[]))}", s["warn"]),
                 Paragraph(f"Found: {', '.join(f.get('inconsistent_values',[]))}", s["body"])],
            ]
            bt = Table(block_data, colWidths=[9.5*cm, 9.5*cm])
            bt.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,-1), colors.HexColor("#fff5f5")),
                ("BOX",         (0,0), (-1,-1), 1, RED),
                ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#fecaca")),
                ("FONTSIZE",    (0,0), (-1,-1), 8),
                ("TOPPADDING",  (0,0), (-1,-1), 5),
                ("BOTTOMPADDING",(0,0),(-1,-1), 5),
                ("LEFTPADDING", (0,0), (-1,-1), 6),
            ]))
            story.append(bt)
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
                    label,
                    r.get("source", ""),
                    _status_badge(status),
                    r.get(detail_field, ""),
                ])
        at = Table(api_rows, colWidths=[3*cm, 5*cm, 4.5*cm, 6.5*cm])
        at.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), BLUE),
            ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 8),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
            ("ROWHEIGHT",   (0,0), (-1,-1), 16),
            ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(at)
        story.append(Spacer(1, 10))

    # Document table
    if docs:
        story.append(Paragraph("Extracted Documents", s["h2"]))
        doc_rows = [["Document", "Status", "Confidence", "File"]]
        for d in docs:
            conf = int((d.get("confidence", 0.9)) * 100)
            doc_rows.append([
                d.get("doc_type", "").replace("_", " "),
                _status_badge(d.get("status", "")),
                f"{conf}%",
                d.get("source_file", ""),
            ])
        dt = Table(doc_rows, colWidths=[5*cm, 3.5*cm, 3*cm, 7.5*cm])
        dt.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), BLUE),
            ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 8),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
            ("ROWHEIGHT",   (0,0), (-1,-1), 15),
            ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(dt)

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GREY))
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
        f"FLAGS: {', '.join(flags) if flags else 'None'}</b>", s["center"]
    )]]
    banner = Table(banner_data, colWidths=[19*cm])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), r_color),
        ("TEXTCOLOR",  (0,0), (-1,-1), WHITE),
        ("ROWHEIGHT",  (0,0), (-1,-1), 24),
    ]))
    story.append(banner)
    story.append(Spacer(1, 12))

    # LLM narrative
    if llm_narrative:
        story.append(Paragraph("AI Risk Analysis Summary", s["h2"]))
        story.append(Paragraph(llm_narrative, s["body"]))
        story.append(Spacer(1, 8))

    # NLP Summary points
    if nlp:
        story.append(Paragraph("Risk Summary Points", s["h2"]))
        for i, pt in enumerate(nlp, 1):
            bg = colors.HexColor("#f0fdf4") if i == len(nlp) else LIGHT
            pt_data = [[Paragraph(f"<b>{i}</b>", s["body"]), Paragraph(pt, s["body"])]]
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
                p.get("name", ""),
                p.get("role", ""),
                p.get("din", ""),
                p.get("pan", ""),
                "YES" if p.get("pep") else "No",
                str(p.get("riskScore", 0)),
            ])
        pt = Table(p_rows, colWidths=[4.5*cm, 3.5*cm, 3*cm, 3*cm, 1.5*cm, 1.5*cm])
        pt.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), BLUE),
            ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 8),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
            ("ROWHEIGHT",   (0,0), (-1,-1), 15),
            ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(pt)
        story.append(Spacer(1, 10))

    # RPT table
    if rpt:
        story.append(Paragraph("Related Party Transactions", s["h2"]))
        r_rows = [["Entity", "Relationship", "Type", "Amount", "Risk", "Flag Reason"]]
        for r in rpt:
            lvl = r.get("riskLevel", "LOW")
            r_rows.append([
                r.get("entity", ""),
                r.get("relationship", ""),
                r.get("transactionType", ""),
                r.get("amount", ""),
                _status_badge(lvl),
                r.get("flagReason", ""),
            ])
        rt = Table(r_rows, colWidths=[3.5*cm, 3.5*cm, 3*cm, 2.5*cm, 2*cm, 4.5*cm])
        rt.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), BLUE),
            ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 8),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
            ("ROWHEIGHT",   (0,0), (-1,-1), 15),
            ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(rt)

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GREY))
    story.append(Paragraph(
        "CONFIDENTIAL — Generated by Pramanik RegTech Platform. For internal NBFC use only.",
        s["small"],
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()

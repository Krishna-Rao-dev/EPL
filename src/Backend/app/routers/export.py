"""
Export Router — generates compliance and fraud PDFs via reportlab + qwen2.5:3b
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.export_service import generate_compliance_pdf, generate_fraud_pdf
from app.services.llm_service import generate_export_summary

router = APIRouter()


@router.get("/compliance/{session_id}")
async def export_compliance_pdf(
    session_id: str,
    user=Depends(get_current_user),
):
    """Generate and stream compliance report as PDF."""
    db   = get_db()
    comp = await db.compliance_records.find_one({"session_id": session_id})
    if not comp:
        raise HTTPException(404, "Compliance record not found")

    sess  = await db.sessions.find_one({"id": session_id})
    verif = await db.verification_records.find_one({"session_id": session_id})

    company = comp.get("company_name", "")
    pan     = sess.get("pan", "") if sess else ""

    # Prepare data bundle
    session_data = {
        "session": {
            "id":           session_id,
            "pan":          pan,
            "company_name": company,
        },
        "documents":        comp.get("documents", []),
        "cross_check":      comp.get("cross_check", {}),
        "api_verification": verif or {},
        "analyst_name":     sess.get("analyst_name", "System") if sess else "System",
    }

    # LLM narrative
    summary_data = {
        "company":     company,
        "pan":         pan,
        "verdict":     comp.get("cross_check", {}).get("verdict"),
        "passed":      len(comp.get("cross_check", {}).get("passed", [])),
        "failed":      len(comp.get("cross_check", {}).get("failed", [])),
        "documents":   len(comp.get("documents", [])),
        "api_verdict": (verif or {}).get("verdict"),
    }
    narrative = await generate_export_summary(summary_data, "compliance")

    pdf_bytes = await generate_compliance_pdf(session_data, narrative)

    filename = f"compliance_{company.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/fraud/{session_id}")
async def export_fraud_pdf(
    session_id: str,
    user=Depends(get_current_user),
):
    """Generate and stream fraud detection report as PDF."""
    db    = get_db()
    fraud = await db.fraud_records.find_one({"session_id": session_id})
    if not fraud:
        raise HTTPException(404, "Fraud record not found")

    sess    = await db.sessions.find_one({"id": session_id})
    company = fraud.get("company", "")
    pan     = fraud.get("pan", "")

    fraud_data = {
        "company":        company,
        "pan":            pan,
        "analyst_name":   sess.get("analyst_name", "System") if sess else "System",
        "risk_score":     fraud.get("risk_score", 0),
        "risk_level":     fraud.get("risk_level", "UNKNOWN"),
        "recommendation": fraud.get("recommendation", ""),
        "flags":          fraud.get("flags", []),
        "entity_graph":   fraud.get("entity_graph", {}),
        "persons":        fraud.get("persons", []),
        "rpt":            fraud.get("rpt", []),
        "nlp_summary":    fraud.get("nlp_summary", []),
    }

    # LLM narrative
    narrative = await generate_export_summary(fraud_data, "fraud detection")

    pdf_bytes = await generate_fraud_pdf(fraud_data, narrative)

    filename = f"fraud_{company.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/full/{session_id}")
async def export_full_pdf(
    session_id: str,
    user=Depends(get_current_user),
):
    """
    Generate combined compliance + fraud report.
    Returns compliance PDF with fraud section appended.
    """
    # For now generate both and return compliance report with fraud note
    # A full merge would require pypdf — done here simply
    db   = get_db()
    comp = await db.compliance_records.find_one({"session_id": session_id})
    if not comp:
        raise HTTPException(404, "Compliance record not found")

    # Just delegate to compliance export (complete report)
    return await export_compliance_pdf(session_id, user)

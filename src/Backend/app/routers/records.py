"""
Past Records Router — real-time search, full report retrieval
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from app.core.database import get_db
from app.core.security import get_current_user
from datetime import datetime
import re

router = APIRouter()


def _serialize(doc: dict) -> dict:
    doc.pop("_id", None)
    for k, v in doc.items():
        if hasattr(v, "isoformat"):
            doc[k] = v.isoformat()
    return doc


@router.get("/search")
async def search_records(
    pan: str = Query(default=""),
    q:   str = Query(default=""),
    user=Depends(get_current_user),
):
    """
    Real-time search by PAN or company name.
    Searches compliance_records joined with fraud_records.
    """
    db = get_db()

    # Build MongoDB query
    search_term = (pan or q).strip().upper()
    if search_term:
        query = {
            "$or": [
                {"pan":          {"$regex": re.escape(search_term), "$options": "i"}},
                {"company_name": {"$regex": re.escape(search_term), "$options": "i"}},
            ]
        }
    else:
        query = {}

    cursor  = db.compliance_records.find(query).sort("created_at", -1).limit(100)
    records = []

    async for rec in cursor:
        session_id = rec.get("session_id", "")
        # Get session info for analyst name and date
        session = await db.sessions.find_one({"id": session_id})
        # Get fraud info
        fraud   = await db.fraud_records.find_one({"session_id": session_id},
                                                   {"risk_level": 1, "risk_score": 1})

        cross    = rec.get("cross_check", {})
        verdict  = cross.get("verdict", "UNKNOWN")
        pan_val  = rec.get("pan") or (session.get("pan") if session else "")
        date_val = rec.get("created_at") or (session.get("created_at") if session else datetime.utcnow())
        analyst  = session.get("analyst_name", "System") if session else "System"

        records.append({
            "id":               session_id,
            "pan":              pan_val,
            "company":          rec.get("company_name", ""),
            "date":             date_val.strftime("%Y-%m-%d") if hasattr(date_val, "strftime") else str(date_val)[:10],
            "analyst":          analyst,
            "complianceStatus": "PASS" if verdict == "PASS" else ("PARTIAL" if verdict == "PARTIAL" else "FAIL"),
            "fraudRisk":        (fraud.get("risk_level", "UNKNOWN") if fraud else "PENDING"),
            "riskScore":        (fraud.get("risk_score", None) if fraud else None),
            "session_id":       session_id,
        })

    return records


@router.get("/list")
async def list_records(
    page:  int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user=Depends(get_current_user),
):
    db     = get_db()
    skip   = (page - 1) * limit
    cursor = db.compliance_records.find({}).sort("created_at", -1).skip(skip).limit(limit)
    total  = await db.compliance_records.count_documents({})
    records = []

    async for rec in cursor:
        session_id = rec.get("session_id", "")
        session    = await db.sessions.find_one({"id": session_id})
        fraud      = await db.fraud_records.find_one({"session_id": session_id},
                                                      {"risk_level": 1})
        cross   = rec.get("cross_check", {})
        verdict = cross.get("verdict", "UNKNOWN")
        pan_val = rec.get("pan") or (session.get("pan") if session else "")
        date_v  = rec.get("created_at", datetime.utcnow())
        analyst = session.get("analyst_name", "System") if session else "System"

        records.append({
            "id":               session_id,
            "pan":              pan_val,
            "company":          rec.get("company_name", ""),
            "date":             date_v.strftime("%Y-%m-%d") if hasattr(date_v, "strftime") else str(date_v)[:10],
            "analyst":          analyst,
            "complianceStatus": "PASS" if verdict == "PASS" else ("PARTIAL" if verdict == "PARTIAL" else "FAIL"),
            "fraudRisk":        fraud.get("risk_level", "PENDING") if fraud else "PENDING",
        })

    return {"records": records, "total": total, "page": page, "limit": limit}


@router.get("/{session_id}")
async def get_record(session_id: str, user=Depends(get_current_user)):
    db      = get_db()
    comp    = await db.compliance_records.find_one({"session_id": session_id})
    fraud   = await db.fraud_records.find_one({"session_id": session_id})
    session = await db.sessions.find_one({"id": session_id})
    verif   = await db.verification_records.find_one({"session_id": session_id})

    if not comp and not fraud:
        raise HTTPException(404, "Record not found")

    result = {
        "session":          _serialize(session or {}),
        "compliance":       _serialize(comp or {}),
        "fraud":            _serialize(fraud or {}),
        "api_verification": _serialize(verif or {}),
    }
    return result


@router.get("/{session_id}/compliance")
async def get_compliance_report(session_id: str, user=Depends(get_current_user)):
    db   = get_db()
    comp = await db.compliance_records.find_one({"session_id": session_id})
    if not comp:
        raise HTTPException(404, "Compliance record not found")
    verif = await db.verification_records.find_one({"session_id": session_id})
    sess  = await db.sessions.find_one({"id": session_id})
    return {
        "session":          _serialize(sess or {}),
        "documents":        comp.get("documents", []),
        "cross_check":      comp.get("cross_check", {}),
        "company_name":     comp.get("company_name", ""),
        "ai_error_flags":   comp.get("ai_error_flags", {}),
        "api_verification": _serialize(verif or {}),
    }


@router.get("/{session_id}/fraud")
async def get_fraud_report(session_id: str, user=Depends(get_current_user)):
    db    = get_db()
    fraud = await db.fraud_records.find_one({"session_id": session_id})
    if not fraud:
        raise HTTPException(404, "Fraud record not found")
    fraud.pop("_id", None)
    if "created_at" in fraud:
        fraud["created_at"] = fraud["created_at"].isoformat()
    return fraud

"""
Verification Router — runs all API checks, returns full verification report
"""
from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.verification_service import (
    run_all_verifications,
    verify_lei_gleif,
    verify_pincode,
    sandbox_pan,
    sandbox_gst,
    sandbox_cin,
    validate_pan_format,
)
from datetime import datetime

router = APIRouter()


@router.post("/run/{session_id}")
async def run_verification(session_id: str, user=Depends(get_current_user)):
    """Run all verifications for a session and store results."""
    db  = get_db()
    rec = await db.compliance_records.find_one({"session_id": session_id})
    if not rec:
        raise HTTPException(404, "Compliance record not found. Run OCR first.")

    documents    = rec.get("documents", [])
    company_name = rec.get("company_name", "")

    result = await run_all_verifications(documents, company_name)
    result["session_id"]  = session_id
    result["verified_at"] = datetime.utcnow().isoformat()

    await db.verification_records.update_one(
        {"session_id": session_id},
        {"$set": result},
        upsert=True,
    )
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {"status": "VERIFIED"}},
    )
    return result


@router.get("/result/{session_id}")
async def get_verification(session_id: str, user=Depends(get_current_user)):
    db  = get_db()
    rec = await db.verification_records.find_one({"session_id": session_id})
    if not rec:
        raise HTTPException(404, "Verification not found. Run verification first.")
    rec.pop("_id", None)
    return rec


# ── Individual endpoints ──────────────────────────────────────
@router.get("/pan/{pan}")
async def verify_pan(pan: str, user=Depends(get_current_user)):
    return await sandbox_pan(pan)


@router.get("/gst/{gstin}")
async def verify_gst(gstin: str, user=Depends(get_current_user)):
    return await sandbox_gst(gstin)


@router.get("/lei/{lei}")
async def verify_lei(lei: str, user=Depends(get_current_user)):
    return await verify_lei_gleif(lei)


@router.get("/cin/{cin}")
async def verify_cin(cin: str, user=Depends(get_current_user)):
    return await sandbox_cin(cin)


@router.get("/pincode/{pincode}")
async def verify_pincode_route(pincode: str, user=Depends(get_current_user)):
    return await verify_pincode(pincode)

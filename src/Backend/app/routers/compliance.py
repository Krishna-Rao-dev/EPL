"""
Compliance Router — upload, OCR pipeline (SSE streaming), cross-check, AI error flagging
"""
import uuid
import json
import asyncio
from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.ocr_service import extract_text_from_bytes
from app.services.llm_service import extract_fields_llm
from app.services.cross_check_service import run_cross_checks
from app.models.schemas import AIErrorFlag

router = APIRouter()

DOC_TYPE_MAP = {
    "pan":    "PAN_CARD",
    "gst":    "GST_CERTIFICATE",
    "lei":    "LEI_CERTIFICATE",
    "incorp": "INCORPORATION_CERTIFICATE",
    "moa":    "MOA",
    "aoa":    "AOA",
    "addr":   "REGISTERED_ADDRESS",
    "elec":   "ELECTRICITY_BILL",
    "tel":    "TELEPHONE_BILL",
}


@router.post("/upload")
async def upload_documents(
    session_id: str = Form(...),
    pan:    UploadFile = File(None),
    gst:    UploadFile = File(None),
    lei:    UploadFile = File(None),
    incorp: UploadFile = File(None),
    moa:    UploadFile = File(None),
    aoa:    UploadFile = File(None),
    addr:   UploadFile = File(None),
    elec:   UploadFile = File(None),
    tel:    UploadFile = File(None),
    user=Depends(get_current_user),
):
    """Store uploaded files in MongoDB as binary."""
    db      = get_db()
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(404, "Session not found")

    uploaded = {}
    files_map = {
        "pan": pan, "gst": gst, "lei": lei, "incorp": incorp,
        "moa": moa, "aoa": aoa, "addr": addr, "elec": elec, "tel": tel,
    }

    for slot_key, upload_file in files_map.items():
        if upload_file and upload_file.filename:
            content = await upload_file.read()
            doc_type = DOC_TYPE_MAP[slot_key]
            await db.uploaded_files.update_one(
                {"session_id": session_id, "doc_type": doc_type},
                {"$set": {
                    "session_id": session_id,
                    "doc_type":   doc_type,
                    "filename":   upload_file.filename,
                    "content":    content,
                    "content_type": upload_file.content_type,
                }},
                upsert=True,
            )
            uploaded[doc_type] = upload_file.filename

    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {"status": "UPLOADED", "uploaded_docs": list(uploaded.keys())}},
    )
    return {"uploaded": uploaded, "session_id": session_id}


async def _ocr_pipeline_generator(session_id: str, db) -> AsyncGenerator[str, None]:
    """
    SSE generator: runs OCR + LLM extraction step by step,
    yields progress events, then saves results.
    """
    steps = [
        "Converting PDFs to images",
        "Preprocessing with OpenCV",
        "Running Tesseract OCR",
        "Extracting fields via Qwen2.5",
        "Running cross-checks",
        "Saving to MongoDB",
    ]
    total = len(steps)

    def sse(data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"

    yield sse({"step": steps[0], "index": 1, "total": total, "status": "running"})
    await asyncio.sleep(0.1)

    # Fetch all uploaded files
    cursor     = db.uploaded_files.find({"session_id": session_id})
    files_docs = []
    async for fd in cursor:
        files_docs.append(fd)

    yield sse({"step": steps[1], "index": 2, "total": total, "status": "running"})
    await asyncio.sleep(0.1)

    # OCR + LLM per document
    results = []
    yield sse({"step": steps[2], "index": 3, "total": total, "status": "running"})

    for fd in files_docs:
        try:
            raw_text, confidence = await extract_text_from_bytes(fd["content"], fd["filename"])
            yield sse({"step": f"OCR: {fd['filename']}", "index": 3, "total": total, "status": "running"})
        except Exception as e:
            raw_text, confidence = "", 0.0
            yield sse({"step": f"OCR error: {fd['filename']}", "index": 3, "total": total, "status": "running"})

        yield sse({"step": steps[3], "index": 4, "total": total, "status": "running"})
        try:
            fields = await extract_fields_llm(raw_text, fd["doc_type"])
            status = "EXTRACTED" if fields else "FAILED"
        except Exception as e:
            fields = {}
            status = "FAILED"

        results.append({
            "doc_type":    fd["doc_type"],
            "source_file": fd["filename"],
            "status":      status,
            "confidence":  confidence,
            "fields":      fields,
            "ocr_text":    raw_text[:500],
        })
        yield sse({"step": f"Extracted: {fd['doc_type']}", "index": 4, "total": total, "status": "running"})

    # Cross-check
    yield sse({"step": steps[4], "index": 5, "total": total, "status": "running"})
    cross_check = run_cross_checks(results)
    await asyncio.sleep(0.1)

    # Determine company name from results
    company_name = ""
    for doc in results:
        if doc["status"] == "EXTRACTED":
            fields = doc["fields"]
            name = (fields.get("entity_name") or fields.get("legal_name") or
                    fields.get("company_name") or fields.get("consumer_name") or "")
            if name and len(name) > 3:
                company_name = name
                break

    # Save to MongoDB
    yield sse({"step": steps[5], "index": 6, "total": total, "status": "running"})
    await db.compliance_records.update_one(
        {"session_id": session_id},
        {"$set": {
            "session_id":   session_id,
            "documents":    results,
            "cross_check":  cross_check,
            "company_name": company_name,
            "created_at":   datetime.utcnow(),
            "ai_error_flags": {},
        }},
        upsert=True,
    )
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {
            "status":       "OCR_COMPLETE",
            "company_name": company_name,
        }},
    )
    await asyncio.sleep(0.1)

    yield sse({
        "step":         "Complete",
        "index":        total,
        "total":        total,
        "status":       "done",
        "result": {
            "documents":  results,
            "crossCheck": cross_check,
            "company":    company_name,
        },
    })


@router.post("/ocr/{session_id}")
async def run_ocr_sse(session_id: str, user=Depends(get_current_user)):
    """SSE endpoint — streams OCR pipeline progress."""
    db = get_db()
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(404, "Session not found")
    return StreamingResponse(
        _ocr_pipeline_generator(session_id, db),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/crosscheck/{session_id}")
async def get_cross_check(session_id: str, user=Depends(get_current_user)):
    db  = get_db()
    rec = await db.compliance_records.find_one({"session_id": session_id})
    if not rec:
        raise HTTPException(404, "Compliance record not found")
    return {
        "documents":   rec.get("documents", []),
        "crossCheck":  rec.get("cross_check", {}),
        "company":     rec.get("company_name", ""),
    }


@router.patch("/aierror/{session_id}")
async def flag_ai_error(session_id: str, body: AIErrorFlag, user=Depends(get_current_user)):
    db  = get_db()
    rec = await db.compliance_records.find_one({"session_id": session_id})
    if not rec:
        raise HTTPException(404, "Compliance record not found")
    flags = rec.get("ai_error_flags", {})
    flags[body.parameter] = body.is_ai_error
    await db.compliance_records.update_one(
        {"session_id": session_id},
        {"$set": {"ai_error_flags": flags}},
    )
    return {"parameter": body.parameter, "is_ai_error": body.is_ai_error}

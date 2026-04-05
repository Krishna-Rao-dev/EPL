"""
Compliance Router — upload, OCR pipeline (SSE streaming), cross-check, AI error flagging.

Change from old version:
  - LLM extraction now goes through typed DocumentAgents
  - Each doc gets an ExtractionResult with proper status/confidence
  - DB storage shape is identical — downstream code unchanged
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
from app.services.cross_check_service import run_cross_checks
from app.models.schemas import AIErrorFlag

# Agent layer
from agents.document_agents import get_agent
from agents.base_agent import ExtractionResult

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

    uploaded  = {}
    files_map = {
        "pan": pan, "gst": gst, "lei": lei, "incorp": incorp,
        "moa": moa, "aoa": aoa, "addr": addr, "elec": elec, "tel": tel,
    }

    for slot_key, upload_file in files_map.items():
        if upload_file and upload_file.filename:
            content  = await upload_file.read()
            doc_type = DOC_TYPE_MAP[slot_key]
            await db.uploaded_files.update_one(
                {"session_id": session_id, "doc_type": doc_type},
                {"$set": {
                    "session_id":   session_id,
                    "doc_type":     doc_type,
                    "filename":     upload_file.filename,
                    "content":      content,
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


async def _process_one_document(fd: dict) -> dict:
    """
    OCR → Agent extraction for a single uploaded file.
    Returns a result dict matching the existing DB schema.
    """
    doc_type = fd["doc_type"]
    filename = fd["filename"]

    # ── OCR ──────────────────────────────────────────────────
    try:
        raw_text, confidence = await extract_text_from_bytes(fd["content"], filename)
    except Exception as e:
        print(f"⚠️ OCR failed for {filename}: {e}")
        raw_text, confidence = "", 0.0

    # ── Agent extraction (1 LLM call) ────────────────────────
    agent = get_agent(doc_type)
    if agent is None:
        print(f"⚠️ No agent registered for {doc_type}")
        return {
            "doc_type":    doc_type,
            "source_file": filename,
            "status":      "FAILED",
            "confidence":  confidence,
            "fields":      {},
            "ocr_text":    raw_text[:500],
            "error":       f"No agent for {doc_type}",
        }

    result: ExtractionResult = await agent.extract(raw_text, confidence)

    return {
        "doc_type":    doc_type,
        "source_file": filename,
        "status":      result.status,       # "EXTRACTED" | "PARTIAL" | "FAILED"
        "confidence":  result.confidence,
        "fields":      result.fields,
        "ocr_text":    raw_text[:500],
        "error":       result.error,        # None on success
    }


async def _ocr_pipeline_generator(session_id: str, db) -> AsyncGenerator[str, None]:
    """
    SSE generator: OCR + agent extraction per doc, then cross-check, then save.
    Streams progress events throughout.
    """
    steps = [
        "Fetching uploaded documents",        # 1
        "Running OCR & extraction agents",    # 2
        "Running cross-checks",               # 3
        "Saving to MongoDB",                  # 4
    ]
    total = len(steps)

    def sse(data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"

    # Step 1 — fetch files
    yield sse({"step": steps[0], "index": 1, "total": total, "status": "running"})
    cursor     = db.uploaded_files.find({"session_id": session_id})
    files_docs = []
    async for fd in cursor:
        files_docs.append(fd)

    if not files_docs:
        yield sse({"step": "No documents found", "index": 1, "total": total, "status": "error"})
        return

    # Step 2 — OCR + agent extraction, one doc at a time (sequential to avoid
    # overloading a single Ollama instance)
    yield sse({"step": steps[1], "index": 2, "total": total, "status": "running"})

    results = []
    for fd in files_docs:
        yield sse({
            "step":   f"Processing: {fd['doc_type']} ({fd['filename']})",
            "index":  2,
            "total":  total,
            "status": "running",
        })

        doc_result = await _process_one_document(fd)
        results.append(doc_result)

        yield sse({
            "step":   f"Done: {fd['doc_type']} → {doc_result['status']}",
            "index":  2,
            "total":  total,
            "status": "running",
        })

    # Step 3 — cross-check
    yield sse({"step": steps[2], "index": 3, "total": total, "status": "running"})
    cross_check = run_cross_checks(results)
    await asyncio.sleep(0.05)

    # Determine company name — walk docs in priority order
    company_name = ""
    name_priority = [
        ("PAN_CARD",                  "entity_name"),
        ("GST_CERTIFICATE",           "legal_name"),
        ("INCORPORATION_CERTIFICATE", "company_name"),
        ("MOA",                       "company_name"),
        ("REGISTERED_ADDRESS",        "company_name"),
        ("ELECTRICITY_BILL",          "consumer_name"),
    ]
    doc_fields_map = {
        r["doc_type"]: r.get("fields", {})
        for r in results
        if r["status"] == "EXTRACTED"
    }
    for dt, field in name_priority:
        name = doc_fields_map.get(dt, {}).get(field, "")
        if name and len(name) > 3:
            company_name = name
            break

    # Step 4 — save
    yield sse({"step": steps[3], "index": 4, "total": total, "status": "running"})

    await db.compliance_records.update_one(
        {"session_id": session_id},
        {"$set": {
            "session_id":     session_id,
            "documents":      results,
            "cross_check":    cross_check,
            "company_name":   company_name,
            "created_at":     datetime.utcnow(),
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

    extracted_count = sum(1 for r in results if r["status"] == "EXTRACTED")
    failed_count    = sum(1 for r in results if r["status"] == "FAILED")

    yield sse({
        "step":   "Complete",
        "index":  total,
        "total":  total,
        "status": "done",
        "result": {
            "documents":       results,
            "crossCheck":      cross_check,
            "company":         company_name,
            "extractedCount":  extracted_count,
            "failedCount":     failed_count,
        },
    })


@router.post("/ocr/{session_id}")
async def run_ocr_sse(session_id: str, user=Depends(get_current_user)):
    """SSE endpoint — streams OCR + agent extraction pipeline progress."""
    db      = get_db()
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
        "documents":  rec.get("documents", []),
        "crossCheck": rec.get("cross_check", {}),
        "company":    rec.get("company_name", ""),
    }


@router.patch("/aierror/{session_id}")
async def flag_ai_error(
    session_id: str,
    body: AIErrorFlag,
    user=Depends(get_current_user),
):
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
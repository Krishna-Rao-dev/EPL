"""
Fraud Analytics Router — upload docs, SSE pipeline, results
"""
import json
import asyncio
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.ocr_service import extract_text_from_bytes
from app.services.llm_service import extract_fields_llm, generate_nlp_summary
from app.services.fraud_service import (
    build_entity_graph, screen_pep, analyze_rpt,
    build_ownership_chains, compute_risk_score,
)

router = APIRouter()

FRAUD_DOC_TYPE_MAP = {
    "board":     "BOARD_OF_DIRECTORS",
    "kmp":       "KMP_LIST",
    "promoter":  "BENEFICIAL_OWNERS",
    "guarantor": "BENEFICIAL_OWNERS",
    "fatca":     "PEP_DECLARATION",
    "benef":     "BENEFICIAL_OWNERS",
    "pep":       "PEP_DECLARATION",
    "rpt":       "RPT_DOCUMENT",
}


@router.post("/upload")
async def upload_fraud_docs(
    session_id: str = Form(...),
    board:     UploadFile = File(None),
    kmp:       UploadFile = File(None),
    promoter:  UploadFile = File(None),
    guarantor: UploadFile = File(None),
    fatca:     UploadFile = File(None),
    benef:     UploadFile = File(None),
    pep:       UploadFile = File(None),
    rpt:       UploadFile = File(None),
    user=Depends(get_current_user),
):
    db      = get_db()
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(404, "Session not found")

    uploaded  = {}
    files_map = {
        "board": board, "kmp": kmp, "promoter": promoter,
        "guarantor": guarantor, "fatca": fatca, "benef": benef,
        "pep": pep, "rpt": rpt,
    }

    for slot_key, upload_file in files_map.items():
        if upload_file and upload_file.filename:
            content  = await upload_file.read()
            doc_type = FRAUD_DOC_TYPE_MAP[slot_key]
            await db.fraud_uploads.update_one(
                {"session_id": session_id, "slot_key": slot_key},
                {"$set": {
                    "session_id": session_id,
                    "slot_key":   slot_key,
                    "doc_type":   doc_type,
                    "filename":   upload_file.filename,
                    "content":    content,
                }},
                upsert=True,
            )
            uploaded[slot_key] = upload_file.filename

    return {"uploaded": uploaded, "session_id": session_id}


async def _fraud_pipeline_generator(session_id: str, db):
    steps = [
        "Parsing director & KMP documents",
        "Building entity relationship graph",
        "Running beneficial ownership analysis",
        "Checking PEP & sanctions databases",
        "Analysing related party transactions",
        "Running NLP summary via Qwen2.5",
        "Computing risk score",
    ]
    total = len(steps)

    def sse(data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"

    # ── Step 1: Parse all fraud docs via OCR + LLM ───────────
    yield sse({"step": steps[0], "index": 1, "total": total, "status": "running"})

    cursor     = db.fraud_uploads.find({"session_id": session_id})
    fraud_docs = {}
    async for fd in cursor:
        try:
            raw_text, _ = await extract_text_from_bytes(fd["content"], fd["filename"])
            fields      = await extract_fields_llm(raw_text, fd["doc_type"])
        except Exception:
            fields = {}
        # Merge same doc types (e.g. multiple BENEFICIAL_OWNERS uploads)
        dt = fd["doc_type"]
        if dt in fraud_docs:
            # Merge lists
            for k, v in fields.items():
                if isinstance(v, list) and isinstance(fraud_docs[dt].get(k), list):
                    fraud_docs[dt][k].extend(v)
                elif k not in fraud_docs[dt]:
                    fraud_docs[dt][k] = v
        else:
            fraud_docs[dt] = fields
        yield sse({"step": f"Parsed: {fd['filename']}", "index": 1, "total": total, "status": "running"})

    board_data = fraud_docs.get("BOARD_OF_DIRECTORS", {})
    benef_data = fraud_docs.get("BENEFICIAL_OWNERS",  {})
    pep_data   = fraud_docs.get("PEP_DECLARATION",    {})
    rpt_data   = fraud_docs.get("RPT_DOCUMENT",       {})

    # Get company info from session
    session    = await db.sessions.find_one({"id": session_id})
    company    = session.get("company_name", "COMPANY")

    # Fill in company name if not in board doc
    if not board_data.get("company_name"):
        board_data["company_name"] = company
    if not benef_data.get("company_name"):
        benef_data["company_name"] = company

    # Get compliance docs for additional context
    comp_rec   = await db.compliance_records.find_one({"session_id": session_id})
    comp_docs  = {d["doc_type"]: d.get("fields", {}) for d in (comp_rec or {}).get("documents", [])}

    # ── Step 2: Build entity graph ────────────────────────────
    yield sse({"step": steps[1], "index": 2, "total": total, "status": "running"})
    entity_graph = build_entity_graph(board_data, benef_data, company, comp_docs)
    await asyncio.sleep(0.2)

    # ── Step 3: Ownership analysis ────────────────────────────
    yield sse({"step": steps[2], "index": 3, "total": total, "status": "running"})
    ownership_chains = build_ownership_chains(benef_data, board_data)
    await asyncio.sleep(0.2)

    # ── Step 4: PEP screening ─────────────────────────────────
    yield sse({"step": steps[3], "index": 4, "total": total, "status": "running"})
    pep_result = screen_pep(pep_data, board_data)
    await asyncio.sleep(0.2)

    # ── Step 5: RPT analysis ──────────────────────────────────
    yield sse({"step": steps[4], "index": 5, "total": total, "status": "running"})
    rpt_result = analyze_rpt(rpt_data, board_data)
    await asyncio.sleep(0.2)

    # ── Step 6: NLP summary ───────────────────────────────────
    yield sse({"step": steps[5], "index": 6, "total": total, "status": "running"})
    compliance_verdict = (comp_rec or {}).get("cross_check", {}).get("verdict", "UNKNOWN")
    nlp_summary = await generate_nlp_summary(
        entity_graph, pep_result, rpt_result,
        ownership_chains, compliance_verdict, company,
    )

    # ── Step 7: Risk score ────────────────────────────────────
    yield sse({"step": steps[6], "index": 7, "total": total, "status": "running"})
    risk_result = compute_risk_score(pep_result, rpt_result, entity_graph, compliance_verdict)
    await asyncio.sleep(0.2)

    # ── Save to MongoDB ───────────────────────────────────────
    fraud_record = {
        "session_id":        session_id,
        "company":           company,
        "pan":               session.get("pan", ""),
        "analyst_name":      session.get("analyst_name", "System"),
        "entity_graph":      entity_graph,
        "persons":           pep_result.get("persons", []),
        "pep_result":        pep_result,
        "rpt":               rpt_result.get("rpt", []),
        "rpt_result":        rpt_result,
        "ownership_chains":  ownership_chains,
        "nlp_summary":       nlp_summary,
        "risk_score":        risk_result["risk_score"],
        "risk_level":        risk_result["risk_level"],
        "recommendation":    risk_result["recommendation"],
        "flags":             risk_result["flags"],
        "compliance_verdict": compliance_verdict,
        "created_at":        datetime.utcnow(),
    }

    await db.fraud_records.update_one(
        {"session_id": session_id},
        {"$set": fraud_record},
        upsert=True,
    )

    # Update master compliance_records with fraud data
    await db.compliance_records.update_one(
        {"session_id": session_id},
        {"$set": {
            "fraud_risk":  risk_result["risk_level"],
            "risk_score":  risk_result["risk_score"],
            "fraud_done":  True,
        }},
    )
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {"status": "FRAUD_COMPLETE"}},
    )

    yield sse({
        "step":   "Complete",
        "index":  total,
        "total":  total,
        "status": "done",
        "result": {
            "riskScore":   risk_result["risk_score"],
            "riskLevel":   risk_result["risk_level"],
            "entityGraph": entity_graph,
            "persons":     pep_result.get("persons", []),
            "rpt":         rpt_result.get("rpt", []),
            "nlpSummary":  nlp_summary,
            "flags":       risk_result["flags"],
        },
    })


@router.post("/analyze/{session_id}")
async def run_fraud_analysis_sse(session_id: str, user=Depends(get_current_user)):
    """SSE endpoint — streams fraud analysis pipeline."""
    db      = get_db()
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(404, "Session not found")
    return StreamingResponse(
        _fraud_pipeline_generator(session_id, db),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/result/{session_id}")
async def get_fraud_result(session_id: str, user=Depends(get_current_user)):
    db  = get_db()
    rec = await db.fraud_records.find_one({"session_id": session_id})
    if not rec:
        raise HTTPException(404, "Fraud record not found")
    rec.pop("_id", None)
    # Normalise datetime
    if "created_at" in rec:
        rec["created_at"] = rec["created_at"].isoformat()
    return rec


@router.get("/graph/{session_id}")
async def get_entity_graph(session_id: str, user=Depends(get_current_user)):
    db  = get_db()
    rec = await db.fraud_records.find_one({"session_id": session_id}, {"entity_graph": 1})
    if not rec:
        raise HTTPException(404, "Fraud record not found")
    return rec.get("entity_graph", {})


@router.get("/summary/{session_id}")
async def get_nlp_summary(session_id: str, user=Depends(get_current_user)):
    db  = get_db()
    rec = await db.fraud_records.find_one({"session_id": session_id}, {"nlp_summary": 1})
    if not rec:
        raise HTTPException(404, "Fraud record not found")
    return {"nlp_summary": rec.get("nlp_summary", [])}


@router.get("/riskscore/{session_id}")
async def get_risk_score(session_id: str, user=Depends(get_current_user)):
    db  = get_db()
    rec = await db.fraud_records.find_one({"session_id": session_id}, {
        "risk_score": 1, "risk_level": 1, "recommendation": 1, "flags": 1
    })
    if not rec:
        raise HTTPException(404, "Fraud record not found")
    rec.pop("_id", None)
    return rec

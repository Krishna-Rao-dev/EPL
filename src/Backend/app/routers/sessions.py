"""
Sessions Router
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.schemas import SessionCreate

router = APIRouter()


@router.post("/create")
async def create_session(body: SessionCreate, user=Depends(get_current_user)):
    pan = body.pan.upper().strip()
    db  = get_db()
    # Check if session for this PAN already exists
    existing = await db.sessions.find_one({"pan": pan, "user_email": user["email"]})
    if existing:
        return {
            "id":           existing["id"],
            "pan":          existing["pan"],
            "company_name": existing.get("company_name"),
            "created_at":   existing["created_at"].isoformat(),
            "status":       existing["status"],
        }
    session_id = f"SESS_{pan}_{uuid.uuid4().hex[:8].upper()}"
    doc = {
        "id":           session_id,
        "pan":          pan,
        "company_name": None,
        "created_at":   datetime.utcnow(),
        "status":       "CREATED",
        "user_email":   user["email"],
        "analyst_name": user["name"],
    }
    await db.sessions.insert_one(doc)
    return {
        "id":           session_id,
        "pan":          pan,
        "company_name": None,
        "created_at":   doc["created_at"].isoformat(),
        "status":       "CREATED",
    }


@router.get("/{session_id}")
async def get_session(session_id: str, user=Depends(get_current_user)):
    db   = get_db()
    sess = await db.sessions.find_one({"id": session_id})
    if not sess:
        raise HTTPException(404, "Session not found")
    return {
        "id":           sess["id"],
        "pan":          sess["pan"],
        "company_name": sess.get("company_name"),
        "created_at":   sess["created_at"].isoformat(),
        "status":       sess["status"],
    }


@router.get("/list/all")
async def list_sessions(user=Depends(get_current_user)):
    db    = get_db()
    cursor = db.sessions.find({"user_email": user["email"]}).sort("created_at", -1).limit(50)
    sessions = []
    async for s in cursor:
        sessions.append({
            "id":           s["id"],
            "pan":          s["pan"],
            "company_name": s.get("company_name"),
            "created_at":   s["created_at"].isoformat(),
            "status":       s["status"],
        })
    return sessions

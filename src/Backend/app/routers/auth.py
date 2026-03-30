"""
Auth Router — login, logout, me, register
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import timedelta

from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, get_current_user,
)
from app.models.schemas import LoginRequest, TokenResponse, UserCreate

router = APIRouter()


@router.post("/register")
async def register(body: UserCreate):
    db   = get_db()
    existing = await db.users.find_one({"email": body.email})
    if existing:
        raise HTTPException(400, "Email already registered")
    user_doc = {
        "email":    body.email,
        "name":     body.name,
        "password": hash_password(body.password),
        "role":     body.role,
        "org":      body.org,
    }
    await db.users.insert_one(user_doc)
    return {"message": "User created successfully"}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    db   = get_db()
    user = await db.users.find_one({"email": body.email})
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(401, "Invalid email or password")
    token = create_access_token(
        {"sub": user["email"]},
        expires_delta=timedelta(minutes=480),
    )
    return {
        "access_token": token,
        "token_type":   "bearer",
        "user": {
            "id":    str(user.get("_id", "")),
            "name":  user["name"],
            "email": user["email"],
            "role":  user["role"],
            "org":   user["org"],
        },
    }


@router.post("/logout")
async def logout(current_user=Depends(get_current_user)):
    # Stateless JWT — just acknowledge
    return {"message": "Logged out"}


@router.get("/me")
async def me(current_user=Depends(get_current_user)):
    return {
        "id":    str(current_user.get("_id", "")),
        "name":  current_user["name"],
        "email": current_user["email"],
        "role":  current_user["role"],
        "org":   current_user["org"],
    }


@router.post("/seed")
async def seed_default_user():
    """Seed the default demo user — call once on first run."""
    db = get_db()
    existing = await db.users.find_one({"email": "analyst@pramanik.in"})
    if existing:
        return {"message": "Demo user already exists"}
    await db.users.insert_one({
        "email":    "analyst@pramanik.in",
        "name":     "Arjun Menon",
        "password": hash_password("password"),
        "role":     "Compliance Analyst",
        "org":      "NBFC Trust Ltd",
    })
    return {"message": "Demo user created: analyst@pramanik.in / password"}

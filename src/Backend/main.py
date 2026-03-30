"""
Pramanik RegTech Platform — FastAPI Backend
Entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import connect_db, close_db
from app.routers import auth, sessions, compliance, verification, fraud, records, export


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="Pramanik RegTech API",
    description="NBFC Compliance & Fraud Detection Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,         prefix="/api/v1/auth",       tags=["Auth"])
app.include_router(sessions.router,     prefix="/api/v1/session",    tags=["Sessions"])
app.include_router(compliance.router,   prefix="/api/v1/compliance", tags=["Compliance"])
app.include_router(verification.router, prefix="/api/v1/verify",     tags=["Verification"])
app.include_router(fraud.router,        prefix="/api/v1/fraud",      tags=["Fraud"])
app.include_router(records.router,      prefix="/api/v1/records",    tags=["Records"])
app.include_router(export.router,       prefix="/api/v1/export",     tags=["Export"])


@app.get("/")
async def root():
    return {"status": "ok", "service": "Pramanik RegTech API v1.0"}


# Alias for Uvicorn
main = app

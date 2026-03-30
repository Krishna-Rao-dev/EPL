"""
Pydantic schemas / response models
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "Compliance Analyst"
    org: str = "NBFC Trust Ltd"


# ── Session ───────────────────────────────────────────────────
class SessionCreate(BaseModel):
    pan: str

class SessionOut(BaseModel):
    id: str
    pan: str
    company_name: Optional[str] = None
    created_at: datetime
    status: str


# ── Compliance ────────────────────────────────────────────────
class OCRProgressEvent(BaseModel):
    step: str
    index: int
    total: int
    status: str   # "running" | "done" | "error"

class CrossCheckItem(BaseModel):
    parameter: str
    majority_value: Optional[str] = None
    inconsistent_docs: Optional[List[str]] = None
    inconsistent_values: Optional[List[str]] = None
    all_values: Optional[dict] = None
    value: Optional[str] = None
    docs: Optional[List[str]] = None

class CrossCheckReport(BaseModel):
    passed: List[CrossCheckItem]
    failed: List[CrossCheckItem]
    warnings: List[dict]
    verdict: str

class AIErrorFlag(BaseModel):
    parameter: str
    is_ai_error: bool


# ── Verification ──────────────────────────────────────────────
class VerificationResult(BaseModel):
    pan: Optional[dict] = None
    gst: Optional[dict] = None
    lei: Optional[dict] = None
    cin: Optional[dict] = None
    pincode: Optional[dict] = None
    name_consistency: Optional[dict] = None
    bill_dates: Optional[dict] = None
    verdict: Optional[str] = None


# ── Fraud ─────────────────────────────────────────────────────
class FraudProgressEvent(BaseModel):
    step: str
    index: int
    total: int
    status: str


# ── Export ────────────────────────────────────────────────────
class ExportRequest(BaseModel):
    session_id: str
    report_type: str   # "compliance" | "fraud" | "full"

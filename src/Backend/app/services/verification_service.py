"""
Verification Service — GLEIF, India Postal API, Sandbox (PAN/GST/CIN)
Ported from notebook Stage 2
"""
import re
import difflib
from datetime import datetime
import httpx

from app.core.config import settings


# ── Format validators ─────────────────────────────────────────
def validate_pan_format(pan: str) -> dict:
    if not pan:
        return {"valid": False, "error": "No PAN provided"}
    pan = pan.upper().strip()
    if re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan):
        entity_map = {"C": "Company", "P": "Individual", "H": "HUF",
                      "F": "Firm", "T": "Trust", "B": "BOI", "A": "AOP"}
        return {"valid": True, "pan": pan, "entity_type": entity_map.get(pan[3], "Unknown")}
    return {"valid": False, "pan": pan, "error": "Invalid PAN format"}


def validate_gstin_format(gstin: str) -> dict:
    if not gstin:
        return {"valid": False, "error": "No GSTIN provided"}
    gstin = gstin.upper().strip()
    if re.match(r"^\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z][A-Z\d]$", gstin):
        return {"valid": True, "gstin": gstin, "state_code": gstin[:2]}
    return {"valid": False, "gstin": gstin, "error": "Invalid GSTIN format"}


def validate_cin_format(cin: str) -> dict:
    if not cin:
        return {"valid": False, "error": "No CIN provided"}
    cin = cin.upper().strip()
    if re.match(r"^[UL]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$", cin):
        return {"valid": True, "cin": cin}
    return {"valid": False, "cin": cin, "error": "Invalid CIN format"}


def validate_lei_format(lei: str) -> dict:
    if not lei:
        return {"valid": False, "error": "No LEI provided"}
    lei = lei.upper().strip()
    if re.match(r"^[A-Z0-9]{20}$", lei):
        return {"valid": True, "lei": lei}
    return {"valid": False, "lei": lei, "error": "Invalid LEI format (must be 20 alphanumeric chars)"}


def validate_pan_gstin_embed(pan: str, gstin: str) -> dict:
    if not pan or not gstin:
        return {"match": False, "error": "Missing PAN or GSTIN"}
    embedded = gstin[2:12].upper()
    pan_upper = pan.upper()
    if embedded == pan_upper:
        return {"match": True, "pan": pan_upper, "embedded_in_gstin": embedded}
    return {"match": False, "pan": pan_upper, "embedded_in_gstin": embedded,
            "error": f"MISMATCH: PAN={pan_upper} but GSTIN embeds={embedded}"}


# ── Real APIs ─────────────────────────────────────────────────
async def verify_lei_gleif(lei: str, expected_name: str = None) -> dict:
    """GLEIF — free, no auth required"""
    if not lei:
        return {"verified": False, "error": "No LEI provided", "source": "GLEIF"}
    fmt = validate_lei_format(lei)
    if not fmt["valid"]:
        return {"verified": False, "source": "GLEIF", **fmt}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"https://api.gleif.org/api/v1/lei-records/{lei}")
        if resp.status_code != 200:
            return {"verified": False, "lei": lei, "status": "NOT_FOUND", "source": "GLEIF"}
        data       = resp.json()["data"]["attributes"]
        reg        = data.get("registration", {})
        entity     = data.get("entity", {})
        legal_name = entity.get("legalName", {}).get("name", "")
        status     = reg.get("status", "")
        name_match = True
        if expected_name and legal_name:
            sim = difflib.SequenceMatcher(None, legal_name.lower(), expected_name.lower()).ratio()
            name_match = sim > 0.80
        return {
            "verified":      status == "ISSUED",
            "lei":           lei,
            "legal_name":    legal_name,
            "status":        status,
            "next_renewal":  reg.get("nextRenewalDate", "N/A"),
            "corroboration": reg.get("corroborationLevel", "N/A"),
            "name_match":    name_match,
            "source":        "GLEIF",
        }
    except httpx.ConnectError:
        return {"verified": fmt["valid"], "lei": lei, "note": "No internet — format check only", "source": "GLEIF_OFFLINE"}
    except Exception as e:
        return {"verified": False, "error": str(e), "source": "GLEIF"}


async def verify_pincode(pincode: str, expected_state: str = None) -> dict:
    """India Postal API — free, no auth"""
    if not pincode:
        return {"verified": False, "error": "No pincode provided"}
    pincode = str(pincode).strip()
    if not re.match(r"^[1-9][0-9]{5}$", pincode):
        return {"verified": False, "pincode": pincode, "error": "Invalid pincode format"}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(f"https://api.postalpincode.in/pincode/{pincode}")
        data = resp.json()
        if not data or data[0]["Status"] != "Success":
            return {"verified": False, "pincode": pincode, "error": "Pincode not found"}
        post_offices = data[0]["PostOffice"]
        if not post_offices:
            return {"verified": False, "pincode": pincode, "error": "No post offices"}
        po    = post_offices[0]
        state = po.get("State", "")
        dist  = po.get("District", "")
        state_match = True
        if expected_state:
            state_match = expected_state.lower() in state.lower() or state.lower() in expected_state.lower()
        return {
            "verified":     True,
            "pincode":      pincode,
            "state":        state,
            "district":     dist,
            "region":       po.get("Region", ""),
            "post_offices": len(post_offices),
            "state_match":  state_match,
            "source":       "INDIA_POSTAL_API",
        }
    except httpx.ConnectError:
        return {"verified": re.match(r"^[1-9][0-9]{5}$", pincode) is not None,
                "pincode": pincode, "note": "No internet — format check only"}
    except Exception as e:
        return {"verified": False, "error": str(e)}


# ── Sandbox — REAL Sandbox.co.in PAN call ────────────────────
async def sandbox_pan(pan: str) -> dict:
    """
    Real Sandbox.co.in PAN verification.
    Requires SANDBOX_PAN_API_KEY in config.
    Falls back to format-only check if key not set.
    """
    if not pan:
        return {"verified": False, "status": "NO_PAN", "source": "SANDBOX"}

    api_key = settings.SANDBOX_PAN_API_KEY
    if not api_key or api_key == "your-sandbox-key-here":
        # Fallback: format check
        fmt = validate_pan_format(pan)
        return {
            "verified": fmt["valid"],
            "status":   "ACTIVE" if fmt["valid"] else "INVALID_FORMAT",
            "source":   "SANDBOX_FORMAT_ONLY",
            "pan":      pan,
            "note":     "Set SANDBOX_PAN_API_KEY in .env for live check",
        }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Step 1: Authenticate
            auth_resp = await client.post(
                settings.SANDBOX_AUTH_URL,
                headers={"x-api-key": api_key, "x-api-version": "2.0"},
            )
            access_token = auth_resp.json().get("access_token", "")

            # Step 2: PAN status
            resp = await client.get(
                f"{settings.SANDBOX_PAN_URL}/{pan}",
                headers={
                    "x-api-key":        api_key,
                    "x-api-version":    "2.0",
                    "Authorization":    f"Bearer {access_token}",
                },
            )
        data   = resp.json()
        status = data.get("data", {}).get("status", "UNKNOWN")
        name   = data.get("data", {}).get("name", "")
        return {
            "verified": status in ("ACTIVE", "Valid"),
            "status":   status,
            "name":     name,
            "pan":      pan,
            "source":   "SANDBOX",
        }
    except Exception as e:
        fmt = validate_pan_format(pan)
        return {
            "verified": fmt["valid"],
            "status":   "API_ERROR",
            "error":    str(e),
            "pan":      pan,
            "source":   "SANDBOX",
        }


async def sandbox_gst(gstin: str) -> dict:
    """GST format validation + sandbox simulation"""
    if not gstin:
        return {"verified": False, "status": "NO_GSTIN", "source": "GST_PORTAL"}
    fmt = validate_gstin_format(gstin)
    if not fmt["valid"]:
        return {"verified": False, "status": "INVALID_FORMAT", "source": "GST_PORTAL", "gstin": gstin}
    # Simulate GST Portal check (no free real API available)
    return {
        "verified":   True,
        "status":     "Active",
        "gstin":      gstin,
        "legal_name": "",    # Would come from real API
        "state":      "",
        "source":     "GST_PORTAL_SANDBOX",
    }


async def sandbox_cin(cin: str) -> dict:
    """CIN format validation + sandbox simulation"""
    if not cin:
        return {"verified": False, "status": "NO_CIN", "source": "MCA21"}
    fmt = validate_cin_format(cin)
    if not fmt["valid"]:
        return {"verified": False, "status": "INVALID_FORMAT", "source": "MCA21", "cin": cin}
    return {
        "verified":     True,
        "status":       "Active",
        "cin":          cin,
        "company_name": "",   # Would come from real MCA21 API
        "roc":          "",
        "source":       "MCA21_SANDBOX",
    }


# ── Bill date validator ───────────────────────────────────────
def validate_bill_date(bill_date_str: str, max_days: int = 90) -> dict:
    if not bill_date_str:
        return {"valid": False, "error": "No bill date found"}
    formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y"]
    parsed  = None
    for fmt in formats:
        try:
            parsed = datetime.strptime(bill_date_str.strip(), fmt)
            break
        except ValueError:
            continue
    if not parsed:
        return {"valid": False, "error": f"Cannot parse date: {bill_date_str}"}
    age_days = (datetime.now() - parsed).days
    valid    = 0 <= age_days <= max_days
    return {
        "valid":      valid,
        "bill_date":  bill_date_str,
        "age_days":   age_days,
        "max_days":   max_days,
        "message":    f"Bill is {age_days} days old — {'WITHIN' if valid else 'EXCEEDS'} {max_days}-day limit",
    }


# ── Name fuzzy match ──────────────────────────────────────────
def normalize_company_name(name: str) -> str:
    if not name:
        return ""
    n = name.upper().strip()
    for old, new in [("PRIVATE LIMITED", "PVT LTD"), ("PVT. LTD.", "PVT LTD"),
                     ("PVT.LTD.", "PVT LTD"), ("LIMITED", "LTD"), ("LTD.", "LTD")]:
        n = n.replace(old, new)
    return " ".join(n.split())


def fuzzy_name_match(names: dict, threshold: float = 0.82) -> dict:
    normalized = {src: normalize_company_name(n) for src, n in names.items() if n}
    if not normalized:
        return {"consistent": True, "base": "", "details": {}}
    results   = {}
    base_src, base_name = list(normalized.items())[0]
    all_match = True
    for src, name in normalized.items():
        score = difflib.SequenceMatcher(None, base_name, name).ratio()
        match = score >= threshold
        if not match:
            all_match = False
        results[src] = {"name": name, "score": round(score, 3), "match": match}
    return {"consistent": all_match, "base": base_name, "details": results, "threshold": threshold}


# ── Master runner ─────────────────────────────────────────────
async def run_all_verifications(documents: list[dict], company_name: str = "") -> dict:
    """
    Run all API verifications for a session's documents.
    Returns full verification report.
    """
    doc_map = {d["doc_type"]: d.get("fields", {}) for d in documents if d.get("status") == "EXTRACTED"}

    def get_field(doc_type: str, field: str):
        return doc_map.get(doc_type, {}).get(field, "")

    pan    = get_field("PAN_CARD", "pan_number") or get_field("GST_CERTIFICATE", "pan_number")
    gstin  = get_field("GST_CERTIFICATE", "gstin")
    lei    = get_field("LEI_CERTIFICATE", "lei_code")
    cin    = get_field("INCORPORATION_CERTIFICATE", "cin")
    pincode = get_field("GST_CERTIFICATE", "pincode") or get_field("REGISTERED_ADDRESS", "pincode")
    state   = get_field("GST_CERTIFICATE", "state")

    # Run all checks concurrently
    import asyncio
    pan_res, gst_res, lei_res, cin_res, pin_res = await asyncio.gather(
        sandbox_pan(pan),
        sandbox_gst(gstin),
        verify_lei_gleif(lei, company_name or get_field("PAN_CARD", "entity_name")),
        sandbox_cin(cin),
        verify_pincode(pincode, state),
    )

    # Enrich GST result with actual company name from OCR
    if gst_res.get("verified"):
        gst_res["legal_name"] = get_field("GST_CERTIFICATE", "legal_name") or company_name
        gst_res["state"]      = get_field("GST_CERTIFICATE", "state")

    # CIN name from OCR
    if cin_res.get("verified"):
        cin_res["company_name"] = get_field("INCORPORATION_CERTIFICATE", "company_name") or company_name
        cin_res["roc"]          = get_field("INCORPORATION_CERTIFICATE", "roc")

    # PAN name from OCR
    if pan_res.get("verified") and not pan_res.get("name"):
        pan_res["name"] = get_field("PAN_CARD", "entity_name") or company_name

    # Format checks
    pan_fmt   = validate_pan_format(pan)
    gstin_fmt = validate_gstin_format(gstin)
    cin_fmt   = validate_cin_format(cin)
    lei_fmt   = validate_lei_format(lei)
    embed     = validate_pan_gstin_embed(pan, gstin)

    # Bill dates
    elec_date = get_field("ELECTRICITY_BILL", "bill_date")
    tel_date  = get_field("TELEPHONE_BILL",   "bill_date")

    # Name consistency
    names_to_check = {
        k: v for k, v in {
            "OCR_PAN":    get_field("PAN_CARD", "entity_name"),
            "OCR_GST":    get_field("GST_CERTIFICATE", "legal_name"),
            "OCR_LEI":    get_field("LEI_CERTIFICATE", "legal_name"),
            "OCR_INCORP": get_field("INCORPORATION_CERTIFICATE", "company_name"),
            "GLEIF":      lei_res.get("legal_name"),
            "SANDBOX_CIN": cin_res.get("company_name"),
        }.items() if v
    }
    name_result = fuzzy_name_match(names_to_check)

    # Verdict
    critical_pass = sum([
        pan_res.get("verified", False),
        gst_res.get("verified", False),
        lei_res.get("verified", False),
        cin_res.get("verified", False),
        pin_res.get("verified", False),
    ])
    verdict = "PASS" if critical_pass >= 3 else "FAIL"

    return {
        "pan":              pan_res,
        "gst":              gst_res,
        "lei":              lei_res,
        "cin":              cin_res,
        "pincode":          pin_res,
        "format_checks": {
            "pan":         pan_fmt,
            "gstin":       gstin_fmt,
            "cin":         cin_fmt,
            "lei":         lei_fmt,
            "pan_gstin_embed": embed,
        },
        "name_consistency": name_result,
        "bill_dates": {
            "electricity": validate_bill_date(elec_date),
            "telephone":   validate_bill_date(tel_date),
        },
        "verdict": verdict,
        "passed":  critical_pass,
        "total":   5,
    }

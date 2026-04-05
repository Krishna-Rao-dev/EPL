"""
Document field schemas — one Pydantic model per document type.

Design rules:
- Every field is Optional — LLM may not find it
- Validators normalize & reject obvious placeholders
- No field is ever a description string like "Full company name"
"""
from __future__ import annotations
import re
from typing import Optional, List
from pydantic import BaseModel, field_validator, model_validator


# ── Shared validators ─────────────────────────────────────────

_PLACEHOLDER_RE = re.compile(
    r"""
    ^(
        \d[-\s]?[Dd]igit           |   # "6-digit PIN"
        [Ff]ull\s                   |   # "Full company name"
        [Ll]egal\s[Bb]usiness       |   # "Legal Business Name"
        [Nn]ame\s[Oo]n\s[Bb]ill    |   # "Name on bill"
        [Xx][Yy][Zz]               |   # "XYZ Limited"
        [A-Z_]{3,}_[A-Z_]{3,}      |   # "PAN_NUMBER_ABCD"
        subscriber\sname            |   # template text
        director\sname              |   # template text
        number\sof\sshares          |   # template text
        DIN\snumber                 |   # template text
        [Mm]inimum\snumber          |   # template text
        [Mm]aximum\snumber             # template text
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

_PAN_RE   = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
_GSTIN_RE = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z][A-Z\d]$")
_CIN_RE   = re.compile(r"^[UL]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$")
_LEI_RE   = re.compile(r"^[A-Z0-9]{20}$")
_PIN_RE   = re.compile(r"^[1-9][0-9]{5}$")
_DATE_RE  = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def _clean(v: str | None) -> str | None:
    """Strip whitespace; return None if empty or placeholder."""
    if v is None:
        return None
    v = str(v).strip()
    if not v or v.lower() in ("null", "none", "n/a", "na", "-", ""):
        return None
    if _PLACEHOLDER_RE.match(v):
        return None
    return v


def _pan(v: str | None) -> str | None:
    v = _clean(v)
    if v is None:
        return None
    v = v.upper().replace(" ", "")
    return v if _PAN_RE.match(v) else None


def _gstin(v: str | None) -> str | None:
    v = _clean(v)
    if v is None:
        return None
    v = v.upper().replace(" ", "")
    return v if _GSTIN_RE.match(v) else None


def _cin(v: str | None) -> str | None:
    v = _clean(v)
    if v is None:
        return None
    v = v.upper().replace(" ", "")
    return v if _CIN_RE.match(v) else None


def _lei(v: str | None) -> str | None:
    v = _clean(v)
    if v is None:
        return None
    v = v.upper().replace(" ", "")
    return v if _LEI_RE.match(v) else None


def _pin(v: str | None) -> str | None:
    v = _clean(v)
    if v is None:
        return None
    v = re.sub(r"\D", "", v)
    return v if _PIN_RE.match(v) else None


def _date(v: str | None) -> str | None:
    v = _clean(v)
    if v is None:
        return None
    # Normalise separators to /
    v = re.sub(r"[-.]", "/", v)
    return v if _DATE_RE.match(v) else None


def _amount(v: str | None) -> str | None:
    v = _clean(v)
    if v is None:
        return None
    # Strip currency symbols and commas, keep digits and decimal
    v = re.sub(r"[₹$,\s]", "", v)
    return v if re.match(r"^\d+(\.\d+)?$", v) else None


# ── Document schemas ──────────────────────────────────────────

class PANCardFields(BaseModel):
    pan_number:   Optional[str] = None
    entity_name:  Optional[str] = None
    date_of_reg:  Optional[str] = None
    entity_type:  Optional[str] = None
    issuing_auth: Optional[str] = None

    @field_validator("pan_number", mode="before")
    @classmethod
    def v_pan(cls, v): return _pan(v)

    @field_validator("entity_name", "issuing_auth", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)

    @field_validator("date_of_reg", mode="before")
    @classmethod
    def v_date(cls, v): return _date(v)

    @field_validator("entity_type", mode="before")
    @classmethod
    def v_entity_type(cls, v):
        v = _clean(v)
        if v is None:
            return None
        v = v.upper()
        return v if v in ("COMPANY", "INDIVIDUAL", "HUF", "FIRM", "TRUST", "BOI", "AOP") else _clean(v)


class GSTCertificateFields(BaseModel):
    gstin:             Optional[str] = None
    pan_number:        Optional[str] = None
    legal_name:        Optional[str] = None
    trade_name:        Optional[str] = None
    state_code:        Optional[str] = None
    state:             Optional[str] = None
    status:            Optional[str] = None
    registration_date: Optional[str] = None
    constitution:      Optional[str] = None
    address:           Optional[str] = None
    pincode:           Optional[str] = None

    @field_validator("gstin", mode="before")
    @classmethod
    def v_gstin(cls, v): return _gstin(v)

    @field_validator("pan_number", mode="before")
    @classmethod
    def v_pan(cls, v): return _pan(v)

    @field_validator("pincode", mode="before")
    @classmethod
    def v_pin(cls, v): return _pin(v)

    @field_validator("registration_date", mode="before")
    @classmethod
    def v_date(cls, v): return _date(v)

    @field_validator("legal_name", "trade_name", "state", "constitution", "address", "state_code", "status", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)

    @model_validator(mode="after")
    def cross_validate(self):
        # PAN must embed in GSTIN positions 3-12
        if self.gstin and self.pan_number:
            embedded = self.gstin[2:12]
            if embedded != self.pan_number:
                self.pan_number = None  # Trust GSTIN over separately extracted PAN
        return self


class LEICertificateFields(BaseModel):
    lei_code:          Optional[str] = None
    legal_name:        Optional[str] = None
    cin:               Optional[str] = None
    pan_number:        Optional[str] = None
    status:            Optional[str] = None
    registration_date: Optional[str] = None
    renewal_date:      Optional[str] = None
    issuing_lou:       Optional[str] = None
    country:           Optional[str] = None

    @field_validator("lei_code", mode="before")
    @classmethod
    def v_lei(cls, v): return _lei(v)

    @field_validator("cin", mode="before")
    @classmethod
    def v_cin(cls, v): return _cin(v)

    @field_validator("pan_number", mode="before")
    @classmethod
    def v_pan(cls, v): return _pan(v)

    @field_validator("registration_date", "renewal_date", mode="before")
    @classmethod
    def v_date(cls, v): return _date(v)

    @field_validator("legal_name", "status", "issuing_lou", "country", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)


class IncorporationCertificateFields(BaseModel):
    company_name:       Optional[str] = None
    cin:                Optional[str] = None
    pan_number:         Optional[str] = None
    date_of_incorp:     Optional[str] = None
    company_type:       Optional[str] = None
    authorized_capital: Optional[str] = None
    state:              Optional[str] = None
    roc:                Optional[str] = None
    address:            Optional[str] = None
    pincode:            Optional[str] = None

    @field_validator("cin", mode="before")
    @classmethod
    def v_cin(cls, v): return _cin(v)

    @field_validator("pan_number", mode="before")
    @classmethod
    def v_pan(cls, v): return _pan(v)

    @field_validator("pincode", mode="before")
    @classmethod
    def v_pin(cls, v): return _pin(v)

    @field_validator("date_of_incorp", mode="before")
    @classmethod
    def v_date(cls, v): return _date(v)

    @field_validator("authorized_capital", mode="before")
    @classmethod
    def v_amount(cls, v): return _amount(v)

    @field_validator("company_name", "company_type", "state", "roc", "address", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)


class MOAFields(BaseModel):
    company_name:       Optional[str] = None
    cin:                Optional[str] = None
    state:              Optional[str] = None
    address:            Optional[str] = None
    pincode:            Optional[str] = None
    authorized_capital: Optional[str] = None
    main_objects:       Optional[List[str]] = None
    subscribers:        Optional[List[dict]] = None

    @field_validator("cin", mode="before")
    @classmethod
    def v_cin(cls, v): return _cin(v)

    @field_validator("pincode", mode="before")
    @classmethod
    def v_pin(cls, v): return _pin(v)

    @field_validator("authorized_capital", mode="before")
    @classmethod
    def v_amount(cls, v): return _amount(v)

    @field_validator("company_name", "state", "address", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)

    @field_validator("main_objects", mode="before")
    @classmethod
    def v_objects(cls, v):
        if not isinstance(v, list):
            return None
        cleaned = [_clean(str(i)) for i in v if _clean(str(i))]
        return cleaned if cleaned else None

    @field_validator("subscribers", mode="before")
    @classmethod
    def v_subscribers(cls, v):
        if not isinstance(v, list):
            return None
        out = []
        for item in v:
            if isinstance(item, dict):
                name   = _clean(item.get("name", ""))
                shares = _clean(item.get("shares", ""))
                if name:
                    out.append({"name": name, "shares": shares})
        return out if out else None


class AOAFields(BaseModel):
    company_name:       Optional[str] = None
    cin:                Optional[str] = None
    authorized_capital: Optional[str] = None
    min_directors:      Optional[str] = None
    max_directors:      Optional[str] = None
    directors:          Optional[List[dict]] = None

    @field_validator("cin", mode="before")
    @classmethod
    def v_cin(cls, v): return _cin(v)

    @field_validator("authorized_capital", mode="before")
    @classmethod
    def v_amount(cls, v): return _amount(v)

    @field_validator("company_name", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)

    @field_validator("min_directors", "max_directors", mode="before")
    @classmethod
    def v_num(cls, v):
        v = _clean(v)
        if v is None:
            return None
        digits = re.sub(r"\D", "", v)
        return digits if digits else None

    @field_validator("directors", mode="before")
    @classmethod
    def v_directors(cls, v):
        if not isinstance(v, list):
            return None
        out = []
        for item in v:
            if isinstance(item, dict):
                name = _clean(item.get("name", ""))
                din  = _clean(item.get("din", ""))
                if name:
                    out.append({"name": name, "din": din})
        return out if out else None


class RegisteredAddressFields(BaseModel):
    company_name:  Optional[str] = None
    cin:           Optional[str] = None
    pan_number:    Optional[str] = None
    gstin:         Optional[str] = None
    lei:           Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    area:          Optional[str] = None
    city:          Optional[str] = None
    state:         Optional[str] = None
    pincode:       Optional[str] = None
    srn:           Optional[str] = None
    filing_date:   Optional[str] = None
    approval_date: Optional[str] = None
    status:        Optional[str] = None

    @field_validator("cin", mode="before")
    @classmethod
    def v_cin(cls, v): return _cin(v)

    @field_validator("pan_number", mode="before")
    @classmethod
    def v_pan(cls, v): return _pan(v)

    @field_validator("gstin", mode="before")
    @classmethod
    def v_gstin(cls, v): return _gstin(v)

    @field_validator("lei", mode="before")
    @classmethod
    def v_lei(cls, v): return _lei(v)

    @field_validator("pincode", mode="before")
    @classmethod
    def v_pin(cls, v): return _pin(v)

    @field_validator("filing_date", "approval_date", mode="before")
    @classmethod
    def v_date(cls, v): return _date(v)

    @field_validator("company_name", "address_line1", "address_line2", "area",
                     "city", "state", "srn", "status", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)


class ElectricityBillFields(BaseModel):
    consumer_name:   Optional[str] = None
    consumer_number: Optional[str] = None
    discom:          Optional[str] = None
    address:         Optional[str] = None
    pincode:         Optional[str] = None
    bill_number:     Optional[str] = None
    bill_date:       Optional[str] = None
    due_date:        Optional[str] = None
    billing_period:  Optional[str] = None
    units_consumed:  Optional[str] = None
    total_amount:    Optional[str] = None
    connection_type: Optional[str] = None

    @field_validator("pincode", mode="before")
    @classmethod
    def v_pin(cls, v): return _pin(v)

    @field_validator("bill_date", "due_date", mode="before")
    @classmethod
    def v_date(cls, v): return _date(v)

    @field_validator("total_amount", mode="before")
    @classmethod
    def v_amount(cls, v): return _amount(v)

    @field_validator("consumer_name", "consumer_number", "discom", "address",
                     "bill_number", "billing_period", "units_consumed",
                     "connection_type", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)


class TelephoneBillFields(BaseModel):
    account_name:     Optional[str] = None
    account_number:   Optional[str] = None
    telephone_number: Optional[str] = None
    provider:         Optional[str] = None
    address:          Optional[str] = None
    pincode:          Optional[str] = None
    bill_number:      Optional[str] = None
    bill_date:        Optional[str] = None
    due_date:         Optional[str] = None
    billing_period:   Optional[str] = None
    total_amount:     Optional[str] = None
    connection_type:  Optional[str] = None

    @field_validator("pincode", mode="before")
    @classmethod
    def v_pin(cls, v): return _pin(v)

    @field_validator("bill_date", "due_date", mode="before")
    @classmethod
    def v_date(cls, v): return _date(v)

    @field_validator("total_amount", mode="before")
    @classmethod
    def v_amount(cls, v): return _amount(v)

    @field_validator("account_name", "account_number", "telephone_number", "provider",
                     "address", "bill_number", "billing_period", "connection_type", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)


# ── Fraud schemas ─────────────────────────────────────────────

class DirectorEntry(BaseModel):
    name:                Optional[str] = None
    din:                 Optional[str] = None
    pan:                 Optional[str] = None
    dob:                 Optional[str] = None
    designation:         Optional[str] = None
    shareholding:        Optional[str] = None
    address:             Optional[str] = None
    nationality:         Optional[str] = None
    other_directorships: Optional[str] = None

    @field_validator("pan", mode="before")
    @classmethod
    def v_pan(cls, v): return _pan(v)

    @field_validator("dob", mode="before")
    @classmethod
    def v_date(cls, v): return _date(v)

    @field_validator("name", "din", "designation", "shareholding",
                     "address", "nationality", "other_directorships", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)


class BoardOfDirectorsFields(BaseModel):
    company_name: Optional[str] = None
    cin:          Optional[str] = None
    pan:          Optional[str] = None
    directors:    Optional[List[DirectorEntry]] = None

    @field_validator("cin", mode="before")
    @classmethod
    def v_cin(cls, v): return _cin(v)

    @field_validator("pan", mode="before")
    @classmethod
    def v_pan(cls, v): return _pan(v)

    @field_validator("company_name", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)

    @field_validator("directors", mode="before")
    @classmethod
    def v_directors(cls, v):
        if not isinstance(v, list):
            return None
        return [DirectorEntry(**d) if isinstance(d, dict) else d for d in v]


class KMPEntry(BaseModel):
    name:        Optional[str] = None
    designation: Optional[str] = None
    id_numbers:  Optional[str] = None
    email:       Optional[str] = None
    phone:       Optional[str] = None

    @field_validator("name", "designation", "id_numbers", "email", "phone", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)


class KMPListFields(BaseModel):
    company_name: Optional[str] = None
    kmps:         Optional[List[KMPEntry]] = None

    @field_validator("company_name", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)


class UBOEntry(BaseModel):
    name:              Optional[str] = None
    pan:               Optional[str] = None
    direct_holding:    Optional[str] = None
    indirect_holding:  Optional[str] = None
    total_effective:   Optional[str] = None
    nature:            Optional[str] = None

    @field_validator("pan", mode="before")
    @classmethod
    def v_pan(cls, v): return _pan(v)

    @field_validator("name", "direct_holding", "indirect_holding",
                     "total_effective", "nature", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)


class RelatedEntityEntry(BaseModel):
    name:          Optional[str] = None
    pan:           Optional[str] = None
    relationship:  Optional[str] = None
    ownership_pct: Optional[str] = None

    @field_validator("pan", mode="before")
    @classmethod
    def v_pan(cls, v): return _pan(v)

    @field_validator("name", "relationship", "ownership_pct", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)


class BeneficialOwnersFields(BaseModel):
    company_name:     Optional[str] = None
    ubos:             Optional[List[UBOEntry]] = None
    related_entities: Optional[List[RelatedEntityEntry]] = None

    @field_validator("company_name", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)


class PEPDeclarationEntry(BaseModel):
    name:          Optional[str] = None
    designation:   Optional[str] = None
    pep_status:    Optional[str] = None
    family_pep:    Optional[str] = None
    associate_pep: Optional[str] = None

    @field_validator("pep_status", mode="before")
    @classmethod
    def v_pep(cls, v):
        v = _clean(v)
        if v is None:
            return None
        v_up = v.upper()
        if "NOT" in v_up:
            return "NOT A PEP"
        if "PEP" in v_up:
            return "PEP"
        return None

    @field_validator("name", "designation", "family_pep", "associate_pep", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)


class PEPDeclarationFields(BaseModel):
    company_name: Optional[str] = None
    declarations: Optional[List[PEPDeclarationEntry]] = None

    @field_validator("company_name", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)


class RPTEntry(BaseModel):
    related_party:    Optional[str] = None
    relationship:     Optional[str] = None
    transaction_type: Optional[str] = None
    amount:           Optional[str] = None
    terms:            Optional[str] = None
    approval:         Optional[str] = None
    risk_flag:        Optional[str] = None

    @field_validator("amount", mode="before")
    @classmethod
    def v_amount(cls, v): return _amount(v)

    @field_validator("related_party", "relationship", "transaction_type",
                     "terms", "approval", "risk_flag", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)


class RPTDocumentFields(BaseModel):
    company_name:               Optional[str] = None
    related_party_transactions: Optional[List[RPTEntry]] = None

    @field_validator("company_name", mode="before")
    @classmethod
    def v_str(cls, v): return _clean(v)


# ── Registry — maps doc_type → schema class ───────────────────
SCHEMA_REGISTRY: dict[str, type[BaseModel]] = {
    "PAN_CARD":                  PANCardFields,
    "GST_CERTIFICATE":           GSTCertificateFields,
    "LEI_CERTIFICATE":           LEICertificateFields,
    "INCORPORATION_CERTIFICATE": IncorporationCertificateFields,
    "MOA":                       MOAFields,
    "AOA":                       AOAFields,
    "REGISTERED_ADDRESS":        RegisteredAddressFields,
    "ELECTRICITY_BILL":          ElectricityBillFields,
    "TELEPHONE_BILL":            TelephoneBillFields,
    "BOARD_OF_DIRECTORS":        BoardOfDirectorsFields,
    "KMP_LIST":                  KMPListFields,
    "BENEFICIAL_OWNERS":         BeneficialOwnersFields,
    "PEP_DECLARATION":           PEPDeclarationFields,
    "RPT_DOCUMENT":              RPTDocumentFields,
}

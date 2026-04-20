"""
Cross-Check Service — consistency verification across all documents
(ported from notebook run_cross_checks function)
"""
import re
import unicodedata
from typing import Any


# ── Field extraction map ──────────────────────────────────────
CROSS_CHECK_FIELDS = [
    {
        "label": "PAN Number",
        "doc_field_map": {
            "PAN_CARD":                  "pan_number",
            "GST_CERTIFICATE":           "pan_number",
            "LEI_CERTIFICATE":           "pan_number",
            "INCORPORATION_CERTIFICATE": "pan_number",
            "REGISTERED_ADDRESS":        "pan_number",
        },
    },
    {
        "label": "Company Name",
        "doc_field_map": {
            "PAN_CARD":                  "entity_name",
            "GST_CERTIFICATE":           "legal_name",
            "LEI_CERTIFICATE":           "legal_name",
            "INCORPORATION_CERTIFICATE": "company_name",
            "MOA":                       "company_name",
            "AOA":                       "company_name",
            "REGISTERED_ADDRESS":        "company_name",
            "ELECTRICITY_BILL":          "consumer_name",
            "TELEPHONE_BILL":            "account_name",
        },
    },
    {
        "label": "Pincode",
        "doc_field_map": {
            "GST_CERTIFICATE":           "pincode",
            "INCORPORATION_CERTIFICATE": "pincode",
            "REGISTERED_ADDRESS":        "pincode",
            "ELECTRICITY_BILL":          "pincode",
            "TELEPHONE_BILL":            "pincode",
        },
    },
    {
        "label": "CIN",
        "doc_field_map": {
            "LEI_CERTIFICATE":           "cin",
            "INCORPORATION_CERTIFICATE": "cin",
            "MOA":                       "cin",
            "REGISTERED_ADDRESS":        "cin",
        },
    },
    {
        "label": "GSTIN",
        "doc_field_map": {
            "GST_CERTIFICATE":    "gstin",
            "REGISTERED_ADDRESS": "gstin",
        },
    },
    {
        "label": "Address",
        "doc_field_map": {
            "GST_CERTIFICATE":           "address",
            "INCORPORATION_CERTIFICATE": "address",
            "REGISTERED_ADDRESS":        "address_line1",
            "ELECTRICITY_BILL":          "address",
            "TELEPHONE_BILL":            "address",
        },
    },
]


def clean_name(val: Any) -> str:
    if val is None: return ""
    s = str(val).upper().strip()
    # Correct common OCR errors
    for old, new in [
        ("PAVATE", "PRIVATE"), ("LID", "LTD"), ("LIIMITED", "LIMITED")
    ]:
        s = s.replace(old, new)
    return " ".join(s.split())


def _normalize(val: Any) -> str:
    s = clean_name(val)
    if not s: return ""
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"[.\-\s]+", " ", s).strip()
    # Normalise company name suffixes
    for old, new in [
        ("PRIVATE LIMITED", "PVT LTD"), ("PVT. LTD.", "PVT LTD"),
        ("PVT.LTD.", "PVT LTD"), ("LIMITED", "LTD"), ("LTD.", "LTD")
    ]:
        s = s.replace(old, new)
    return " ".join(s.split())


def run_cross_checks(documents: list[dict]) -> dict:
    """
    documents: list of {doc_type, status, fields, ...}
    Returns cross-check report matching frontend schema.
    """
    doc_map = {d["doc_type"]: d.get("fields", {}) for d in documents if d.get("status") == "EXTRACTED"}

    report = {"passed": [], "failed": [], "warnings": []}

    for check in CROSS_CHECK_FIELDS:
        label       = check["label"]
        field_map   = check["doc_field_map"]
        found       = {}          # {doc_type: raw_value}
        missing_from = []

        for doc_type, field_name in field_map.items():
            if doc_type not in doc_map:
                continue
            val = doc_map[doc_type].get(field_name)
            if val and str(val).strip():
                found[doc_type] = str(val).strip()
            else:
                missing_from.append(doc_type)

        if not found:
            continue

        normalized = {dt: _normalize(v) for dt, v in found.items()}
        unique_norms = set(normalized.values())

        if len(unique_norms) == 1:
            # Consistent
            report["passed"].append({
                "parameter": label,
                "value":     clean_name(list(found.values())[0]),
                "docs":      list(found.keys()),
            })
        else:
            # Mismatch — find majority
            from collections import Counter
            norm_counter = Counter(normalized.values())
            majority_norm = norm_counter.most_common(1)[0][0]

            # Map back to raw value for majority
            majority_val  = next(v for dt, v in found.items() if _normalize(v) == majority_norm)

            inconsistent_docs = [
                dt for dt, nv in normalized.items() if nv != majority_norm
            ]
            inconsistent_vals = [
                found[dt] for dt in inconsistent_docs
            ]

            report["failed"].append({
                "parameter":           label,
                "majority_value":      clean_name(majority_val),
                "inconsistent_docs":   inconsistent_docs,
                "inconsistent_values": inconsistent_vals,
                "all_values":          found,
            })

        if missing_from:
            report["warnings"].append({
                "parameter":    label,
                "missing_from": missing_from,
                "issue":        "Expected but not extracted — verify manually",
            })

    verdict = "FAIL" if report["failed"] else ("PARTIAL" if report["warnings"] else "PASS")
    report["verdict"] = verdict
    return report

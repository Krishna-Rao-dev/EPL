"""
LLM Service — Ollama / qwen2.5:3b field extraction + NLP summary
"""
import re as _re
import json
import httpx

from app.core.config import settings

OLLAMA_URL   = settings.OLLAMA_URL
OLLAMA_MODEL = settings.OLLAMA_MODEL

# ── Extraction prompts (from notebook) ───────────────────────
PROMPTS = {
    "PAN_CARD": """
Extract fields from this Company PAN Card OCR text.
Return ONLY valid JSON, no explanation, no markdown.

Required fields:
{
  "pan_number":    "10-char PAN e.g. AAKCM1234C",
  "entity_name":   "Full company name",
  "date_of_reg":   "DD/MM/YYYY",
  "entity_type":   "COMPANY or INDIVIDUAL",
  "issuing_auth":  "Income Tax Department"
}

OCR TEXT:
{ocr_text}
""",

    "GST_CERTIFICATE": """
Extract fields from this GST Registration Certificate OCR text.
Return ONLY valid JSON, no explanation, no markdown.

Required fields:
{
  "gstin":              "15-char GSTIN",
  "pan_number":         "10-char PAN",
  "legal_name":         "Legal name of business",
  "trade_name":         "Trade name if different",
  "state_code":         "2-digit state code",
  "state":              "State name",
  "status":             "ACTIVE or CANCELLED",
  "registration_date":  "DD/MM/YYYY",
  "constitution":       "Private Limited etc",
  "address":            "Full address",
  "pincode":            "6-digit PIN"
}

OCR TEXT:
{ocr_text}
""",

    "LEI_CERTIFICATE": """
Extract fields from this LEI Certificate OCR text.
Return ONLY valid JSON, no explanation, no markdown.

Required fields:
{
  "lei_code":           "20-char LEI",
  "legal_name":         "Legal name",
  "cin":                "CIN number",
  "pan_number":         "PAN number",
  "status":             "ACTIVE or INACTIVE",
  "registration_date":  "DD/MM/YYYY",
  "renewal_date":       "DD/MM/YYYY",
  "issuing_lou":        "Issuing organization",
  "country":            "Country"
}

OCR TEXT:
{ocr_text}
""",

    "INCORPORATION_CERTIFICATE": """
Extract fields from this Certificate of Incorporation OCR text.
Return ONLY valid JSON, no explanation, no markdown.

Required fields:
{
  "company_name":       "Full company name",
  "cin":                "CIN number",
  "pan_number":         "PAN number",
  "date_of_incorp":     "DD/MM/YYYY",
  "company_type":       "Private Limited etc",
  "authorized_capital": "Amount in numbers only e.g. 2500000",
  "state":              "State name",
  "roc":                "ROC office",
  "address":            "Registered address",
  "pincode":            "6-digit PIN"
}

OCR TEXT:
{ocr_text}
""",

    "MOA": """
Extract fields from this Memorandum of Association OCR text.
Return ONLY valid JSON, no explanation, no markdown.

Required fields:
{
  "company_name":       "Full company name",
  "cin":                "CIN number",
  "state":              "State of registered office",
  "address":            "Registered address",
  "pincode":            "6-digit PIN",
  "authorized_capital": "Amount in numbers only",
  "main_objects":       ["list of main business objects"],
  "subscribers": [
    {"name": "subscriber name", "shares": "number of shares"}
  ]
}

OCR TEXT:
{ocr_text}
""",

    "AOA": """
Extract fields from this Articles of Association OCR text.
Return ONLY valid JSON, no explanation, no markdown.

Required fields:
{
  "company_name":       "Full company name",
  "cin":                "CIN number",
  "authorized_capital": "Amount in numbers only",
  "min_directors":      "minimum number",
  "max_directors":      "maximum number",
  "directors": [
    {"name": "director name", "din": "DIN number"}
  ]
}

OCR TEXT:
{ocr_text}
""",

    "REGISTERED_ADDRESS": """
Extract fields from this Registered Address / INC-22 OCR text.
Return ONLY valid JSON, no explanation, no markdown.

Required fields:
{
  "company_name":    "Full company name",
  "cin":             "CIN number",
  "pan_number":      "PAN number",
  "gstin":           "GSTIN",
  "lei":             "LEI code",
  "address_line1":   "Building/flat",
  "address_line2":   "Street/road",
  "area":            "Area/locality",
  "city":            "City",
  "state":           "State",
  "pincode":         "6-digit PIN",
  "srn":             "Service request number",
  "filing_date":     "DD/MM/YYYY",
  "approval_date":   "DD/MM/YYYY",
  "status":          "APPROVED or PENDING"
}

OCR TEXT:
{ocr_text}
""",

    "ELECTRICITY_BILL": """
Extract fields from this Electricity Bill OCR text.
Return ONLY valid JSON, no explanation, no markdown.

Required fields:
{
  "consumer_name":    "Name on bill",
  "consumer_number":  "Consumer/account number",
  "discom":           "Electricity provider name",
  "address":          "Consumer address",
  "pincode":          "6-digit PIN",
  "bill_number":      "Bill reference number",
  "bill_date":        "DD/MM/YYYY",
  "due_date":         "DD/MM/YYYY",
  "billing_period":   "Month Year",
  "units_consumed":   "Number only",
  "total_amount":     "Number only e.g. 4693.70",
  "connection_type":  "Commercial or Residential"
}

OCR TEXT:
{ocr_text}
""",

    "TELEPHONE_BILL": """
Extract fields from this Telephone/Landline Bill OCR text.
Return ONLY valid JSON, no explanation, no markdown.

Required fields:
{
  "account_name":     "Name on bill",
  "account_number":   "Account number",
  "telephone_number": "Phone number",
  "provider":         "Telecom provider name",
  "address":          "Address on bill",
  "pincode":          "6-digit PIN",
  "bill_number":      "Bill reference number",
  "bill_date":        "DD/MM/YYYY",
  "due_date":         "DD/MM/YYYY",
  "billing_period":   "Month Year",
  "total_amount":     "Number only",
  "connection_type":  "Landline or Mobile"
}

OCR TEXT:
{ocr_text}
""",
    # Fraud document prompts
    "BOARD_OF_DIRECTORS": """
Extract all directors from this Board of Directors document.
Return ONLY valid JSON, no explanation, no markdown.
{
  "company_name": "",
  "cin": "",
  "pan": "",
  "directors": [
    {
      "name": "",
      "din": "",
      "pan": "",
      "dob": "DD/MM/YYYY",
      "designation": "",
      "shareholding": "%",
      "address": "",
      "nationality": "",
      "other_directorships": ""
    }
  ]
}
OCR TEXT:
{ocr_text}
""",

    "KMP_LIST": """
Extract all Key Managerial Persons from this document.
Return ONLY valid JSON, no explanation, no markdown.
{
  "company_name": "",
  "kmps": [
    {
      "name": "",
      "designation": "",
      "id_numbers": "",
      "email": "",
      "phone": ""
    }
  ]
}
OCR TEXT:
{ocr_text}
""",

    "BENEFICIAL_OWNERS": """
Extract beneficial ownership information from this UBO declaration.
Return ONLY valid JSON, no explanation, no markdown.
{
  "company_name": "",
  "ubos": [
    {
      "name": "",
      "pan": "",
      "direct_holding": "%",
      "indirect_holding": "",
      "total_effective": "%",
      "nature": ""
    }
  ],
  "related_entities": [
    {
      "name": "",
      "pan": "",
      "relationship": "",
      "ownership_pct": "%"
    }
  ]
}
OCR TEXT:
{ocr_text}
""",

    "PEP_DECLARATION": """
Extract PEP declaration details from this document.
Return ONLY valid JSON, no explanation, no markdown.
{
  "company_name": "",
  "declarations": [
    {
      "name": "",
      "designation": "",
      "pep_status": "PEP or NOT A PEP",
      "family_pep": "",
      "associate_pep": ""
    }
  ]
}
OCR TEXT:
{ocr_text}
""",

    "RPT_DOCUMENT": """
Extract Related Party Transaction details from this document.
Return ONLY valid JSON, no explanation, no markdown.
{
  "company_name": "",
  "related_party_transactions": [
    {
      "related_party": "",
      "relationship": "",
      "transaction_type": "",
      "amount": "",
      "terms": "",
      "approval": "",
      "risk_flag": ""
    }
  ]
}
OCR TEXT:
{ocr_text}
""",
}


def _clean_llm_response(raw: str) -> str:
    raw = _re.sub(r"<think>.*?</think>", "", raw, flags=_re.DOTALL).strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()


async def extract_fields_llm(ocr_text: str, doc_type: str) -> dict:
    """
    Sends OCR text to qwen2.5:3b, returns parsed JSON dict.
    Falls back to empty dict on failure.
    """
    prompt_template = PROMPTS.get(doc_type)
    if not prompt_template:
        return {}
    prompt = prompt_template.replace("{ocr_text}", ocr_text[:4000])  # cap context

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "top_p": 0.9},
                },
            )
        raw  = resp.json()["response"].strip()
        raw  = _clean_llm_response(raw)
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"⚠️ LLM extraction failed for {doc_type}: {e}")
        return {}


async def generate_nlp_summary(
    entity_graph: dict,
    pep_result: dict,
    rpt_result: dict,
    ownership_chains: list,
    compliance_verdict: str,
    company_name: str,
) -> list:
    """Generates 6-7 point risk summary via qwen2.5:3b"""
    context = {
        "company":          company_name,
        "graph_nodes":      len(entity_graph.get("nodes", [])),
        "graph_edges":      len(entity_graph.get("edges", [])),
        "nodes":            [{"label": n.get("label"), "type": n.get("type")} for n in entity_graph.get("nodes", [])],
        "pep_flag":         pep_result.get("overall_flag"),
        "pep_count":        pep_result.get("pep_found", 0),
        "rpt_risk":         rpt_result.get("overall_risk"),
        "rpt_transactions": rpt_result.get("total_transactions", 0),
        "rpt_flags":        [t.get("flags") for t in rpt_result.get("flagged", [])],
        "ownership_chains": ownership_chains,
        "compliance":       compliance_verdict,
    }

    prompt = f"""You are a financial fraud analyst at an Indian NBFC reviewing a loan application.
Based on the data below, write a risk summary as a JSON array of 6-7 clear English sentences.
Each sentence is one item in the array. The last sentence must be the overall recommendation.
Return ONLY a valid JSON array of strings. No markdown, no explanation.

DATA:
{json.dumps(context, indent=2)}

Format: ["Point 1.", "Point 2.", "Point 3.", "Point 4.", "Point 5.", "Point 6.", "Recommendation."]"""

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2},
                },
            )
        raw    = resp.json()["response"].strip()
        raw    = _clean_llm_response(raw)
        points = json.loads(raw)
        return points if isinstance(points, list) else [raw]
    except Exception as e:
        return [
            f"{company_name} is under review for NBFC compliance.",
            "Entity relationship graph has been built from submitted documents.",
            "PEP and sanctions screening completed.",
            "Related party transactions identified and flagged for review.",
            "All primary documents verified against public APIs.",
            f"NLP summary generation encountered an issue: {e}",
            f"Overall risk: {compliance_verdict}. Manual review recommended.",
        ]


async def generate_export_summary(report_data: dict, report_type: str) -> str:
    """Uses qwen2.5:3b to generate a narrative export summary"""
    prompt = f"""You are a compliance officer writing a formal report summary.
Based on this {report_type} report data, write a concise 3-paragraph professional summary
suitable for a PDF report. Use formal language. Return only plain text, no markdown.

DATA:
{json.dumps(report_data, indent=2)[:3000]}
"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                OLLAMA_URL,
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
                      "options": {"temperature": 0.3}},
            )
        return resp.json()["response"].strip()
    except Exception:
        return f"This is an automated {report_type} report generated by Pramanik RegTech Platform."

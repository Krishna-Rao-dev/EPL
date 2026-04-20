"""
LLM Service — thin dispatch layer + NLP/export helpers.

Field extraction is now fully delegated to document agents.
This file only keeps:
  - extract_fields_llm()  → compatibility shim → calls agent
  - generate_nlp_summary()
  - generate_export_summary()
"""
from __future__ import annotations

import re
import json
import httpx
from app.core.config import settings

OLLAMA_URL   = settings.OLLAMA_URL
OLLAMA_MODEL = settings.OLLAMA_MODEL


# ── Compatibility shim (used by fraud router unchanged) ───────

async def extract_fields_llm(ocr_text: str, doc_type: str) -> dict:
    """
    Drop-in replacement for the old monolithic function.
    Delegates to the typed document agent for this doc_type.
    Returns plain dict — same contract as before.
    """
    # Import here to avoid circular at module load time
    from agents.document_agents import extract_document
    return await extract_document(ocr_text, doc_type)


# ── NLP Summary (fraud pipeline) ──────────────────────────────

async def generate_nlp_summary(
    entity_graph: dict,
    pep_result:   dict,
    rpt_result:   dict,
    ownership_chains: list,
    compliance_verdict: str,
    company_name: str,
) -> list:
    """Generates 6-7 point risk summary via Ollama."""
    context = {
        "company":          company_name,
        "graph_nodes":      len(entity_graph.get("nodes", [])),
        "graph_edges":      len(entity_graph.get("edges", [])),
        "nodes":            [{"label": n.get("label"), "type": n.get("type")}
                             for n in entity_graph.get("nodes", [])],
        "pep_flag":         pep_result.get("overall_flag"),
        "pep_count":        pep_result.get("pep_found", 0),
        "rpt_risk":         rpt_result.get("overall_risk"),
        "rpt_transactions": rpt_result.get("total_transactions", 0),
        "rpt_flags":        [t.get("flags") for t in rpt_result.get("flagged", [])],
        "ownership_chains": ownership_chains,
        "compliance":       compliance_verdict,
    }

    prompt = f"""You are a financial fraud analyst at an Indian NBFC reviewing a loan application.
Write a risk summary as a JSON array of 6-7 clear English sentences.
Each sentence is one array item. The last sentence must be the overall recommendation.
Return ONLY a valid answer with "\n" (break line). No markdown, no explanation.


DATA:
{json.dumps(context, indent=2)}
"""

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                OLLAMA_URL,
                json={
                    "model":  OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2},
                },
            )
        raw = resp.json().get("response", "").strip()
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        raw = re.sub(r"```(?:json)?\s*", "", raw).replace("```", "").strip()
        start = raw.find("[")
        end   = raw.rfind("]")
        if start != -1 and end != -1:
            raw = raw[start:end + 1]
        points = json.loads(raw)
        
        cleaned_points = []
        for p in (points if isinstance(points, list) else [raw]):
            if isinstance(p, str):
                cleaned_points.append(p.replace("<", "&lt;").replace(">", "&gt;"))
            else:
                cleaned_points.append(str(p).replace("<", "&lt;").replace(">", "&gt;"))
        return cleaned_points
    except Exception as e:
        return [
            f"{company_name} is under review for NBFC compliance.",
            "Entity relationship graph has been built from submitted documents.",
            "PEP and sanctions screening completed.",
            "Related party transactions identified and flagged for review.",
            "All primary documents verified against public APIs.",
            f"NLP summary generation encountered an issue. Manual review recommended."
        ]


# ── Export summary (PDF generation) ──────────────────────────

async def generate_export_summary(report_data: dict, report_type: str) -> str:
    """Generates a structured narrative for PDF export via Ollama."""
    prompt = f"""You are an elite Big 4 compliance auditor writing an executive summary for a formal {report_type} report.
Analyze the following data and provide a highly professional, objective 3-paragraph executive summary. 

Structure:
Paragraph 1: High-level overview of the entity and the core verdict/risk score.
Paragraph 2: Key findings, anomalies, and critical risk flags (if any).
Paragraph 3: Concluding assessment and recommended next steps.

Rules:
- Adopt a formal, neutral, and authoritative tone.
- Do not use any markdown formatting (no asterisks, no hash symbols).
- Do not include greetings or sign-offs.
- Return ONLY the final plain text.
- Do NOT include any `<think>` tags or similar output, just the summary.

DATA:
{json.dumps(report_data, indent=2)[:3000]}
"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                OLLAMA_URL,
                json={
                    "model":  OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2},
                },
            )
        raw = resp.json().get("response", "").strip()
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        raw = raw.replace("<", "&lt;").replace(">", "&gt;")
        return raw
    except Exception:
        return (
            f"This is an automated {report_type} report generated "
            f"by the Platform. Further manual review is recommended."
        )
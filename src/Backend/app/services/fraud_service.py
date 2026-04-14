"""
Fraud Analysis Service
Entity graph building, PEP screening, RPT analysis, risk score

FIXES:
- All .get() calls use `or ""` / `or []` instead of default="" to handle
  explicit None values coming from Pydantic-validated agent output
- _name_match guards against None on both sides
- other_directorships None-safe split
"""
from typing import Optional


# ── Helpers ───────────────────────────────────────────────────

def _s(val) -> str:
    """Safe string — converts None/anything to str, strips whitespace."""
    if val is None:
        return ""
    return str(val).strip()


def _name_match(label: str, name) -> bool:
    """Case-insensitive substring match, None-safe on both sides."""
    if not label or not name:
        return False
    ln = _s(label).replace("\n", " ").upper()
    nm = _s(name).upper()
    if not ln or not nm:
        return False
    return ln == nm or ln in nm or nm in ln


def _split_directorships(raw) -> list[str]:
    """Split other_directorships string (or None) into a clean list."""
    if not raw:
        return []
    return [
        x.strip() for x in _s(raw).replace(";", ",").split(",")
        if x.strip() and x.strip().upper() not in ("NONE", "NIL", "NA", "N/A", "-", "NULL", "")
    ]


# ── Entity Graph Builder ──────────────────────────────────────

def build_entity_graph(
    board_data: dict,
    benef_data: dict,
    company_name: str,
    compliance_doc_data: dict = None,
) -> dict:
    nodes    = []
    edges    = []
    node_ids = {}

    def add_node(id_key: str, label: str, node_type: str, risk: str = "low") -> str:
        if id_key not in node_ids:
            node_ids[id_key] = id_key
            nodes.append({"id": id_key, "label": label, "type": node_type, "risk": risk})
        return id_key

    company_id = add_node("company", company_name.replace(" ", "\n"), "company", "low")

    # Directors
    directors = board_data.get("directors") or []
    for i, d in enumerate(directors[:5]):
        name         = _s(d.get("name")) or f"Director {i+1}"
        shareholding = _s(d.get("shareholding"))
        did          = f"dir{i+1}"

        add_node(did, name, "person", "low")
        edge_label = f"Director {shareholding}" if shareholding and shareholding not in ("%", "") else "Director"
        edges.append({"from": did, "to": company_id, "label": edge_label, "type": "ownership"})

        for j, oc in enumerate(_split_directorships(d.get("other_directorships"))[:2]):
            oc_id = f"other_co_{i}_{j}"
            add_node(oc_id, oc.replace(" ", "\n"), "company", "medium")
            edges.append({"from": did, "to": oc_id, "label": "Director", "type": "directorship"})

    # Beneficial owners
    ubos             = benef_data.get("ubos") or []
    related_entities = benef_data.get("related_entities") or []

    for i, ubo in enumerate(ubos[:3]):
        name = _s(ubo.get("name")) or f"UBO {i+1}"
        uid  = f"ubo_{i}"

        matched_id = None
        for node in nodes:
            if node["type"] == "person" and _name_match(node["label"], name):
                matched_id = node["id"]
                break
        if not matched_id:
            matched_id = add_node(uid, name, "person", "low")

        pct = _s(ubo.get("direct_holding")) or _s(ubo.get("total_effective"))
        edges.append({
            "from":  matched_id,
            "to":    company_id,
            "label": f"Owns {pct}" if pct else "Beneficial Owner",
            "type":  "beneficial",
        })

    for i, entity in enumerate(related_entities[:3]):
        name = _s(entity.get("name")) or f"Related Entity {i+1}"
        eid  = f"related_{i}"
        rel  = _s(entity.get("relationship")) or "Related"
        pct  = _s(entity.get("ownership_pct"))
        add_node(eid, name.replace(" ", "\n"), "company", "medium")
        edges.append({
            "from":  eid,
            "to":    company_id,
            "label": f"Owns {pct}" if pct else rel,
            "type":  "ownership",
        })

    # Utility/bank node from compliance docs
    if compliance_doc_data:
        discom = _s((compliance_doc_data.get("ELECTRICITY_BILL") or {}).get("discom"))
        if discom:
            bank_id = add_node("bank1", discom.replace(" ", "\n"), "bank", "low")
            edges.append({"from": company_id, "to": bank_id, "label": "Utility Account", "type": "financial"})

    return {"nodes": nodes, "edges": edges}


# ── PEP Screening ─────────────────────────────────────────────

def screen_pep(pep_data: dict, board_data: dict) -> dict:
    declarations = pep_data.get("declarations") or []

    pep_found = sum(
        1 for d in declarations
        if _s(d.get("pep_status")).upper() == "PEP"
        and "NOT" not in _s(d.get("pep_status")).upper()
    )

    results   = []
    directors = board_data.get("directors") or []

    for d in directors:
        name       = _s(d.get("name"))
        pep_status = False

        for decl in declarations:
            if _name_match(_s(decl.get("name")), name):
                status_str = _s(decl.get("pep_status")).upper()
                pep_status = (status_str == "PEP" and "NOT" not in status_str)
                break

        results.append({
            "name":               name,
            "din":                _s(d.get("din")),
            "pan":                _s(d.get("pan")),
            "dob":                _s(d.get("dob")),
            "address":            _s(d.get("address")),
            "role":               _s(d.get("designation")) or "Director",
            "pep":                pep_status,
            "sanctions":          False,
            "riskScore":          40 if pep_status else 15,
            "otherDirectorships": _split_directorships(d.get("other_directorships")),
        })

    return {
        "overall_flag": "PEP_DETECTED" if pep_found > 0 else "CLEAR",
        "pep_found":    pep_found,
        "persons":      results,
        "total":        len(results),
    }


# ── RPT Analysis ──────────────────────────────────────────────

def analyze_rpt(rpt_data: dict, board_data: dict) -> dict:
    transactions = rpt_data.get("related_party_transactions") or []

    flagged  = []
    max_risk = 0
    risk_order = {"LOW": 10, "MEDIUM": 30, "HIGH": 50}

    formatted = []
    for t in transactions:
        rp       = _s(t.get("related_party"))
        rel      = _s(t.get("relationship"))
        rf       = _s(t.get("risk_flag")) or "LOW"
        rf_upper = rf.upper()
        risk_lvl = "HIGH" if "HIGH" in rf_upper else ("MEDIUM" if "MEDIUM" in rf_upper else "LOW")
        risk_num = risk_order.get(risk_lvl, 10)
        max_risk = max(max_risk, risk_num)

        entry = {
            "entity":          rp,
            "relationship":    rel,
            "transactionType": _s(t.get("transaction_type")),
            "amount":          _s(t.get("amount")) or "Unknown",
            "riskLevel":       risk_lvl,
            "flagReason":      _s(t.get("terms")) or rf,
        }
        formatted.append(entry)
        if risk_lvl in ("HIGH", "MEDIUM"):
            flagged.append({"entity": rp, "risk": risk_lvl, "flags": rf})

    overall = "HIGH" if max_risk >= 50 else ("MEDIUM" if max_risk >= 30 else "LOW")
    return {
        "overall_risk":       overall,
        "max_risk_score":     max_risk,
        "total_transactions": len(transactions),
        "flagged":            flagged,
        "rpt":                formatted,
    }


# ── Ownership Chains ──────────────────────────────────────────

def build_ownership_chains(benef_data: dict, board_data: dict) -> list:
    chains  = []
    company = _s(benef_data.get("company_name"))

    for ubo in (benef_data.get("ubos") or []):
        pct = _s(ubo.get("direct_holding")) or _s(ubo.get("total_effective")) or "?"
        chains.append({
            "owner":   _s(ubo.get("name")),
            "holding": pct,
            "nature":  _s(ubo.get("nature")) or "Direct",
            "company": company,
        })

    for rel in (benef_data.get("related_entities") or []):
        chains.append({
            "owner":      _s(rel.get("name")),
            "holding":    _s(rel.get("ownership_pct")) or "?",
            "nature":     _s(rel.get("relationship")) or "Indirect",
            "via_entity": _s(rel.get("name")),
            "company":    company,
        })

    return chains


# ── Final Risk Score ──────────────────────────────────────────

def compute_risk_score(
    pep_result: dict,
    rpt_result: dict,
    entity_graph: dict,
    compliance_verdict: str,
) -> dict:
    score = 0
    flags = []

    if pep_result.get("pep_found", 0) > 0:
        score += 40
        flags.append("PEP_DETECTED")

    rpt_score = min(rpt_result.get("max_risk_score", 0), 30)
    score += rpt_score
    if rpt_result.get("overall_risk") in ("HIGH", "MEDIUM"):
        flags.append(f"RPT_RISK_{rpt_result['overall_risk']}")

    if len(entity_graph.get("nodes", [])) > 5:
        score += 10
        flags.append("COMPLEX_ENTITY_STRUCTURE")

    if len(entity_graph.get("edges", [])) > 7:
        score += 5
        flags.append("HIGH_RELATIONSHIP_COUNT")

    if _s(compliance_verdict).upper() == "FAIL":
        score += 15
        flags.append("COMPLIANCE_FAILED")

    score = min(score, 100)
    level = "HIGH" if score >= 70 else ("MEDIUM" if score >= 40 else "LOW")

    recs = {
        "HIGH":   "REJECT — High fraud risk. Do not proceed.",
        "MEDIUM": "ENHANCED_DUE_DILIGENCE — Deeper investigation required before sanctioning.",
        "LOW":    "STANDARD_DUE_DILIGENCE — Proceed with normal periodic monitoring.",
    }
    return {
        "risk_score":     score,
        "risk_level":     level,
        "flags":          flags,
        "recommendation": recs[level],
    }
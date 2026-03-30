"""
Fraud Analysis Service
Entity graph building, PEP screening, RPT analysis, risk score
"""
from datetime import datetime


# ── Entity Graph Builder ──────────────────────────────────────
def build_entity_graph(
    board_data: dict,
    benef_data: dict,
    company_name: str,
    compliance_doc_data: dict = None,
) -> dict:
    """
    Build entity graph nodes and edges from parsed fraud docs.
    Returns {nodes, edges} matching frontend EntityGraph schema.
    """
    nodes = []
    edges = []
    node_ids = {}

    def add_node(id_key: str, label: str, node_type: str, risk: str = "low") -> str:
        if id_key not in node_ids:
            node_ids[id_key] = id_key
            nodes.append({"id": id_key, "label": label, "type": node_type, "risk": risk})
        return id_key

    # Main company node
    company_id = add_node("company", company_name.replace(" ", "\n"), "company", "low")

    # Directors from board doc
    directors  = board_data.get("directors", [])
    for i, d in enumerate(directors[:5]):
        name      = d.get("name", f"Director {i+1}")
        did       = f"dir{i+1}"
        shareholding = d.get("shareholding", "")
        din       = d.get("din", "")
        add_node(did, name, "person", "low")
        label = f"Director {shareholding}" if shareholding and shareholding not in ("%", "") else "Director"
        edges.append({"from": did, "to": company_id, "label": label, "type": "ownership"})

        # Other directorships
        other = d.get("other_directorships", "")
        if other and other.strip() and other.strip() not in ("None", "NIL", "Nil", "-"):
            other_companies = [x.strip() for x in other.replace(";", ",").split(",") if x.strip()]
            for j, oc in enumerate(other_companies[:2]):
                oc_id = f"other_co_{i}_{j}"
                add_node(oc_id, oc.replace(" ", "\n"), "company", "medium")
                edges.append({"from": did, "to": oc_id, "label": "Director", "type": "directorship"})

    # Beneficial owners
    ubos = benef_data.get("ubos", [])
    related_entities = benef_data.get("related_entities", [])

    for i, ubo in enumerate(ubos[:3]):
        name = ubo.get("name", f"UBO {i+1}")
        uid  = f"ubo_{i}"
        # Check if already added as director
        matched_id = None
        for node in nodes:
            if node["type"] == "person" and _name_match(node["label"], name):
                matched_id = node["id"]
                break
        if not matched_id:
            matched_id = add_node(uid, name, "person", "low")
        pct = ubo.get("direct_holding", "") or ubo.get("total_effective", "")
        edges.append({
            "from": matched_id, "to": company_id,
            "label": f"Owns {pct}" if pct else "Beneficial Owner",
            "type": "beneficial",
        })

    for i, entity in enumerate(related_entities[:3]):
        name = entity.get("name", f"Related Entity {i+1}")
        eid  = f"related_{i}"
        rel  = entity.get("relationship", "Related")
        pct  = entity.get("ownership_pct", "")
        add_node(eid, name.replace(" ", "\n"), "company", "medium")
        edges.append({
            "from": eid, "to": company_id,
            "label": f"Owns {pct}" if pct else rel,
            "type": "ownership",
        })

    # Add bank node if company has bank relationship (from compliance docs)
    if compliance_doc_data:
        # Look for any bank in electricity/utility bills
        discom = compliance_doc_data.get("ELECTRICITY_BILL", {}).get("discom", "")
        if discom:
            bank_id = add_node("bank1", discom.replace(" ", "\n"), "bank", "low")
            edges.append({"from": company_id, "to": bank_id, "label": "Utility Account", "type": "financial"})

    return {"nodes": nodes, "edges": edges}


def _name_match(label: str, name: str) -> bool:
    ln = label.replace("\n", " ").upper().strip()
    nm = name.upper().strip()
    return ln == nm or ln in nm or nm in ln


# ── PEP Screening ─────────────────────────────────────────────
def screen_pep(pep_data: dict, board_data: dict) -> dict:
    """
    Check PEP declarations and cross-reference with directors.
    """
    declarations = pep_data.get("declarations", [])
    pep_found    = sum(1 for d in declarations if "PEP" == d.get("pep_status", "").upper()
                       and "NOT" not in d.get("pep_status", "").upper())

    results = []
    directors = board_data.get("directors", [])
    for d in directors:
        name       = d.get("name", "")
        pep_status = False
        # Look for matching declaration
        for decl in declarations:
            if _name_match(decl.get("name", ""), name):
                pep_status = "PEP" == decl.get("pep_status", "").upper() and "NOT" not in decl.get("pep_status", "")
                break
        results.append({
            "name":       name,
            "din":        d.get("din", ""),
            "pan":        d.get("pan", ""),
            "dob":        d.get("dob", ""),
            "address":    d.get("address", ""),
            "role":       d.get("designation", "Director"),
            "pep":        pep_status,
            "sanctions":  False,  # Would integrate with real sanctions DB
            "riskScore":  40 if pep_status else 15,
            "otherDirectorships": [
                x.strip() for x in d.get("other_directorships", "").replace(";", ",").split(",")
                if x.strip() and x.strip() not in ("None", "NIL", "Nil", "-")
            ],
        })

    return {
        "overall_flag": "PEP_DETECTED" if pep_found > 0 else "CLEAR",
        "pep_found":    pep_found,
        "persons":      results,
        "total":        len(results),
    }


# ── RPT Analysis ──────────────────────────────────────────────
def analyze_rpt(rpt_data: dict, board_data: dict) -> dict:
    """
    Analyse related party transactions and assign risk levels.
    """
    transactions = rpt_data.get("related_party_transactions", [])
    directors    = {d.get("name", "").upper() for d in board_data.get("directors", [])}

    flagged    = []
    max_risk   = 0
    risk_order = {"LOW": 10, "MEDIUM": 30, "HIGH": 50}

    formatted = []
    for t in transactions:
        rp       = t.get("related_party", "")
        rel      = t.get("relationship", "")
        rf       = t.get("risk_flag", "LOW — standard")
        risk_lvl = "HIGH" if "HIGH" in rf.upper() else ("MEDIUM" if "MEDIUM" in rf.upper() else "LOW")
        risk_num = risk_order.get(risk_lvl, 10)
        max_risk = max(max_risk, risk_num)

        entry = {
            "entity":          rp,
            "relationship":    rel,
            "transactionType": t.get("transaction_type", ""),
            "amount":          t.get("amount", "Unknown"),
            "riskLevel":       risk_lvl,
            "flagReason":      t.get("terms", "") or rf,
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
    chains = []
    company = benef_data.get("company_name", "")
    for ubo in benef_data.get("ubos", []):
        pct = ubo.get("direct_holding") or ubo.get("total_effective") or "?"
        chains.append({
            "owner":   ubo.get("name"),
            "holding": pct,
            "nature":  ubo.get("nature", "Direct"),
            "company": company,
        })
    for rel in benef_data.get("related_entities", []):
        chains.append({
            "owner":      rel.get("name"),
            "holding":    rel.get("ownership_pct", "?"),
            "nature":     rel.get("relationship", "Indirect"),
            "via_entity": rel.get("name"),
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

    if compliance_verdict == "FAIL":
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

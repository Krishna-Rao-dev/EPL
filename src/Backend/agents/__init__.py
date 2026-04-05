"""
Document Extraction Agents package.

Usage:
    from agents.document_agents import get_agent, extract_document
    from agents.base_agent import ExtractionResult
    from agents.schemas import SCHEMA_REGISTRY
"""
from agents.document_agents import get_agent, extract_document, _AGENT_INSTANCES
from agents.base_agent import ExtractionResult

__all__ = ["get_agent", "extract_document", "ExtractionResult", "_AGENT_INSTANCES"]

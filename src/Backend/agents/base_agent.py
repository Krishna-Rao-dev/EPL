"""
Base Document Agent.

Every doc-type agent inherits from this.
It owns: prompt building → LLM call → JSON parse → Pydantic validate → return typed result.

One LLM call per document. No exceptions.
"""
from __future__ import annotations

import re
import json
import httpx
from abc import ABC, abstractmethod
from typing import Optional, Type
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from agents.schemas import SCHEMA_REGISTRY


class ExtractionResult(BaseModel):
    """Wrapper returned by every agent.extract() call."""
    doc_type:   str
    status:     str          # "EXTRACTED" | "PARTIAL" | "FAILED"
    fields:     dict         # validated field dict (Pydantic .model_dump())
    raw_json:   Optional[str] = None   # raw LLM output for debugging
    error:      Optional[str] = None
    confidence: float = 0.0  # passed in from OCR layer


class DocumentAgent(ABC):
    """
    Abstract base for all document extraction agents.

    Subclasses must define:
      - doc_type: str                   e.g. "PAN_CARD"
      - _build_prompt(ocr_text) -> str  returns the full prompt string
    """

    doc_type: str        # override in subclass
    _schema:  type[BaseModel]  # auto-resolved in __init_subclass__

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Auto-wire schema from registry when subclass is defined
        if hasattr(cls, "doc_type") and cls.doc_type:
            schema = SCHEMA_REGISTRY.get(cls.doc_type)
            if schema:
                cls._schema = schema

    # ── Abstract interface ────────────────────────────────────

    @abstractmethod
    def _build_prompt(self, ocr_text: str) -> str:
        """Return the complete prompt string to send to the LLM."""
        ...

    # ── Shared LLM call ───────────────────────────────────────

    async def _call_llm(self, prompt: str) -> str:
        """Single Ollama call. Returns raw response string."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                settings.OLLAMA_URL,
                json={
                    "model":  settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "top_p":       0.9,
                        "num_predict": 1024,
                    },
                },
            )
        return resp.json().get("response", "").strip()

    # ── JSON extraction from LLM output ──────────────────────

    @staticmethod
    def _parse_json(raw: str) -> dict | None:
        """
        Robustly extract a JSON object from LLM output.
        Handles: markdown fences, <think> blocks, leading text.
        """
        # Strip <think>...</think>
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        # Strip markdown fences
        raw = re.sub(r"```(?:json)?\s*", "", raw).replace("```", "").strip()
        # Find outermost { ... }
        start = raw.find("{")
        end   = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = raw[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Try to fix trailing commas (common LLM mistake)
            candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                return None

    # ── Pydantic validation ───────────────────────────────────

    def _validate(self, raw_dict: dict) -> tuple[dict, str]:
        """
        Run raw dict through the doc-type Pydantic schema.
        Returns (validated_dict, status).
        status: "EXTRACTED" if ≥1 non-null field, "FAILED" otherwise.
        """
        schema: type[BaseModel] = self._schema
        try:
            model = schema.model_validate(raw_dict)
        except ValidationError:
            # Partial — try field by field
            model = schema.model_construct()

        validated = model.model_dump(exclude_none=False)

        # Count non-null fields
        non_null = sum(
            1 for v in validated.values()
            if v is not None and v != [] and v != {}
        )
        status = "EXTRACTED" if non_null > 0 else "FAILED"
        return validated, status

    # ── Public entrypoint ─────────────────────────────────────

    async def extract(self, ocr_text: str, confidence: float = 0.0) -> ExtractionResult:
        """
        Full pipeline: build prompt → LLM → parse → validate → return.
        Never raises — always returns an ExtractionResult.
        """
        if not ocr_text or not ocr_text.strip():
            return ExtractionResult(
                doc_type=self.doc_type,
                status="FAILED",
                fields={},
                error="Empty OCR text",
                confidence=confidence,
            )

        # Cap OCR input — enough context, not too much for 3b model
        ocr_snippet = ocr_text[:3500]
        prompt      = self._build_prompt(ocr_snippet)

        raw_response = ""
        try:
            raw_response = await self._call_llm(prompt)
        except httpx.ConnectError:
            return ExtractionResult(
                doc_type=self.doc_type,
                status="FAILED",
                fields={},
                error=f"Ollama not reachable at {settings.OLLAMA_URL}",
                confidence=confidence,
            )
        except Exception as e:
            return ExtractionResult(
                doc_type=self.doc_type,
                status="FAILED",
                fields={},
                error=f"LLM call failed: {e}",
                confidence=confidence,
            )

        # ── Log raw LLM output ────────────────────────────────
        print(f"\n{'='*60}")
        print(f"[{self.doc_type}] RAW LLM RESPONSE:")
        print(raw_response)
        print(f"{'='*60}\n")

        raw_dict = self._parse_json(raw_response)
        if raw_dict is None:
            print(f"❌ [{self.doc_type}] JSON PARSE FAILED — could not find valid JSON in response")
            return ExtractionResult(
                doc_type=self.doc_type,
                status="FAILED",
                fields={},
                raw_json=raw_response[:300],
                error="Could not parse JSON from LLM response",
                confidence=confidence,
            )

        print(f"[{self.doc_type}] PARSED JSON:")
        print(json.dumps(raw_dict, indent=2))

        validated, status = self._validate(raw_dict)

        print(f"[{self.doc_type}] AFTER PYDANTIC VALIDATION:")
        print(json.dumps(validated, indent=2, default=str))
        print(
            f"{'✅' if status == 'EXTRACTED' else '⚠️'} "
            f"{self.doc_type}: {status} — "
            f"{sum(1 for v in validated.values() if v is not None)} fields extracted"
        )

        return ExtractionResult(
            doc_type=self.doc_type,
            status=status,
            fields=validated,
            raw_json=raw_response[:200] if status == "FAILED" else None,
            confidence=confidence,
        )
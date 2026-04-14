"""
Base Document Agent.

Pipeline: prompt → LLM → parse JSON → Pydantic validate → return typed result.

Features:
- MAX_RETRIES: controls extra LLM attempts on JSON parse failure
  Set to 1 now (cheap). Increase to 3 when you have budget.
- Retry prompt is tighter — tells model exactly what went wrong
- One LLM call per document on success; up to 1+MAX_RETRIES on failure
"""
from __future__ import annotations

import re
import json
from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from agents.schemas import SCHEMA_REGISTRY

# ── Retry config — change this when you have budget ──────────
MAX_RETRIES = 1   # 0 = no retries, 1 = one extra attempt, 3 = generous


class ExtractionResult(BaseModel):
    doc_type:   str
    status:     str           # "EXTRACTED" | "PARTIAL" | "FAILED"
    fields:     dict
    raw_json:   Optional[str] = None
    error:      Optional[str] = None
    confidence: float = 0.0
    attempts:   int   = 1


class DocumentAgent(ABC):
    doc_type: str
    _schema:  type[BaseModel]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "doc_type") and cls.doc_type:
            schema = SCHEMA_REGISTRY.get(cls.doc_type)
            if schema:
                cls._schema = schema

    @abstractmethod
    def _build_prompt(self, ocr_text: str) -> str: ...

    def _build_retry_prompt(self, ocr_text: str, bad_response: str, error_msg: str) -> str:
        """Tighter prompt on retry — tells model exactly what broke."""
        return f"""Your previous response could not be parsed as valid JSON.
Error: {error_msg}
Your previous response started with: {bad_response[:120]}

Try again. Rules:
- Return ONLY a JSON object
- Start with {{ and end with }}
- No markdown fences, no explanation text, no trailing commas
- Use null for missing fields, not empty strings or placeholder text

{self._build_prompt(ocr_text)}"""

    async def _call_llm(self, prompt: str) -> str:
        from langchain_groq import ChatGroq
        from langchain_core.messages import HumanMessage
        llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model="llama-3.1-8b-instant",
            temperature=0.0,
            max_tokens=1024,
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        return response.content.strip()

    @staticmethod
    def _parse_json(raw: str) -> dict | None:
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        raw = re.sub(r"```(?:json)?\s*", "", raw).replace("```", "").strip()
        start = raw.find("{")
        end   = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = raw[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Fix trailing commas — common LLM mistake
            candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                return None

    def _validate(self, raw_dict: dict) -> tuple[dict, str]:
        schema: type[BaseModel] = self._schema
        try:
            model = schema.model_validate(raw_dict)
        except ValidationError:
            model = schema.model_construct()
        validated = model.model_dump(exclude_none=False)
        non_null  = sum(
            1 for v in validated.values()
            if v is not None and v != [] and v != {}
        )
        return validated, ("EXTRACTED" if non_null > 0 else "FAILED")

    async def extract(self, ocr_text: str, confidence: float = 0.0) -> ExtractionResult:
        if not ocr_text or not ocr_text.strip():
            return ExtractionResult(
                doc_type=self.doc_type, status="FAILED",
                fields={}, error="Empty OCR text", confidence=confidence,
            )

        ocr_snippet = ocr_text[:3500]
        prompt      = self._build_prompt(ocr_snippet)
        attempts    = 0
        last_raw    = ""
        last_error  = ""

        while attempts <= MAX_RETRIES:
            attempts += 1

            try:
                if attempts == 1:
                    raw_response = await self._call_llm(prompt)
                else:
                    retry_prompt = self._build_retry_prompt(ocr_snippet, last_raw, last_error)
                    raw_response = await self._call_llm(retry_prompt)
                    print(f"   ↻ [{self.doc_type}] Retry attempt {attempts - 1}")
            except Exception as e:
                return ExtractionResult(
                    doc_type=self.doc_type, status="FAILED", fields={},
                    error=f"LLM call failed: {e}", confidence=confidence, attempts=attempts,
                )

            # Log
            print(f"\n{'='*60}")
            print(f"[{self.doc_type}] RAW LLM RESPONSE (attempt {attempts}):")
            print(raw_response)
            print(f"{'='*60}\n")

            raw_dict = self._parse_json(raw_response)

            if raw_dict is None:
                last_raw   = raw_response
                last_error = "No valid JSON object found in response"
                print(f"❌ [{self.doc_type}] JSON parse failed (attempt {attempts})")
                if attempts <= MAX_RETRIES:
                    continue
                return ExtractionResult(
                    doc_type=self.doc_type, status="FAILED", fields={},
                    raw_json=raw_response[:300],
                    error=f"JSON parse failed after {attempts} attempt(s)",
                    confidence=confidence, attempts=attempts,
                )

            print(f"[{self.doc_type}] PARSED JSON (attempt {attempts}):")
            print(json.dumps(raw_dict, indent=2))

            validated, status = self._validate(raw_dict)

            print(f"[{self.doc_type}] AFTER PYDANTIC VALIDATION:")
            print(json.dumps(validated, indent=2, default=str))
            print(
                f"{'✅' if status == 'EXTRACTED' else '⚠️'} "
                f"{self.doc_type}: {status} — "
                f"{sum(1 for v in validated.values() if v is not None)} fields | "
                f"{attempts} attempt(s)"
            )

            return ExtractionResult(
                doc_type=self.doc_type, status=status, fields=validated,
                raw_json=raw_response[:200] if status == "FAILED" else None,
                confidence=confidence, attempts=attempts,
            )

        return ExtractionResult(
            doc_type=self.doc_type, status="FAILED", fields={},
            error="Exhausted retries", confidence=confidence, attempts=attempts,
        )
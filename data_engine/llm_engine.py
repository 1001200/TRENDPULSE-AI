"""
TrendPulse LLM Engine
=====================

LLM reasoning layer for the TrendPulse Data Engine.

Design principles:
- Deterministic data processing remains the source of truth.
- LLM reasoning is advisory, not authoritative.
- No raw dataset is blindly sent to an LLM.
- The engine works even when no LLM provider/API key is configured.
- Provider-specific code is isolated behind a small interface.
- Every LLM decision contains evidence/context.
- Failures never break the core data pipeline.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Protocol


# ============================================================
# DATA STRUCTURES
# ============================================================


@dataclass
class LLMDecision:
    """A single decision produced by the LLM layer."""

    decision_type: str
    decision: str
    confidence: float
    reason: str
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LLMAnalysis:
    """Complete result returned by the LLM reasoning layer."""

    enabled: bool
    provider: Optional[str]
    model: Optional[str]
    confidence: str
    recommendations: List[str] = field(default_factory=list)
    mapping_decisions: List[Dict[str, Any]] = field(default_factory=list)
    cleaning_decisions: List[Dict[str, Any]] = field(default_factory=list)
    anomaly_decisions: List[Dict[str, Any]] = field(default_factory=list)
    explanation: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================
# PROVIDER INTERFACE
# ============================================================


class LLMProvider(Protocol):
    """
    Minimal provider interface.

    Any future provider must implement generate().
    """

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        ...


# ============================================================
# CONFIGURATION
# ============================================================


DEFAULT_MODEL = os.getenv(
    "TRENDPULSE_LLM_MODEL",
    "gpt-4o-mini",
)

DEFAULT_PROVIDER = os.getenv(
    "TRENDPULSE_LLM_PROVIDER",
    "",
).strip().lower()


def is_llm_configured() -> bool:
    """
    Return True only when an LLM provider has explicitly been configured.

    We deliberately do not automatically activate an external API.
    """

    provider = DEFAULT_PROVIDER

    if provider in {"openai", "azure_openai"}:
        return bool(
            os.getenv("OPENAI_API_KEY")
            or os.getenv("AZURE_OPENAI_API_KEY")
        )

    return False


# ============================================================
# SAFE SERIALIZATION
# ============================================================


def _safe_json(value: Any) -> Any:
    """
    Convert common pandas/numpy/Python objects into JSON-safe values.

    This keeps the LLM layer independent from pandas internals.
    """

    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if hasattr(value, "item"):
        try:
            return _safe_json(value.item())
        except Exception:
            pass

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass

    if isinstance(value, dict):
        return {
            str(key): _safe_json(val)
            for key, val in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [_safe_json(item) for item in value]

    return str(value)


def _compact_context(
    data: Optional[Dict[str, Any]],
    max_chars: int = 12000,
) -> str:
    """
    Safely serialize pipeline context and cap its size.

    The LLM should receive evidence, not an unrestricted dataset dump.
    """

    if not data:
        return "{}"

    safe_data = _safe_json(data)

    try:
        text = json.dumps(
            safe_data,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    except Exception:
        text = str(safe_data)

    if len(text) <= max_chars:
        return text

    return (
        text[:max_chars]
        + "\n\n[Context truncated for safety and token control.]"
    )


# ============================================================
# PROMPTS
# ============================================================


SYSTEM_PROMPT = """
You are the TrendPulse Data Intelligence reasoning layer.

TrendPulse is a data-processing system for small clothing and retail
businesses.

The deterministic data engine is authoritative for:
- data cleaning
- schema normalization
- validation
- anomaly detection
- statistical calculations
- profiling
- quality scores

You are NOT allowed to override deterministic evidence.

Your job is to:
1. interpret evidence,
2. explain suspicious situations,
3. recommend human-review actions,
4. identify possible business implications,
5. provide conservative reasoning when evidence is weak.

Never invent facts.
Never fabricate missing values.
Never silently change numerical values.
Never claim an anomaly is definitely fraudulent.
Never treat correlation as causation.

Return valid JSON only.
"""


def _build_reasoning_prompt(
    pipeline_context: Dict[str, Any],
) -> str:
    context = _compact_context(pipeline_context)

    return f"""
Analyze the following TrendPulse pipeline evidence.

PIPELINE EVIDENCE:
{context}

Return exactly this JSON structure:

{{
  "recommendations": [
    "string"
  ],
  "mapping_decisions": [
    {{
      "column": "string",
      "decision": "accept|review|reject",
      "confidence": 0.0,
      "reason": "string"
    }}
  ],
  "cleaning_decisions": [
    {{
      "column": "string",
      "decision": "accept|review|reject",
      "confidence": 0.0,
      "reason": "string"
    }}
  ],
  "anomaly_decisions": [
    {{
      "row": "string",
      "decision": "review|likely_valid|likely_error",
      "confidence": 0.0,
      "reason": "string"
    }}
  ],
  "explanation": "string"
}}

Confidence must be between 0.0 and 1.0.
Only make decisions supported by the supplied evidence.
"""


# ============================================================
# LOCAL DETERMINISTIC FALLBACK
# ============================================================


def _deterministic_analysis(
    pipeline_context: Optional[Dict[str, Any]] = None,
) -> LLMAnalysis:
    """
    Safe fallback used when the LLM is disabled.

    This is intentionally conservative.
    """

    context = pipeline_context or {}

    recommendations: List[str] = []
    anomaly_decisions: List[Dict[str, Any]] = []

    anomaly_summary = context.get("anomaly_summary", {})
    quality_report = context.get("quality_report", {})
    validation = context.get("validation", {})

    total_anomalies = anomaly_summary.get(
        "total_anomalies",
        context.get("anomalies_count", 0),
    )

    if total_anomalies:
        recommendations.append(
            "Statistical anomalies require validation before strategic decisions."
        )

    if validation.get("issues"):
        recommendations.append(
            "Validation issues should be reviewed before downstream analysis."
        )

    quality_score = quality_report.get("quality_score")

    if isinstance(quality_score, (int, float)):
        if quality_score < 80:
            recommendations.append(
                "Dataset quality is low; investigate validation and cleaning issues."
            )
        elif quality_score < 95:
            recommendations.append(
                "Dataset quality is acceptable but contains issues worth reviewing."
            )

    anomalies = context.get("anomalies", [])

    for anomaly in anomalies:
        row = anomaly.get("row")

        anomaly_decisions.append(
            {
                "row": str(row) if row is not None else "unknown",
                "decision": "review",
                "confidence": 0.99,
                "reason": (
                    "The deterministic anomaly detector identified this "
                    "observation as anomalous; human validation is recommended."
                ),
            }
        )

    if not recommendations:
        recommendations.append(
            "No high-priority reasoning actions were identified from the available evidence."
        )

    return LLMAnalysis(
        enabled=False,
        provider=None,
        model=None,
        confidence="deterministic",
        recommendations=recommendations,
        anomaly_decisions=anomaly_decisions,
        explanation=(
            "LLM reasoning is disabled; deterministic evidence was used."
        ),
    )


# ============================================================
# OPENAI PROVIDER
# ============================================================


class OpenAIProvider:
    """
    Optional OpenAI provider.

    Import is performed lazily so the TrendPulse pipeline can run
    without the OpenAI package installed.
    """

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "OpenAI provider requested but the 'openai' package "
                "is not installed."
            ) from exc

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured."
            )

        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "LLM returned an empty response."
            )

        return content


# ============================================================
# PROVIDER FACTORY
# ============================================================


def _get_provider() -> Optional[LLMProvider]:
    """
    Return the configured provider.

    Currently supported:
    - openai

    Unknown providers return None instead of breaking the pipeline.
    """

    if DEFAULT_PROVIDER == "openai":
        if not is_llm_configured():
            return None

        return OpenAIProvider(model=DEFAULT_MODEL)

    return None


# ============================================================
# RESPONSE PARSING
# ============================================================


def _parse_llm_response(
    response: str,
    provider: str,
    model: str,
) -> LLMAnalysis:
    """
    Parse and validate the structured LLM response.
    """

    try:
        parsed = json.loads(response)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"LLM returned invalid JSON: {exc}"
        ) from exc

    recommendations = parsed.get(
        "recommendations",
        [],
    )

    mapping_decisions = parsed.get(
        "mapping_decisions",
        [],
    )

    cleaning_decisions = parsed.get(
        "cleaning_decisions",
        [],
    )

    anomaly_decisions = parsed.get(
        "anomaly_decisions",
        [],
    )

    explanation = parsed.get(
        "explanation",
        "",
    )

    if not isinstance(recommendations, list):
        recommendations = []

    if not isinstance(mapping_decisions, list):
        mapping_decisions = []

    if not isinstance(cleaning_decisions, list):
        cleaning_decisions = []

    if not isinstance(anomaly_decisions, list):
        anomaly_decisions = []

    if not isinstance(explanation, str):
        explanation = str(explanation)

    return LLMAnalysis(
        enabled=True,
        provider=provider,
        model=model,
        confidence="llm",
        recommendations=[
            str(item)
            for item in recommendations
        ],
        mapping_decisions=[
            _safe_json(item)
            for item in mapping_decisions
        ],
        cleaning_decisions=[
            _safe_json(item)
            for item in cleaning_decisions
        ],
        anomaly_decisions=[
            _safe_json(item)
            for item in anomaly_decisions
        ],
        explanation=explanation,
    )


# ============================================================
# MAIN ANALYSIS FUNCTION
# ============================================================


def analyze_pipeline(
    pipeline_context: Optional[Dict[str, Any]] = None,
    *,
    enabled: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Run the TrendPulse reasoning layer.

    Parameters
    ----------
    pipeline_context:
        Deterministic evidence produced by the data engine.

    enabled:
        Explicitly enable/disable LLM reasoning.

        None:
            Use environment/provider configuration.

        False:
            Always use deterministic fallback.

        True:
            Attempt configured LLM provider. If unavailable or failed,
            safely fall back to deterministic reasoning.

    Returns
    -------
    dict
        JSON-safe LLM analysis.
    """

    context = pipeline_context or {}

    # Explicitly disabled.
    if enabled is False:
        return _deterministic_analysis(context).to_dict()

    provider = _get_provider()

    # No provider configured.
    if provider is None:
        return _deterministic_analysis(context).to_dict()

    try:
        prompt = _build_reasoning_prompt(context)

        response = provider.generate(
            SYSTEM_PROMPT,
            prompt,
        )

        analysis = _parse_llm_response(
            response=response,
            provider=DEFAULT_PROVIDER,
            model=DEFAULT_MODEL,
        )

        return analysis.to_dict()

    except Exception as exc:
        fallback = _deterministic_analysis(context)

        result = fallback.to_dict()
        result["error"] = str(exc)
        result["explanation"] = (
            "LLM reasoning failed safely; deterministic evidence was used."
        )

        return result


# ============================================================
# SPECIALIZED HELPERS
# ============================================================


def explain_anomalies(
    anomalies: List[Dict[str, Any]],
    *,
    enabled: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Ask the reasoning layer to interpret detected anomalies.
    """

    return analyze_pipeline(
        {
            "anomalies": anomalies,
            "anomaly_summary": {
                "total_anomalies": len(anomalies),
            },
        },
        enabled=enabled,
    )


def review_mapping(
    mapping_details: List[Dict[str, Any]],
    *,
    enabled: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Ask the reasoning layer to review deterministic column mapping.
    """

    return analyze_pipeline(
        {
            "mapping_details": mapping_details,
        },
        enabled=enabled,
    )


def review_cleaning(
    cleaning_summary: Dict[str, Any],
    cleaning_audit: Optional[List[Dict[str, Any]]] = None,
    *,
    enabled: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Ask the reasoning layer to review cleaning decisions.
    """

    return analyze_pipeline(
        {
            "cleaning_summary": cleaning_summary,
            "cleaning_audit": cleaning_audit or [],
        },
        enabled=enabled,
    )


# ============================================================
# PUBLIC API
# ============================================================


__all__ = [
    "LLMDecision",
    "LLMAnalysis",
    "LLMProvider",
    "OpenAIProvider",
    "analyze_pipeline",
    "explain_anomalies",
    "review_mapping",
    "review_cleaning",
    "is_llm_configured",
]
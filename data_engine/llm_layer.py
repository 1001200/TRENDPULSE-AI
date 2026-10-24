"""
TrendPulse LLM reasoning layer.

The LLM is an advisor, not the executor:

deterministic engine
    -> evidence
    -> LLM
    -> structured recommendation
    -> deterministic validation
    -> execution/audit

The module works without an LLM installed. This makes the core pipeline
fully usable offline and testable.

Important:
- The LLM never directly modifies the dataset.
- The LLM output is validated before being returned.
- Invalid LLM output falls back safely to deterministic reasoning.
- Provider/API failures must not break the data pipeline.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Optional


LLM_VERSION = "1.1"


# ---------------------------------------------------------------------------
# Deterministic fallback
# ---------------------------------------------------------------------------

def _fallback_analysis(
    profile: dict,
    anomalies: dict,
    mapping: dict,
) -> dict:
    warnings = []

    if anomalies.get("summary", {}).get("total_anomalies", 0):
        warnings.append(
            "Statistical anomalies require validation before strategic decisions."
        )

    if mapping.get("unmatched_columns"):
        warnings.append(
            "Some source columns could not be mapped confidently."
        )

    if not warnings:
        warnings.append(
            "No high-priority data-quality concern requires LLM escalation."
        )

    return {
        "enabled": False,
        "provider": None,
        "model": None,
        "confidence": "deterministic",
        "recommendations": warnings,
        "mapping_decisions": [],
        "cleaning_decisions": [],
        "anomaly_decisions": [],
        "explanation": (
            "LLM reasoning is disabled; deterministic evidence was used."
        ),
        "error": None,
    }


# ---------------------------------------------------------------------------
# Output validation
# ---------------------------------------------------------------------------

def _validate_llm_result(result: Any) -> dict:
    """
    Validate and normalize an LLM result.

    The LLM is untrusted input. Only the fields required by the TrendPulse
    contract are accepted.
    """

    if not isinstance(result, dict):
        raise TypeError("LLM client must return a dictionary.")

    validated = {
        "enabled": bool(result.get("enabled", True)),
        "provider": result.get("provider", "custom"),
        "model": result.get("model"),
        "confidence": result.get("confidence", "unknown"),
        "recommendations": [],
        "mapping_decisions": [],
        "cleaning_decisions": [],
        "anomaly_decisions": [],
        "explanation": str(result.get("explanation", "")),
        "error": result.get("error"),
    }

    # recommendations -------------------------------------------------------

    recommendations = result.get("recommendations", [])

    if recommendations is None:
        recommendations = []

    if not isinstance(recommendations, list):
        raise TypeError(
            "LLM field 'recommendations' must be a list."
        )

    validated["recommendations"] = [
        str(item)
        for item in recommendations
        if item is not None
    ]

    # mapping decisions -----------------------------------------------------

    mapping_decisions = result.get("mapping_decisions", [])

    if mapping_decisions is None:
        mapping_decisions = []

    if not isinstance(mapping_decisions, list):
        raise TypeError(
            "LLM field 'mapping_decisions' must be a list."
        )

    validated["mapping_decisions"] = mapping_decisions

    # cleaning decisions ----------------------------------------------------

    cleaning_decisions = result.get("cleaning_decisions", [])

    if cleaning_decisions is None:
        cleaning_decisions = []

    if not isinstance(cleaning_decisions, list):
        raise TypeError(
            "LLM field 'cleaning_decisions' must be a list."
        )

    validated["cleaning_decisions"] = cleaning_decisions

    # anomaly decisions -----------------------------------------------------

    anomaly_decisions = result.get("anomaly_decisions", [])

    if anomaly_decisions is None:
        anomaly_decisions = []

    if not isinstance(anomaly_decisions, list):
        raise TypeError(
            "LLM field 'anomaly_decisions' must be a list."
        )

    normalized_anomaly_decisions = []

    for decision in anomaly_decisions:
        if not isinstance(decision, dict):
            continue

        normalized = {
            "row": str(decision.get("row", "")),
            "decision": str(
                decision.get("decision", "review")
            ),
            "confidence": decision.get("confidence", 0.0),
            "reason": str(
                decision.get("reason", "")
            ),
        }

        try:
            normalized["confidence"] = float(
                normalized["confidence"]
            )
        except (TypeError, ValueError):
            normalized["confidence"] = 0.0

        normalized["confidence"] = max(
            0.0,
            min(1.0, normalized["confidence"]),
        )

        normalized_anomaly_decisions.append(normalized)

    validated["anomaly_decisions"] = normalized_anomaly_decisions

    # Basic contract validation --------------------------------------------

    if not validated["recommendations"] and not validated["explanation"]:
        validated["explanation"] = (
            "LLM returned no actionable reasoning."
        )

    return validated


# ---------------------------------------------------------------------------
# Main analysis entry point
# ---------------------------------------------------------------------------

def analyze_dataset(
    *,
    profile: dict,
    anomalies: dict,
    mapping: dict,
    client: Optional[Callable[[dict], dict]] = None,
) -> dict:
    """
    Ask an LLM to reason over deterministic evidence.

    The client must be callable:

        client(payload) -> dict

    Any invalid response or client failure is converted into a safe
    deterministic fallback instead of breaking the data pipeline.
    """

    payload = {
        "task": "analyze_business_dataset",
        "profile": profile,
        "anomalies": anomalies,
        "mapping": mapping,
        "constraints": [
            "Do not invent facts.",
            "Do not directly modify data.",
            "Return recommendations only.",
            "Prefer deterministic evidence.",
            "Do not override deterministic validation.",
            "Treat anomaly detection results as evidence requiring review.",
        ],
    }

    # Custom / injected client ---------------------------------------------

    if client is not None:
        try:
            result = client(payload)

            validated = _validate_llm_result(result)

            validated["enabled"] = True
            validated.setdefault("provider", "custom")

            return validated

        except Exception as exc:
            fallback = _fallback_analysis(
                profile,
                anomalies,
                mapping,
            )

            fallback["error"] = (
                f"LLM client failed: {type(exc).__name__}: {exc}"
            )

            return fallback

    # No client available ---------------------------------------------------

    return _fallback_analysis(
        profile,
        anomalies,
        mapping,
    )


# ---------------------------------------------------------------------------
# OpenAI provider
# ---------------------------------------------------------------------------

def openai_client_from_environment() -> Optional[Callable[[dict], dict]]:
    """
    Create an OpenAI-backed callable from environment configuration.

    Returns None when:
    - OPENAI_API_KEY is missing
    - openai package is not installed
    """

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        return None

    model = os.getenv(
        "TRENDPULSE_LLM_MODEL",
        "gpt-4.1-mini",
    )

    client = OpenAI(api_key=api_key)

    def call(payload: dict) -> dict:
        response = client.responses.create(
            model=model,
            input=json.dumps(
                payload,
                default=str,
            ),
        )

        text = response.output_text

        try:
            parsed = json.loads(text)

            if not isinstance(parsed, dict):
                raise TypeError(
                    "OpenAI response JSON must be an object."
                )

            parsed["enabled"] = True
            parsed["provider"] = "openai"
            parsed["model"] = model

            return parsed

        except (json.JSONDecodeError, TypeError):
            return {
                "enabled": True,
                "provider": "openai",
                "model": model,
                "confidence": "unknown",
                "explanation": text,
                "recommendations": [],
                "mapping_decisions": [],
                "cleaning_decisions": [],
                "anomaly_decisions": [],
            }

    return call


__all__ = [
    "LLM_VERSION",
    "analyze_dataset",
    "openai_client_from_environment",
]
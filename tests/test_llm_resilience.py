import pandas as pd

from data_engine.llm_layer import analyze_dataset


def _sample_inputs():
    profile = {
        "dataset": {
            "rows": 3,
            "columns": 3,
        }
    }

    anomalies = {
        "version": "4.0",
        "anomalies": [
            {
                "row": 2,
                "column": "price",
                "value": 999999,
                "severity": "critical",
            }
        ],
        "summary": {
            "total_anomalies": 1,
        },
    }

    mapping = {
        "mapping": {
            "Order Date": "date",
            "Selling Price": "price",
        },
        "unmatched_columns": [],
        "mapping_details": [],
        "mapping_conflicts": {},
    }

    return profile, anomalies, mapping


def test_llm_client_exception_does_not_break_pipeline():
    profile, anomalies, mapping = _sample_inputs()

    def broken_client(payload):
        raise RuntimeError("Simulated LLM provider failure")

    result = analyze_dataset(
        profile=profile,
        anomalies=anomalies,
        mapping=mapping,
        client=broken_client,
    )

    print("\nLLM EXCEPTION FALLBACK")
    print(result)

    assert isinstance(result, dict)
    assert result["enabled"] is False
    assert result["confidence"] == "deterministic"
    assert result["error"] is not None
    assert "Simulated LLM provider failure" in result["error"]
    assert result["recommendations"]


def test_llm_invalid_return_type_does_not_break_pipeline():
    profile, anomalies, mapping = _sample_inputs()

    def invalid_client(payload):
        return "this is not a dictionary"

    result = analyze_dataset(
        profile=profile,
        anomalies=anomalies,
        mapping=mapping,
        client=invalid_client,
    )

    print("\nLLM INVALID RETURN FALLBACK")
    print(result)

    assert isinstance(result, dict)
    assert result["enabled"] is False
    assert result["confidence"] == "deterministic"
    assert result["error"] is not None
    assert "dictionary" in result["error"]
    assert result["recommendations"]


def test_llm_invalid_recommendations_do_not_break_pipeline():
    profile, anomalies, mapping = _sample_inputs()

    def invalid_client(payload):
        return {
            "enabled": True,
            "provider": "fake",
            "model": "test-model",
            "confidence": "high",
            "recommendations": "this should be a list",
            "explanation": "Invalid response",
        }

    result = analyze_dataset(
        profile=profile,
        anomalies=anomalies,
        mapping=mapping,
        client=invalid_client,
    )

    print("\nLLM INVALID FIELD FALLBACK")
    print(result)

    assert isinstance(result, dict)
    assert result["enabled"] is False
    assert result["confidence"] == "deterministic"
    assert result["error"] is not None
    assert "recommendations" in result["error"]
    assert result["recommendations"]


def test_llm_bad_anomaly_decision_is_safely_normalized():
    profile, anomalies, mapping = _sample_inputs()

    def messy_client(payload):
        return {
            "enabled": True,
            "provider": "fake",
            "model": "test-model",
            "confidence": "high",
            "recommendations": [
                "Review the suspicious transaction."
            ],
            "anomaly_decisions": [
                {
                    "row": 2,
                    "decision": "review",
                    "confidence": "not-a-number",
                    "reason": "Suspicious transaction.",
                },
                "completely invalid decision",
            ],
            "explanation": "Manual review is recommended.",
        }

    result = analyze_dataset(
        profile=profile,
        anomalies=anomalies,
        mapping=mapping,
        client=messy_client,
    )

    print("\nLLM MALFORMED ANOMALY DECISION")
    print(result)

    assert result["enabled"] is True
    assert result["provider"] == "fake"
    assert len(result["anomaly_decisions"]) == 1

    decision = result["anomaly_decisions"][0]

    assert decision["row"] == "2"
    assert decision["decision"] == "review"
    assert decision["confidence"] == 0.0
    assert decision["reason"] == "Suspicious transaction."


def test_llm_confidence_is_clamped():
    profile, anomalies, mapping = _sample_inputs()

    def extreme_confidence_client(payload):
        return {
            "enabled": True,
            "provider": "fake",
            "confidence": "high",
            "recommendations": [
                "Review transaction."
            ],
            "anomaly_decisions": [
                {
                    "row": 2,
                    "decision": "review",
                    "confidence": 500,
                    "reason": "Extreme confidence test.",
                },
                {
                    "row": 3,
                    "decision": "review",
                    "confidence": -100,
                    "reason": "Negative confidence test.",
                },
            ],
            "explanation": "Test confidence normalization.",
        }

    result = analyze_dataset(
        profile=profile,
        anomalies=anomalies,
        mapping=mapping,
        client=extreme_confidence_client,
    )

    print("\nLLM CONFIDENCE CLAMPING")
    print(result)

    assert result["enabled"] is True

    decisions = result["anomaly_decisions"]

    assert decisions[0]["confidence"] == 1.0
    assert decisions[1]["confidence"] == 0.0
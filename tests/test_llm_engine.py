from data_engine.llm_engine import (
    analyze_pipeline,
    explain_anomalies,
    is_llm_configured,
)


def test_llm_disabled_fallback():
    result = analyze_pipeline(
        {
            "anomalies": [
                {
                    "row": 9,
                    "column": "price",
                    "value": 999999,
                }
            ],
            "anomaly_summary": {
                "total_anomalies": 1,
            },
        },
        enabled=False,
    )

    print("\nLLM FALLBACK RESULT")
    print(result)

    assert result["enabled"] is False
    assert result["confidence"] == "deterministic"
    assert len(result["recommendations"]) >= 1
    assert len(result["anomaly_decisions"]) == 1


def test_llm_does_not_break_without_configuration():
    result = analyze_pipeline(
        {
            "quality_report": {
                "quality_score": 90.0,
            }
        }
    )

    print("\nNO-CONFIGURATION RESULT")
    print(result)

    assert isinstance(result, dict)
    assert "enabled" in result
    assert "recommendations" in result
    assert "explanation" in result


def test_anomaly_explanation_fallback():
    result = explain_anomalies(
        [
            {
                "row": 5,
                "column": "quantity",
                "value": 500,
                "severity": "critical",
            }
        ],
        enabled=False,
    )

    print("\nANOMALY EXPLANATION")
    print(result)

    assert result["enabled"] is False
    assert result["anomaly_decisions"][0]["row"] == "5"


def test_llm_result_is_json_safe():
    result = analyze_pipeline(
        {
            "quality_report": {
                "quality_score": 98.0,
            }
        },
        enabled=False,
    )

    import json

    serialized = json.dumps(result)

    assert isinstance(serialized, str)


def test_llm_configuration_detection():
    result = is_llm_configured()

    print("\nLLM CONFIGURED:", result)

    assert isinstance(result, bool)
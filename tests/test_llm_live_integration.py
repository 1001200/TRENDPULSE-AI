import pandas as pd

from data_engine.processor import process_dataframe


def fake_llm_client(payload):
    assert payload["task"] == "analyze_business_dataset"
    assert "profile" in payload
    assert "anomalies" in payload
    assert "mapping" in payload
    assert "constraints" in payload

    return {
        "recommendations": [
            "Review the unusually high-value transaction before using it for business decisions.",
            "Validate the quantity and price against the original order.",
        ],
        "mapping_decisions": [],
        "cleaning_decisions": [],
        "anomaly_decisions": [
            {
                "row": "9",
                "decision": "review",
                "confidence": 0.98,
                "reason": (
                    "The transaction contains an unusually high "
                    "quantity and price."
                ),
            }
        ],
        "explanation": (
            "The anomalous transaction should be manually validated "
            "before being treated as normal business activity."
        ),
    }


def test_real_llm_path_with_fake_client():
    df = pd.DataFrame(
        {
            "Order Date": [
                "2026-08-20",
                "2026-08-21",
                "2026-08-22",
                "2026-08-23",
                "2026-08-24",
                "2026-08-25",
                "2026-08-26",
                "2026-08-27",
                "2026-08-28",
                "2026-08-29",
            ],
            "Product Name": [
                "Black Tee",
                "Blue Jeans",
                "White Hoodie",
                "Black Tee",
                "Blue Jeans",
                "White Hoodie",
                "Black Tee",
                "Blue Jeans",
                "White Hoodie",
                "Luxury Product",
            ],
            "Category": [
                "T-Shirt",
                "Jeans",
                "Hoodie",
                "T-Shirt",
                "Jeans",
                "Hoodie",
                "T-Shirt",
                "Jeans",
                "Hoodie",
                "Luxury",
            ],
            "Qty Sold": [5, 6, 4, 5, 7, 6, 5, 4, 6, 500],
            "Selling Price": [
                "₹699",
                749,
                799,
                699,
                749,
                "₹799",
                699,
                749,
                799,
                999999,
            ],
            "Customer ID": [
                "C001",
                "C002",
                "C003",
                "C004",
                "C005",
                "C006",
                "C007",
                "C008",
                "C009",
                "C010",
            ],
        }
    )

    result = process_dataframe(
        df,
        enable_llm=True,
        llm_client=fake_llm_client,
    )

    assert result["status"] == "success"

    llm = result["llm_analysis"]

    assert llm is not None
    assert llm["enabled"] is True
    assert llm["recommendations"]
    assert llm["anomaly_decisions"]

    assert llm["anomaly_decisions"][0]["decision"] == "review"

    print("\n======================================")
    print("TRENDPULSE REAL LLM PATH TEST")
    print("======================================")
    print("LLM enabled:", llm["enabled"])
    print("Provider:", llm.get("provider"))
    print("Model:", llm.get("model"))
    print("Confidence:", llm.get("confidence"))

    print("\nRecommendations:")
    for recommendation in llm["recommendations"]:
        print("-", recommendation)

    print("\nAnomaly decisions:")
    for decision in llm["anomaly_decisions"]:
        print(decision)

    print("\nExplanation:")
    print(llm["explanation"])

    print("\nREAL LLM PATH TEST PASSED")
from data_engine.semantic_mapper import find_semantic_match


# ============================================================
# Test Columns
# ============================================================

test_columns = [

    "pieces dispatched",

    "items moved",

    "buyer identifier",

    "transaction reference",

    "amount charged",

    "product classification",

    "something completely unrelated"

]


# ============================================================
# Run Tests
# ============================================================

print("\n======================================")
print("     TRENDPULSE SEMANTIC MAPPER")
print("======================================")


for column in test_columns:

    result = find_semantic_match(
        column
    )

    print("\n--------------------------------------")

    print(
        f"Input: {column}"
    )

    print(
        f"Match: {result['match']}"
    )

    print(
        f"Matched phrase: "
        f"{result['matched_phrase']}"
    )

    print(
        f"Similarity: "
        f"{result['score']}"
    )

    print(
        f"Second best: "
        f"{result['second_best_score']}"
    )

    print(
        f"Margin: "
        f"{result['margin']}"
    )

    print(
        f"Confidence: "
        f"{result['confidence']}"
    )
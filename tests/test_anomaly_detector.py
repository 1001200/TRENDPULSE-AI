import pandas as pd

from data_engine.anomaly_detector import (
    analyze_anomalies
)


# ============================================================
# Test Dataset
# ============================================================

df = pd.DataFrame({

    "product": [
        "Product A",
        "Product B",
        "Product C",
        "Product D",
        "Product E",
        "Product F",
        "Product G",
        "Product H",
        "Product I",
        "Product J",
        "Product K"
    ],

    "quantity": [
        5,
        6,
        4,
        5,
        7,
        6,
        5,
        4,
        6,
        100,
        500
    ],

    "price": [
        699,
        749,
        699,
        799,
        699,
        749,
        799,
        699,
        749,
        99999,
        999999
    ]
})


# ============================================================
# Run Detector
# ============================================================

(
    anomalies,
    summary
) = analyze_anomalies(
    df
)


# ============================================================
# Output
# ============================================================

print("\n======================================")
print("   TRENDPULSE ANOMALY DETECTOR")
print("======================================")


print("\nDataset:")

print(
    df
)


print("\nAnomaly Summary:")

print(
    f"Total anomalies: "
    f"{summary['total_anomalies']}"
)

print(
    f"By column: "
    f"{summary['by_column']}"
)

print(
    f"By method: "
    f"{summary['by_method']}"
)

print(
    f"By severity: "
    f"{summary['by_severity']}"
)


print("\nDetected Anomalies:")

if not anomalies:

    print(
        "No anomalies detected."
    )

else:

    for anomaly in anomalies:

        print(
            f"Row={anomaly['row']} | "
            f"Column={anomaly['column']} | "
            f"Value={anomaly['value']} | "
            f"Method={anomaly['method']} | "
            f"Score={anomaly['score']} | "
            f"Severity={anomaly['severity']} | "
            f"Direction={anomaly['direction']} | "
            f"{anomaly['reason']}"
        )
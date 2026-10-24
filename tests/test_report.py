from data_engine.report import create_quality_report


validation_report = {
    "missing_columns": [],
    "duplicate_rows": 0,
    "invalid_quantity_rows": 1,
    "invalid_price_rows": 0
}


report = create_quality_report(
    validation_report,
    rows_received=5
)


print("\n================================")
print("     TRENDPULSE DATA QUALITY")
print("================================")

print(
    "Rows received:",
    report["rows_received"]
)

print(
    "Missing columns:",
    report["missing_columns"]
)

print(
    "Duplicate rows:",
    report["duplicate_rows"]
)

print(
    "Invalid quantity rows:",
    report["invalid_quantity_rows"]
)

print(
    "Invalid price rows:",
    report["invalid_price_rows"]
)

print(
    "Quality score:",
    f'{report["quality_score"]}%'
)
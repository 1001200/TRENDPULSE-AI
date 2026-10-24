from data_engine.processor import process_file


file_path = "data/raw/test_clothing_sales.csv"


result = process_file(file_path)


print("\n====================================")
print("      TRENDPULSE DATA PIPELINE")
print("====================================")


print("\nRows received:")
print(result["rows_received"])


print("\nRows after cleaning:")
print(result["rows_after_cleaning"])


print("\nColumn mapping:")

for original, standard in result["column_mapping"].items():
    print(f"{original}  ->  {standard}")


print("\nUnmatched columns:")
print(result["unmatched_columns"])


print("\nValidation report:")

for key, value in result["validation"].items():
    print(f"{key}: {value}")


print("\n===== QUALITY REPORT =====")

for key, value in result["quality_report"].items():
    print(f"{key}: {value}")


print("\nProcessed data:")
print(result["processed_data"])
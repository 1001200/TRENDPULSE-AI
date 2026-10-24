from data_engine.profiler import profile_dataset
from data_engine.detector import detect_dataset_type


file_path = "data/raw/test_clothing_sales.csv"


profile = profile_dataset(file_path)


result = detect_dataset_type(
    profile["column_names"]
)


print("\n======================================")
print("       TRENDPULSE DATASET DETECTOR")
print("======================================")


print("\nDetected dataset type:")
print(result["dataset_type"])


print("\nConfidence:")
print(
    f'{result["confidence"]}%'
)


print("\nAll dataset scores:")

for dataset_type, score in result["scores"].items():

    print(
        f"{dataset_type}: {score}%"
    )
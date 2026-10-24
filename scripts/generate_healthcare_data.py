import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)
n = 350

start_date = datetime(2024, 1, 1)
dates = [start_date + timedelta(days=int(d)) for d in np.random.randint(0, 180, n)]

diagnoses = ["Cardiovascular", "Hypertension", "Type 2 Diabetes", "Asthma", "Orthopedic"]
insurance = ["BlueCross", "Medicare", "Aetna", "UnitedHealth", "Uninsured"]

df = pd.DataFrame({
    "Patient_MRN": [f"PT-{1000 + i}" for i in range(n)],
    "Admission_Date": [d.strftime("%m/%d/%Y") for d in dates],
    "Patient_Age": np.random.randint(18, 85, n),
    "Systolic_BP": np.random.normal(128, 16, n).astype(int),
    "Heart_Rate_BPM": np.random.normal(74, 11, n).astype(int),
    "Treatment_Cost": [f"${np.random.gamma(4, 1200):,.2f}" for _ in range(n)],
    "Primary_Diagnosis": np.random.choice(diagnoses, n, p=[0.3, 0.25, 0.2, 0.15, 0.1]),
    "Length_of_Stay_Days": np.random.poisson(4.5, n) + 1,
    "Insurance_Provider": np.random.choice(insurance, n),
    "Readmitted_30d": np.random.choice(["Yes", "No"], n, p=[0.18, 0.82]),
})

# Inject 8 missing values and 4 duplicates to test resilience
df.loc[12:15, "Systolic_BP"] = np.nan
df.loc[30:33, "Primary_Diagnosis"] = None
df = pd.concat([df, df.iloc[[5, 22, 67]]], ignore_index=True)

df.to_csv("data/raw/sample_healthcare_clinic.csv", index=False)
print("Created sample_healthcare_clinic.csv with", len(df), "rows")

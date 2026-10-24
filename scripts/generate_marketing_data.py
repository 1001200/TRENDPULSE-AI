import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)
n = 280

start_date = datetime(2024, 2, 1)
dates = [start_date + timedelta(days=int(d)) for d in np.random.randint(0, 120, n)]

channels = ["Google Ads", "Meta Instagram", "TikTok Ads", "LinkedIn B2B", "YouTube PreRoll"]
audiences = ["Gen Z", "Millennials", "B2B Decision Makers", "High Income Families"]

df = pd.DataFrame({
    "Campaign_Code": [f"CMP-{2000 + i}" for i in range(n)],
    "Launch_Date": [d.strftime("%Y-%m-%d") for d in dates],
    "Channel_Platform": np.random.choice(channels, n),
    "Target_Audience": np.random.choice(audiences, n),
    "Impressions": np.random.randint(5000, 250000, n),
    "Clicks": np.random.randint(100, 12000, n),
    "Ad_Spend": [f"${x:,.2f}" for x in np.random.uniform(300, 15000, n)],
    "Conversions": np.random.randint(5, 850, n),
    "Attributed_Revenue": [f"${x:,.2f}" for x in np.random.uniform(500, 45000, n)],
    "Active_Status": np.random.choice(["Active", "Paused", "Completed"], n),
})

# Inject dirty formatting
df.loc[10, "Ad_Spend"] = "$ 12,450.00"
df.loc[25, "Attributed_Revenue"] = "(1,500.00)"  # negative in accounting format
df = pd.concat([df, df.iloc[[1, 15]]], ignore_index=True)

df.to_csv("data/raw/sample_marketing_campaigns.csv", index=False)
print("Created sample_marketing_campaigns.csv with", len(df), "rows")

import sqlite3
import os
import glob

# Find all .db or sqlite files
db_files = glob.glob("**/*.db", recursive=True) + glob.glob("**/*.sqlite*", recursive=True)
print("DB files found:", db_files)

for db_path in db_files:
    print(f"\n--- Checking {db_path} ---")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cur.fetchall()]
    print("Tables:", tables)
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM `{t}`")
        cnt = cur.fetchone()[0]
        print(f"  {t}: {cnt} rows")
        if cnt > 0 and t in ['orders', 'order_items', 'products', 'sales', 'sales_records', 'data_quality_logs', 'upload_history']:
            cur.execute(f"SELECT * FROM `{t}` LIMIT 2")
            print(f"    sample: {cur.fetchall()}")
    conn.close()

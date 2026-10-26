import urllib.request
import uuid
import json

boundary = "----TrendPulseBoundary" + uuid.uuid4().hex
payload = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="files"; filename="september_sales.csv"\r\n'
    f"Content-Type: text/csv\r\n\r\n"
    f"Product,Category,Size,Price,Quantity,Date,Buyer\n"
    f"90s Acid Wash Denim Jacket,Outerwear,XL,$2,400,1,2026-09-15,@denim_collector\n"
    f"Oversized Striped Knit Sweater,Tops,Medium,Rs 1,250,1,2026-09-16,@knit_fan\n"
    f"\r\n--{boundary}--\r\n"
).encode("utf-8")

# 1. Analyze
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/ingest/analyze",
    data=payload,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    session_id = data["session_id"]
    print("[1] Analyze success! Session ID:", session_id)
    print("    Detected records:", data["summary"]["total_rows"])
    print("    Issues detected:", len(data["issues"]))

# 2. Get Stage Status
req_stage = urllib.request.Request(f"http://127.0.0.1:8000/api/v1/ingest/stage/{session_id}")
with urllib.request.urlopen(req_stage) as resp:
    stage_data = json.loads(resp.read().decode("utf-8"))
    print("[2] Staging verification OK! Preview count:", len(stage_data["preview_rows"]))

# 3. Apply Stage Update (e.g., auto-clean all safe issues via bulk action)
update_payload = json.dumps({
    "session_id": session_id,
    "bulk_action": "accept_all_cleaning"
}).encode("utf-8")
req_update = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/ingest/stage-update",
    data=update_payload,
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req_update) as resp:
    upd_data = json.loads(resp.read().decode("utf-8"))
    print("[3] Stage update OK! Valid rows ready:", upd_data["summary"]["valid_rows"])

# 4. Confirm Import
confirm_payload = json.dumps({"session_id": session_id}).encode("utf-8")
req_confirm = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/ingest/confirm-import",
    data=confirm_payload,
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req_confirm) as resp:
    conf_data = json.loads(resp.read().decode("utf-8"))
    print("[4] Confirm Import OK!")
    print("    Message:", conf_data["message"])
    print("    Imported count:", conf_data["imported_count"])
    print("    Entities saved:", conf_data["entities_saved"])

# 5. Verify History & Stats
with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/ingest/stats") as resp:
    stats = json.loads(resp.read().decode("utf-8"))
    print("[5] Stats: Products=", stats["products"], "Sales=", stats["sales"])

print("\n=== FULL HTTP INGESTION WORKFLOW VALIDATED SUCCESSFULLY! ===")

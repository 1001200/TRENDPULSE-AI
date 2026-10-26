import urllib.request
import uuid
import json

boundary = "----TrendPulseTestBoundary" + uuid.uuid4().hex
payload = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="files"; filename="thrift_drop.csv"\r\n'
    f"Content-Type: text/csv\r\n\r\n"
    f"Item Name,Category,Size,Retail Price,Qty,Sale Date,Buyer\n"
    f"Oversized Grunge Flannel,Tops,Medium,$1,150,1,2026-10-20,@vintage_hunter\n"
    f"Y2K Cargo Pants,Bottoms,L,$1,800,1,2026-10-21,@cargo_lover\n"
    f"\r\n--{boundary}--\r\n"
).encode("utf-8")

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/ingest/analyze",
    data=payload,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
)

with urllib.request.urlopen(req) as response:
    print("HTTP Response Code:", response.status)
    data = json.loads(response.read().decode("utf-8"))
    print("Success:", data.get("success"))
    print("Session ID:", data.get("session_id"))
    print("Files Analyzed:", [f["filename"] for f in data.get("files", [])])
    print("Summary:", data.get("summary"))
    print("Preview Rows:", len(data.get("preview_rows", [])))

import uuid
import time
import copy
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from backend.app.pipeline.extractors import (
    detect_file_format,
    extract_csv,
    extract_excel,
    extract_pdf,
    extract_docx,
    extract_txt,
    extract_image,
    detect_record_type
)
from backend.app.pipeline.detector import (
    detect_column_mappings_with_confidence,
    clean_header,
    SYNONYM_MAP
)
from backend.app.pipeline.cleaner import (
    clean_currency_and_number,
    clean_quantity,
    clean_date,
    clean_size,
    clean_product_name,
    clean_category,
    validate_price_range,
    infer_category_and_aesthetic
)
from backend.app.pipeline.audit import AuditLedger
from backend.app.models.models import (
    Product, SaleOrder, InventoryItem, ContentItem,
    CustomerInquiry, DataQualityLog
)

# In-memory staging store with TTL (1 hour)
_STAGING_SESSIONS: Dict[str, Dict[str, Any]] = {}
SESSION_TTL_SECONDS = 3600


def _clean_expired_sessions():
    now = time.time()
    expired = [sid for sid, data in _STAGING_SESSIONS.items() if now - data.get("created_at", now) > SESSION_TTL_SECONDS]
    for sid in expired:
        _STAGING_SESSIONS.pop(sid, None)


def get_staged_session(session_id: str) -> Optional[Dict[str, Any]]:
    _clean_expired_sessions()
    return _STAGING_SESSIONS.get(session_id)


def analyze_uploaded_files(
    files_payload: List[Tuple[str, bytes]],
    db: Session
) -> Dict[str, Any]:
    """
    Parses multiple uploaded files, runs data detection and cleaning layers,
    identifies issues and duplicate risks, and stores staged results for seller review.
    """
    _clean_expired_sessions()
    session_id = f"session_{uuid.uuid4().hex[:10]}"

    # Fetch existing DB identifiers for duplicate cross-check
    existing_order_ids = set(
        res[0] for res in db.query(SaleOrder.order_id).filter(SaleOrder.order_id.isnot(None)).all()
    )
    existing_product_ids = set(
        res[0] for res in db.query(Product.product_id).filter(Product.product_id.isnot(None)).all()
    )
    existing_upload_sources = set(
        res[0] for res in db.query(DataQualityLog.source_name).all()
    )

    per_file_results = []
    combined_raw_rows = []
    combined_cleaned_rows = []
    all_issues = []

    global_row_counter = 0
    seen_in_batch_orders = {}  # order_id -> row_id
    seen_in_batch_keys = {}    # normalized_key -> row_id
    seen_exact_row_hashes = {} # row_hash -> row_id

    for file_idx, (filename, content) in enumerate(files_payload, start=1):
        file_id = f"file_{file_idx}"
        file_res = {
            "file_id": file_id,
            "filename": filename,
            "size_bytes": len(content),
            "format": "unknown",
            "status": "processing",
            "detected_record_type": "unknown",
            "record_type_confidence": 0.0,
            "records_count": 0,
            "error": None,
            "warning": None,
            "is_duplicate_upload": False,
        }

        # Check duplicate upload warning
        if filename in existing_upload_sources:
            file_res["is_duplicate_upload"] = True
            file_res["warning"] = f"A file named '{filename}' was previously imported. Review records carefully to prevent accidental duplication."

        # 1. Format Detection
        try:
            fmt = detect_file_format(filename, content)
            file_res["format"] = fmt.upper()
        except Exception as e:
            file_res["status"] = "failed"
            file_res["error"] = str(e)
            per_file_results.append(file_res)
            continue

        # 2. Format Extraction
        headers = []
        extracted_rows = []
        ext_warning = None
        raw_text_extracted = None

        try:
            if fmt == "csv":
                headers, extracted_rows, ext_warning = extract_csv(content)
            elif fmt in ("xlsx", "xls"):
                headers, extracted_rows, ext_warning = extract_excel(content, is_xls=(fmt == "xls"))
            elif fmt == "pdf":
                headers, extracted_rows, ext_warning, raw_text_extracted = extract_pdf(content)
            elif fmt == "docx":
                headers, extracted_rows, ext_warning, raw_text_extracted = extract_docx(content)
            elif fmt == "txt":
                headers, extracted_rows, ext_warning = extract_txt(content)
            elif fmt in ("png", "jpg", "jpeg", "webp"):
                headers, extracted_rows, ext_warning, raw_text_extracted = extract_image(content, filename)
            else:
                file_res["status"] = "failed"
                file_res["error"] = f"Unsupported file format '{fmt}'."
                per_file_results.append(file_res)
                continue
        except Exception as e:
            file_res["status"] = "failed"
            file_res["error"] = f"Failed to extract records: {str(e)}"
            per_file_results.append(file_res)
            continue

        if ext_warning:
            file_res["warning"] = (file_res["warning"] + " " + ext_warning) if file_res["warning"] else ext_warning

        if not extracted_rows:
            file_res["status"] = "failed"
            file_res["error"] = file_res["warning"] or "No readable business records found in this file."
            file_res["records_count"] = 0
            per_file_results.append(file_res)
            continue

        # 3. Detect Record Type & Column Mappings
        record_type, rec_conf = detect_record_type(headers, extracted_rows)
        file_res["detected_record_type"] = record_type
        file_res["record_type_confidence"] = round(rec_conf * 100, 1)
        file_res["records_count"] = len(extracted_rows)

        col_mappings = detect_column_mappings_with_confidence(headers)
        # Simplify mapping for fast lookup: { standard_field: original_col }
        active_map = {std: info["source_col"] for std, info in col_mappings.items() if info["source_col"]}

        file_res["column_mappings"] = col_mappings
        file_res["status"] = "ready"

        # 4. Process individual rows for this file
        for source_row_idx, raw_dict in enumerate(extracted_rows, start=1):
            global_row_counter += 1
            row_id = f"row_{global_row_counter}"

            def get_fval(key: str) -> Any:
                src = active_map.get(key)
                return raw_dict.get(src) if src else None

            # Raw snapshot
            raw_entry = copy.deepcopy(raw_dict)
            raw_entry["_row_id"] = row_id
            raw_entry["_file_id"] = file_id
            raw_entry["_file_name"] = filename
            raw_entry["_source_row_idx"] = source_row_idx
            combined_raw_rows.append(raw_entry)

            # Cleaned snapshot with normalization
            cleaned_entry = {
                "_row_id": row_id,
                "_file_id": file_id,
                "_file_name": filename,
                "_source_row_idx": source_row_idx,
                "_excluded": False,
                "_validation_status": "ready",  # ready, warning, error, duplicate
                "_issue_ids": []
            }

            row_has_error = False
            row_has_warning = False

            # Extract fields
            # Extract fields
            raw_name = get_fval("product_name")
            raw_id = get_fval("product_id")
            raw_order = get_fval("order_id")
            raw_price = get_fval("retail_price")
            raw_cost = get_fval("cost_price")
            raw_qty = get_fval("quantity")
            raw_date = get_fval("sale_date")
            raw_cat = get_fval("category")
            raw_size = get_fval("size")
            raw_channel = get_fval("channel")
            raw_customer = get_fval("customer")
            raw_status = get_fval("sale_status")
            raw_inquiry = get_fval("inquiry_type")
            raw_outcome = get_fval("outcome")
            raw_notes = get_fval("notes")

            # Check Identical Duplicate Row
            row_repr = tuple(sorted((str(k).strip(), str(v).strip()) for k, v in raw_dict.items() if v is not None and str(v).strip()))
            row_hash = hash(row_repr)
            if row_hash in seen_exact_row_hashes:
                prev_row_id = seen_exact_row_hashes[row_hash]
                issue_id = f"iss_{uuid.uuid4().hex[:6]}"
                all_issues.append({
                    "id": issue_id,
                    "row_id": row_id,
                    "file_name": filename,
                    "column": "Entire Row",
                    "issue_type": "duplicate_confirmed",
                    "severity": "ERROR",
                    "title": "Exact Duplicate Row",
                    "description": f"This row is an exact duplicate of {prev_row_id}.",
                    "original_value": "Identical row content",
                    "suggested_value": "Exclude record",
                    "status": "pending",
                    "allowed_actions": ["exclude", "accept"]
                })
                cleaned_entry["_issue_ids"].append(issue_id)
                cleaned_entry["_validation_status"] = "duplicate"
                cleaned_entry["_excluded"] = True
                row_has_error = True
            else:
                seen_exact_row_hashes[row_hash] = row_id

            # Clean Product Name
            cleaned_name, name_note = clean_product_name(raw_name)
            if not cleaned_name:
                cleaned_name = f"Curated Item #{global_row_counter}"
                issue_id = f"iss_{uuid.uuid4().hex[:6]}"
                all_issues.append({
                    "id": issue_id,
                    "row_id": row_id,
                    "file_name": filename,
                    "column": "product_name",
                    "issue_type": "missing_value",
                    "severity": "WARNING",
                    "title": "Missing Product Name",
                    "description": "Product name was missing in uploaded record.",
                    "original_value": raw_name or "NULL",
                    "suggested_value": cleaned_name,
                    "status": "pending",
                    "allowed_actions": ["accept", "edit", "exclude"]
                })
                cleaned_entry["_issue_ids"].append(issue_id)
                row_has_warning = True
            elif name_note:
                issue_id = f"iss_{uuid.uuid4().hex[:6]}"
                all_issues.append({
                    "id": issue_id,
                    "row_id": row_id,
                    "file_name": filename,
                    "column": "product_name",
                    "issue_type": "formatting_cleaned",
                    "severity": "INFO",
                    "title": "Normalized Product Name",
                    "description": name_note,
                    "original_value": str(raw_name),
                    "suggested_value": cleaned_name,
                    "status": "accepted",
                    "allowed_actions": ["edit"]
                })
                cleaned_entry["_issue_ids"].append(issue_id)
            cleaned_entry["product_name"] = cleaned_name

            # Clean Price
            retail_price, p_note = clean_currency_and_number(raw_price)
            if raw_price is None or str(raw_price).strip().lower() in ("", "[blank]", "none", "nan") or retail_price is None:
                issue_id = f"iss_{uuid.uuid4().hex[:6]}"
                all_issues.append({
                    "id": issue_id,
                    "row_id": row_id,
                    "file_name": filename,
                    "column": "retail_price",
                    "issue_type": "invalid_value",
                    "severity": "ERROR",
                    "title": "Missing or Invalid Price",
                    "description": f"Price is missing or could not be parsed from '{raw_price}'.",
                    "original_value": str(raw_price),
                    "suggested_value": "0.00",
                    "status": "pending",
                    "allowed_actions": ["edit", "exclude"]
                })
                cleaned_entry["_issue_ids"].append(issue_id)
                retail_price = None
                row_has_error = True
            elif retail_price <= 0:
                issue_id = f"iss_{uuid.uuid4().hex[:6]}"
                all_issues.append({
                    "id": issue_id,
                    "row_id": row_id,
                    "file_name": filename,
                    "column": "retail_price",
                    "issue_type": "invalid_value",
                    "severity": "ERROR",
                    "title": "Non-Positive Price Detected",
                    "description": f"Price is negative or zero ({retail_price}). Requires review before import.",
                    "original_value": str(raw_price),
                    "suggested_value": str(abs(retail_price)),
                    "status": "pending",
                    "allowed_actions": ["accept", "edit", "exclude"]
                })
                cleaned_entry["_issue_ids"].append(issue_id)
                retail_price = None
                row_has_error = True
            elif p_note:
                issue_id = f"iss_{uuid.uuid4().hex[:6]}"
                all_issues.append({
                    "id": issue_id,
                    "row_id": row_id,
                    "file_name": filename,
                    "column": "retail_price",
                    "issue_type": "formatting_cleaned",
                    "severity": "INFO",
                    "title": "Cleaned Currency Formatting",
                    "description": p_note,
                    "original_value": str(raw_price),
                    "suggested_value": f"{retail_price:.2f}",
                    "status": "accepted",
                    "allowed_actions": ["edit"]
                })
                cleaned_entry["_issue_ids"].append(issue_id)

            cleaned_entry["retail_price"] = retail_price

            # Price Range Validation (only if price is valid)
            if retail_price is not None and retail_price > 0:
                valid_p, p_warn = validate_price_range(retail_price, "retail")
                if p_warn:
                    issue_id = f"iss_{uuid.uuid4().hex[:6]}"
                    all_issues.append({
                        "id": issue_id,
                        "row_id": row_id,
                        "file_name": filename,
                        "column": "retail_price",
                        "issue_type": "invalid_value",
                        "severity": "WARNING",
                        "title": "Unusual Price Range",
                        "description": p_warn,
                        "original_value": f"₹{retail_price}",
                        "suggested_value": f"₹{retail_price}",
                        "status": "pending",
                        "allowed_actions": ["accept", "edit"]
                    })
                    cleaned_entry["_issue_ids"].append(issue_id)
                    row_has_warning = True

            # Clean Cost / COGS
            cost_price, c_note = clean_currency_and_number(raw_cost)
            if cost_price is None or cost_price < 0:
                cost_price = round((retail_price or 0.0) * 0.35, 2)
            cleaned_entry["cost_price"] = cost_price

            # Clean Category & Aesthetic
            cleaned_cat, cleaned_aes, inf_note = infer_category_and_aesthetic(cleaned_name, raw_cat, None)
            if inf_note and raw_cat:
                issue_id = f"iss_{uuid.uuid4().hex[:6]}"
                all_issues.append({
                    "id": issue_id,
                    "row_id": row_id,
                    "file_name": filename,
                    "column": "category",
                    "issue_type": "formatting_cleaned",
                    "severity": "INFO",
                    "title": "Standardized Category",
                    "description": inf_note,
                    "original_value": str(raw_cat),
                    "suggested_value": cleaned_cat,
                    "status": "accepted",
                    "allowed_actions": ["edit"]
                })
                cleaned_entry["_issue_ids"].append(issue_id)
            cleaned_entry["category"] = cleaned_cat
            cleaned_entry["aesthetic"] = cleaned_aes

            # Clean Size
            cleaned_size, s_note = clean_size(raw_size)
            if s_note:
                issue_id = f"iss_{uuid.uuid4().hex[:6]}"
                all_issues.append({
                    "id": issue_id,
                    "row_id": row_id,
                    "file_name": filename,
                    "column": "size",
                    "issue_type": "formatting_cleaned",
                    "severity": "INFO",
                    "title": "Normalized Clothing Size",
                    "description": s_note,
                    "original_value": str(raw_size),
                    "suggested_value": cleaned_size,
                    "status": "accepted",
                    "allowed_actions": ["edit"]
                })
                cleaned_entry["_issue_ids"].append(issue_id)
            cleaned_entry["size"] = cleaned_size

            # Clean Quantity
            quantity, q_note = clean_quantity(raw_qty)
            if quantity is None or quantity <= 0:
                issue_id = f"iss_{uuid.uuid4().hex[:6]}"
                all_issues.append({
                    "id": issue_id,
                    "row_id": row_id,
                    "file_name": filename,
                    "column": "quantity",
                    "issue_type": "invalid_value",
                    "severity": "ERROR",
                    "title": "Invalid Quantity",
                    "description": f"Quantity '{raw_qty}' is non-numeric or less than or equal to 0.",
                    "original_value": str(raw_qty),
                    "suggested_value": "1",
                    "status": "pending",
                    "allowed_actions": ["edit", "exclude"]
                })
                cleaned_entry["_issue_ids"].append(issue_id)
                quantity = None
                row_has_error = True
            elif q_note:
                issue_id = f"iss_{uuid.uuid4().hex[:6]}"
                all_issues.append({
                    "id": issue_id,
                    "row_id": row_id,
                    "file_name": filename,
                    "column": "quantity",
                    "issue_type": "formatting_cleaned",
                    "severity": "INFO",
                    "title": "Normalized Quantity",
                    "description": q_note,
                    "original_value": str(raw_qty),
                    "suggested_value": str(quantity),
                    "status": "accepted",
                    "allowed_actions": ["edit"]
                })
                cleaned_entry["_issue_ids"].append(issue_id)
            cleaned_entry["quantity"] = quantity

            # Clean Date
            sale_dt, dt_note = clean_date(raw_date)
            if not sale_dt:
                issue_id = f"iss_{uuid.uuid4().hex[:6]}"
                all_issues.append({
                    "id": issue_id,
                    "row_id": row_id,
                    "file_name": filename,
                    "column": "sale_date",
                    "issue_type": "invalid_value",
                    "severity": "ERROR",
                    "title": "Invalid Transaction Date",
                    "description": f"Date '{raw_date}' is invalid and cannot be parsed into a transaction date.",
                    "original_value": str(raw_date),
                    "suggested_value": "Exclude or edit date",
                    "status": "pending",
                    "allowed_actions": ["edit", "exclude"]
                })
                cleaned_entry["_issue_ids"].append(issue_id)
                cleaned_entry["sale_date"] = None
                row_has_error = True
            else:
                if dt_note and raw_date:
                    issue_id = f"iss_{uuid.uuid4().hex[:6]}"
                    all_issues.append({
                        "id": issue_id,
                        "row_id": row_id,
                        "file_name": filename,
                        "column": "sale_date",
                        "issue_type": "formatting_cleaned",
                        "severity": "INFO",
                        "title": "Standardized Date Format",
                        "description": dt_note,
                        "original_value": str(raw_date),
                        "suggested_value": sale_dt.strftime("%Y-%m-%d"),
                        "status": "accepted",
                        "allowed_actions": ["edit"]
                    })
                    cleaned_entry["_issue_ids"].append(issue_id)
                cleaned_entry["sale_date"] = sale_dt.strftime("%Y-%m-%d")

            # Clean Product ID / SKU (Deterministic slug if unprovided)
            if raw_id and str(raw_id).strip().lower() not in ("none", "nan", ""):
                product_id = str(raw_id).strip()
            else:
                clean_slug = re.sub(r'[^A-Z0-9]+', '-', f"{cleaned_cat}-{cleaned_name}-{cleaned_size}".upper()).strip('-')
                product_id = clean_slug
            cleaned_entry["product_id"] = product_id

            # Clean Order ID
            if not raw_order or str(raw_order).strip().lower() in ("", "[blank]", "none", "nan", "blank"):
                issue_id = f"iss_{uuid.uuid4().hex[:6]}"
                all_issues.append({
                    "id": issue_id,
                    "row_id": row_id,
                    "file_name": filename,
                    "column": "order_id",
                    "issue_type": "missing_value",
                    "severity": "ERROR",
                    "title": "Missing Order ID",
                    "description": "Order ID is blank or missing. Record cannot be validated without transaction identifier.",
                    "original_value": str(raw_order) if raw_order is not None else "[blank]",
                    "suggested_value": "Exclude record",
                    "status": "pending",
                    "allowed_actions": ["edit", "exclude"]
                })
                cleaned_entry["_issue_ids"].append(issue_id)
                cleaned_entry["order_id"] = None
                row_has_error = True
            else:
                str_order = str(raw_order).strip()
                cleaned_entry["order_id"] = str_order

                # Duplicate / Conflict Check
                if str_order in existing_order_ids:
                    issue_id = f"iss_{uuid.uuid4().hex[:6]}"
                    all_issues.append({
                        "id": issue_id,
                        "row_id": row_id,
                        "file_name": filename,
                        "column": "order_id",
                        "issue_type": "duplicate_confirmed",
                        "severity": "ERROR",
                        "title": "Order ID Already Exists in Database",
                        "description": f"Order ID '{str_order}' already exists in your TrendPulse records. Importing it may cause duplicate sales data.",
                        "original_value": str_order,
                        "suggested_value": "Exclude duplicate order",
                        "status": "pending",
                        "allowed_actions": ["exclude", "accept"]
                    })
                    cleaned_entry["_issue_ids"].append(issue_id)
                    cleaned_entry["_validation_status"] = "duplicate"
                    row_has_error = True
                elif str_order in seen_in_batch_orders:
                    prev_id = seen_in_batch_orders[str_order]
                    issue_id = f"iss_{uuid.uuid4().hex[:6]}"
                    all_issues.append({
                        "id": issue_id,
                        "row_id": row_id,
                        "file_name": filename,
                        "column": "order_id",
                        "issue_type": "conflicting_order_id",
                        "severity": "WARNING",
                        "title": "Multi-item / Conflicting Order ID",
                        "description": f"Order ID '{str_order}' appears on multiple rows (first seen in {prev_id}). Flagged for review.",
                        "original_value": str_order,
                        "suggested_value": "Review multi-item order",
                        "status": "pending",
                        "allowed_actions": ["accept", "exclude"]
                    })
                    cleaned_entry["_issue_ids"].append(issue_id)
                    row_has_warning = True
                else:
                    seen_in_batch_orders[str_order] = row_id

            # Clean Channel & Customer
            channel = str(raw_channel).strip() if raw_channel and str(raw_channel).lower() not in ("nan", "none") else "Instagram DM"
            customer = str(raw_customer).strip() if raw_customer and str(raw_customer).lower() not in ("nan", "none") else f"@buyer_{global_row_counter}"
            cleaned_entry["channel"] = channel
            cleaned_entry["customer"] = customer

            # Clean Sale Status
            if raw_status and str(raw_status).strip().lower() not in ("nan", "none", ""):
                status_clean = str(raw_status).strip().lower()
            else:
                status_clean = "completed"
            cleaned_entry["sale_status"] = status_clean

            # Duplicate Check: Potential Duplicate Transaction (same product + date + customer)
            potential_key = f"{cleaned_name.lower()}|{cleaned_entry['sale_date']}|{customer.lower()}"
            if potential_key in seen_in_batch_keys:
                prev_id = seen_in_batch_keys[potential_key]
                issue_id = f"iss_{uuid.uuid4().hex[:6]}"
                all_issues.append({
                    "id": issue_id,
                    "row_id": row_id,
                    "file_name": filename,
                    "column": "Transaction",
                    "issue_type": "duplicate_potential",
                    "severity": "WARNING",
                    "title": "Possible Duplicate Transaction",
                    "description": f"Matching product ('{cleaned_name}'), sale date, and customer with row {prev_id}. Review if this is a repeat purchase or accidental duplicate.",
                    "original_value": f"{cleaned_name} ({cleaned_entry['sale_date']})",
                    "suggested_value": "Review record",
                    "status": "pending",
                    "allowed_actions": ["accept", "exclude"]
                })
                cleaned_entry["_issue_ids"].append(issue_id)
                if cleaned_entry["_validation_status"] == "ready":
                    cleaned_entry["_validation_status"] = "warning"
                row_has_warning = True
            else:
                seen_in_batch_keys[potential_key] = row_id

            # Set overall row validation status
            if row_has_error:
                cleaned_entry["_validation_status"] = "error" if cleaned_entry["_validation_status"] != "duplicate" else "duplicate"
            elif row_has_warning:
                cleaned_entry["_validation_status"] = "warning"

            # Other retail fields
            cleaned_entry["inquiry_type"] = str(raw_inquiry).strip() if raw_inquiry else "DM"
            cleaned_entry["outcome"] = str(raw_outcome).strip() if raw_outcome and str(raw_outcome).lower() not in ("nan", "none") else ""
            cleaned_entry["notes"] = str(raw_notes).strip() if raw_notes and str(raw_notes).lower() not in ("nan", "none") else ""

            combined_cleaned_rows.append(cleaned_entry)

        per_file_results.append(file_res)

    # Compute Summary Statistics
    total_rows = len(combined_cleaned_rows)
    confirmed_dupes = sum(1 for iss in all_issues if iss["issue_type"] == "duplicate_confirmed")
    potential_dupes = sum(1 for iss in all_issues if iss["issue_type"] == "duplicate_potential")
    missing_vals = sum(1 for iss in all_issues if iss["issue_type"] == "missing_value")
    invalid_vals = sum(1 for iss in all_issues if iss["issue_type"] == "invalid_value")
    formatting_cleaned = sum(1 for iss in all_issues if iss["issue_type"] == "formatting_cleaned")

    ready_rows = sum(1 for r in combined_cleaned_rows if r["_validation_status"] in ("ready", "warning") and not r["_excluded"])
    error_rows = sum(1 for r in combined_cleaned_rows if r["_validation_status"] in ("error", "duplicate"))

    # Quality score (0 to 100%)
    penalty = (confirmed_dupes * 5.0) + (invalid_vals * 4.0) + (missing_vals * 2.0) + (potential_dupes * 1.5)
    quality_score = max(15.0, round(100.0 - (penalty / max(1, total_rows) * 15.0), 1)) if total_rows > 0 else 100.0

    summary = {
        "total_files": len(files_payload),
        "total_rows": total_rows,
        "valid_rows": ready_rows,
        "flagged_rows": error_rows + sum(1 for r in combined_cleaned_rows if r["_validation_status"] == "warning"),
        "confirmed_duplicates": confirmed_dupes,
        "potential_duplicates": potential_dupes,
        "missing_values": missing_vals,
        "invalid_values": invalid_vals,
        "formatting_cleaned": formatting_cleaned,
        "quality_score": quality_score,
        "ready_to_import_count": ready_rows
    }

    # Save session
    session_data = {
        "session_id": session_id,
        "created_at": time.time(),
        "files": per_file_results,
        "raw_rows": combined_raw_rows,
        "cleaned_rows": combined_cleaned_rows,
        "issues": all_issues,
        "summary": summary
    }
    _STAGING_SESSIONS[session_id] = session_data

    return {
        "success": True,
        "session_id": session_id,
        "files": per_file_results,
        "summary": summary,
        "issues": all_issues,
        "preview_rows": combined_cleaned_rows[:100],  # Return up to 100 preview rows
        "total_preview_count": len(combined_cleaned_rows)
    }


def update_staged_batch(session_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applies seller corrections, inclusions, exclusions, and cell edits to staged data.
    """
    session = get_staged_session(session_id)
    if not session:
        raise ValueError("Staged upload session expired or not found. Please re-upload your files.")

    cleaned_rows = session["cleaned_rows"]
    issues = session["issues"]

    # 1. Row Exclusions / Inclusions
    if "exclude_row_ids" in updates:
        ex_set = set(updates["exclude_row_ids"])
        for r in cleaned_rows:
            if r["_row_id"] in ex_set:
                r["_excluded"] = True

    if "include_row_ids" in updates:
        inc_set = set(updates["include_row_ids"])
        for r in cleaned_rows:
            if r["_row_id"] in inc_set:
                r["_excluded"] = False

    # 2. Accept Specific Issues
    if "accept_issue_ids" in updates:
        acc_set = set(updates["accept_issue_ids"])
        for iss in issues:
            if iss["id"] in acc_set:
                iss["status"] = "accepted"
                # If issue had a suggested value, apply to row
                r_id = iss["row_id"]
                col = iss["column"]
                sug = iss["suggested_value"]
                for r in cleaned_rows:
                    if r["_row_id"] == r_id and col in r:
                        r[col] = sug
                        # Demote error/duplicate status if resolved
                        if r["_validation_status"] in ("duplicate", "error"):
                            r["_validation_status"] = "ready"

    # 3. Exclude Specific Issues / Records
    if "exclude_issue_ids" in updates:
        exc_set = set(updates["exclude_issue_ids"])
        for iss in issues:
            if iss["id"] in exc_set:
                iss["status"] = "excluded"
                r_id = iss["row_id"]
                for r in cleaned_rows:
                    if r["_row_id"] == r_id:
                        r["_excluded"] = True

    # 4. Cell Edits: [{ row_id, column, value }]
    if "cell_edits" in updates:
        for edit in updates["cell_edits"]:
            r_id = edit.get("row_id")
            col = edit.get("column")
            val = edit.get("value")
            for r in cleaned_rows:
                if r["_row_id"] == r_id and col in r:
                    r[col] = val
                    if r["_validation_status"] == "error":
                        r["_validation_status"] = "ready"

    # 5. Bulk Actions: 'accept_all_safe', 'exclude_confirmed_duplicates', 'include_all'
    bulk_action = updates.get("bulk_action")
    if bulk_action == "accept_all_safe":
        for iss in issues:
            if iss["severity"] in ("INFO", "WARNING") and iss["status"] == "pending":
                iss["status"] = "accepted"
    elif bulk_action == "exclude_confirmed_duplicates":
        for iss in issues:
            if iss["issue_type"] == "duplicate_confirmed":
                iss["status"] = "excluded"
                r_id = iss["row_id"]
                for r in cleaned_rows:
                    if r["_row_id"] == r_id:
                        r["_excluded"] = True
    elif bulk_action == "include_all":
        for r in cleaned_rows:
            r["_excluded"] = False

    # Recalculate summary
    total_rows = len(cleaned_rows)
    ready_rows = sum(1 for r in cleaned_rows if r["_validation_status"] in ("ready", "warning") and not r["_excluded"])
    error_rows = sum(1 for r in cleaned_rows if r["_validation_status"] in ("error", "duplicate") and not r["_excluded"])

    session["summary"]["valid_rows"] = ready_rows
    session["summary"]["ready_to_import_count"] = ready_rows

    return {
        "success": True,
        "session_id": session_id,
        "summary": session["summary"],
        "issues": issues,
        "preview_rows": cleaned_rows[:100],
        "total_preview_count": len(cleaned_rows)
    }


def commit_staged_batch(session_id: str, db: Session) -> Dict[str, Any]:
    """
    Commits approved cleaned records into the database within an atomic transaction.
    """
    session = get_staged_session(session_id)
    if not session:
        raise ValueError("Staged upload session expired or not found. Please re-upload your files.")

    cleaned_rows = session["cleaned_rows"]
    summary = session["summary"]
    files = session["files"]
    issues = session["issues"]

    # Filter records eligible for import (must not be excluded, duplicate, or error)
    approved_rows = [
        r for r in cleaned_rows
        if not r.get("_excluded", False)
        and r.get("_validation_status") not in ("error", "duplicate")
        and r.get("sale_date")
        and r.get("quantity") is not None and r.get("quantity") > 0
        and r.get("retail_price") is not None and r.get("retail_price") > 0
        and r.get("order_id")
    ]

    if not approved_rows:
        raise ValueError("No valid records are marked for import. All rows are either excluded or contain unresolved errors.")

    batch_id = f"batch_{uuid.uuid4().hex[:8]}"
    source_names = ", ".join(f["filename"] for f in files if f.get("status") == "ready") or "Batch Import"

    saved_products = 0
    saved_sales = 0
    saved_inventory = 0
    saved_inquiries = 0

    seen_order_keys = set()
    existing_product_ids = set(
        p[0] for p in db.query(Product.product_id).all()
    )
    audit_records = []

    try:
        for idx, row in enumerate(approved_rows, start=1):
            product_id = row["product_id"]
            p_name = row["product_name"]
            cat = row["category"]
            aes = row.get("aesthetic") or "Vintage / Resale"
            size = row["size"]
            retail_price = float(row.get("retail_price", 0.0) or 0.0)
            cost_price = float(row.get("cost_price", 0.0) or 0.0)
            qty = int(row.get("quantity", 1) or 1)
            sale_date_str = row.get("sale_date")
            channel = row.get("channel", "Instagram DM")
            customer = row.get("customer", "@buyer")
            order_id = row.get("order_id")
            sale_status = row.get("sale_status", "completed").lower()

            try:
                sale_dt = datetime.strptime(sale_date_str, "%Y-%m-%d")
            except Exception:
                continue

            # 1. Upsert Product
            if product_id not in existing_product_ids:
                product = Product(
                    product_id=product_id,
                    product_name=p_name,
                    category=cat,
                    brand="Vintage / Independent",
                    aesthetic=aes,
                    size=size,
                    condition="Gently Used",
                    cost_price=cost_price,
                    retail_price=retail_price,
                    source_file=row.get("_file_name", "Upload"),
                    source_row_idx=row.get("_source_row_idx", idx),
                    date_sourced=sale_dt,
                    created_at=sale_dt
                )
                db.add(product)
                db.flush()
                saved_products += 1
                existing_product_ids.add(product_id)

                # Inventory item
                inv = InventoryItem(
                    product_id=product_id,
                    quantity_on_hand=max(0, qty - 1 if qty > 0 else 0),
                    date_stocked=sale_dt,
                    status="Sold" if qty >= 1 else "Available"
                )
                db.add(inv)
                saved_inventory += 1

            # 2. Insert Sale Order (prevent identical duplicate in-batch commit)
            order_key = f"{order_id}|{product_id}|{row.get('_source_row_idx', idx)}"
            if order_key not in seen_order_keys and retail_price > 0:
                sale = SaleOrder(
                    order_id=order_id,
                    product_id=product_id,
                    sale_date=sale_dt,
                    quantity=qty,
                    selling_price=retail_price,
                    discount_amount=0.0,
                    channel=channel,
                    customer_identifier=customer,
                    inquiry_type=row.get("inquiry_type", "DM"),
                    sale_status=sale_status,
                    notes=row.get("notes", "")
                )
                db.add(sale)
                saved_sales += 1
                seen_order_keys.add(order_key)

            # 3. Customer Inquiry if present
            outcome = row.get("outcome")
            if outcome:
                inq = CustomerInquiry(
                    product_id=product_id,
                    inquiry_date=sale_dt,
                    inquiry_type=row.get("inquiry_type", "DM"),
                    customer_identifier=customer,
                    outcome=outcome,
                    notes=row.get("notes", "")
                )
                db.add(inq)
                saved_inquiries += 1

        # Format audit trail JSON from issues
        for iss in issues:
            audit_records.append({
                "row": iss.get("row_id"),
                "file": iss.get("file_name"),
                "column": iss.get("column"),
                "original_value": str(iss.get("original_value")),
                "cleaned_value": str(iss.get("suggested_value")),
                "issue": iss.get("title"),
                "action_taken": iss.get("status"),
                "severity": iss.get("severity", "INFO"),
                "rule_name": iss.get("issue_type")
            })

        # Save DataQualityLog
        log_entry = DataQualityLog(
            batch_id=batch_id,
            uploaded_at=datetime.utcnow(),
            source_name=source_names,
            total_rows=summary["total_rows"],
            valid_rows=len(approved_rows),
            flagged_rows=summary["flagged_rows"],
            skipped_rows=summary["total_rows"] - len(approved_rows),
            mutations_count=len(audit_records),
            info_count=summary["formatting_cleaned"],
            warning_count=summary["missing_values"] + summary["potential_duplicates"],
            error_count=summary["invalid_values"] + summary["confirmed_duplicates"],
            quality_score=summary["quality_score"],
            audit_trail_json=audit_records[:300],  # cap stored audit log
            cleaning_rules_applied=["multi_format_extract", "duplicate_detection", "clean_currency", "clean_size", "clean_product_name", "category_normalization"]
        )
        db.add(log_entry)
        db.commit()

        # Clean up session
        _STAGING_SESSIONS.pop(session_id, None)

        return {
            "success": True,
            "batch_id": batch_id,
            "message": f"Successfully imported {len(approved_rows)} validated business records.",
            "imported_count": len(approved_rows),
            "excluded_count": summary["total_rows"] - len(approved_rows),
            "entities_saved": {
                "products": saved_products,
                "sales": saved_sales,
                "inventory": saved_inventory,
                "inquiries": saved_inquiries
            },
            "quality_score": summary["quality_score"],
            "source_name": source_names
        }

    except Exception as e:
        db.rollback()
        raise ValueError(f"Database transaction failed during import: {str(e)}")

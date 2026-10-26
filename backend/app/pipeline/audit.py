from typing import List, Dict, Any


class AuditLedger:
    def __init__(self, batch_id: str, source_name: str = "Upload"):
        self.batch_id = batch_id
        self.source_name = source_name
        self.records: List[Dict[str, Any]] = []
        self.total_rows = 0
        self.flagged_rows_set = set()
        self.skipped_rows_set = set()
        self.rules_applied = set()
        self._severity_counts = {"INFO": 0, "WARNING": 0, "ERROR": 0}

    def set_total_rows(self, count: int):
        self.total_rows = count

    def log(
        self,
        row_idx: int,
        column: str,
        original_val: Any,
        cleaned_val: Any,
        issue: str,
        action_taken: str,
        severity: str = "INFO",  # INFO, WARNING, ERROR
        rule_name: str = ""
    ):
        """Records a cell-level mutation or data quality observation."""
        self.flagged_rows_set.add(row_idx)
        self._severity_counts[severity] = self._severity_counts.get(severity, 0) + 1
        if rule_name:
            self.rules_applied.add(rule_name)

        self.records.append({
            "row": row_idx,
            "column": column,
            "original_value": str(original_val) if original_val is not None else "NULL",
            "cleaned_value": str(cleaned_val) if cleaned_val is not None else "NULL",
            "issue": issue,
            "action_taken": action_taken,
            "severity": severity,
            "rule_name": rule_name or "general"
        })

    def log_skip(self, row_idx: int, reason: str):
        """Records a completely skipped row."""
        self.skipped_rows_set.add(row_idx)
        self.log(
            row_idx=row_idx,
            column="Row",
            original_val="(entire row)",
            cleaned_val="SKIPPED",
            issue=reason,
            action_taken="Skipped row",
            severity="WARNING",
            rule_name="skip_blank_row"
        )

    def compute_health_score(self) -> float:
        """
        Computes 0.0 - 100.0% data quality health score based on mutation severity and total row impact.
        """
        if self.total_rows == 0:
            return 100.0

        penalty = 0.0
        for r in self.records:
            sev = r.get("severity", "INFO")
            if sev == "INFO":
                penalty += 0.5
            elif sev == "WARNING":
                penalty += 2.0
            elif sev == "ERROR":
                penalty += 5.0

        score = max(15.0, 100.0 - (penalty / max(1, self.total_rows) * 20.0))
        return round(min(100.0, score), 1)

    def to_summary_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "source_name": self.source_name,
            "total_rows": self.total_rows,
            "valid_rows": self.total_rows - len(self.flagged_rows_set),
            "flagged_rows": len(self.flagged_rows_set),
            "skipped_rows": len(self.skipped_rows_set),
            "mutations_count": len(self.records),
            "info_count": self._severity_counts.get("INFO", 0),
            "warning_count": self._severity_counts.get("WARNING", 0),
            "error_count": self._severity_counts.get("ERROR", 0),
            "quality_score": self.compute_health_score(),
            "audit_trail": self.records,
            "cleaning_rules_applied": sorted(list(self.rules_applied))
        }

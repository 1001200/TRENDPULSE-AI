"""
Optional semantic column matcher.

The deterministic mapper remains the source of truth. Sentence-transformers
is used only when installed and enabled; otherwise a lightweight lexical
fallback is returned. No network/model download is performed automatically.
"""

from __future__ import annotations

import re
from typing import Iterable


CANONICAL_PHRASES = {
    "date": ["date", "order date", "sale date", "transaction date", "purchase date"],
    "product": ["product", "product name", "item", "item name", "product title"],
    "category": ["category", "product category", "item category", "product type"],
    "subcategory": ["subcategory", "sub category", "product subcategory", "sub type"],
    "quantity": ["quantity", "qty", "units sold", "quantity sold", "pieces sold", "items sold"],
    "price": ["price", "selling price", "sale price", "unit price", "amount"],
    "customer_id": ["customer id", "customer number", "buyer id"],
    "order_id": ["order id", "order number", "transaction id"],
    "discount": ["discount", "discount percentage", "discount rate"],
    "size": ["size", "product size", "item size", "garment size"],
    "color": ["color", "colour", "product color", "product colour"],
    "sku": ["sku", "stock keeping unit", "product sku", "product code", "barcode"],
    "cost_price": ["cost price", "purchase price", "unit cost", "buying price", "cogs"],
    "stock": ["stock", "inventory", "units in stock", "quantity in stock", "available stock"],
    "revenue": ["revenue", "total revenue", "sales revenue", "total sales", "line total"],
}



def _normalize(text) -> str:
    text = str(text).strip().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def build_candidate_phrases(canonical_columns: Iterable[str] | None = None):
    columns = list(canonical_columns) if canonical_columns else list(CANONICAL_PHRASES)
    return {
        c: CANONICAL_PHRASES.get(c, [c])
        for c in columns
    }


def _lexical_score(source: str, phrase: str) -> float:
    a = set(_normalize(source).split())
    b = set(_normalize(phrase).split())
    if not a or not b:
        return 0.0
    overlap = len(a & b) / max(len(a | b), 1)
    substring = 1.0 if _normalize(phrase) in _normalize(source) else 0.0
    return max(overlap, substring * 0.95)


def get_model():
    # Deliberately opt-in. Importing TrendPulse must not trigger model downloads.
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None
    return SentenceTransformer("all-MiniLM-L6-v2")


def find_semantic_match(column_name, candidate_columns=None):
    candidates = build_candidate_phrases(candidate_columns)
    source = _normalize(column_name)

    scored = []
    for canonical, phrases in candidates.items():
        score = max((_lexical_score(source, p) for p in phrases), default=0.0)
        phrase = max(phrases, key=lambda p: _lexical_score(source, p), default="")
        scored.append((score, canonical, phrase))

    scored.sort(reverse=True)
    if not scored:
        return {"match": None, "score": 0.0, "confidence": "low",
                "matched_phrase": None, "second_best_score": 0.0, "margin": 0.0}

    best = scored[0]
    second = scored[1][0] if len(scored) > 1 else 0.0
    margin = best[0] - second

    if best[0] >= 0.80 and margin >= 0.15:
        confidence = "high"
    elif best[0] >= 0.55 and margin >= 0.08:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "match": best[1] if confidence != "low" else None,
        "score": round(best[0], 4),
        "confidence": confidence,
        "matched_phrase": best[2],
        "second_best_score": round(second, 4),
        "margin": round(margin, 4),
    }

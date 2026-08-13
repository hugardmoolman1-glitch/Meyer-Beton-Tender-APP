"""
Historical pricing lookups.

Every BOQ line item ever entered (across all tenders) carries its own
cost_price and selling_price, so that table IS the price history - there's
no separate ledger to keep in sync. This module just does fuzzy matching on
description text so that e.g. "19mm crushed stone" quoted last year surfaces
when a new tender asks for "Crushed stone 19mm".
"""

from __future__ import annotations

from typing import List, Optional

from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from app import models

MIN_MATCH_SCORE = 60.0


def find_similar_line_items(
    db: Session,
    description: str,
    exclude_line_item_id: Optional[int] = None,
    limit: int = 10,
) -> List[tuple[models.BOQLineItem, float]]:
    candidates = (
        db.query(models.BOQLineItem)
        .filter(models.BOQLineItem.description.isnot(None))
        .filter(
            (models.BOQLineItem.cost_price.isnot(None)) | (models.BOQLineItem.selling_price.isnot(None))
        )
    )
    if exclude_line_item_id is not None:
        candidates = candidates.filter(models.BOQLineItem.id != exclude_line_item_id)

    scored = []
    for item in candidates.all():
        score = fuzz.token_set_ratio(description, item.description)
        if score >= MIN_MATCH_SCORE:
            scored.append((item, float(score)))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:limit]


def suggest_prices(db: Session, description: str, exclude_line_item_id: Optional[int] = None):
    matches = find_similar_line_items(db, description, exclude_line_item_id)
    cost_prices = [m.cost_price for m, _ in matches if m.cost_price is not None]
    selling_prices = [m.selling_price for m, _ in matches if m.selling_price is not None]

    def _avg(values: List[float]) -> Optional[float]:
        return round(sum(values) / len(values), 2) if values else None

    return matches, _avg(cost_prices), _avg(selling_prices)

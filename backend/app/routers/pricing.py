from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services import pricing

router = APIRouter(prefix="/api/pricing", tags=["pricing"])


def _to_entry(item: models.BOQLineItem, score: float) -> schemas.PriceHistoryEntry:
    return schemas.PriceHistoryEntry(
        line_item_id=item.id,
        tender_id=item.tender_id,
        tender_title=item.tender.title,
        description=item.description,
        unit=item.unit,
        cost_price=item.cost_price,
        selling_price=item.selling_price,
        recorded_at=item.updated_at,
        match_score=score,
    )


@router.get("/history", response_model=list[schemas.PriceHistoryEntry])
def price_history(description: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    matches = pricing.find_similar_line_items(db, description)
    return [_to_entry(item, score) for item, score in matches]


@router.get("/items", response_model=list[schemas.PricedItemOut])
def priced_items(search: Optional[str] = None, db: Session = Depends(get_db)):
    """Every line item that has a cost or selling price, newest first - the price history book."""
    if search and search.strip():
        items = [item for item, _ in pricing.find_similar_line_items(db, search.strip(), limit=200)]
    else:
        items = (
            db.query(models.BOQLineItem)
            .filter((models.BOQLineItem.cost_price.isnot(None)) | (models.BOQLineItem.selling_price.isnot(None)))
            .order_by(models.BOQLineItem.updated_at.desc())
            .limit(500)
            .all()
        )

    out = []
    for item in items:
        margin = None
        if item.cost_price is not None and item.selling_price:
            margin = round((item.selling_price - item.cost_price) / item.selling_price * 100, 1)
        out.append(
            schemas.PricedItemOut(
                line_item_id=item.id,
                tender_id=item.tender_id,
                tender_title=item.tender.title,
                tender_status=item.tender.status,
                item_no=item.item_no,
                description=item.description,
                unit=item.unit,
                quantity=item.quantity,
                cost_price=item.cost_price,
                selling_price=item.selling_price,
                margin_pct=margin,
                recorded_at=item.updated_at,
            )
        )
    return out


@router.get("/suggest/{line_item_id}", response_model=schemas.PriceSuggestion)
def suggest_price(line_item_id: int, db: Session = Depends(get_db)):
    line_item = db.get(models.BOQLineItem, line_item_id)
    if not line_item:
        raise HTTPException(status_code=404, detail="Line item not found")

    matches, avg_cost, avg_selling = pricing.suggest_prices(
        db, line_item.description, exclude_line_item_id=line_item_id
    )
    return schemas.PriceSuggestion(
        suggested_cost_price=avg_cost,
        suggested_selling_price=avg_selling,
        based_on=[_to_entry(item, score) for item, score in matches],
    )

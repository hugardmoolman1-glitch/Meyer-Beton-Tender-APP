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

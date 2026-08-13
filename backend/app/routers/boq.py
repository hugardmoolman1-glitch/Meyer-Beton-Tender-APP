from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services import boq_parser

router = APIRouter(tags=["boq"])


@router.post("/api/tenders/{tender_id}/boq/upload", response_model=schemas.BOQUploadResult)
async def upload_boq(tender_id: int, file: UploadFile, db: Session = Depends(get_db)):
    tender = db.get(models.Tender, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    content = await file.read()
    try:
        parsed_items, warnings = boq_parser.parse_boq(file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    created: List[models.BOQLineItem] = []
    for parsed in parsed_items:
        line_item = models.BOQLineItem(
            tender_id=tender_id,
            item_no=parsed.item_no,
            description=parsed.description,
            unit=parsed.unit,
            quantity=parsed.quantity,
        )
        db.add(line_item)
        created.append(line_item)
    db.commit()
    for item in created:
        db.refresh(item)

    return schemas.BOQUploadResult(
        line_items_created=len(created),
        items=created,
        warnings=warnings,
    )


@router.get("/api/tenders/{tender_id}/line-items", response_model=List[schemas.LineItemOut])
def list_line_items(tender_id: int, db: Session = Depends(get_db)):
    tender = db.get(models.Tender, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    return (
        db.query(models.BOQLineItem)
        .filter(models.BOQLineItem.tender_id == tender_id)
        .order_by(models.BOQLineItem.id.asc())
        .all()
    )


@router.post("/api/tenders/{tender_id}/line-items", response_model=schemas.LineItemOut, status_code=201)
def create_line_item(tender_id: int, payload: schemas.LineItemCreate, db: Session = Depends(get_db)):
    tender = db.get(models.Tender, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    line_item = models.BOQLineItem(tender_id=tender_id, **payload.model_dump())
    db.add(line_item)
    db.commit()
    db.refresh(line_item)
    return line_item


@router.patch("/api/line-items/{line_item_id}", response_model=schemas.LineItemOut)
def update_line_item(line_item_id: int, payload: schemas.LineItemUpdate, db: Session = Depends(get_db)):
    line_item = db.get(models.BOQLineItem, line_item_id)
    if not line_item:
        raise HTTPException(status_code=404, detail="Line item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(line_item, field, value)
    db.commit()
    db.refresh(line_item)
    return line_item


@router.delete("/api/line-items/{line_item_id}", status_code=204)
def delete_line_item(line_item_id: int, db: Session = Depends(get_db)):
    line_item = db.get(models.BOQLineItem, line_item_id)
    if not line_item:
        raise HTTPException(status_code=404, detail="Line item not found")
    db.delete(line_item)
    db.commit()
    return None

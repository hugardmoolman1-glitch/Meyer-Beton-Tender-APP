from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services import etenders_source

router = APIRouter(prefix="/api/tenders", tags=["tenders"])


@router.get("", response_model=List[schemas.TenderOut])
def list_tenders(status: Optional[models.TenderStatus] = None, db: Session = Depends(get_db)):
    query = db.query(models.Tender)
    if status is not None:
        query = query.filter(models.Tender.status == status)
    return query.order_by(models.Tender.closing_date.asc().nullslast()).all()


@router.post("", response_model=schemas.TenderOut, status_code=201)
def create_tender(payload: schemas.TenderCreate, db: Session = Depends(get_db)):
    tender = models.Tender(source="manual", **payload.model_dump())
    db.add(tender)
    db.commit()
    db.refresh(tender)
    return tender


@router.post("/fetch", response_model=schemas.TenderFetchResult)
def fetch_tenders(db: Session = Depends(get_db)):
    try:
        fetched = etenders_source.fetch_open_tenders()
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    created = 0
    for item in fetched:
        exists = (
            db.query(models.Tender)
            .filter(
                models.Tender.source == etenders_source.SOURCE_NAME,
                models.Tender.external_id == item.external_id,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            models.Tender(
                source=etenders_source.SOURCE_NAME,
                external_id=item.external_id,
                title=item.title,
                buyer=item.buyer,
                category=item.category,
                description=item.description,
                province=item.province,
                published_date=item.published_date,
                closing_date=item.closing_date,
                source_url=item.source_url,
            )
        )
        created += 1
    db.commit()

    return schemas.TenderFetchResult(
        fetched=len(fetched),
        created=created,
        skipped=len(fetched) - created,
    )


@router.get("/{tender_id}", response_model=schemas.TenderOut)
def get_tender(tender_id: int, db: Session = Depends(get_db)):
    tender = db.get(models.Tender, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    return tender


@router.patch("/{tender_id}", response_model=schemas.TenderOut)
def update_tender(tender_id: int, payload: schemas.TenderUpdate, db: Session = Depends(get_db)):
    tender = db.get(models.Tender, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tender, field, value)
    db.commit()
    db.refresh(tender)
    return tender


@router.delete("/{tender_id}", status_code=204)
def delete_tender(tender_id: int, db: Session = Depends(get_db)):
    tender = db.get(models.Tender, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    db.delete(tender)
    db.commit()
    return None

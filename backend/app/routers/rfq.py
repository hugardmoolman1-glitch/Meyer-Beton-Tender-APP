from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services import email_sender, rfq_drafter

router = APIRouter(tags=["rfq"])


@router.post("/api/tenders/{tender_id}/rfq/generate", response_model=List[schemas.RFQEmailOut])
def generate_rfq_drafts(tender_id: int, payload: schemas.RFQGenerateRequest, db: Session = Depends(get_db)):
    tender = db.get(models.Tender, tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    if payload.line_item_ids:
        line_items = (
            db.query(models.BOQLineItem)
            .filter(models.BOQLineItem.id.in_(payload.line_item_ids), models.BOQLineItem.tender_id == tender_id)
            .all()
        )
    else:
        line_items = db.query(models.BOQLineItem).filter(models.BOQLineItem.tender_id == tender_id).all()

    if not line_items:
        raise HTTPException(status_code=400, detail="This tender has no line items to send yet - upload a BOQ first")

    if payload.supplier_ids:
        suppliers = db.query(models.Supplier).filter(models.Supplier.id.in_(payload.supplier_ids)).all()
        if not suppliers:
            raise HTTPException(status_code=400, detail="None of the given supplier_ids exist")
        matches = {s.id: line_items for s in suppliers}
    else:
        suppliers = db.query(models.Supplier).all()
        if not suppliers:
            raise HTTPException(status_code=400, detail="No suppliers exist yet - add suppliers first")
        matches = rfq_drafter.match_suppliers_to_line_items(suppliers, line_items)
        if not matches:
            raise HTTPException(
                status_code=400,
                detail="No suppliers' categories matched these line items - assign categories to suppliers "
                "or pass explicit supplier_ids",
            )

    suppliers_by_id = {s.id: s for s in suppliers}
    drafts: List[models.RFQEmail] = []
    for supplier_id, matched_items in matches.items():
        supplier = suppliers_by_id[supplier_id]
        subject, body = rfq_drafter.build_email(tender, supplier, matched_items, payload.extra_message)
        draft = models.RFQEmail(
            tender_id=tender_id,
            supplier_id=supplier_id,
            subject=subject,
            body=body,
            line_items=matched_items,
        )
        db.add(draft)
        drafts.append(draft)

    db.commit()
    for draft in drafts:
        db.refresh(draft)
    return drafts


@router.get("/api/tenders/{tender_id}/rfq", response_model=List[schemas.RFQEmailOut])
def list_rfq_drafts(tender_id: int, db: Session = Depends(get_db)):
    return db.query(models.RFQEmail).filter(models.RFQEmail.tender_id == tender_id).all()


@router.get("/api/rfq/{rfq_id}", response_model=schemas.RFQEmailOut)
def get_rfq_draft(rfq_id: int, db: Session = Depends(get_db)):
    draft = db.get(models.RFQEmail, rfq_id)
    if not draft:
        raise HTTPException(status_code=404, detail="RFQ draft not found")
    return draft


@router.patch("/api/rfq/{rfq_id}", response_model=schemas.RFQEmailOut)
def update_rfq_draft(rfq_id: int, payload: schemas.RFQEmailUpdate, db: Session = Depends(get_db)):
    draft = db.get(models.RFQEmail, rfq_id)
    if not draft:
        raise HTTPException(status_code=404, detail="RFQ draft not found")
    if draft.status == models.RFQStatus.sent:
        raise HTTPException(status_code=400, detail="This RFQ has already been sent and can't be edited")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(draft, field, value)
    db.commit()
    db.refresh(draft)
    return draft


@router.delete("/api/rfq/{rfq_id}", status_code=204)
def delete_rfq_draft(rfq_id: int, db: Session = Depends(get_db)):
    draft = db.get(models.RFQEmail, rfq_id)
    if not draft:
        raise HTTPException(status_code=404, detail="RFQ draft not found")
    db.delete(draft)
    db.commit()
    return None


def _send(draft: models.RFQEmail, db: Session) -> None:
    email_sender.send_email(draft.supplier.email, draft.subject, draft.body)
    draft.status = models.RFQStatus.sent
    draft.sent_at = datetime.utcnow()
    db.commit()


@router.post("/api/rfq/{rfq_id}/send", response_model=schemas.RFQSendResult)
def send_rfq_draft(rfq_id: int, db: Session = Depends(get_db)):
    draft = db.get(models.RFQEmail, rfq_id)
    if not draft:
        raise HTTPException(status_code=404, detail="RFQ draft not found")
    if draft.status == models.RFQStatus.sent:
        raise HTTPException(status_code=400, detail="This RFQ has already been sent")

    try:
        _send(draft, db)
    except email_sender.SMTPNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # smtplib errors etc.
        raise HTTPException(status_code=502, detail=f"Failed to send email: {exc}") from exc

    return schemas.RFQSendResult(sent=True, message=f"Sent to {draft.supplier.email}")


@router.post("/api/tenders/{tender_id}/rfq/send-all", response_model=schemas.RFQBulkSendResult)
def send_all_rfq_drafts(tender_id: int, db: Session = Depends(get_db)):
    drafts = (
        db.query(models.RFQEmail)
        .filter(models.RFQEmail.tender_id == tender_id, models.RFQEmail.status == models.RFQStatus.draft)
        .all()
    )
    if not drafts:
        raise HTTPException(status_code=400, detail="There are no unsent drafts for this tender")

    sent, errors = 0, []
    for draft in drafts:
        try:
            _send(draft, db)
            sent += 1
        except email_sender.SMTPNotConfiguredError as exc:
            # Nothing else will succeed either - stop and report it once.
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:  # one bad address shouldn't block the rest
            db.rollback()
            errors.append(f"{draft.supplier.name} ({draft.supplier.email}): {exc}")

    return schemas.RFQBulkSendResult(sent=sent, failed=len(errors), errors=errors)

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, computed_field

from app.models import RFQStatus, TenderStatus


# ---------- Tender ----------

class TenderBase(BaseModel):
    title: str
    buyer: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    province: Optional[str] = None
    published_date: Optional[datetime] = None
    closing_date: Optional[datetime] = None
    source_url: Optional[str] = None


class TenderCreate(TenderBase):
    pass


class TenderUpdate(BaseModel):
    title: Optional[str] = None
    buyer: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    province: Optional[str] = None
    published_date: Optional[datetime] = None
    closing_date: Optional[datetime] = None
    source_url: Optional[str] = None
    status: Optional[TenderStatus] = None


class TenderOut(TenderBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    external_id: Optional[str] = None
    status: TenderStatus
    created_at: datetime
    updated_at: datetime


class TenderFetchResult(BaseModel):
    fetched: int
    created: int
    skipped: int
    not_relevant: int = 0
    message: Optional[str] = None


# ---------- BOQ Line Items ----------

class LineItemBase(BaseModel):
    item_no: Optional[str] = None
    description: str
    unit: Optional[str] = None
    quantity: Optional[float] = None
    category: Optional[str] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    notes: Optional[str] = None


class LineItemCreate(LineItemBase):
    pass


class LineItemUpdate(BaseModel):
    item_no: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    quantity: Optional[float] = None
    category: Optional[str] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    notes: Optional[str] = None


class LineItemOut(LineItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tender_id: int
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def margin(self) -> Optional[float]:
        if self.cost_price is not None and self.selling_price is not None and self.cost_price != 0:
            return round((self.selling_price - self.cost_price) / self.cost_price * 100, 2)
        return None


class BOQUploadResult(BaseModel):
    line_items_created: int
    items: List[LineItemOut]
    warnings: List[str] = []


# ---------- Pricing history ----------

class PriceHistoryEntry(BaseModel):
    line_item_id: int
    tender_id: int
    tender_title: str
    description: str
    unit: Optional[str] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    recorded_at: datetime
    match_score: float


class PricedItemOut(BaseModel):
    line_item_id: int
    tender_id: int
    tender_title: str
    tender_status: TenderStatus
    item_no: Optional[str] = None
    description: str
    unit: Optional[str] = None
    quantity: Optional[float] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    margin_pct: Optional[float] = None  # (selling - cost) / selling * 100
    recorded_at: datetime


class PriceSuggestion(BaseModel):
    suggested_cost_price: Optional[float] = None
    suggested_selling_price: Optional[float] = None
    based_on: List[PriceHistoryEntry]


# ---------- Suppliers ----------

class SupplierBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    categories: Optional[str] = None
    notes: Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    categories: Optional[str] = None
    notes: Optional[str] = None


class SupplierOut(SupplierBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class SupplierMatch(BaseModel):
    supplier: SupplierOut
    matched_line_item_ids: List[int]


# ---------- RFQ ----------

class RFQGenerateRequest(BaseModel):
    supplier_ids: Optional[List[int]] = None  # if omitted, auto-match by category
    line_item_ids: Optional[List[int]] = None  # if omitted, use all of the tender's line items
    extra_message: Optional[str] = None


class RFQEmailUpdate(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None


class RFQEmailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tender_id: int
    supplier_id: int
    subject: str
    body: str
    status: RFQStatus
    created_at: datetime
    sent_at: Optional[datetime] = None
    line_items: List[LineItemOut] = []


class RFQSendResult(BaseModel):
    sent: bool
    message: str


class RFQBulkSendResult(BaseModel):
    sent: int
    failed: int
    errors: List[str] = []

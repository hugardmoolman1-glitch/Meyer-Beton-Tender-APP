import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class TenderStatus(str, enum.Enum):
    open = "open"
    submitted = "submitted"
    won = "won"
    lost = "lost"
    closed = "closed"


class RFQStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"


class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, default="manual", nullable=False)  # e.g. "etenders", "manual"
    external_id = Column(String, index=True, nullable=True)  # id/OCID from source, for de-duplication
    title = Column(String, nullable=False)
    buyer = Column(String, nullable=True)  # issuing organ of state / client
    category = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    province = Column(String, nullable=True)
    published_date = Column(DateTime, nullable=True)
    closing_date = Column(DateTime, nullable=True)
    status = Column(Enum(TenderStatus), default=TenderStatus.open, nullable=False)
    source_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    line_items = relationship("BOQLineItem", back_populates="tender", cascade="all, delete-orphan")
    rfq_emails = relationship("RFQEmail", back_populates="tender", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_tender_source_external_id"),)


class BOQLineItem(Base):
    __tablename__ = "boq_line_items"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False)
    item_no = Column(String, nullable=True)
    description = Column(Text, nullable=False)
    unit = Column(String, nullable=True)
    quantity = Column(Float, nullable=True)
    category = Column(String, nullable=True)  # used to match line item to supplier categories
    cost_price = Column(Float, nullable=True)  # what we pay our supplier, per unit
    selling_price = Column(Float, nullable=True)  # what we quote the client, per unit
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tender = relationship("Tender", back_populates="line_items")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    categories = Column(String, nullable=True)  # comma-separated keywords, e.g. "cement,aggregate,steel"
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RFQEmail(Base):
    __tablename__ = "rfq_emails"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    status = Column(Enum(RFQStatus), default=RFQStatus.draft, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)

    tender = relationship("Tender", back_populates="rfq_emails")
    supplier = relationship("Supplier")
    line_items = relationship(
        "BOQLineItem",
        secondary="rfq_email_line_items",
        backref="rfq_emails",
    )


class RFQEmailLineItem(Base):
    __tablename__ = "rfq_email_line_items"

    id = Column(Integer, primary_key=True, index=True)
    rfq_email_id = Column(Integer, ForeignKey("rfq_emails.id"), nullable=False)
    boq_line_item_id = Column(Integer, ForeignKey("boq_line_items.id"), nullable=False)

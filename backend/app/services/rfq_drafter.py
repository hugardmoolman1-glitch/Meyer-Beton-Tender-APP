"""
Builds RFQ (request-for-quote) email drafts to send BOQ line items out to
suppliers for pricing. Drafts are always saved as status="draft" for a human
to review/edit before anything is actually emailed - see email_sender.py for
the (explicit, separate) send step.
"""

from __future__ import annotations

from typing import Dict, List

from app import models


def match_suppliers_to_line_items(
    suppliers: List[models.Supplier], line_items: List[models.BOQLineItem]
) -> Dict[int, List[models.BOQLineItem]]:
    """
    Category-keyword match: a supplier's `categories` field is a comma
    separated list of keywords (e.g. "cement,aggregate"). A line item matches
    a supplier if any of the supplier's keywords appear in the line item's
    category or description. Suppliers with no categories set match every
    line item (treated as general suppliers).
    """
    matches: Dict[int, List[models.BOQLineItem]] = {}
    for supplier in suppliers:
        keywords = [k.strip().lower() for k in (supplier.categories or "").split(",") if k.strip()]
        if not keywords:
            matches[supplier.id] = list(line_items)
            continue

        matched_items = []
        for item in line_items:
            haystack = f"{item.category or ''} {item.description}".lower()
            if any(kw in haystack for kw in keywords):
                matched_items.append(item)
        if matched_items:
            matches[supplier.id] = matched_items
    return matches


def build_email(
    tender: models.Tender,
    supplier: models.Supplier,
    line_items: List[models.BOQLineItem],
    extra_message: str | None = None,
) -> tuple[str, str]:
    subject = f"Request for Quote: {tender.title}"

    lines = [
        f"Hi {supplier.name},",
        "",
        f"We're pricing the following tender ({tender.title}"
        + (f", client: {tender.buyer}" if tender.buyer else "")
        + (f", closing {tender.closing_date.date()}" if tender.closing_date else "")
        + ") and would appreciate your best pricing on the items below.",
        "",
    ]
    if extra_message:
        lines.extend([extra_message, ""])

    lines.append(f"{'Item':<8}{'Description':<60}{'Unit':<10}{'Qty':>10}")
    lines.append("-" * 88)
    for item in line_items:
        item_no = (item.item_no or "")[:7]
        description = (item.description or "")[:59]
        unit = (item.unit or "")[:9]
        qty = "" if item.quantity is None else f"{item.quantity:g}"
        lines.append(f"{item_no:<8}{description:<60}{unit:<10}{qty:>10}")

    lines.extend(
        [
            "",
            "Please could you send us your rates per item, along with your lead time and validity period.",
            "",
            "Kind regards,",
            "Meyer Beton",
        ]
    )

    return subject, "\n".join(lines)

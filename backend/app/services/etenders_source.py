"""
Fetches tender listings from South Africa's national eTenders portal.

The public OCDS (Open Contracting Data Standard) release API is used:
    https://ocds-api.etenders.gov.za/api/OCDSReleases

Each release under `releases[]` roughly has this shape:
    {
        "ocid": "...",
        "id": "...",
        "tender": {
            "id": "...",
            "title": "...",
            "description": "...",
            "status": "active" | "complete" | "cancelled" | ...,
            "tenderPeriod": {"startDate": "...", "endDate": "..."},
            "mainProcurementCategory": "...",
        },
        "buyer": {"name": "..."},
        "date": "...",  # publication date
    }

NOTE: this module could not be exercised against the live API from this
sandboxed development environment (outbound web access to non-package-registry
hosts is blocked here). The parsing logic below follows the public OCDS
release schema and eTenders' documented field names, but it should be
verified against a real response once this app is deployed somewhere with
outbound internet access, and adjusted if the portal's response shape has
drifted since this was written.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

ETENDERS_OCDS_API = "https://ocds-api.etenders.gov.za/api/OCDSReleases"
SOURCE_NAME = "etenders"


@dataclass
class FetchedTender:
    external_id: str
    title: str
    buyer: Optional[str]
    category: Optional[str]
    description: Optional[str]
    province: Optional[str]
    published_date: Optional[datetime]
    closing_date: Optional[datetime]
    source_url: Optional[str]


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _release_to_tender(release: dict) -> Optional[FetchedTender]:
    tender = release.get("tender") or {}
    title = tender.get("title") or release.get("id")
    if not title:
        return None

    external_id = tender.get("id") or release.get("ocid") or release.get("id")
    buyer = (release.get("buyer") or {}).get("name")
    period = tender.get("tenderPeriod") or {}

    return FetchedTender(
        external_id=str(external_id),
        title=title,
        buyer=buyer,
        category=tender.get("mainProcurementCategory"),
        description=tender.get("description"),
        province=(release.get("buyer") or {}).get("address", {}).get("region")
        if isinstance(release.get("buyer"), dict)
        else None,
        published_date=_parse_date(release.get("date")),
        closing_date=_parse_date(period.get("endDate")),
        source_url=tender.get("documents", [{}])[0].get("url") if tender.get("documents") else None,
    )


def fetch_open_tenders(page_size: int = 50, max_pages: int = 3, timeout: int = 15) -> List[FetchedTender]:
    """
    Pull recent tender releases from the eTenders OCDS API and return the
    ones that still look open (closing date in the future, or status active).

    Raises RuntimeError with a human-readable message on network/parse failure
    so the API layer can surface something actionable instead of a raw
    traceback (this portal is not reachable from every environment).
    """
    results: List[FetchedTender] = []
    for page in range(1, max_pages + 1):
        url = f"{ETENDERS_OCDS_API}?PageNumber={page}"
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Could not reach the eTenders OCDS API ({url}): {exc}. "
                "If this is running somewhere without outbound internet access, "
                "add tenders manually instead."
            ) from exc
        except (json.JSONDecodeError, TimeoutError) as exc:
            raise RuntimeError(f"Unexpected response from eTenders OCDS API: {exc}") from exc

        releases = payload.get("releases") or []
        if not releases:
            break

        now = datetime.utcnow()
        for release in releases:
            fetched = _release_to_tender(release)
            if fetched is None:
                continue
            if fetched.closing_date and fetched.closing_date < now:
                continue
            results.append(fetched)

    return results

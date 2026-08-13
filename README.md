# Meyer Beton Tender Desk

An internal tool for digitizing Meyer Beton's tender process:

1. **Find tenders** - pull open tenders from South Africa's national eTenders portal, or add them manually.
2. **Track a tender's BOQ** - upload a Bill of Quantities (Excel, PDF, or Word) and it's parsed into line items automatically.
3. **Keep price history** - every line item stores its cost price (what we pay) and selling price (what we quote), across every tender. When pricing a new tender, the app suggests prices based on similar line items priced before.
4. **Get supplier quotes** - generate RFQ (request-for-quote) email drafts per supplier, matched to the relevant BOQ line items by category. Drafts are always reviewed by a person before sending - nothing goes out automatically.

## Architecture

- `backend/` - FastAPI + SQLAlchemy, SQLite by default (swap `DATABASE_URL` for Postgres in production).
- `frontend/` - React + TypeScript (Vite).

## Deploying

To run this somewhere with real internet access (needed for "Fetch from
eTenders" - see the note below), see **[DEPLOY.md](DEPLOY.md)** for a
Docker-based VPS setup with an optional one-command HTTPS option.

## Running locally

### Backend

```bash
cd backend
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/uvicorn app.main:app --reload --port 8000
```

This creates `backend/data/tenders.db` (SQLite) on first run - no separate database setup needed.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The frontend expects the backend at `http://localhost:8000` by default (see `frontend/.env`, `VITE_API_BASE`).

## Sending supplier emails

RFQ emails are always created as **drafts** first, editable in the UI, and only sent when you click Send on a specific draft. To enable actual sending, set these environment variables on the backend before starting it:

```
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=you@example.com
SMTP_PASSWORD=...
SMTP_FROM_EMAIL=you@example.com
SMTP_USE_TLS=true   # optional, defaults to true
```

Without these set, clicking Send returns a clear error explaining what to configure - drafts can still be reviewed and copied out manually in the meantime.

## Tender source (eTenders)

Tenders are fetched from South Africa's public eTenders OCDS API (`https://ocds-api.etenders.gov.za/api/OCDSReleases`) via `backend/app/services/etenders_source.py`. This integration was written against the publicly documented OCDS release schema but **could not be tested against the live API from the sandboxed environment this app was built in** (no outbound internet access there beyond package registries). Before relying on it:

- Run "Fetch from eTenders" once from the Tenders page and check the results look sane.
- If the portal's response shape has changed, adjust `_release_to_tender()` in that file - the parsing is isolated to one function.
- Manual tender entry always works regardless, as a fallback.

To add another tender source (a specific client portal, for example), add a new module alongside `etenders_source.py` with the same `fetch_open_tenders() -> List[FetchedTender]` shape and wire it into the `/api/tenders/fetch` endpoint in `backend/app/routers/tenders.py`.

## BOQ parsing

`backend/app/services/boq_parser.py` handles `.xlsx`, `.pdf`, and `.docx` BOQs. It looks for a header row containing recognizable column names (Description, Unit, Qty, Item No) and reads line items from the rows beneath it. BOQ layouts vary a lot - if a file doesn't parse cleanly, the upload result shows a warning, and items can always be added or corrected by hand in the line items table afterwards. Legacy `.xls` files aren't supported - re-save as `.xlsx` first.

## Data model notes

- **Price history isn't a separate table** - every `BOQLineItem` (one per tender) already carries its own cost/selling price, so the full set of line items across all tenders *is* the price history. The "Suggest from history" button on a line item fuzzy-matches its description against every other priced line item in the database (via `rapidfuzz`) and averages the cost/selling prices of the closest matches.
- **Supplier-to-line-item matching** is a simple comma-separated keyword match on each supplier's `categories` field against line item description/category text (see `rfq_drafter.py`). Suppliers with no categories set are treated as general and matched to everything. This is intentionally simple for a first version - swap in something smarter later if keyword matching isn't accurate enough.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.database import Base, engine
from app.routers import boq, pricing, rfq, suppliers, tenders

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Meyer Beton Tender App", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tenders.router)
app.include_router(boq.router)
app.include_router(pricing.router)
app.include_router(suppliers.router)
app.include_router(rfq.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}

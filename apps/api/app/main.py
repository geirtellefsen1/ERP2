from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

from app.routers import auth, clients, tasks, accounts, coa_import, journals, posting_periods, bank_feeds, reconciliation, reports, ai, documents

app = FastAPI(title="BPO Nexus API", version="0.8.0", description="AI-First BPO Platform")

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(tasks.router)
app.include_router(accounts.router)
app.include_router(coa_import.router)
app.include_router(journals.router)
app.include_router(posting_periods.router)
app.include_router(bank_feeds.router)
app.include_router(reconciliation.router)
app.include_router(reports.router)
app.include_router(ai.router)
app.include_router(documents.router)


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="0.8.0")


@app.get("/")
async def root():
    return {"message": "BPO Nexus API", "version": "0.8.0", "docs": "/docs"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.config import get_settings
from app.routers import (
    agencies,
    clients,
    users,
    auth,
    oauth,
    accounts,
    journal,
    bank,
    reports,
    documents,
    ai,
    agent,
    payroll,
    integrations,
    billing_stripe,
    onboarding,
    dsr,
)

settings = get_settings()

app = FastAPI(
    title="BPO Nexus API",
    version="1.4.0",
    description="AI-First Business Process Outsourcing Platform",
)

# CORS — allow the frontend (and any other origins listed in CORS_ORIGINS env var)
allowed_origins = [
    o.strip() for o in settings.cors_origins.split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(oauth.router)
app.include_router(agencies.router)
app.include_router(clients.router)
app.include_router(users.router)
app.include_router(accounts.router)
app.include_router(journal.router)
app.include_router(bank.router)
app.include_router(reports.router)
app.include_router(documents.router)
app.include_router(ai.router)
app.include_router(agent.router)
app.include_router(payroll.router)
app.include_router(integrations.router)
app.include_router(billing_stripe.router)
app.include_router(onboarding.router)
app.include_router(dsr.router)


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="1.4.0")


@app.get("/")
async def root():
    return {"message": "BPO Nexus API", "version": "1.4.0", "docs": "/docs"}

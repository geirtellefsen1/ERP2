from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.routers import agencies, clients, users, auth, accounts, journal, bank, reports, documents, ai, agent, payroll, leave, filing, hospitality, services, forecast

app = FastAPI(
    title="BPO Nexus API",
    version="2.0.0",
    description="AI-First Business Process Outsourcing Platform — Full Build Complete",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in [
    auth.router, agencies.router, clients.router, users.router,
    accounts.router, journal.router, bank.router, reports.router,
    documents.router, ai.router, agent.router,
    payroll.router, leave.router, filing.router,
    hospitality.router, services.router, forecast.router,
]:
    app.include_router(router)


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="2.0.0")


@app.get("/")
async def root():
    return {"message": "BPO Nexus API", "version": "2.0.0", "docs": "/docs", "repo": "geirtellefsen1/ERP2"}

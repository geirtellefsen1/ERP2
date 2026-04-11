from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.routers import agencies, clients, users, auth, accounts, journal, bank, reports

app = FastAPI(
    title="BPO Nexus API",
    version="0.8.0",
    description="AI-First Business Process Outsourcing Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(agencies.router)
app.include_router(clients.router)
app.include_router(users.router)
app.include_router(accounts.router)
app.include_router(journal.router)
app.include_router(bank.router)
app.include_router(reports.router)


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="0.8.0")


@app.get("/")
async def root():
    return {"message": "BPO Nexus API", "version": "0.8.0", "docs": "/docs"}


@app.get("/api/v1")
async def api_root():
    return {
        "version": "1",
        "auth": "/api/v1/auth",
        "agencies": "/api/v1/agencies",
        "clients": "/api/v1/clients",
        "users": "/api/v1/users",
        "accounts": "/api/v1/accounts",
        "journal": "/api/v1/journal",
        "banking": "/api/v1/banking",
        "reports": "/api/v1/reports",
    }

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.routers import agencies, clients, users
from app.config import get_settings

app = FastAPI(
    title="BPO Nexus API",
    version="0.2.0",
    description="AI-First Business Process Outsourcing Platform — Agency Command Centre",
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(agencies.router)
app.include_router(clients.router)
app.include_router(users.router)


# ─── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="0.2.0")


@app.get("/")
async def root():
    return {"message": "BPO Nexus API", "version": "0.2.0", "docs": "/docs"}


@app.get("/api/v1")
async def api_root():
    return {
        "version": "1",
        "agencies": "/api/v1/agencies",
        "clients": "/api/v1/clients",
        "users": "/api/v1/users",
    }

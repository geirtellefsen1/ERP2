# Developer Onboarding

Welcome to ClaudERP. This guide will get you from zero to running the full stack locally.

## Prerequisites

- Python 3.12+
- Node.js 18+ and pnpm
- Docker and Docker Compose
- Git

## 1. Clone the Repository

```bash
git clone https://github.com/geirtellefsen1/bpo-nexus.git
cd bpo-nexus
```

## 2. Environment Setup

```bash
cp .env.example .env
```

Edit `.env` and fill in the required values. At minimum you need:
- `DATABASE_URL` — PostgreSQL connection string (Docker Compose provides a default)
- `REDIS_URL` — Redis connection string (Docker Compose provides a default)
- `SECRET_KEY` — JWT signing key (generate with `openssl rand -hex 32`)

## 3. Start Services

```bash
docker compose up -d
```

This starts:
- PostgreSQL 16 on port 5432
- Redis 7 on port 6379
- FastAPI backend on port 8000
- Next.js frontend on port 3000

## 4. Run Database Migrations

```bash
cd apps/api
alembic upgrade head
```

## 5. Verify Everything Works

```bash
# API health check
curl http://localhost:8000/health
# Expected: {"status":"ok"}

# Swagger API docs
open http://localhost:8000/docs

# Web dashboard
open http://localhost:3000
```

## 6. Run Tests

```bash
# API test suite (~27 test modules)
cd apps/api
pip install -r requirements.txt
pytest tests/ -v

# Web tests
cd apps/web
pnpm install
pnpm test
```

## Project Layout

| Directory               | What lives here                              |
|-------------------------|----------------------------------------------|
| `apps/api/app/`         | FastAPI application code                     |
| `apps/api/app/routers/` | REST endpoint definitions                   |
| `apps/api/app/services/`| Business logic (auth, banking, payroll, etc) |
| `apps/api/app/models.py`| SQLAlchemy ORM models                        |
| `apps/api/alembic/`     | Database migration files                     |
| `apps/api/tests/`       | Pytest test suite                            |
| `apps/web/`             | Next.js 14 frontend                          |
| `apps/mobile/`          | Expo React Native mobile app                 |
| `packages/shared/`      | Shared TypeScript types                      |
| `infra/`                | Docker, Terraform, Cloudflare configs        |
| `docs/`                 | Architecture docs, ADRs, compliance, runbooks|

## Key Concepts

- **Multi-tenancy:** All data is scoped by `agency_id`. Row-level security enforces isolation at the database level.
- **Jurisdictions:** Tax rules, VAT rates, and filing logic are encapsulated per country in `app/jurisdictions/` (Norway, Sweden, Finland).
- **5-tier services:** Core -> Accounting -> Banking -> Verticals -> Integrations. Each tier builds on the one below.
- **Auth:** Custom JWT with refresh-token rotation. See [ADR 0001](adr/0001-custom-jwt-over-auth0.md).

## Useful Links

- [Architecture Overview](architecture.md)
- [Deployment Guide](deploy.md)
- [Jurisdiction Pivot](pivot.md)
- [ADR Index](adr/)
- [API Docs (local)](http://localhost:8000/docs)

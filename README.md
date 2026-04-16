# ClaudERP — AI-First Nordic Accounting BPO Platform

> Built by **Saga Advisory AS** | Live at [erp.tellefsen.org](https://erp.tellefsen.org)

**Stack:** FastAPI (Python 3.12) · Next.js 14 · Expo (React Native) · PostgreSQL 16 · Redis 7 · Claude API

---

## Architecture Overview

| Layer     | Technology           | Description                                      |
|-----------|----------------------|--------------------------------------------------|
| **API**   | FastAPI              | REST backend with 5-tier service architecture    |
| **Web**   | Next.js 14           | App Router dashboard for accountants and clients |
| **Mobile**| Expo (React Native)  | iOS/Android app for on-the-go access             |
| **Infra** | Docker, Terraform    | DigitalOcean deployment with Cloudflare CDN      |
| **DB**    | PostgreSQL 16        | Multi-tenant with row-level security             |
| **Cache** | Redis 7              | Session management, refresh-token revocation     |
| **AI**    | Claude API           | Document processing, anomaly detection, chat     |

The API follows a 5-tier architecture: **core** (auth, tenancy) -> **accounting** (journals, chart of accounts) -> **banking** (reconciliation, open banking) -> **verticals** (hospitality, professional services) -> **integrations** (Aiia, Stripe, WhatsApp).

---

## Phase Progress

| Phase | Scope                              | Status      |
|-------|-------------------------------------|-------------|
| P1    | Auth, multi-tenancy, core API       | In Progress |
| P2    | Accounting engine, bank recon       | In Progress |
| P3    | Verticals, payroll, filing          | In Progress |
| P4    | AI features, document processing    | Planned     |
| P5    | Mobile app, client portal           | Planned     |

---

## Quick Start

```bash
# 1. Clone and enter
git clone https://github.com/geirtellefsen1/bpo-nexus.git
cd bpo-nexus

# 2. Copy environment config
cp .env.example .env

# 3. Start all services
docker compose up -d

# 4. Verify
curl http://localhost:8000/health          # {"status":"ok"}
open http://localhost:3000                 # Web dashboard
open http://localhost:8000/docs            # Swagger API docs
```

---

## Testing

```bash
# Run the full API test suite (~27 modules)
cd apps/api
pip install -r requirements.txt
pytest tests/ -v

# Run web tests
cd apps/web
pnpm install && pnpm test
```

---

## Project Structure

```
ClaudERP/
├── apps/
│   ├── api/                FastAPI backend
│   │   ├── app/
│   │   │   ├── main.py     App entry point + router registration
│   │   │   ├── routers/    REST endpoints (auth, journal, billing, ...)
│   │   │   ├── services/   Business logic (auth, banking, payroll, ...)
│   │   │   ├── jurisdictions/  NO/SE/FI tax and compliance rules
│   │   │   └── models.py   SQLAlchemy models
│   │   ├── alembic/        Database migrations
│   │   └── tests/          Pytest test suite
│   ├── web/                Next.js 14 frontend
│   └── mobile/             Expo React Native app
├── packages/
│   └── shared/             Shared TypeScript types
├── infra/
│   ├── docker/             Dockerfiles
│   ├── terraform/          DigitalOcean IaC
│   ├── cloudflare/         CDN and DNS config
│   └── uptime/             Health check probes
├── docs/                   Architecture, compliance, runbooks
├── docker-compose.yml
└── .env.example
```

---

## Documentation

See the [docs/](docs/) directory:

- [Architecture](docs/architecture.md) — system architecture overview
- [Deployment](docs/deploy.md) — deployment guide
- [Developer Onboarding](docs/developer-onboarding.md) — getting started
- [Jurisdiction Pivot](docs/pivot.md) — ZA/NO/UK to NO/SE/FI pivot
- [ADRs](docs/adr/) — architecture decision records
- [Compliance](docs/compliance/) — RoPA, DPIA
- [Runbooks](docs/runbooks/) — incident response, breach notification
- [SLA](docs/public/sla.md) — service level agreement

---

## Key Integrations

| Service         | Purpose                          |
|-----------------|----------------------------------|
| Claude API      | AI document processing and chat  |
| Aiia (Mastercard) | Nordic open banking            |
| Stripe          | Subscription billing             |
| BankID          | Norwegian/Swedish authentication |
| Altinn          | Norwegian tax filing             |
| Skatteverket    | Swedish tax filing               |

---

## License

Confidential — Saga Advisory AS 2026

# BPO Nexus

> AI-First Business Process Outsourcing Platform — built by Saga Advisory AS

**Stack:** FastAPI · Next.js 14 · PostgreSQL 16 · Redis 7 · Docker · Terraform · Claude API

---

## 🚀 Quick Start

```bash
# 1. Clone & enter
git clone https://github.com/geirtellefsen1/bpo-nexus.git
cd bpo-nexus

# 2. Start all services
docker compose up -d

# 3. Verify
curl http://localhost:8000/health     → {"status":"ok"}
open http://localhost:3000           → BPO Nexus landing page
open http://localhost:8000/docs       → Swagger API docs
```

---

## 📁 Project Structure

```
bpo-nexus/
├── apps/
│   ├── api/               FastAPI backend (Python 3.12)
│   │   ├── app/
│   │   │   ├── main.py    FastAPI app entry point
│   │   │   ├── config.py  Pydantic settings
│   │   │   └── models.py  SQLAlchemy models
│   │   └── requirements.txt
│   └── web/               Next.js 14 frontend
│       ├── app/           App Router pages
│       └── package.json
├── packages/
│   └── shared/            Shared TypeScript types
├── infra/
│   ├── docker/            Dockerfiles
│   └── terraform/         DigitalOcean IaC
├── docker-compose.yml
└── .env.example
```

---

## 📋 Sprint Progress

| Sprint | Goal                        | Status |
|--------|-----------------------------|--------|
| 1      | Project scaffold            | ✅ Done |
| 2      | Database schema + migrations | 🔜 Next |
| ...    | ...                         | ...    |

Full plan: 22 sprints across 5 phases (see BPO Nexus Master Build Prompt)

---

## 🔑 Key APIs & Credentials

| Service        | Purpose                        | Config via |
|----------------|--------------------------------|------------|
| Auth0          | JWT auth, SSO, MFA             | `.env`     |
| Claude API     | AI processing layer            | `.env`     |
| DigitalOcean   | Droplets, DB, Spaces, DNS       | Terraform  |
| Twilio         | WhatsApp (via OpenClaw)        | `.env`     |
| Resend         | Transactional email            | `.env`     |
| TrueLayer      | Open Banking (UK/EU)           | `.env`     |
| AWS Textract   | Document OCR                   | `.env`     |

---

## 🧪 Testing

```bash
# API
cd apps/api && pip install -q pytest pytest-asyncio && pytest tests/ -v

# Web
cd apps/web && pnpm test
```

---

## 📜 License

Confidential — Saga Advisory AS © 2026


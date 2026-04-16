# ClaudERP Architecture

## System Overview

```
                          ┌─────────────────┐
                          │   Cloudflare     │
                          │   CDN / DNS      │
                          └────────┬────────┘
                                   │
                 ┌─────────────────┼─────────────────┐
                 │                 │                  │
          ┌──────▼──────┐  ┌──────▼──────┐  ┌───────▼──────┐
          │  Next.js 14 │  │   FastAPI   │  │  Expo Mobile │
          │  Web App    │  │   REST API  │  │  iOS/Android │
          │  :3000      │  │   :8000     │  │              │
          └─────────────┘  └──────┬──────┘  └──────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │              │
             ┌──────▼──────┐ ┌───▼────┐ ┌───────▼───────┐
             │ PostgreSQL  │ │ Redis  │ │  Celery       │
             │ 16          │ │ 7      │ │  Workers      │
             │ :5432       │ │ :6379  │ │               │
             └─────────────┘ └────────┘ └───────────────┘
```

## Application Layer

### API (FastAPI)
The backend follows a 5-tier service architecture:

```
Tier 1: Core
  └── Auth, tenancy, RBAC, secrets management

Tier 2: Accounting
  └── Chart of accounts, journal entries, general ledger

Tier 3: Banking
  └── Bank reconciliation, open banking (Aiia), payment processing

Tier 4: Verticals
  └── Hospitality, professional services, industry-specific logic

Tier 5: Integrations
  └── Aiia, Stripe, WhatsApp, Claude AI, BankID, tax filing
```

### Web (Next.js 14)
- App Router with server components
- Dashboard for accountants and agency administrators
- Client portal for end-customer access
- Cookie consent and GDPR compliance built in

### Mobile (Expo)
- React Native app for iOS and Android
- Mirrors key dashboard functionality for on-the-go access

## Data Layer

### PostgreSQL 16
- Multi-tenant architecture with row-level security (RLS)
- Agency-scoped data isolation via `agency_id`
- Alembic migrations (currently 14 migration files)
- TimescaleDB hypertables for time-series financial data

### Redis 7
- Refresh token storage and revocation
- Rate limiting
- Session caching
- Celery task broker

## External Integrations

| Integration       | Purpose                                    |
|-------------------|--------------------------------------------|
| **Aiia**          | Nordic open banking (account data, payments)|
| **Stripe**        | Subscription billing and webhook handling  |
| **Claude API**    | Document OCR, anomaly detection, AI chat   |
| **BankID**        | Strong authentication (Norway, Sweden)     |
| **Altinn**        | Norwegian government tax filing API        |
| **Skatteverket**  | Swedish tax authority integration          |
| **WhatsApp**      | Client communication channel               |

## Jurisdictions

The platform supports three Nordic jurisdictions with dedicated rule engines:

- **Norway (NO)** — MVA (VAT), Altinn filing, SAF-T, Norwegian chart of accounts
- **Sweden (SE)** — Moms (VAT), Skatteverket filing, SIE format, BAS chart of accounts
- **Finland (FI)** — ALV (VAT), Vero filing, Finnish chart of accounts

Each jurisdiction module (`app/jurisdictions/`) encapsulates tax rates, filing rules, payroll calculations, and compliance requirements.

## Infrastructure

- **Hosting:** DigitalOcean Droplets
- **CDN/DNS:** Cloudflare
- **IaC:** Terraform for provisioning
- **CI/CD:** GitHub Actions
- **Monitoring:** Uptime probes, status page
- **HA Plan:** Read replica database, multi-replica API (ADR 0002)

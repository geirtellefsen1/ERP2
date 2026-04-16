# Deployment Guide

## Overview

ClaudERP is deployed on DigitalOcean infrastructure, fronted by Cloudflare for CDN and DNS. The live instance runs at [erp.tellefsen.org](https://erp.tellefsen.org).

## Detailed Deployment Instructions

See [JR-DEPLOYMENT.md](../JR-DEPLOYMENT.md) in the repository root for the full deployment runbook, including:

- DigitalOcean Droplet provisioning
- Docker container deployment
- Database setup and migrations
- SSL/TLS configuration
- Environment variable management
- Domain and DNS configuration via Cloudflare

## Architecture

```
GitHub (push to main)
  └── GitHub Actions CI
        └── Build + Test
              └── Deploy to DigitalOcean
                    ├── API container (FastAPI)
                    ├── Web container (Next.js)
                    ├── PostgreSQL 16
                    ├── Redis 7
                    └── Celery workers
```

## Infrastructure as Code

Terraform configurations live in `infra/terraform/` and manage:
- DigitalOcean Droplets
- Managed PostgreSQL database
- DNS records
- Firewall rules

## Quick Deploy Checklist

1. Ensure `.env` is configured with all required secrets (see `.env.example`)
2. Run database migrations: `alembic upgrade head`
3. Build and push Docker images
4. Deploy via `docker compose up -d` on the target server
5. Verify health: `curl https://erp.tellefsen.org/health`

## High Availability

See [ADR 0002](adr/0002-ha-db-and-api.md) for the planned HA architecture with read replicas and multi-replica API.

## Monitoring

- Uptime probes configured in `infra/uptime/`
- Status page available for service health monitoring
- Incident runbook: [runbooks/incident.md](runbooks/incident.md)

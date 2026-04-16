# ADR 0002: High Availability — Database Read Replica + Multi-Replica API

## Status
Proposed

## Context
ClaudERP runs on a single DigitalOcean droplet with one PostgreSQL instance and one API process. A single hardware failure or deployment error causes total downtime. For production readiness with paying customers, we need:
- Database resilience: survive a primary failure without data loss
- API resilience: survive a single instance failure without downtime
- Zero-downtime deployments

## Decision
1. **Database**: Add a DigitalOcean Managed PostgreSQL read replica. The replica is promoted automatically by DO if the primary fails. Read-heavy queries (reports, dashboards) can be routed to the replica.
2. **API**: Run 2+ API replicas behind a DigitalOcean Load Balancer. Health checks on /health determine routing.
3. **Redis**: Keep single instance for now (refresh token revocation is not critical enough to warrant Redis Sentinel). Document upgrade path.

## Consequences
- Monthly cost increases ~$40 (1 read replica + 1 extra API droplet + LB)
- Application must handle read-replica lag (eventual consistency for reports is acceptable)
- Deployments become rolling (drain → deploy → health check → route)
- Failover runbook needed at docs/runbooks/failover.md

## Revisit Triggers
- >1000 concurrent users → add API auto-scaling
- >100GB database → evaluate pgBouncer connection pooling
- Redis downtime incidents → upgrade to Redis Sentinel or KeyDB

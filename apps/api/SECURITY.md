# ClaudERP API — security posture

Last full review: **2026-04-13** (Tier 5 release gate)

This file documents the security-relevant choices in the API and the
dependency CVE status at release time. Update it when packages bump,
when a new pip-audit run finds something new, or when a mitigation
changes.

## 1. Dependency CVE scan

Run `pip-audit -r requirements.txt` from `apps/api/`. Results at
release time, after the Tier 5 security bumps:

| Package            | Version | CVE              | Fix version | Status in ClaudERP |
|--------------------|---------|------------------|-------------|--------------------|
| `python-jose`      | 3.4.0   | PYSEC-2024-232/3 | 3.4.0       | **FIXED** |
| `python-multipart` | 0.0.22  | CVE-2024-53981   | 0.0.18      | **FIXED** |
| `python-multipart` | 0.0.22  | CVE-2026-24486   | 0.0.22      | **FIXED** |
| `fastapi`          | 0.115.14| —                | —           | Latest in 0.115.x line |
| `starlette`        | 0.46.2  | CVE-2024-47874   | 0.40.0      | **FIXED** (via fastapi 0.115.14) |
| `starlette`        | 0.46.2  | CVE-2025-54121   | 0.47.2      | **Residual** — needs fastapi >= 0.116 |
| `starlette`        | 0.46.2  | CVE-2025-62727   | 0.49.1      | **Residual** — needs fastapi >= 0.120 |
| `pyasn1`           | 0.4.8   | CVE-2026-30922   | 0.6.3       | **Residual** — blocked by python-jose 3.4.0 (pins pyasn1 <0.5.0) |
| `pytest`           | 8.3.3   | CVE-2025-71176   | 9.0.3       | **Residual** — dev-only, not shipped in production image |

### Residual risk rationale

- **starlette CVE-2025-54121 / CVE-2025-62727** — both require a
  FastAPI major version bump (>= 0.116). The 0.116+ line tightens a
  number of runtime type checks and is worth a dedicated upgrade
  sprint, not a rushed release-time bump. Both CVEs are
  information-disclosure class (not RCE), and the mitigating controls
  in ClaudERP (RLS, per-agency JWT signing, rate limiting) reduce the
  blast radius. **Tracked for Tier 6.**

- **pyasn1 CVE-2026-30922** — pinned transitively by
  python-jose 3.4.0 (`pyasn1<0.5.0,>=0.4.1`). The CVE is a
  denial-of-service in the BER decoder. ClaudERP only decodes BER
  payloads it has produced itself (JWT signing), so a malicious
  payload would need to originate inside our own trust boundary to
  trigger it. **Revisited once python-jose publishes a release that
  relaxes the pyasn1 pin.**

- **pytest CVE-2025-71176** — development-only. `pytest` is not
  installed in the production Docker image. Verify this by
  inspecting `docker-compose.prod.yml` + the api Dockerfile; the
  production build stage should use `--no-dev` (uv) or a dedicated
  runtime requirements file. No runtime exposure.

## 2. Code-level controls

### 2.1 Tenancy isolation

- **Row-Level Security** (migration 006) on every tenant-scoped table.
  `tenant_isolation` policy filters rows by
  `current_setting('app.current_agency_id')`.
- Every HTTP request goes through `set_tenant_context(db,
  current_user.agency_id)` before any tenant query. Background tasks
  set the same variable inside their own sessions.
- The Postgres app role (`claud_erp_app`) is created with
  `NOBYPASSRLS` so superuser bypass is not available to live traffic.
  Migrations and background jobs run as the superuser role
  (`claud_erp`) which does bypass — this is why tenant-scope code
  must set `app.current_agency_id` explicitly; the test
  `test_rls_denies_without_session_variable` proves the fail-safe.

### 2.2 Integration secrets

- All per-agency secrets live in `integration_configs`
  (migration 009) under Fernet symmetric encryption.
  `app/services/secrets.py` owns the key derivation and encryption
  functions. `INTEGRATION_SECRETS_KEY` env var must be set in every
  environment above local dev — the service refuses to start if it
  sees the dev-placeholder key in production.
- Display-side masking goes through `svc.mask_for_display()`; secret
  values are **never** returned to the UI, only masked values like
  `••••1234`.
- The integration settings UI (`/dashboard/settings` →
  Integrations) treats empty strings as "don't change", so users can
  save a form without re-entering secrets they cannot see.

### 2.3 JWT signing

- Dedicated `JWT_SIGNING_KEY` (HMAC-SHA-256), never reused from any
  other provider's API key.
- Dev/test mode derives a stable placeholder key from a known constant
  **with a loud startup warning**. Production enforces
  `len(key) >= 32` at boot time; the app refuses to start otherwise.

### 2.4 Rate limiting

- Per-IP rate limiting on `/auth/login` and `/auth/register` via
  Redis (see `services/rate_limit.py`). Defaults: 10/min login,
  30/min general.
- Configurable per-environment via `RATE_LIMIT_*` settings.

### 2.5 File storage

- Local storage (dev/tests) enforces path-traversal defense: any key
  containing `..`, leading `/`, or that resolves outside the base
  directory is rejected with `StorageError`.
- DO Spaces uses private ACLs + presigned URLs with a configurable
  TTL. The API never streams file bytes through itself in production
  — the frontend follows the presigned URL directly.

### 2.6 Banking + BankID adapters

- Aiia adapter refuses to call any endpoint without an `access_token`;
  all live callers go through integration_configs and hit the
  decryption code path.
- BankID adapters are stubbed through a mock until the vendor
  certificates are in place. The real adapter will accept mTLS
  client certs from `BANKID_CERT_PATH`, not from a database row.

## 3. Operational checklist for a production deploy

- [ ] `INTEGRATION_SECRETS_KEY` is a 32-byte random Fernet key,
      *not* the dev placeholder.
- [ ] `JWT_SIGNING_KEY` is ≥ 32 bytes (`openssl rand -hex 32`).
- [ ] `DATABASE_URL` points at the app role (`claud_erp_app`,
      `NOBYPASSRLS`), not the superuser role.
- [ ] Alembic `upgrade head` has been run against the target DB,
      including migration 010 (TimescaleDB hypertables — the
      migration degrades gracefully on vanilla Postgres).
- [ ] TLS terminates at the load balancer; no plaintext HTTP ever
      hits the API container.
- [ ] Redis is not exposed to the public internet.
- [ ] `RATE_LIMIT_*` values are reviewed for the expected traffic.
- [ ] Sentry or equivalent error reporting is wired up.
- [ ] The production docker image does NOT include `pytest`,
      `pip-audit`, or any dev tooling.

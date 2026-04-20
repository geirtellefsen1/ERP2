# JR — Full Redeploy from Scratch (commit `899f2c9`)

Complete redeploy prompt for ClaudERP. This replaces both
`JR-SPRINT-4.md` and `JR-SPRINT-4-HOTFIX.md` — it's a single
end-to-end runbook covering build, push, deploy, migrate, and verify.

---

## What's deployed

**Branch:** `claude/erp-job-breakdown-3eCnk`
**Commit:** `899f2c9` — `feat(ehf): hotel Q1 demo baseline + full NS 4102 hotel kontoplan`
**Target:** `erp.tellefsen.org` (DigitalOcean droplet `45.55.44.133`)

### What's in this version (cumulative)

- **Full NS 4102 hotel kontoplan** — ~95 accounts covering a legacy
  Norwegian hotel: departmental revenue (rom 12%, mat 15%, drikke 25%),
  split output VAT (2720/2725/2728), equity accounts (2010/2050),
  hotel-specific COGS/OPEX (vaskeri, rengjøring, Booking.com provisjon, etc.)
- **Hotel Q1 demo baseline** — 7 journal entries seeding realistic
  opening balance (19.895M) + 3 months of revenue, payroll, COGS, OPEX
  so P&L and Balance Sheet have meaningful data before EHF import
- **Auto-COA-seeding** — import flow auto-seeds NS 4102 if client has
  zero accounts (no more "Missing account 2400" errors)
- **EHF import** — full 4-step wizard: upload → preview → book → reports
- **10 hotel-specific sample suppliers** — Asko, Hafslund, Telenor,
  Vectura Vinmonopolet, Gjensidige, Norsk Vaskeri, Lilleborg,
  Booking.com, Securitas, Nordea
- **Client PATCH security fix** — multi-tenant isolation on client edits
- **OpenClaw WhatsApp prompts** — nb/sv/fi/en system prompts

---

## Critical deployment context

Read this section fully before starting.

### Port 8003 — do not use 8000

**Host port 8000 is held by `hydra-engine` (Energy-RT).** ClaudERP API
runs on host port **8003**, mapped to container-internal port 8000.

The `docker-compose.prod.yml` on the droplet MUST have `"8003:8000"` for
the API service. The repo copy may still say `"8000:8000"` — **never
overwrite the droplet copy** with the repo version without checking this.

### Nginx proxy

`/etc/nginx/sites-available/erp.tellefsen.org` must proxy `/api/*` to
`http://127.0.0.1:8003` (not 8000). A backup exists as
`.bak-sprint4`. Verify after deploy:

```bash
grep proxy_pass /etc/nginx/sites-available/erp.tellefsen.org
# Must show: proxy_pass http://127.0.0.1:8003;
```

### Build args — MANDATORY for web image

Next.js bakes `NEXT_PUBLIC_API_URL` at **build time**. If you skip the
`--build-arg` flags, the bundle defaults to `http://localhost:8000` and
login shows "Cannot connect to server." This is the #1 deployment bug
we've hit twice already.

### Migrations

Run `alembic upgrade head` after deploy. The `mfa_secret` column
(and any other pending migrations) must be applied or login will 500.

---

## Step 1 — Build images (on Donald)

```bash
cd ~/code/erp2
git fetch origin
git checkout claude/erp-job-breakdown-3eCnk
git pull origin claude/erp-job-breakdown-3eCnk

# Confirm correct commit
git log -1 --oneline
# Expected: 899f2c9 feat(ehf): hotel Q1 demo baseline + full NS 4102 hotel kontoplan

APP_URL="https://erp.tellefsen.org"
TAG="899f2c9"

# ── API image (no build args needed) ──
docker build -f infra/docker/Dockerfile.api \
  -t registry.digitalocean.com/claud-erp/api:$TAG .

# ── WEB image (BOTH build args are MANDATORY) ──
docker build -f infra/docker/Dockerfile.web \
  --build-arg NEXT_PUBLIC_API_URL=$APP_URL \
  --build-arg NEXT_PUBLIC_APP_URL=$APP_URL \
  -t registry.digitalocean.com/claud-erp/web:$TAG .

# ── Push to registry ──
docker push registry.digitalocean.com/claud-erp/api:$TAG
docker push registry.digitalocean.com/claud-erp/web:$TAG
```

---

## Step 2 — Deploy on droplet

```bash
ssh root@45.55.44.133
cd /opt/claud-erp

# ── Verify compose file port mapping ──
grep -n '8003:8000\|8000:8000' docker-compose.prod.yml
# MUST show 8003:8000 for the API service.
# If it shows 8000:8000, edit it to 8003:8000 BEFORE proceeding.

# ── Pull new images ──
TAG="899f2c9"
export TAG
docker compose -f docker-compose.prod.yml pull api web

# ── Stop and restart ──
docker compose -f docker-compose.prod.yml up -d api web

# ── Run database migrations ──
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
# This applies mfa_secret column + any other pending migrations.

# ── Wait for health ──
sleep 8
docker compose -f docker-compose.prod.yml ps
# Both api and web should show "Up" / "healthy"
```

---

## Step 3 — Verify nginx

```bash
# Confirm nginx points to 8003
grep proxy_pass /etc/nginx/sites-available/erp.tellefsen.org
# Expected: proxy_pass http://127.0.0.1:8003;

# Confirm hydra-engine is still running on 8000
ss -tlnp | grep 8000
# Expected: hydra-engine / Energy-RT process — leave it alone

# Confirm ClaudERP API on 8003
ss -tlnp | grep 8003
# Expected: docker-proxy for claud-erp-api
```

---

## Step 4 — Smoke tests

```bash
# Health endpoint
curl -sf https://erp.tellefsen.org/health | jq
# Expected: {"status": "ok", ...}

# Sample invoices endpoint
curl -s https://erp.tellefsen.org/api/v1/ehf/sample-invoices | jq '. | length'
# Expected: 10

# First supplier name
curl -s https://erp.tellefsen.org/api/v1/ehf/sample-invoices | jq '.[0].supplier_name'
# Expected: a Norwegian hotel supplier (Asko, Hafslund, etc.)
```

---

## Step 5 — Full verification flow

### 5.1 — Login

Open `https://erp.tellefsen.org/login` in a **private/incognito** window.

- Email: `demo@claud-erp.com`
- Password: `demo1234`

Must redirect to `/dashboard` without "Cannot connect to server."
If it shows that error, the web image was built without `--build-arg` — go back to Step 1.

### 5.2 — Load Q1 Demo Baseline

1. In TopBar, select a Norwegian client (or create one: `Demo Hotell AS`, country NO).
2. Sidebar → Finance → **EHF Import**.
3. On the Upload step, find the amber panel "Load Q1 Baseline" and click it.
4. Expected result:
   - `seeded: true`
   - `entries: 7` journal entries created
   - `period: "Q1 2026"`
   - `hotel_name: "Fjordview Grand Hotel"`
5. Now go to Finance → **Reports**:
   - **P&L** should show revenue (~2.2M) and expenses across hotel departments
   - **Balance Sheet** should show assets = liabilities + equity (~19.895M opening + Q1 activity)
   - `check: true` (balance sheet balances)

### 5.3 — Import 10 Sample EHF Invoices

1. Go back to Finance → **EHF Import**.
2. Click "Load 10 Sample Invoices" → preview table populates.
3. Click **Book all to ledger**.
4. Expected on the "Booked" step:
   - Invoices booked: **10 / 10**
   - Journal entries: **10**
   - Zero errors
   - All entries show balanced indicator
5. Click **Next: Reports**:
   - P&L expenses should have **increased** by the net amount of the 10 invoices
   - Balance Sheet: `2400 Leverandørgjeld` (liability) increased by gross totals
   - `check: true` still holds

### 5.4 — Idempotency checks

- Loading Q1 baseline a second time on the same client should be refused
  ("Client already has journal entries").
- Loading sample invoices a second time should still work but should NOT
  re-seed the COA (no "auto-seeded" notice, since accounts already exist).

### 5.5 — DB sanity check

```bash
docker compose -f docker-compose.prod.yml exec api \
  psql $DATABASE_URL -c \
  "SELECT c.name, COUNT(a.id) AS accounts, \
          (SELECT COUNT(*) FROM journal_entries je WHERE je.client_id = c.id) AS entries \
   FROM clients c \
   LEFT JOIN accounts a ON a.client_id = c.id \
   GROUP BY c.id, c.name \
   ORDER BY accounts;"
```

Demo client should show ~95 accounts and ≥17 journal entries (7 baseline + 10 samples).

---

## Rollback

If anything goes sideways, roll back to the last known-good commit:

```bash
ssh root@45.55.44.133
cd /opt/claud-erp
TAG=3a110dd   # previous hotfix version
export TAG
docker compose -f docker-compose.prod.yml pull api web
docker compose -f docker-compose.prod.yml up -d api web
```

No DB changes to revert — journal entries and accounts created are all
valid double-entry bookkeeping rows. They're safe to keep. If you want
to purge demo data for a specific client:

```sql
-- Replace <client_id> with the actual ID
DELETE FROM journal_lines WHERE entry_id IN (
  SELECT id FROM journal_entries WHERE client_id = <client_id>
);
DELETE FROM journal_entries WHERE client_id = <client_id>;
DELETE FROM accounts WHERE client_id = <client_id>;
```

---

## Troubleshooting quick reference

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Cannot connect to server" on login | Web image built without `--build-arg` | Rebuild web image with both `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_APP_URL` set to `https://erp.tellefsen.org` |
| Login 500 / `mfa_secret` error | Migration not applied | `docker compose exec api alembic upgrade head` |
| "Missing account 2400" on import | Should be auto-fixed now; if still happens, COA seed failed | Check API logs: `docker compose logs api --tail=50` |
| API unreachable / 502 | Port mapping wrong | Verify `docker-compose.prod.yml` has `8003:8000`, nginx has `proxy_pass http://127.0.0.1:8003` |
| hydra-engine down | Someone overwrote port 8000 | Check `ss -tlnp \| grep 8000` — ClaudERP must NOT be on 8000 |

---

## Report back

After deploy, post to Telegram:

1. Commit hash: `docker compose -f docker-compose.prod.yml exec api cat /app/.git-commit 2>/dev/null || echo "check registry tag"`
2. `docker compose -f docker-compose.prod.yml ps` output
3. Screenshot or text from verification 5.2 (baseline loaded, 7 entries)
4. Screenshot or text from verification 5.3 (10/10 invoices booked)
5. Balance sheet `check: true` confirmation
6. DB sanity check output (accounts + entries count)
7. Error scan: `docker compose logs api --tail=200 | grep -iE "error|traceback"`

🦞

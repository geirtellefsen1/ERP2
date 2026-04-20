# JR — Sprint 4 Hotfix #2 (EHF COA Upsert)

Drop-in deploy prompt for the follow-up hotfix. Stacks on top of the
already-deployed `899f2c9`.

---

## What's in this hotfix

**Branch:** `claude/erp-job-breakdown-3eCnk`
**Minimum commit:** `ef48b22` or newer
**Previous deployed commit:** `899f2c9`

### The bug

EHF sample import was still failing with "Missing account 2400
(Leverandørgjeld). Seed chart of accounts first." — all 10 invoices
errored out. Root cause: the client had a **partial** chart of accounts
(leftover from the earlier 43-account NS 4102 template or an aborted
seed). The previous `_ensure_coa_seeded` helper skipped seeding entirely
if the client had ANY accounts, so the missing 2400 / 2710 / 2720 etc.
were never added.

### The fix

- **`apps/api/app/routers/ehf.py`**: `_ensure_coa_seeded` now **upserts
  by code** — adds template accounts that don't already exist, leaves
  existing accounts and their `parent_id` links untouched. Safe for
  clients with custom or partial COAs.
- Notice string now distinguishes "auto-seeded" (empty COA) from
  "topped up" (partial COA) so you can see what happened.

### Migrations

**None.** Pure code fix.

### Files changed

- `apps/api/app/routers/ehf.py` (only `_ensure_coa_seeded` function)
- Web image **does not need rebuild** — no frontend changes.

---

## Operational context

Unchanged from previous hotfix:

- Host port 8000 → `hydra-engine` (Energy-RT). Leave it alone.
- `claud-erp-api` on host port **8003** (container-internal 8000).
- Nginx proxies `/api/*` to `http://127.0.0.1:8003`.

---

## Deploy steps

```bash
# ── 1. On the build machine (Donald) ──────────────────────────────

cd ~/code/erp2
git fetch origin
git checkout claude/erp-job-breakdown-3eCnk
git pull
SHA=$(git rev-parse --short HEAD)
echo "Building $SHA"     # should be ef48b22 or newer

TAG=$SHA

# API image only — web doesn't need rebuild
docker build -f infra/docker/Dockerfile.api \
  -t registry.digitalocean.com/claud-erp/api:$TAG .

docker push registry.digitalocean.com/claud-erp/api:$TAG

# ── 2. On the droplet ─────────────────────────────────────────────

ssh root@45.55.44.133
cd /opt/claud-erp

# Verify compose still has 8003:8000 for API
grep -n '8003:8000\|"8000:8000"' docker-compose.prod.yml

# Pull + restart ONLY the api container
TAG=ef48b22
export TAG
docker compose -f docker-compose.prod.yml pull api
docker compose -f docker-compose.prod.yml up -d api

# Wait for health
sleep 8
docker compose -f docker-compose.prod.yml ps
```

---

## Verification

### 1. Smoke test

```bash
curl -sf https://erp.tellefsen.org/health | jq
# Expected: {"status": "ok", ...}

curl -s https://erp.tellefsen.org/api/v1/ehf/sample-invoices | jq '. | length'
# Expected: 10
```

### 2. The actual fix — retry the failing import

1. Log in at `https://erp.tellefsen.org` as `demo@claud-erp.com` /
   `demo1234`.
2. In TopBar, select the **same client that failed last time** (the
   one that showed all 10 "Missing account 2400" errors).
3. Sidebar → Finance → **EHF Import**.
4. Click "Load 10 Sample Invoices" → preview populates.
5. Click **Book all to ledger**.
6. Expected on the "Booked" step:
   - Invoices booked: **10 / 10**
   - Journal entries: **10**
   - **Blue notice box**:
     `Chart of accounts topped up for <Client Name>: N missing accounts added (NO — NS 4102).`
     (note: "topped up", not "auto-seeded" — confirms the upsert path ran)
   - **Zero errors**
7. Next: Reports →
   - P&L: expenses populated
   - Balance Sheet: `2400 Leverandørgjeld` = sum of gross totals
   - `check: true`

### 3. Idempotency check

Click "Load 10 Sample Invoices" → "Book all" **a second time** on the
same client.

- Bookings succeed (10 more journal entries posted).
- **No "auto-seeded" or "topped up" notice** this time — COA is now
  complete so upsert adds nothing.

### 4. DB sanity check

```bash
docker compose -f /opt/claud-erp/docker-compose.prod.yml exec api \
  psql $DATABASE_URL -c \
  "SELECT c.name, COUNT(a.id) AS accounts \
   FROM clients c LEFT JOIN accounts a ON a.client_id = c.id \
   GROUP BY c.id, c.name ORDER BY accounts;"
```

Every client that went through the import flow should now show
**≈ 95 accounts** (full NS 4102 hotel template). Any client showing
43-94 is a leftover from the old template — safe to re-run the import
flow to top them up.

Also verify 2400 exists per client:

```bash
docker compose -f /opt/claud-erp/docker-compose.prod.yml exec api \
  psql $DATABASE_URL -c \
  "SELECT c.name, a.code, a.name AS account_name \
   FROM accounts a JOIN clients c ON c.id = a.client_id \
   WHERE a.code IN ('2400','2710','2720','2725','2728') \
   ORDER BY c.name, a.code;"
```

Every client should show all 5 rows.

---

## Rollback

```bash
ssh root@45.55.44.133
cd /opt/claud-erp
TAG=899f2c9 docker compose -f docker-compose.prod.yml pull api
TAG=899f2c9 docker compose -f docker-compose.prod.yml up -d api
```

No data cleanup needed — accounts added under the hotfix are standard
NS 4102 rows and safe to keep even after rollback.

---

## Report back

After deploy, post to Telegram:

1. Commit hash deployed (registry tag used)
2. `docker compose -f /opt/claud-erp/docker-compose.prod.yml ps` output
3. Screenshot / text from verification step 2:
   - `10 / 10` booked ✅/❌
   - Notice text (should contain "topped up" or "auto-seeded")
4. Output of the DB sanity check showing 2400/2710/2720/2725/2728 per client
5. Any `ERROR` lines in last 200 API log lines:
   `docker compose logs api --tail=200 | grep -iE "error|traceback"`

🦞

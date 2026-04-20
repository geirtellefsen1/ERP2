# JR — Sprint 4 Hotfix (EHF Auto-Seed COA)

Drop-in deploy prompt for the EHF import hotfix. Stacks on top of the
already-deployed Sprint 4 (commit `4876c34`).

---

## What's in this hotfix

**Branch:** `claude/erp-job-breakdown-3eCnk`
**Minimum commit:** `3a110dd` or newer
**Previous deployed commit:** `4876c34`

### The bug

EHF import was throwing "Missing account 2400 (Leverandørgjeld). Seed
chart of accounts first." for any client that didn't have a COA seeded
yet (e.g. `Acme Corporation`). All 10 sample bookings failed.

### The fix

- **`apps/api/app/routers/ehf.py`**: new `_ensure_coa_seeded(db, client)`
  helper that seeds NS 4102 (NO) or BAS 2024 (SE) automatically if the
  client has zero accounts. Wired into both `POST /api/v1/ehf/import`
  and `POST /api/v1/ehf/import-samples`.
- New `notices: list[str]` field on `ImportResult` surfaces the
  auto-seed action to the user.
- **`apps/web/app/dashboard/import/page.tsx`**: renders notices in a
  blue info box above the errors list.
- Safety: refuses to seed if the client already has any accounts,
  so custom/partial COAs are never overwritten.

### Migrations

**None.** Pure code fix — no schema changes, no data backfill.

---

## Operational context (read before deploying)

Since the last deploy the droplet landscape has shifted:

- **Host port 8000 is now held by `hydra-engine`** (Energy-RT, PID
  667045). Don't kick it off.
- **`claud-erp-api` is now on host port `8003`** (container-internal
  still `8000`). Mapping in `/opt/claud-erp/docker-compose.prod.yml`
  on the droplet is `"8003:8000"`. The repo copy may still say
  `"8000:8000"` — if so, **do not** overwrite the droplet copy when
  pulling, or run `git stash` on that file before pull.
- **Nginx** on the host now proxies `/api/*` to `http://127.0.0.1:8003`
  (was 8000). Config file:
  `/etc/nginx/sites-available/erp.tellefsen.org` — backup already
  exists as `.bak-sprint4`.

---

## Deploy steps

```bash
# ── 1. On the build machine (Donald) ──────────────────────────────

cd ~/code/erp2   # or wherever the clone lives
git fetch origin
git checkout claude/erp-job-breakdown-3eCnk
git pull
SHA=$(git rev-parse --short HEAD)
echo "Building $SHA"         # should be 3a110dd or newer

APP_URL="https://erp.tellefsen.org"
TAG=$SHA

# API image — straight build, no build args
docker build -f infra/docker/Dockerfile.api \
  -t registry.digitalocean.com/claud-erp/api:$TAG .

# WEB image — BOTH --build-arg FLAGS ARE MANDATORY
# Without these, Next.js bakes localhost:8000 into the bundle and
# login fails with "Cannot connect to server" (the #1 known bug).
docker build -f infra/docker/Dockerfile.web \
  --build-arg NEXT_PUBLIC_API_URL=$APP_URL \
  --build-arg NEXT_PUBLIC_APP_URL=$APP_URL \
  -t registry.digitalocean.com/claud-erp/web:$TAG .

docker push registry.digitalocean.com/claud-erp/api:$TAG
docker push registry.digitalocean.com/claud-erp/web:$TAG

# ── 2. On the droplet ─────────────────────────────────────────────

ssh root@45.55.44.133
cd /opt/claud-erp

# Confirm current compose file still has 8003:8000 (do NOT overwrite
# this value from the repo copy):
grep -n '8003:8000\|"8000:8000"' docker-compose.prod.yml

# Pull and restart both services
TAG=3a110dd   # or whatever SHA you just built
export TAG
docker compose -f docker-compose.prod.yml pull api web
docker compose -f docker-compose.prod.yml up -d api web

# Wait for health
sleep 8
docker compose -f docker-compose.prod.yml ps
```

---

## Verification

### 1. Smoke test (direct)

```bash
# Health
curl -sf https://erp.tellefsen.org/health | jq
# Expected: {"status": "ok", ...}

# Sample endpoint still works
curl -s https://erp.tellefsen.org/api/v1/ehf/sample-invoices | jq '. | length'
# Expected: 10
```

### 2. Login smoke test

Open `https://erp.tellefsen.org/login` in a private window.

- Email: `demo@claud-erp.com`
- Password: `demo1234`

Should redirect to `/dashboard` without "Cannot connect to server."

### 3. The actual hotfix verification — the happy path

1. In TopBar, select a client **that has no COA seeded yet** — e.g.
   `Acme Corporation`. If none exists, create one: Clients → Add
   Client → Name `HotfixTest AS`, Country `Norway`, skip seeding.
2. Sidebar → Finance → **EHF Import**.
3. Click "Load 10 Sample Invoices" → preview populates.
4. Click **Book all to ledger**.
5. Expected result on the "Booked" step:
   - Invoices booked: **10 / 10**
   - Journal Entries: **10**
   - **1 blue notice box** at the top: `Chart of accounts auto-seeded
     for Acme Corporation: 43 accounts (NO — NS 4102).`
   - **Zero errors.**
   - Ledger table shows 10 entries, all balanced.
6. Click **Next: Reports**.
   - P&L: expense totals are non-zero.
   - Balance Sheet: `2400 Leverandørgjeld` (liability) shows the sum
     of all 10 gross invoice totals. `check: true`.

### 4. Safety check — don't over-seed

Run the flow again on the same client:

- Click "Book all" a second time (upload any sample XML again).
- Expected: bookings succeed, **no "auto-seeded" notice** this time
  (because the COA already exists).
- Verifies the `existing > 0` guard in `_ensure_coa_seeded`.

### 5. DB sanity check

```bash
docker compose -f /opt/claud-erp/docker-compose.prod.yml exec api \
  psql $DATABASE_URL -c \
  "SELECT c.name, COUNT(a.id) AS account_count \
   FROM clients c LEFT JOIN accounts a ON a.client_id = c.id \
   GROUP BY c.id, c.name ORDER BY account_count;"
```

Every client that went through the hotfix should show ≥ 43 accounts.
No client should have 1-42 (that would mean a partial seed —
investigate).

---

## Rollback

If anything goes sideways:

```bash
ssh root@45.55.44.133
cd /opt/claud-erp
TAG=4876c34 docker compose -f docker-compose.prod.yml pull api web
TAG=4876c34 docker compose -f docker-compose.prod.yml up -d api web
```

No data cleanup needed — any accounts auto-seeded under the hotfix are
standard NS 4102 rows and are safe to keep. Journal entries created
under the hotfix are also valid double-entry and should remain.

---

## Report back

After deploy, post to Telegram:

- Commit hash deployed (`docker exec claud-erp-api git rev-parse --short HEAD`
  if baked in, or the registry tag)
- Output of `docker compose -f /opt/claud-erp/docker-compose.prod.yml ps`
- Result of verification step 3 (screenshot or text: booked X/10,
  notice shown ✅/❌)
- Output of the DB sanity check SQL above
- Any `ERROR` lines in the last 200 API log lines:
  `docker compose logs api --tail=200 | grep -iE "error|traceback"`

🦞

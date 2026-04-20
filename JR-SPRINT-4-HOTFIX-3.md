# JR — Sprint 4 Hotfix #3 (EHF COA Commit Fix)

Drop-in deploy prompt. Stacks on whatever is currently deployed
(whether that's `899f2c9` or `ef48b22`).

---

## What's in this hotfix

**Branch:** `claude/erp-job-breakdown-3eCnk`
**Minimum commit:** `aafd1d9` or newer
**Previous target:** `ef48b22` (deploy may or may not have succeeded)

### The bug

After the previous hotfix, EHF sample import **still** fails with
all 10 invoices erroring on "Missing account 2400 (Leverandørgjeld).
Seed chart of accounts first."

### Root cause

`database.py` configures the session with `autoflush=False`. The COA
upsert logic does `db.add() + db.flush()` per account, but within the
same session/transaction the subsequent `_book_invoice()` query
**didn't reliably see** the flushed rows. Net effect: accounts got
written to the DB transaction buffer but `accounts.get("2400")`
returned `None`.

### The fix

- **`apps/api/app/routers/ehf.py`**: explicit `db.commit()` after
  `_ensure_coa_seeded()` in all three endpoints (`/import`,
  `/import-samples`, `/demo-baseline`) when new accounts were added.
  This persists the seed to the DB before booking starts, so
  `_book_invoice()` always finds 2400 / 2710 / etc.
- Commit `aafd1d9` also includes the upsert-by-code fix from
  `ef48b22` (it stacks cleanly on `899f2c9`).

### Migrations

**None.** Pure code fix.

### Files changed

- `apps/api/app/routers/ehf.py` (only — 3 edits, 4 added lines total)
- **Web image does NOT need rebuild.**

---

## Operational context (unchanged)

- Host port 8000 → `hydra-engine` (Energy-RT). Leave it alone.
- `claud-erp-api` on host port **8003** (container-internal 8000).
- Nginx: `/api/*` → `http://127.0.0.1:8003`.

---

## Deploy steps

```bash
# ── 1. On the build machine (Donald) ──────────────────────────────

cd ~/code/erp2
git fetch origin
git checkout claude/erp-job-breakdown-3eCnk
git pull
SHA=$(git rev-parse --short HEAD)
echo "Building $SHA"     # must be aafd1d9 or newer

TAG=$SHA

# API image only — web doesn't need rebuild
docker build -f infra/docker/Dockerfile.api \
  -t registry.digitalocean.com/claud-erp/api:$TAG .

docker push registry.digitalocean.com/claud-erp/api:$TAG

# ── 2. On the droplet ─────────────────────────────────────────────

ssh root@45.55.44.133
cd /opt/claud-erp

# Confirm compose still has 8003:8000 for API
grep -n '8003:8000\|"8000:8000"' docker-compose.prod.yml

# Pull + restart ONLY the api container
TAG=aafd1d9
export TAG
docker compose -f docker-compose.prod.yml pull api
docker compose -f docker-compose.prod.yml up -d api

# Verify the new code is actually running
sleep 5
docker compose -f docker-compose.prod.yml exec api \
  grep -c "db.commit()" /app/app/routers/ehf.py
# Expected: 6 or more (was 3 before this fix).
# If the grep returns ≤3, the old image is still running — pull again.

docker compose -f docker-compose.prod.yml ps
```

---

## Verification

### 1. Smoke test

```bash
curl -sf https://erp.tellefsen.org/health | jq
curl -s https://erp.tellefsen.org/api/v1/ehf/sample-invoices | jq '. | length'
# Expected: 10
```

### 2. Retry the failing import

1. Log in at `https://erp.tellefsen.org` as `demo@claud-erp.com` /
   `demo1234`.
2. TopBar → select the **same client that kept failing** (probably
   `Acme Corporation` or whatever was in use).
3. Sidebar → Finance → **EHF Import**.
4. Click "Load 10 Sample Invoices" → preview shows 10 rows.
5. Click **Book all to ledger**.
6. Expected on the Booked step:
   - Invoices booked: **10 / 10** ✅
   - Journal entries: **10**
   - **Blue notice box**: either
     `Chart of accounts auto-seeded…` (if client had zero accounts) or
     `Chart of accounts topped up for <Client>: N missing accounts added (NO — NS 4102).`
   - **Zero errors**
7. Next: Reports →
   - P&L: expenses populated (non-zero)
   - Balance Sheet: `2400 Leverandørgjeld` = sum of gross totals
   - `check: true`

### 3. Idempotency check

Click "Load 10 Sample Invoices" → "Book all" **again** on the same
client.

- 10 more bookings succeed (20 total JEs now).
- **No notice box this time** — COA is complete, upsert adds nothing.

### 4. DB verification

```bash
docker compose -f /opt/claud-erp/docker-compose.prod.yml exec api \
  psql $DATABASE_URL -c \
  "SELECT c.name, a.code, a.name \
   FROM accounts a JOIN clients c ON c.id = a.client_id \
   WHERE a.code IN ('2400','2710','2720','2725','2728') \
   ORDER BY c.name, a.code;"
```

Every client that went through the import flow should now show all
5 rows (one for each critical account code).

```bash
docker compose -f /opt/claud-erp/docker-compose.prod.yml exec api \
  psql $DATABASE_URL -c \
  "SELECT c.name, COUNT(a.id) AS accounts, \
          (SELECT COUNT(*) FROM journal_entries je WHERE je.client_id = c.id) AS entries \
   FROM clients c LEFT JOIN accounts a ON a.client_id = c.id \
   GROUP BY c.id, c.name ORDER BY accounts;"
```

Any client used for testing should show ≥ 95 accounts and ≥ 10 entries.

---

## Rollback

```bash
ssh root@45.55.44.133
cd /opt/claud-erp
TAG=899f2c9 docker compose -f docker-compose.prod.yml pull api
TAG=899f2c9 docker compose -f docker-compose.prod.yml up -d api
```

No data cleanup needed. Accounts / journal entries created under the
hotfix are standard NS 4102 double-entry rows and safe to keep.

---

## Report back

Post to Telegram:

1. Output of the `grep -c "db.commit()"` check (must be ≥ 6)
2. Commit tag deployed (`aafd1d9` or newer)
3. `docker compose -f /opt/claud-erp/docker-compose.prod.yml ps` output
4. Screenshot or text from verification step 2:
   - `10 / 10` booked ✅/❌
   - Notice text (auto-seeded / topped up / none)
5. Output of the 5-row DB verification query
6. Any `ERROR` lines in last 200 API log lines:
   `docker compose logs api --tail=200 | grep -iE "error|traceback"`

🦞

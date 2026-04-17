# JR — Sprint 3 Deployment (Nordic + i18n)

Drop-in deployment prompt for the Sprint 3 release. Assumes the base
deployment from `JR-DEPLOYMENT.md` is already live and working at
`https://erp.tellefsen.org`.

---

## What's in this sprint

**Branch:** `claude/erp-job-breakdown-3eCnk`
**Minimum commit:** `88debeb` or newer

### Backend (FastAPI)
- New service: `app/services/nordic.py` (VAT rates, org nr validators,
  chart of accounts templates for NO/SE)
- New router: `app/routers/nordic.py`
  - `GET  /api/v1/nordic/vat-rates?country=NO|SE&locale=en|no|sv`
  - `POST /api/v1/nordic/validate-org-number` — NO mod-11 / SE Luhn
  - `GET  /api/v1/nordic/coa-template?country=NO|SE&locale=en|no|sv`
  - `POST /api/v1/nordic/seed-accounts?client_id=X&country=NO|SE`
- New endpoints: `GET/PATCH /api/v1/agencies/me` (agency settings save)
- New endpoints: `GET/PATCH /api/v1/users/me` (profile save)
- `POST /api/v1/clients` now auto-seeds COA based on country (NO → NS 4102,
  SE → BAS 2024). ~40 accounts per client, parent/child hierarchy
  preserved.
- `schemas.AgencyUpdate` now accepts `countries_enabled`

### Frontend (Next.js)
- `/dashboard/clients` rewritten — full Nordic fields, edit modal, live
  org-nr validation, country filter, auto-set currency from country
- `/dashboard/settings` — agency + profile sections now persist to API
  (loading state + save button wired)
- Invoice/expense forms — country-aware VAT selectors (NO MVA:
  25/15/12/6/0%, SE Moms: 25/12/6/0%)
- TopBar — locale switcher (EN/NO/SE/FI)
- Sidebar fully translated via `useTranslations("Navigation")`
- Translation files extended: `Common`, `Navigation`, `Clients`,
  `Invoices`, `Expenses`, `Settings` namespaces in `en`/`nb`/`sv`/`fi`
- `lib/client-context.tsx` — `ClientSummary` now includes
  `default_currency` (downstream pages use it for formatting)

### Migrations
**No new migrations in this sprint.** Sprint 2's migration `019` already
added the fields needed (vat_number, address, city, etc.). If migration
019 is not applied on prod, run it first — see `JR-DEPLOYMENT.md` §
"Alembic widening" for the VARCHAR(64) fix that's bundled at the top of
migration 019.

---

## Deploy steps

```bash
# 1. SSH into droplet
ssh root@45.55.44.133

# 2. Pull the new branch
cd /opt/claud-erp
git fetch origin
git checkout claude/erp-job-breakdown-3eCnk
git pull origin claude/erp-job-breakdown-3eCnk

# 3. Verify the commit
git log -1 --oneline
# Expected: 88debeb or newer

# 4. Rebuild both containers
#    IMPORTANT: web must be rebuilt to pick up:
#    - New clients/settings pages
#    - i18n provider wired into dashboard layout
#    - Locale switcher in TopBar
#    - NEXT_PUBLIC_API_URL="" baked in (same-origin)
docker compose -f docker-compose.prod.yml build --no-cache web api
docker compose -f docker-compose.prod.yml up -d web api

# 5. Apply migrations (safe to re-run; 019 checks idempotently)
docker compose -f docker-compose.prod.yml exec api alembic upgrade head

# 6. Smoke test the new endpoints
curl -s https://erp.tellefsen.org/api/v1/nordic/vat-rates?country=NO | jq
# Expected: JSON array with 5 rates (25/15/12/6/0)

curl -sX POST https://erp.tellefsen.org/api/v1/nordic/validate-org-number \
  -H "Content-Type: application/json" \
  -d '{"org_number":"974760673","country":"NO"}' | jq
# Expected: {"valid":true,"formatted":"974 760 673","error":null}
#           (974760673 = Brønnøysundregistrene itself, always valid)
```

---

## Functional verification (do this after deploy)

Open `https://erp.tellefsen.org` and test as a logged-in bookkeeper:

1. **Locale switcher** — Click the globe icon in TopBar → switch to `NO`.
   Sidebar should change: "Clients" → "Kunder", "Invoices" → "Fakturaer",
   "Settings" → "Innstillinger". Locale persists across reloads.

2. **Client creation with COA seeding**
   - Dashboard → Clients → "Add Client"
   - Name: "Test Hotell AS", Country: Norway, Industry: Hospitality
   - Org nr: type `974760673` → tab out → should validate ✅
   - Click "Add Client"
   - Verify the success toast says "chart of accounts seeded"
   - Run: `docker compose exec api psql -U postgres -d bpo_nexus -c \
     "SELECT COUNT(*) FROM accounts WHERE client_id = (SELECT id FROM clients WHERE name='Test Hotell AS');"`
   - Expected: ~40 accounts

3. **Client edit** — Click the pencil icon on a client row. Should open
   modal pre-populated with all fields (address, VAT nr, phone, etc.).
   Change phone number, save, reload — change persists.

4. **Settings → Agency** — Should load agency name from API (not
   hardcoded "BPO Nexus Demo"). Change name, save, reload — persists.

5. **Settings → Profile** — Should load from API. Change full name,
   save, reload — persists. Sidebar footer updates to show new name.

6. **Invoice VAT rates** — Select a Norwegian client in TopBar → New
   Invoice → VAT dropdown shows 5 options with "MVA" labels. Select a
   Swedish client → dropdown shows 4 options with "moms" labels.

7. **Expense VAT rates** — Same country-aware behavior. Column header
   also adapts ("MVA" for NO, "Moms" for SE).

---

## Rollback

If anything's broken:

```bash
cd /opt/claud-erp
git checkout 33740a9          # last known-good Sprint 2 commit
docker compose -f docker-compose.prod.yml build --no-cache web api
docker compose -f docker-compose.prod.yml up -d web api
```

No data migrations to revert — Sprint 3 is purely additive at the DB
level (only reads existing schema; COA seeding inserts new rows in the
`accounts` table which is harmless).

---

## Known gotchas

1. **Locale is client-side only.** It's stored in `localStorage` under
   `claud_erp_locale`. If you're testing in incognito, it defaults to
   English. This is by design — no URL restructuring needed.

2. **COA auto-seed only runs on `POST /api/v1/clients`**, not on clients
   created before this sprint. To retro-seed an existing client:
   ```bash
   curl -sX POST 'https://erp.tellefsen.org/api/v1/nordic/seed-accounts?client_id=1&country=NO' \
     -H "Authorization: Bearer <token>"
   ```
   It refuses if the client already has accounts. Delete existing ones
   first if you want a fresh seed.

3. **Sidebar collapsed state** isn't translated — only the expanded
   labels. Tooltips use the translated label, so it still works.

4. **`/dashboard/clients` table** uses `formatDate` (locale "nb-NO") for
   the "Created" column. Dates render as `17. apr. 2026` regardless of
   selected UI locale — that's intentional for consistency with
   accounting records.

---

## Report back

After deploy, post in Telegram with:
- Commit hash deployed
- Result of the 7 verification steps above (`✅` / `❌ <what failed>`)
- `docker compose ps` output
- Any new entries in `/var/log/caddy/access.log` for suspicious 5xx

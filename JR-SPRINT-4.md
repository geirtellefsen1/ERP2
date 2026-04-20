# JR — Sprint 4 Deployment (EHF Import + End-to-End Flow)

Drop-in deployment prompt for the Sprint 4 release. Assumes Sprint 3
(Nordic + i18n) is already live per `JR-SPRINT-3.md`.

---

## What's in this sprint

**Branch:** `claude/erp-job-breakdown-3eCnk`
**Minimum commit:** `821890d` or newer
**Release codename:** "EHF end-to-end"

### Backend (FastAPI)

- **New service:** `app/services/ehf.py`
  - `EHFInvoice` / `EHFLineItem` dataclasses (UBL 2.1 shaped)
  - `generate_ehf_xml()` — emits PEPPOL BIS 3.0 / UBL 2.1 invoice XML
  - `parse_ehf_xml()` — extracts supplier, line items, VAT breakdown
  - `suggest_account_code()` — keyword → NS 4102 account mapping
  - `SAMPLE_SUPPLIERS` — 10 realistic Norwegian suppliers with
    correct MVA rates (Asko 15%, Hafslund 25%, Telenor 25%, etc.)
  - `generate_sample_invoices()` — fabricates 10 invoices with
    plausible dates / amounts
- **New router:** `app/routers/ehf.py` mounted at `/api/v1/ehf`
  - `GET  /sample-invoices` — preview 10 samples as JSON
  - `GET  /sample-invoices/download` — download 10 EHF XMLs as a ZIP
  - `POST /parse` — upload EHF XML(s), return parsed fields (no booking)
  - `POST /import` — upload + parse + auto-book to GL (auth required)
  - `POST /import-samples?client_id=X` — generate samples and book
  - Double-entry booking pattern:
    `DR 6xxx expense account + DR 2710 input VAT / CR 2400 accounts payable`
- **Security fix:** `PATCH /api/v1/clients/{id}` now requires
  `get_current_user` and filters by `agency_id`. Previously
  unauthenticated — multi-tenant bleed risk. **Non-optional.**

### Frontend (Next.js)

- **New page:** `/dashboard/import` — 4-step wizard
  1. Upload — drag-drop zone + "Load 10 Sample Invoices" + ZIP download
  2. Preview — parsed invoice table with NS 4102 account badges
  3. Booked — journal ledger showing each posted entry, balanced/unbalanced
  4. Reports — live P&L and Balance Sheet reflecting the new entries
- **Sidebar:** new "EHF Import" link under Finance section
- **Error handling:** `lib/api.ts` now extracts FastAPI's 422
  `detail[]` arrays into human-readable strings — no more generic
  "Request Failed" toasts

### Migrations

**No new migrations in this sprint.** EHF import uses existing
`accounts`, `journal_entries`, `journal_lines`, `expenses` tables
(all present since Sprint 2 migration 019). Journal entries are
standard double-entry; no schema additions.

### Docs (no runtime effect)

- `ERP-AGENT-INSTRUCTIONS.md` — system prompt for ERP ops agent on Donald
- `docs/openclaw/OPENCLAW-SYSTEM-PROMPT-{en,nb,sv,fi}.md` — WhatsApp agent prompts
- `docs/openclaw/README.md` — index

---

## Deploy steps

```bash
# 1. SSH into droplet
ssh root@45.55.44.133

# 2. Pull the new commits
cd /opt/claud-erp
git fetch origin
git checkout claude/erp-job-breakdown-3eCnk
git pull origin claude/erp-job-breakdown-3eCnk

# 3. Verify the commit
git log -1 --oneline
# Expected: 821890d or newer

# 4. Rebuild both containers
#    - api: new ehf router + services, updated clients PATCH auth
#    - web: new /dashboard/import page, updated Sidebar, updated lib/api.ts
docker compose -f docker-compose.prod.yml build --no-cache web api
docker compose -f docker-compose.prod.yml up -d web api

# 5. No migrations to apply, but confirm schema is up-to-date
docker compose -f docker-compose.prod.yml exec api alembic current
# Expected: head (019 or later)

# 6. Smoke test the new endpoints
curl -s https://erp.tellefsen.org/api/v1/ehf/sample-invoices | jq '. | length'
# Expected: 10

curl -s -o /tmp/samples.zip https://erp.tellefsen.org/api/v1/ehf/sample-invoices/download
unzip -l /tmp/samples.zip | tail -5
# Expected: 10 .xml files, ~4-8 KB each
```

---

## Functional verification (do this after deploy)

Log in as a bookkeeper at `https://erp.tellefsen.org` and run this
end-to-end flow:

1. **Select a Norwegian client** in TopBar (create one if needed —
   use `Test Hotell AS`, country NO, so COA auto-seeds to NS 4102).

2. **Navigate to Finance → EHF Import.**

3. **Step 1 — Upload**
   - Click "Load 10 Sample Invoices" → preview table populates.
   - Alt path: click "Download sample ZIP" → drag-drop one of the
     XMLs back into the upload zone → preview populates with 1 row.

4. **Step 2 — Preview**
   - Each row shows supplier, invoice ref, net / VAT / total,
     suggested NS 4102 account badge (e.g. `6300 Energikostnader`
     for Hafslund, `4000 Varer til videresalg` for Asko).
   - Click "Book all to ledger" → advances to Step 3.

5. **Step 3 — Booked ledger**
   - Each invoice shows 3 journal lines (DR expense + DR 2710 /
     CR 2400) with balanced indicator.
   - All 10 should show "✅ balanced" (debit total = credit total).

6. **Step 4 — Reports**
   - P&L section: expense total has increased by the net amount booked.
   - Balance Sheet: `2400 Accounts Payable` (liability) increased by
     the total gross. `2710 Input VAT` (asset) increased by VAT sum.
   - `check` field on balance sheet must be `true` (assets =
     liabilities + equity).

7. **Multi-tenant isolation spot check**
   - Log in as a second agency / second bookkeeper.
   - Try to `PATCH /api/v1/clients/{id}` where the id belongs to
     agency A from agency B's token.
   - Expected: 404 Client not found. Previously this would have
     succeeded — this is the security fix.

8. **Error surface check**
   - On Clients page, try to create a client with invalid org nr.
   - Error banner should now show the specific field message (e.g.
     `vat_number: Invalid format`) instead of "Request Failed".

---

## Rollback

If anything's broken:

```bash
cd /opt/claud-erp
git checkout 88debeb          # last known-good Sprint 3 commit
docker compose -f docker-compose.prod.yml build --no-cache web api
docker compose -f docker-compose.prod.yml up -d web api
```

No DB changes to revert. Any test journal entries posted via the
import page can be left in place (they affect only the clients you
booked them against) or removed with:

```sql
-- ⚠️ Only run if you want to purge test bookings
DELETE FROM journal_lines WHERE entry_id IN (
  SELECT id FROM journal_entries
  WHERE description LIKE 'EHF import:%'
  AND client_id = <test_client_id>
);
DELETE FROM journal_entries
  WHERE description LIKE 'EHF import:%'
  AND client_id = <test_client_id>;
```

---

## Known gotchas

1. **COA must exist on the client before import.** If the client has
   zero accounts, booking fails because the NS 4102 account codes
   won't resolve. Fix: run the Sprint 3 seed endpoint first —
   `POST /api/v1/nordic/seed-accounts?client_id=X&country=NO`.

2. **Account 2710 (Input VAT) and 2400 (Accounts Payable) must
   exist.** Both are in the standard NS 4102 template. If seeding
   was done with a reduced template, booking will 500 with
   `Account code 2710 not found for client X`.

3. **Sample invoices use fixed dates** — they span the last 30 days
   relative to generation. If booked, they land in the current
   period's P&L. This is intentional for demo purposes.

4. **EHF import only handles supplier invoices (A/P side).**
   Customer invoices (A/R) still go through the existing
   `/dashboard/invoices` flow. Sprint 5 will add AR side.

5. **`suggest_account_code()` is keyword-based**, not AI. It matches
   on supplier name and description substrings. Unmapped rows get
   suggested account `7790 Annen kostnad` (catch-all). Bookkeeper
   should review before hitting "Book all".

6. **The security fix on client PATCH is breaking for any stale
   sessions** that were editing clients without a token. If you see
   401s on the Clients edit modal post-deploy, that's the fix
   working — affected users just need to refresh.

---

## Report back

After deploy, post in Telegram with:
- Commit hash deployed (`git log -1 --oneline`)
- Result of the 8 verification steps above (`✅` / `❌ <what failed>`)
- `docker compose ps` output
- Sample import result: `curl -s .../api/v1/ehf/sample-invoices | jq '.[0].supplier_name'`
  (should return a Norwegian supplier name like "Asko Oslo AS")
- Any `ERROR` or `TRACEBACK` lines from the last 200 API log lines:
  `docker compose logs api --tail=200 | grep -iE "error|traceback"`

🦞

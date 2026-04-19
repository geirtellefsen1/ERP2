# OpenClaw — WhatsApp Agent Configuration

System prompts for OpenClaw, the client-facing WhatsApp agent for ClaudERP.

## Files

| File | Language | Target |
|---|---|---|
| `OPENCLAW-SYSTEM-PROMPT-EN.md` | English | Default / fallback |
| `OPENCLAW-SYSTEM-PROMPT-NB.md` | Norsk Bokmål (nb-NO) | Norwegian clients |
| `OPENCLAW-SYSTEM-PROMPT-SV.md` | Svenska (sv-SE) | Swedish clients |
| `OPENCLAW-SYSTEM-PROMPT-FI.md` | Suomi (fi-FI) | Finnish clients |

## Language Selection

OpenClaw auto-detects the client's language from their first message and
loads the matching system prompt. If detection fails, defaults to English.

Each prompt includes a language-switching rule: if the client writes in a
different Nordic language, OpenClaw switches to match immediately.

## Conversation Flows (all languages)

1. **Document submission** — photo/PDF intake, registers with bookkeeper
2. **Balance query** — VAT balance, invoice status, account overview
3. **Payslip request** — employee identity verification, PDF delivery
4. **Expense submission** — collect details, create claim for approval
5. **Escalation** — tax advice, low confidence, complaints → human handoff

## Integration

- **Runtime:** MiniMax 2.77 on Donald (Mac Mini)
- **Channel:** Twilio WhatsApp Business API
- **Backend:** BPO Nexus API (`/api/v1/*`)
- **Escalation:** Routes to agency's human operator
- **Confidence threshold:** 85% — below this, escalate

## Country-Specific Notes

| Country | VAT term | Chart of Accounts | Payroll report | Filing portal |
|---|---|---|---|---|
| Norway | MVA | NS 4102 | A-melding (monthly, 5th) | Altinn |
| Sweden | Moms | BAS 2024 | AGD (monthly, 12th) | Skatteverket |
| Finland | ALV | — | Tulorekisteri (per payment, 5 days) | OmaVero |

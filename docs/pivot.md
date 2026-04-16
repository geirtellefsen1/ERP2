# Jurisdiction Pivot: ZA/NO/UK to NO/SE/FI

## Summary

ClaudERP originally targeted three jurisdictions: South Africa (ZA), Norway (NO), and the United Kingdom (UK). The platform has pivoted to focus exclusively on the Nordic region: Norway (NO), Sweden (SE), and Finland (FI).

## Why We Pivoted

1. **Market focus:** Saga Advisory AS operates in the Nordic accounting BPO space. Concentrating on three closely related Nordic jurisdictions allows deeper expertise and faster feature delivery.

2. **Regulatory alignment:** Norway, Sweden, and Finland share EU/EEA regulatory frameworks (GDPR, PSD2, AML directives). This dramatically simplifies compliance compared to spanning Africa, Europe, and the UK with divergent legal regimes.

3. **Banking infrastructure:** All three Nordic countries are served by Aiia (Mastercard Open Banking), providing a single integration point for bank account access and payment initiation. The original plan required TrueLayer (UK), separate South African banking APIs, and TrueLayer/Aiia for Norway.

4. **Tax system similarity:** Nordic VAT systems (MVA, Moms, ALV) follow similar EU VAT directive patterns, making it feasible to share significant tax logic across jurisdictions.

5. **Authentication:** BankID is the dominant strong authentication method in Norway and Sweden, with similar Finnish solutions. This replaces the need for multiple identity verification systems across disparate regions.

## What Changed

| Area                    | Before (ZA/NO/UK)                         | After (NO/SE/FI)                              |
|-------------------------|-------------------------------------------|-----------------------------------------------|
| **Banking integration** | TrueLayer (UK), custom (ZA), Aiia (NO)    | Aiia for all three countries                  |
| **Tax filing**          | SARS (ZA), Altinn (NO), HMRC (UK)         | Altinn (NO), Skatteverket (SE), Vero (FI)     |
| **VAT system**          | ZA VAT, Norwegian MVA, UK VAT             | MVA (NO), Moms (SE), ALV (FI)                |
| **Currency**            | ZAR, NOK, GBP                             | NOK, SEK, EUR                                |
| **Auth/identity**       | Multiple systems                          | BankID (NO/SE) + Finnish equivalents          |
| **Compliance**          | POPIA (ZA), GDPR (NO), UK GDPR            | GDPR across all three (EEA)                  |
| **Chart of accounts**   | Country-specific, divergent               | NS 4102 (NO), BAS (SE), Finnish standard     |
| **Payroll**             | Three completely different systems         | Similar Nordic social security models         |
| **Language**            | English, Norwegian, Afrikaans              | Norwegian, Swedish, Finnish, English          |

## What Remains

- **Core architecture** — the multi-tenant, 5-tier service architecture is jurisdiction-agnostic and unchanged
- **Auth system** — custom JWT with refresh-token rotation works for any jurisdiction
- **AI features** — Claude API integration for document processing is language/jurisdiction-independent
- **Billing** — Stripe integration is global
- **Database schema** — the `jurisdictions` table and jurisdiction-scoped models support any set of countries

## Implementation

Jurisdiction-specific logic lives in `apps/api/app/jurisdictions/`:
- `norway.py` — Norwegian tax rates, MVA rules, Altinn filing, SAF-T export
- `sweden.py` — Swedish tax rates, Moms rules, Skatteverket filing, SIE format
- `finland.py` — Finnish tax rates, ALV rules, Vero filing
- `base.py` — Abstract base class defining the jurisdiction interface

Each module implements a common interface (`JurisdictionProvider`) ensuring consistent behavior across countries while encapsulating country-specific rules.

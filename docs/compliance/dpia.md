# Data Protection Impact Assessment — ClaudERP

**Controller:** ClaudERP AS (Norway)
**Assessment date:** 2026-04-16
**Assessor:** [NAME], Data Protection Officer
**Next review:** 2027-04-16

This DPIA is conducted pursuant to Article 35 of Regulation (EU) 2016/679 (GDPR),
as incorporated into Norwegian law via *Personopplysningsloven*. Processing activities
assessed here involve large-scale processing of employee personal data (including national
identity numbers), automated financial decision-making, and cross-border data transfers.

---

## 1. Description of Processing

### 1.1 Overview

ClaudERP is a multi-tenant Nordic accounting BPO platform serving bureau firms in Norway,
Sweden, and Finland. The platform processes:

- **Payroll** for employees of client companies across three jurisdictions (NO/SE/FI),
  including salary calculations, statutory deductions, and regulatory filings.
- **Banking data** via Aiia (Open Banking / PSD2) for payment initiation and
  transaction reconciliation.
- **Client financial data** including invoices, ledger entries, VAT returns, and
  annual accounts.
- **AI-assisted analysis** via the Claude API (Anthropic) for document extraction,
  accounting queries, and anomaly detection.
- **Identity verification** for client company representatives under AML/KYC obligations.
- **Audit logging** of all system actions for regulatory compliance and security.

### 1.2 Data Flows

```
Client Company
    │
    ▼
ClaudERP Platform (PostgreSQL, RLS-isolated per tenant)
    ├── Payroll Engine (NO/SE/FI) ──► Tax Authorities (Skatteetaten / Skatteverket / Verohallinto)
    ├── Aiia Open Banking ──► Client Bank(s) [PSD2, EEA only]
    ├── Claude API (Anthropic, USA) ──► Stateless; zero-retention policy
    ├── Email Service Provider (EEA) ──► Transactional notifications
    └── Audit Log (append-only) ──► Internal security review
```

### 1.3 Categories of Data Subjects

- Employees and contractors of client companies (NO/SE/FI)
- Client company representatives and authorised signatories
- ClaudERP staff (BPO agents, administrators)

### 1.4 Volume and Scale

- Multiple BPO agencies, each managing dozens to hundreds of client companies
- Thousands of employee payroll records per monthly cycle
- Continuous banking transaction ingestion via Aiia

---

## 2. Necessity and Proportionality

### 2.1 Lawful Basis

| Processing Activity | Legal Basis | Justification |
|---|---|---|
| Payroll processing | Art. 6(1)(b) contract; Art. 6(1)(c) legal obligation | Required by employment contracts and tax/social security legislation in NO/SE/FI |
| Banking data (Aiia) | Art. 6(1)(b) contract; Art. 6(1)(c) PSD2 | Necessary to execute salary payments and reconcile transactions |
| Client financial data | Art. 6(1)(b) contract; Art. 6(1)(c) bookkeeping law | Required by Bokforingsloven / Bokforingslagen / Kirjanpitolaki |
| AI analysis (Claude API) | Art. 6(1)(f) legitimate interest; Art. 6(1)(b) contract | Efficient processing of accounting tasks; data minimised before submission |
| Identity verification | Art. 6(1)(c) AML/KYC (Hvitvaskingsloven) | Legal obligation for regulated financial services |
| Audit logging | Art. 6(1)(c) legal obligation; Art. 6(1)(f) legitimate interest | Required by bookkeeping law and necessary for security |

### 2.2 Data Minimisation

- Only data strictly necessary for each processing activity is collected.
- National ID numbers (fodselsnummer, personnummer, henkilotunnus) are used solely
  for statutory reporting and are not exposed in UI beyond masked display.
- AI analysis receives pseudonymised or redacted data where feasible — national ID
  numbers are stripped before submission to the Claude API.

### 2.3 Retention Limits

Retention periods are aligned with the shortest legally mandated period per jurisdiction
(see RoPA for detailed retention schedule). Data is purged automatically upon expiry.

### 2.4 Data Subject Rights

The platform supports:
- **Right of access** (Art. 15): Exportable data packages per data subject.
- **Right to rectification** (Art. 16): Corrections via tenant admin or support request.
- **Right to erasure** (Art. 17): Honoured except where legal retention obligations apply.
- **Right to data portability** (Art. 20): Machine-readable export (JSON/CSV).
- **Right to object** (Art. 21): Applicable to AI analysis — can be disabled per tenant.

---

## 3. Risks to Data Subjects

### 3.1 Risk Assessment Matrix

| Risk | Likelihood | Severity | Mitigation | Verification |
|---|---|---|---|---|
| **Cross-tenant data leakage** — one tenant's users access another tenant's payroll or financial data due to inadequate isolation | Low | Critical | PostgreSQL Row-Level Security (RLS) enforces tenant isolation at the database layer. Every query is scoped via `current_setting('app.current_tenant_id')`. Defence-in-depth with application-layer tenant checks. | [`test_rls.py`](../../tests/test_rls.py) — automated tests verify that cross-tenant queries return zero rows and that RLS policies cannot be bypassed. |
| **AI data exposure** — personal data sent to Claude API is retained, used for model training, or exposed to third parties | Low | High | Anthropic's zero-data-retention API policy ensures inputs are not stored beyond the request lifecycle and are never used for training. Standard Contractual Clauses (SCCs) govern the US transfer. PII (national IDs) is redacted before submission. | Contract review (Anthropic DPA); redaction logic in AI service layer; periodic audit of API call payloads. |
| **Credential theft** — attacker obtains database credentials, API keys, or encryption keys from the application or storage | Low | Critical | All secrets are encrypted at rest using envelope encryption via `services/secrets.py`. Database credentials are rotated on schedule. Secrets are never logged or exposed in error messages. | [`test_tier5_security.py`](../../tests/test_tier5_security.py) — automated tests verify encryption of stored secrets, absence of plaintext credentials, and key rotation. |
| **Insider threat** — authorised employee or contractor accesses data beyond their role, exfiltrates data, or makes unauthorised changes | Low | High | Role-based access control (RBAC) with principle of least privilege. All write operations and authentication events are logged to an append-only audit table. MFA required for administrative access. | Audit log review (quarterly); RBAC configuration tests; anomaly detection on access patterns. |
| **Payroll calculation error** — incorrect salary, tax, or social security calculations lead to financial harm for employees | Medium | High | Country-specific payroll engines with statutory formula implementations. Dual-review workflow (preparer + approver) before submission. Automated validation against known rate tables. | Payroll unit tests per jurisdiction; reconciliation checks; manual approval gate. |
| **Banking integration compromise** — Aiia Open Banking credentials stolen or man-in-the-middle attack on payment initiation | Low | Critical | Certificate-pinned HTTPS for Aiia connections. OAuth2 tokens are short-lived and scoped. Payment initiation requires SCA (Strong Customer Authentication) via PSD2 flow. | Aiia integration tests; TLS certificate monitoring; SCA flow validation. |
| **Unauthorised bulk data export** — attacker or insider exports large volumes of personal data | Low | High | Rate limiting on API endpoints. Export operations require elevated permissions and are audit-logged. No bulk export available to `client_readonly` role. | RBAC tests; audit log coverage for export endpoints. |
| **Database backup exposure** — unencrypted backups are accessed by unauthorised parties | Low | Critical | All database backups are encrypted with AES-256. Backup access restricted to infrastructure team with separate credentials. Backup integrity verified on schedule. | Infrastructure audit; backup restoration tests. |

### 3.2 Residual Risk Assessment

After mitigations, the residual risk for all identified threats is assessed as **Low** or
**Acceptable**. The highest residual risk remains payroll calculation error (medium
likelihood, mitigated by dual-review and automated validation but dependent on
correctness of rate table updates from tax authorities).

---

## 4. Mitigations — Summary of Technical and Organisational Measures

### 4.1 Technical Controls

| Control | Description | Status |
|---|---|---|
| Row-Level Security (RLS) | PostgreSQL RLS policies isolate tenant data at the query level | Implemented; continuously tested |
| Envelope encryption | Secrets encrypted via `services/secrets.py` using AES-256 envelope encryption | Implemented; tested by `test_tier5_security.py` |
| TLS 1.2+ everywhere | All external connections encrypted in transit; mTLS for internal services | Implemented |
| Audit logging | Append-only audit table capturing all write ops and auth events | Implemented |
| RBAC | Four-tier role model with least privilege; MFA for admins | Implemented |
| AI data redaction | National IDs stripped before Claude API calls; zero-retention API policy | Implemented |
| Certificate pinning | Aiia Open Banking connections use pinned certificates | Implemented |
| Automated testing | Security properties verified by `test_rls.py`, `test_tier5_security.py`, `test_migration_*.py` | CI/CD enforced |

### 4.2 Organisational Controls

| Control | Description | Frequency |
|---|---|---|
| DPO review | DPIA and RoPA reviewed by DPO | Annually or upon change |
| Staff training | GDPR and security awareness training for all staff | Annually |
| Vendor review | Processor agreements (Anthropic, Aiia, email provider) reviewed | Annually |
| Penetration testing | External penetration test of the platform | Annually |
| Incident response | Breach notification runbook maintained and tested | See `docs/runbooks/breach-notification.md` |
| Access review | User access rights reviewed and pruned | Quarterly |

---

## 5. Consultation

### 5.1 Data Subject Consultation

Data subjects (employees of client companies) are informed of processing via their
employer's privacy notice, which must reference ClaudERP as a processor. Template
privacy notice language is provided to BPO agencies during onboarding.

### 5.2 DPO Opinion

> *[To be completed by DPO after review]*
>
> The processing described in this DPIA is necessary and proportionate. Technical controls
> (RLS, encryption, audit logging) and organisational measures (RBAC, training, vendor review)
> adequately mitigate identified risks. No prior consultation with the supervisory authority
> under Article 36 is required at this time.
>
> **DPO signature:** ___________________________
> **Date:** ___________________________

---

## 6. Decision

- [ ] Processing may proceed as described.
- [ ] Processing may proceed with additional mitigations (listed below).
- [ ] Prior consultation with the supervisory authority (Datatilsynet) is required under Art. 36.

**Additional mitigations required (if any):**

> *None identified at this time.*

**Approved by:** [NAME], [TITLE]
**Date:** ___________________________

---

## Revision History

| Date | Author | Changes |
|---|---|---|
| 2026-04-16 | [NAME] | Initial assessment |

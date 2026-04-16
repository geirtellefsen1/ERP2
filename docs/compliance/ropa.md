# Records of Processing Activities — ClaudERP

**Controller:** ClaudERP AS (Norway)
**Date of last review:** 2026-04-16
**DPO contact:** [NAME / EMAIL]

This register is maintained in accordance with Article 30 of Regulation (EU) 2016/679 (GDPR),
as incorporated into the EEA Agreement and Norwegian law via *Personopplysningsloven*.

---

## Processing Activities Register

| Processing Activity | Category of Data | Data Subjects | Legal Basis | Retention Period | Recipients | Transfer Outside EEA |
|---|---|---|---|---|---|---|
| **Payroll Processing — Norway** | Employee PII (name, national ID, salary, tax data, bank account), employer org data | Employees, contractors of client companies (NO) | Art. 6(1)(b) contract performance; Art. 6(1)(c) legal obligation (Skatteforvaltningsloven, Folketrygdloven) | Duration of employment + 5 years (Bokføringsloven §13) | Skatteetaten (Norwegian Tax Admin), NAV, employer's bank | No |
| **Payroll Processing — Sweden** | Employee PII (name, personnummer, salary, tax data, bank account), employer org data | Employees, contractors of client companies (SE) | Art. 6(1)(b) contract performance; Art. 6(1)(c) legal obligation (Skatteförfarandelagen, Socialavgiftslagen) | Duration of employment + 7 years (Bokföringslagen 7 kap. §2) | Skatteverket (Swedish Tax Agency), Försäkringskassan, employer's bank | No |
| **Payroll Processing — Finland** | Employee PII (name, henkilötunnus, salary, tax data, bank account), employer org data | Employees, contractors of client companies (FI) | Art. 6(1)(b) contract performance; Art. 6(1)(c) legal obligation (Ennakkoperintälaki, Kirjanpitolaki) | Duration of employment + 6 years (Kirjanpitolaki 2 luku §10) | Verohallinto (Finnish Tax Admin), Kela, employer's bank | No |
| **Banking Data (Aiia Open Banking)** | Bank account details, transaction history, balance data, payment initiation data | Client companies, their employees (for salary payments) | Art. 6(1)(b) contract performance; Art. 6(1)(c) legal obligation (PSD2) | Active relationship + 5 years (AML retention) | Aiia A/S (processor, Denmark — EEA), client's bank(s) | No (Aiia operates within EEA) |
| **Client Financial Data** | Invoices, ledger entries, accounts receivable/payable, VAT returns, annual accounts | Client companies, their customers/suppliers | Art. 6(1)(b) contract performance; Art. 6(1)(c) legal obligation (Bokføringsloven/Bokföringslagen/Kirjanpitolaki) | Active relationship + 5–7 years depending on jurisdiction | Tax authorities (NO/SE/FI), external auditors (when appointed) | No |
| **Employee PII (BPO Staff)** | Name, contact details, employment contract data, system access credentials | ClaudERP employees and contractors | Art. 6(1)(b) employment contract; Art. 6(1)(c) legal obligation | Duration of employment + 5 years | Payroll provider, tax authorities, pension provider | No |
| **AI Analysis (Claude API)** | Anonymised/pseudonymised financial documents, accounting queries, extracted entities | Client companies (indirectly) | Art. 6(1)(f) legitimate interest (efficient processing); Art. 6(1)(b) contract performance | Transient — API calls are stateless; no persistent storage by Anthropic under zero-retention data policy | Anthropic, Inc. (processor, USA) | Yes — USA. Safeguards: Standard Contractual Clauses (SCCs); Anthropic's zero-data-retention API policy; no model training on inputs |
| **Identity Verification** | Name, national ID number, proof-of-identity documents | Client company representatives, authorised signatories | Art. 6(1)(c) legal obligation (AML/KYC — Hvitvaskingsloven) | Active relationship + 5 years (AML retention) | None (processed internally) | No |
| **Audit Logging** | User IDs, IP addresses, timestamps, action descriptions, affected record IDs | All system users (BPO staff, client users) | Art. 6(1)(c) legal obligation (Bokføringsloven); Art. 6(1)(f) legitimate interest (security) | 5 years | Internal security team; law enforcement upon lawful request | No |
| **Email Delivery** | Recipient email address, subject line, delivery status, message body (transactional) | Client users, employees, authority contacts | Art. 6(1)(b) contract performance; Art. 6(1)(f) legitimate interest (operational notifications) | 90 days delivery logs; message content not stored after send | Email service provider (processor, EEA) | No |

---

## Technical Controls

The following technical measures are implemented to protect the processing activities listed above:

### Row-Level Security (RLS)
- PostgreSQL RLS policies enforce tenant isolation at the database level.
- Every query is scoped to the authenticated tenant via `current_setting('app.current_tenant_id')`.
- Verified by automated test suite: `test_rls.py`.

### Encryption at Rest
- All database volumes use AES-256 encryption.
- Secrets (API keys, credentials, tokens) are encrypted before storage via `services/secrets.py` using envelope encryption.
- Verified by automated test suite: `test_tier5_security.py`.

### Encryption in Transit
- All external connections require TLS 1.2+.
- Internal service-to-service communication uses mTLS.
- Aiia Open Banking connections use certificate-pinned HTTPS.

### Audit Logging
- All write operations and authentication events are logged to an append-only audit table.
- Logs include: user ID, tenant ID, timestamp, action, affected resource, source IP.
- Logs are retained for 5 years in compliance with Bokføringsloven.

### Access Control (RBAC)
- Role-based access control with principle of least privilege.
- Roles: `superadmin`, `tenant_admin`, `accountant`, `client_readonly`.
- MFA required for all administrative access.

### AI Data Handling
- Claude API is called under Anthropic's zero-data-retention policy — inputs are not used for training and are not stored beyond the API request lifecycle.
- PII is minimised before submission where feasible; national ID numbers are redacted.

---

## Review Schedule

This register must be reviewed:
- At least **annually** by the DPO.
- Whenever a **new processing activity** is introduced.
- Following any **data breach** or **regulatory inquiry**.

| Review Date | Reviewer | Changes Made |
|---|---|---|
| 2026-04-16 | [NAME] | Initial version |

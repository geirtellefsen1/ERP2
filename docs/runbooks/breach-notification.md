# Data Breach Notification Runbook

**Owner:** ClaudERP AS — Security & Compliance Team
**Last updated:** 2026-04-16
**Review cycle:** Annually or after any breach event

This runbook implements the notification obligations under Articles 33 and 34 of the GDPR,
as incorporated into Norwegian law via *Personopplysningsloven*. The supervisory authority
for ClaudERP AS is **Datatilsynet** (the Norwegian Data Protection Authority).

---

## Key Contacts

| Role | Name | Email | Phone |
|---|---|---|---|
| Data Protection Officer (DPO) | [NAME] | [EMAIL] | [PHONE] |
| Chief Technology Officer (CTO) | [NAME] | [EMAIL] | [PHONE] |
| Legal Counsel | [NAME] | [EMAIL] | [PHONE] |
| Supervisory Authority | Datatilsynet | post@datatilsynet.no | +47 22 39 69 00 |
| Datatilsynet breach portal | — | https://www.datatilsynet.no/rettigheter-og-plikter/virksomhetenes-plikter/avviksbehandling/ | — |

---

## The 72-Hour Clock

Under Article 33 GDPR, the controller must notify the supervisory authority **without undue
delay and, where feasible, not later than 72 hours** after becoming aware of a personal data
breach — unless the breach is unlikely to result in a risk to the rights and freedoms of
natural persons.

```
 Hour 0                    Hour 72
  │                          │
  ▼                          ▼
  DISCOVERY ─► TRIAGE ─► CONTAINMENT ─► ASSESSMENT ─► NOTIFICATION ─► REMEDIATION
  (T+0)        (T+1h)     (T+4h)        (T+24h)       (T+72h max)     (ongoing)
```

**If you are unsure whether an event constitutes a breach, treat it as one and start
the clock.** It is better to start the process and stand down than to miss the deadline.

---

## Step 1: Discovery (T+0)

**Objective:** Confirm the event and start the clock.

### Actions

1. **Record the exact time** the breach was discovered (or reported). This is T+0.
2. **Log the discovery** in the incident tracker with:
   - Who discovered / reported it
   - Initial description of what happened
   - Systems and data believed to be affected
3. **Notify the DPO and CTO immediately** via phone (do not rely solely on email).
4. **Do NOT attempt to fix the issue before notifying** — containment comes after triage.
5. **Preserve evidence** — do not delete logs, restart services, or alter affected systems
   unless required for containment.

### Discovery Sources

Breaches may be discovered through:
- Automated alerts (monitoring, anomaly detection, `audit_log` analysis)
- Staff observation (unusual data access, unexpected exports)
- External report (data subject, partner, security researcher)
- Third-party notification (Aiia, Anthropic, hosting provider)
- Regulatory inquiry (Datatilsynet, Skatteetaten, etc.)

---

## Step 2: Triage (T+0 to T+1h)

**Objective:** Assess scope and determine severity.

### Actions

1. **Assemble the incident team:**
   - DPO (mandatory)
   - CTO or on-call engineer
   - Legal counsel (if high severity)
2. **Classify the breach type:**
   - **Confidentiality breach** — unauthorised access or disclosure
   - **Integrity breach** — unauthorised alteration of data
   - **Availability breach** — loss of access to or destruction of data
3. **Determine scope:**
   - Which tenants are affected?
   - How many data subjects?
   - What categories of data? (payroll, banking, national IDs, financial records)
   - Which jurisdictions? (NO, SE, FI — may trigger parallel notification obligations)
4. **Assign severity:**
   - **Critical** — national ID numbers, bank accounts, or payroll data exposed; multiple tenants; evidence of exfiltration
   - **High** — PII exposed but limited scope; single tenant; no evidence of exfiltration
   - **Medium** — non-sensitive data exposed; availability breach with no data loss
   - **Low** — near-miss or contained before data exposure
5. **Document triage findings** in the incident tracker.

---

## Step 3: Containment (T+1h to T+4h)

**Objective:** Stop the breach from continuing or expanding.

### Actions

1. **Isolate affected systems** (e.g., revoke compromised credentials, disable affected
   user accounts, block suspicious IPs).
2. **Rotate secrets** if credential compromise is suspected — use `services/secrets.py`
   key rotation procedure.
3. **Revoke Aiia tokens** if banking integration is affected.
4. **Revoke Claude API keys** if AI integration is compromised.
5. **Enable enhanced logging** on affected systems if not already active.
6. **Verify RLS integrity** — run `test_rls.py` against production to confirm tenant
   isolation is intact.
7. **Take forensic snapshots** of affected database and application state before any
   remediation changes.
8. **Document all containment actions** with timestamps.

---

## Step 4: Assessment (T+4h to T+24h)

**Objective:** Determine whether notification is required and prepare content.

### Decision Tree

```
Is personal data involved?
├── No  → Log as security incident; no GDPR notification required
└── Yes
    └── Is the breach likely to result in a risk to rights and freedoms?
        ├── No  → Document reasoning; notify DPO; no authority notification required
        └── Yes
            └── Is the risk HIGH to rights and freedoms?
                ├── No  → Notify supervisory authority (Art. 33) within 72h
                └── Yes → Notify supervisory authority (Art. 33) AND data subjects (Art. 34)
```

### Assessment Criteria

Consider:
- **Nature of the data** — national IDs and bank accounts are high-risk; aggregated
  financial statistics are lower risk.
- **Volume** — how many data subjects are affected?
- **Ease of identification** — can affected individuals be identified from the exposed data?
- **Severity of consequences** — financial loss, identity theft, discrimination, reputational damage.
- **Special characteristics of data subjects** — employees may be vulnerable.
- **Whether data was encrypted** — if data was encrypted and keys were not compromised,
  risk may be low.

### Multi-Jurisdiction Considerations

| Jurisdiction | Supervisory Authority | Notes |
|---|---|---|
| Norway | Datatilsynet (primary — ClaudERP establishment) | Lead authority under one-stop-shop |
| Sweden | Integritetsskyddsmyndigheten (IMY) | Notify if substantially affects SE data subjects |
| Finland | Tietosuojavaltuutetun toimisto | Notify if substantially affects FI data subjects |

---

## Step 5: Notification (by T+72h)

### 5a: Supervisory Authority Notification (Article 33)

**Deadline:** 72 hours from discovery. If full details are not yet available, an initial
notification may be submitted with additional details provided in phases.

**Method:** Submit via Datatilsynet's online breach notification portal:
https://www.datatilsynet.no/rettigheter-og-plikter/virksomhetenes-plikter/avviksbehandling/

**Required content (Art. 33(3)):**

Use the template below.

### 5b: Data Subject Notification (Article 34)

**Required when:** the breach is likely to result in a **high risk** to the rights and
freedoms of natural persons.

**Method:** Direct communication (email to affected data subjects). If individual
notification is disproportionate, a public communication or similar measure may be used.

**Required content (Art. 34(2)):**

Use the template below.

---

## Step 6: Remediation (Ongoing)

### Actions

1. **Root cause analysis** — determine how the breach occurred and why existing controls
   did not prevent it.
2. **Implement fixes** — patch vulnerabilities, strengthen controls, update configurations.
3. **Verify fixes** — run relevant test suites (`test_rls.py`, `test_tier5_security.py`,
   `test_migration_*.py`) to confirm mitigations are effective.
4. **Update DPIA** — if the breach reveals new or underestimated risks, revise the
   Data Protection Impact Assessment (`docs/compliance/dpia.md`).
5. **Update this runbook** — incorporate lessons learned.
6. **Conduct postmortem** — follow the postmortem template in `docs/runbooks/incident.md`.
7. **Report to management** — provide a final incident report to the board / management.
8. **Follow up with Datatilsynet** — if an initial notification was submitted, provide the
   final detailed report once the investigation is complete.

---

## Templates

### Template A: Internal Incident Report

```
INTERNAL — DATA BREACH INCIDENT REPORT

Incident ID:        [INC-YYYY-NNN]
Discovery time:     [YYYY-MM-DD HH:MM UTC]
Reported by:        [Name, role]
Classification:     [Confidentiality / Integrity / Availability]
Severity:           [Critical / High / Medium / Low]

DESCRIPTION
-----------
[What happened, in plain language]

SCOPE
-----
Tenants affected:    [List or count]
Data subjects:       [Approximate count]
Data categories:     [e.g., employee names, national IDs, bank accounts]
Jurisdictions:       [NO / SE / FI]

TIMELINE
--------
T+0  [HH:MM] — Discovery: [description]
T+X  [HH:MM] — Triage: [description]
T+X  [HH:MM] — Containment: [actions taken]
T+X  [HH:MM] — Assessment: [conclusion]
T+X  [HH:MM] — Notification: [authority / data subjects / not required]

CONTAINMENT ACTIONS
-------------------
1. [Action taken, timestamp]
2. [Action taken, timestamp]

ROOT CAUSE
----------
[Preliminary or final root cause analysis]

REMEDIATION
-----------
1. [Fix applied or planned, owner, deadline]
2. [Fix applied or planned, owner, deadline]

NOTIFICATION STATUS
-------------------
Authority notified:        [Yes / No — date and reference number if yes]
Data subjects notified:    [Yes / No — method and date if yes]
Reason if not notified:    [Explain if notification not required]

Prepared by:    [Name]
Reviewed by:    [DPO name]
Date:           [YYYY-MM-DD]
```

### Template B: Supervisory Authority Notification (Art. 33)

```
PERSONAL DATA BREACH NOTIFICATION — DATATILSYNET

1. CONTROLLER
   Name:               ClaudERP AS
   Org. number:        [ORG NUMBER]
   Address:            [ADDRESS]
   DPO contact:        [NAME], [EMAIL], [PHONE]

2. BREACH DETAILS
   Date/time of breach:         [YYYY-MM-DD HH:MM UTC, or "unknown"]
   Date/time of discovery:      [YYYY-MM-DD HH:MM UTC]
   Nature of breach:            [Confidentiality / Integrity / Availability]
   Description:                 [Clear description of what occurred]

3. DATA AND DATA SUBJECTS
   Categories of data subjects: [e.g., employees of client companies in Norway]
   Approximate number:          [count or range]
   Categories of data:          [e.g., names, national ID numbers, salary data]
   Approximate number of records: [count or range]

4. CONSEQUENCES
   Likely consequences:         [e.g., risk of identity theft, financial loss]

5. MEASURES TAKEN
   Containment measures:        [What was done to stop the breach]
   Remediation measures:        [What is being done to prevent recurrence]
   Data subject notification:   [Whether data subjects have been / will be notified]

6. ADDITIONAL INFORMATION
   [Any other relevant details; indicate if this is an initial or supplementary notification]

Submitted by:   [Name, title]
Date:           [YYYY-MM-DD]
Reference:      [INC-YYYY-NNN]
```

### Template C: Data Subject Notification (Art. 34)

```
Subject: Important notice about your personal data — ClaudERP

Dear [Name / "Valued User"],

We are writing to inform you of a personal data breach that may affect your
personal information.

WHAT HAPPENED
[Plain-language description of the breach — what occurred and when.]

WHAT DATA WAS AFFECTED
[List the categories of personal data involved, e.g., your name, national ID number,
salary information.]

WHAT WE HAVE DONE
[Description of containment and remediation measures taken.]

WHAT YOU CAN DO
[Practical advice, e.g.:
- Monitor your bank statements for unusual activity.
- Be alert for phishing emails or calls referencing your employer.
- Contact your bank if you suspect misuse of your account details.
- You may request a credit check freeze from [relevant credit bureau].]

CONTACT
If you have questions or wish to exercise your data protection rights, please contact
our Data Protection Officer:

  Name:   [DPO NAME]
  Email:  [DPO EMAIL]
  Phone:  [DPO PHONE]

You also have the right to lodge a complaint with the supervisory authority:

  Datatilsynet
  https://www.datatilsynet.no
  post@datatilsynet.no
  +47 22 39 69 00

We sincerely apologise for this incident and are taking all necessary steps to
prevent recurrence.

Regards,
[Name]
[Title]
ClaudERP AS
```

---

## Post-Incident Review

After every breach (including near-misses), conduct a review within **5 business days**:

1. Was the breach detected promptly? If not, what monitoring gaps exist?
2. Was the 72-hour notification deadline met? If not, why?
3. Were containment actions effective and timely?
4. Does the DPIA need to be updated?
5. Does this runbook need to be updated?
6. Are additional technical controls needed?
7. Is staff training adequate?

Document findings and actions in the postmortem (see `docs/runbooks/incident.md`).

---

## Revision History

| Date | Author | Changes |
|---|---|---|
| 2026-04-16 | [NAME] | Initial version |

# Incident Response Runbook — ClaudERP

**Owner:** ClaudERP AS — Engineering & Operations Team
**Last updated:** 2026-04-16
**Review cycle:** Semi-annually or after any P1/P2 incident

---

## Severity Matrix

| Severity | Definition | Examples | Response SLA | Update Cadence |
|---|---|---|---|---|
| **P1 — Critical** | Total platform outage or data breach affecting multiple tenants | Full outage; confirmed data breach; complete loss of payroll processing | **15 minutes** | Every 30 minutes |
| **P2 — Major** | Major feature broken; single-tenant data issue; degraded but not down | Aiia banking integration down; payroll engine failing for one jurisdiction; auth service broken | **30 minutes** | Every 1 hour |
| **P3 — Minor** | Minor degradation; non-critical feature affected; workaround available | Slow report generation; email delivery delays; non-blocking UI errors | **2 hours** | Every 4 hours |
| **P4 — Cosmetic** | Cosmetic issue; minor inconvenience; no business impact | UI alignment bug; typo in notification; minor logging issue | **Next business day** | Upon resolution |

### Escalation Rules

- Any incident not resolved within **2x the response SLA** escalates to the next severity level.
- P1 and P2 incidents automatically page the CTO.
- Any suspected data breach immediately triggers the breach notification runbook
  (`docs/runbooks/breach-notification.md`) regardless of initial severity classification.

---

## First Responder Checklist

When you are alerted to an incident, follow these steps in order:

- [ ] **Acknowledge** the alert within the response SLA for the assessed severity.
- [ ] **Assess severity** using the matrix above. When in doubt, classify higher.
- [ ] **Open an incident channel** (e.g., `#incident-YYYY-MM-DD` in Slack or equivalent).
- [ ] **Post the initial situation report** using the communication template below.
- [ ] **Assign roles:**
  - **Incident Commander (IC):** Owns coordination and communication.
  - **Technical Lead:** Owns diagnosis and remediation.
  - **Communicator:** Owns external/customer communication (P1/P2 only).
- [ ] **Begin diagnosis** — check dashboards, logs, and recent deployments.
- [ ] **Contain the impact** — if possible, mitigate before full root cause analysis.
- [ ] **Communicate** status updates at the cadence specified for the severity level.
- [ ] **Resolve** the incident and confirm with monitoring.
- [ ] **Close** the incident channel and schedule the postmortem (P1/P2 mandatory; P3 optional).

---

## Scenario Playbooks

### Scenario 1: Full Platform Outage (P1)

**Symptoms:** All users unable to access the platform; health checks failing; no API responses.

**Likely causes:** Infrastructure failure, DNS issue, database outage, misconfigured deployment.

**Steps:**
1. Check infrastructure provider status page for region-wide outage.
2. Verify DNS resolution: `dig clauderp.com` / check DNS provider dashboard.
3. Check load balancer / reverse proxy health and configuration.
4. Check application pods/containers: are they running? Check for crash loops.
5. Check database connectivity: `pg_isready -h <host>`.
6. Check recent deployments — if a deploy occurred within the last 2 hours, consider rollback.
7. If database is down:
   - Check disk space, connection limits, replication lag.
   - Attempt restart; if corruption suspected, fail over to replica.
8. If application is down but DB is healthy:
   - Check application logs for startup errors.
   - Verify environment variables and secrets are accessible.
   - Rollback to the last known good deployment.
9. Once restored, verify with smoke tests and confirm monitoring is green.

### Scenario 2: Data Breach (P1)

**Symptoms:** Unauthorised data access detected; external report of data exposure; anomalous data export patterns.

**Steps:**
1. **Immediately** invoke the breach notification runbook: `docs/runbooks/breach-notification.md`.
2. Notify DPO and CTO by phone.
3. Preserve evidence — do not restart services or delete logs.
4. Identify the attack vector and scope.
5. Contain: revoke compromised credentials, block suspicious IPs, disable affected accounts.
6. Run `test_rls.py` against production to verify tenant isolation integrity.
7. Run `test_tier5_security.py` to verify secrets encryption.
8. Take forensic database snapshot.
9. Follow breach runbook for assessment, notification, and remediation.

### Scenario 3: Claude API Outage (P2)

**Symptoms:** AI-assisted features returning errors or timing out; Claude API returning 5xx or rate limit responses.

**Steps:**
1. Check Anthropic status page: https://status.anthropic.com
2. Check Claude API error responses — distinguish between rate limiting (429) and outage (5xx).
3. If rate-limited:
   - Review recent usage for unexpected spikes.
   - Enable request queuing / backoff if not already active.
4. If API is down:
   - Enable graceful degradation: AI features should show "temporarily unavailable" message.
   - Manual processing workflows remain available for critical tasks.
   - No payroll or banking operations are blocked — AI is advisory only.
5. Monitor Anthropic status page for resolution.
6. Once restored, process any queued AI requests.
7. No data loss expected — AI calls are stateless.

### Scenario 4: Aiia Banking Integration Outage (P2)

**Symptoms:** Bank connections failing; transaction sync not completing; payment initiation errors.

**Steps:**
1. Check Aiia status page / partner dashboard.
2. Check if the issue is all banks or specific banks / regions.
3. Check Aiia API error responses and OAuth token validity.
4. If token expired: trigger token refresh flow.
5. If Aiia is down:
   - Pause automated payment initiation — do NOT retry payments blindly.
   - Notify affected tenants that bank sync is temporarily delayed.
   - Queue pending payments for retry once service is restored.
   - Manual bank file import (CSV/CAMT) remains available as fallback.
6. Once restored:
   - Process queued payments with duplicate detection enabled.
   - Trigger full transaction sync to reconcile any gaps.
   - Verify reconciliation completeness before closing.

### Scenario 5: Payroll Calculation Error (P2)

**Symptoms:** Payroll run produces incorrect figures; tax calculations do not match expected values; employee/employer reports a discrepancy.

**Steps:**
1. **Do NOT submit affected payroll runs** to tax authorities until resolved.
2. Identify scope: which jurisdiction (NO/SE/FI), which tenants, which payroll period.
3. Check whether the error is in:
   - Rate tables (tax rates, social security rates) — compare against official rates.
   - Calculation logic — review recent code changes to payroll engine.
   - Input data — incorrect employee data or configuration.
4. If rate tables are outdated:
   - Update rate tables from authoritative source.
   - Recalculate affected payroll runs.
5. If calculation logic is wrong:
   - Revert to last known good version if recently deployed.
   - Fix and deploy with expedited review.
   - Recalculate all affected payroll runs.
6. Notify affected tenants with corrected figures.
7. If payroll was already submitted to authorities:
   - Prepare correction filings per jurisdiction requirements.
   - Notify affected employees if net pay was impacted.
8. Conduct root cause analysis — add regression tests for the specific failure.

### Scenario 6: TLS Certificate Expiry (P3)

**Symptoms:** Browser certificate warnings; API clients failing with SSL errors; monitoring alerts for certificate expiry.

**Steps:**
1. Identify which certificate(s) expired or are about to expire.
2. Check if automated certificate renewal (e.g., Let's Encrypt / cert-manager) is configured.
3. If automated renewal failed:
   - Check renewal logs for errors (DNS challenge failure, rate limits, permissions).
   - Manually trigger certificate renewal.
4. If manual certificate:
   - Generate CSR, obtain new certificate from CA, install.
5. Verify new certificate is deployed: `openssl s_client -connect <host>:443`.
6. Verify no certificate pinning issues with Aiia or other partners.
7. Add monitoring for certificate expiry (alert at 30, 14, and 7 days before expiry).
8. Consider migrating to automated certificate management if not already in place.

---

## Communication Templates

### Internal Status Update (Incident Channel)

```
INCIDENT UPDATE — [INC-YYYY-NNN]

Severity:    [P1/P2/P3/P4]
Status:      [Investigating / Identified / Mitigating / Resolved]
IC:          [Name]
Tech Lead:   [Name]

CURRENT SITUATION
[What is happening right now. What is broken. Who is affected.]

ACTIONS TAKEN
- [Action 1 — timestamp]
- [Action 2 — timestamp]

NEXT STEPS
- [What we are doing next]

ETA TO RESOLUTION
[Estimate or "unknown"]

NEXT UPDATE
[Time of next scheduled update]
```

### Customer Communication (P1/P2)

```
Subject: [ClaudERP] Service Disruption — [Brief Description]

We are currently experiencing [brief description of the issue].

Impact: [What is affected — e.g., "bank synchronisation is temporarily unavailable"]
Start time: [HH:MM UTC, YYYY-MM-DD]
Status: [Investigating / Identified / Mitigating]

We are actively working to resolve this issue. [Workaround if available.]

We will provide an update by [time].

— ClaudERP Operations Team
```

### Customer Resolution Notification

```
Subject: [ClaudERP] Resolved — [Brief Description]

The service disruption reported at [start time] has been resolved at [resolution time].

Root cause: [Brief, non-technical explanation]
Duration: [X hours Y minutes]
Impact: [What was affected]

We apologise for the inconvenience. A detailed review is underway to prevent recurrence.

— ClaudERP Operations Team
```

---

## Postmortem Template

A postmortem is **mandatory** for P1 and P2 incidents, and **recommended** for P3 incidents.
The postmortem should be completed within **5 business days** of resolution.

```
POSTMORTEM — [INC-YYYY-NNN]

Date:           [YYYY-MM-DD]
Severity:       [P1/P2/P3]
Duration:       [Start time — End time (total duration)]
Authors:        [Names]
Reviewers:      [Names]

SUMMARY
[2-3 sentence summary of what happened and the impact.]

TIMELINE (UTC)
HH:MM — [Event]
HH:MM — [Event]
HH:MM — [Event]

ROOT CAUSE
[Detailed technical explanation of why the incident occurred.]

IMPACT
- Users affected:     [count or description]
- Tenants affected:   [count or description]
- Duration:           [X hours Y minutes]
- Data loss:          [Yes/No — details if yes]
- SLA impact:         [Was the SLA breached? Credit implications?]

WHAT WENT WELL
- [Thing that worked]
- [Thing that worked]

WHAT WENT WRONG
- [Thing that failed or was too slow]
- [Thing that failed or was too slow]

WHERE WE GOT LUCKY
- [Something that could have been worse]

ACTION ITEMS
| Action | Owner | Priority | Deadline | Status |
|---|---|---|---|---|
| [Fix / improvement] | [Name] | [P1-P4] | [Date] | [Open/Done] |

LESSONS LEARNED
[Key takeaways for the team.]

DATA BREACH IMPLICATIONS
[Was personal data affected? If yes, reference breach notification runbook and INC ID.
If no, state "No personal data was affected."]
```

---

## On-Call Responsibilities

- The on-call engineer is the default first responder for all automated alerts.
- On-call rotation is weekly, Monday 09:00 UTC to Monday 09:00 UTC.
- On-call engineer must:
  - Acknowledge P1 alerts within 15 minutes, P2 within 30 minutes.
  - Have laptop and internet access available at all times during on-call shift.
  - Escalate if unable to respond (backup on-call).
- After-hours P1/P2 pages go to both primary and backup on-call simultaneously.

---

## Related Documents

- Breach Notification Runbook: `docs/runbooks/breach-notification.md`
- Data Protection Impact Assessment: `docs/compliance/dpia.md`
- Records of Processing Activities: `docs/compliance/ropa.md`
- Service Level Agreement: `docs/public/sla.md`

---

## Revision History

| Date | Author | Changes |
|---|---|---|
| 2026-04-16 | [NAME] | Initial version |

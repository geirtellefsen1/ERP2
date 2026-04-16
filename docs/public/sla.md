# Service Level Agreement — ClaudERP

**Effective date:** 2026-04-16
**Last updated:** 2026-04-16
**Version:** 1.0

This Service Level Agreement ("SLA") applies to the ClaudERP platform services provided
by ClaudERP AS ("Provider") to its customers ("Customer"). This SLA is incorporated by
reference into the Master Services Agreement between the parties.

---

## 1. Uptime Commitment

### 1.1 Monthly Uptime Target

The Provider commits to a **99.9% monthly uptime** target for the ClaudERP platform,
measured as the percentage of total minutes in a calendar month during which the platform
is available for normal use.

### 1.2 Uptime Calculation

```
Monthly Uptime % = ((Total Minutes in Month − Downtime Minutes) / Total Minutes in Month) × 100
```

**Downtime** is defined as any period of 5 or more consecutive minutes during which
the platform's primary functions (authentication, payroll processing, financial data
access, banking integration) are unavailable to the Customer, as measured by the
Provider's external monitoring systems.

### 1.3 What Counts as Downtime

- Platform returns HTTP 5xx errors for >50% of requests over a 5-minute window.
- Users are unable to authenticate.
- Core payroll or financial data is inaccessible.
- Banking integration (Aiia) is non-functional due to Provider-side issues.

### 1.4 What Does NOT Count as Downtime

See Section 4 (Exclusions).

---

## 2. Service Credit Schedule

If the Provider fails to meet the monthly uptime target, the Customer is entitled to
service credits as follows:

| Monthly Uptime | Service Credit (% of monthly fee) |
|---|---|
| 99.0% to < 99.9% | **10%** |
| 99.0% to < 99.5% | **25%** |
| < 99.0% | **50%** |

### 2.1 Credit Terms

- Service credits are applied to the **next monthly invoice**. Credits are not paid out
  in cash and are not transferable.
- The maximum credit in any calendar month is **50% of that month's fees**.
- Credits must be requested by the Customer within **30 days** of the end of the
  affected month, by contacting support@clauderp.com with the subject line
  "SLA Credit Request — [Month/Year]".
- The Provider will validate the claim against its monitoring records and respond
  within **10 business days**.

### 2.2 Credit Calculation Example

> A Growth-tier customer paying 10,000 NOK/month experiences 99.3% uptime in March.
> This falls in the <99.5% bracket.
> Credit = 25% x 10,000 NOK = **2,500 NOK** applied to the April invoice.

---

## 3. Support Tiers

Response times below apply to support requests submitted through the designated support
channels for each tier.

| | **Starter** | **Growth** | **Enterprise** |
|---|---|---|---|
| **Channels** | Email | Email + Chat | Dedicated account manager + Email + Chat + Phone |
| **P1 (Critical) response** | 24 hours | 8 hours | 1 hour |
| **P2 (Major) response** | 24 hours | 8 hours | 2 hours |
| **P3 (Minor) response** | 48 hours | 24 hours | 8 hours |
| **P4 (Cosmetic) response** | Best effort | 48 hours | 24 hours |
| **Support hours** | Business hours (CET) | Business hours (CET) | 24/7 |
| **Dedicated CSM** | No | No | Yes |
| **Custom integrations support** | No | Limited | Full |

### 3.1 Severity Definitions

| Severity | Definition |
|---|---|
| **P1 — Critical** | Total platform outage; complete inability to process payroll or access financial data. |
| **P2 — Major** | Major feature broken (e.g., banking integration, payroll engine for one jurisdiction); no workaround. |
| **P3 — Minor** | Minor degradation; feature partially working; workaround available. |
| **P4 — Cosmetic** | UI issue, typo, or minor inconvenience with no business impact. |

### 3.2 Response vs. Resolution

- **Response time** is the time from ticket submission to first meaningful human response
  (automated acknowledgements do not count).
- **Resolution time** is best-effort and depends on complexity. The Provider will communicate
  estimated resolution times upon triage.

---

## 4. Exclusions

The following are **not** counted as downtime and do not qualify for service credits:

### 4.1 Scheduled Maintenance

- The Provider may perform scheduled maintenance during designated windows.
- Customers will be notified at least **48 hours in advance** via email and in-app banner.
- Scheduled maintenance windows will not exceed **4 hours per occurrence** and will be
  planned outside peak business hours (typically weekends or 22:00-06:00 CET).
- Scheduled maintenance is limited to **8 hours per calendar month**.

### 4.2 Force Majeure

Downtime caused by events beyond the Provider's reasonable control, including but not
limited to:
- Natural disasters, war, terrorism, or civil unrest.
- Government actions or regulatory orders.
- Internet backbone failures or DNS infrastructure outages.
- Pandemic-related disruptions.

### 4.3 Customer-Caused Issues

Downtime or degradation caused by:
- Customer's own systems, networks, or internet connectivity.
- Customer's misuse of the platform or violation of acceptable use policies.
- Customer-requested configuration changes.
- Customer's failure to maintain supported browser/client versions.

### 4.4 Third-Party Service Outages

Downtime in third-party services that are outside the Provider's control:
- Banking provider (Aiia) outages caused by upstream bank issues.
- Tax authority system outages (Skatteetaten, Skatteverket, Verohallinto).
- Claude API (Anthropic) outages — AI features are advisory and non-blocking.

The Provider will use commercially reasonable efforts to mitigate the impact of
third-party outages and will communicate status to affected customers.

---

## 5. Reporting and Transparency

### 5.1 Uptime Dashboard

The Provider will maintain a public status page displaying real-time and historical
platform availability.

### 5.2 Monthly Uptime Reports

Enterprise-tier customers receive a monthly uptime report including:
- Actual uptime percentage.
- List of incidents (if any) with duration and root cause summary.
- SLA credit status (if applicable).

### 5.3 Incident Communication

- P1 incidents: status updates every 30 minutes until resolution.
- P2 incidents: status updates every 1 hour until resolution.
- Post-incident reports (postmortem summaries) shared within 5 business days for P1/P2 incidents.

---

## 6. Customer Obligations

To receive the benefits of this SLA, the Customer must:
- Use the platform in accordance with the acceptable use policy.
- Maintain current contact information for incident notifications.
- Report issues promptly through designated support channels.
- Cooperate with the Provider in troubleshooting and resolving issues.

---

## 7. SLA Review

This SLA is reviewed annually. The Provider reserves the right to update this SLA with
**30 days written notice** to the Customer. Material changes that reduce service levels
will not take effect until the next contract renewal period.

---

## 8. Definitions

| Term | Definition |
|---|---|
| **Platform** | The ClaudERP web application, API, and associated services. |
| **Downtime** | A period of 5+ consecutive minutes where primary platform functions are unavailable. |
| **Business Hours** | Monday to Friday, 08:00 to 17:00 CET, excluding Norwegian public holidays. |
| **Monthly Fee** | The subscription fee for the Customer's tier in the affected month. |

---

## Revision History

| Date | Version | Author | Changes |
|---|---|---|---|
| 2026-04-16 | 1.0 | [NAME] | Initial version |

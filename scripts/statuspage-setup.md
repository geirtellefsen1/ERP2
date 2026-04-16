# Status Page Setup Guide — ClaudERP

This guide covers setting up uptime monitoring and a public status page for
ClaudERP. Choose **Option A** for production use or **Option B** for a
self-hosted, zero-cost alternative.

---

## Monitored Endpoints

| Service        | URL                                    | Expected | Interval |
|----------------|----------------------------------------|----------|----------|
| API health     | https://erp.tellefsen.org/health       | 200      | 60 s     |
| Web frontend   | https://erp.tellefsen.org/             | 200      | 60 s     |
| Client portal  | https://erp.tellefsen.org/portal       | 200/302  | 180 s    |

### Alert Thresholds

- **Degraded** — 2 consecutive check failures
- **Major outage** — 5 consecutive check failures

---

## Option A: BetterStack (recommended for production)

BetterStack (formerly Better Uptime) provides hosted monitoring, incident
management, and a branded status page.

### 1. Create account & team

1. Sign up at <https://betterstack.com/>.
2. Create a team called **ClaudERP Ops**.

### 2. Add monitors

Create three monitors with the URLs listed above. Set:

- **Check frequency**: 60 s for API and Web, 180 s for Portal.
- **Request timeout**: 15 s.
- **Confirmation period**: 120 s (API/Web), 300 s (Portal).

Group all three under a monitor group named **ClaudERP**.

### 3. Configure alerting

- **Email** — add the on-call distribution list.
- **Slack webhook** — create an incoming webhook in Slack and paste it into
  BetterStack's Slack integration settings. Route alerts to `#ops-alerts`.

### 4. Public status page

- Subdomain: `status-clauderp` (BetterStack-hosted) or custom domain
  `status.tellefsen.org`.
- Add all three monitors as resources with public names: **API**,
  **Web Application**, **Client Portal**.
- Set timezone to `Europe/Oslo`.

### 5. Terraform (optional)

The Terraform configuration in `infra/uptime/betterstack_monitor.tf` can
provision all of the above automatically. See `infra/uptime/README.md` for
instructions.

---

## Option B: Self-hosted with Upptime (GitHub Actions)

[Upptime](https://upptime.js.org/) runs entirely on GitHub Actions and
publishes results to GitHub Pages — no external service required.

### 1. Fork the template

Fork <https://github.com/upptime/upptime> into your organisation.

### 2. Configure `.upptimerc.yml`

```yaml
owner: tellefsen-group
repo: clauderp-status

sites:
  - name: API
    url: https://erp.tellefsen.org/health
    expectedStatusCodes:
      - 200

  - name: Web Application
    url: https://erp.tellefsen.org/
    expectedStatusCodes:
      - 200

  - name: Client Portal
    url: https://erp.tellefsen.org/portal
    expectedStatusCodes:
      - 200
      - 302

status-website:
  cname: status.tellefsen.org
  name: ClaudERP Status
  theme: light

notifications:
  - type: slack
    channel: ops-alerts
```

### 3. Enable GitHub Pages

In **Settings > Pages**, set the source to the `gh-pages` branch.

### 4. Custom domain

Add a CNAME record `status.tellefsen.org -> <org>.github.io` and set the
`cname` field in `.upptimerc.yml`.

---

## DNS

Regardless of option chosen, create the following DNS record when ready:

```
status.tellefsen.org  CNAME  <provider-target>
```

Replace `<provider-target>` with the value from BetterStack or GitHub Pages.

# Cloudflare Zone — erp.tellefsen.org

Terraform configuration that provisions a Cloudflare zone in front of the
origin server (Caddy) with WAF, bot management, rate limiting, and TLS
hardening.

## What this provisions

| Resource | Purpose |
|---|---|
| `cloudflare_zone` | Pro-plan zone for `tellefsen.org` |
| `cloudflare_record` | Proxied A record for `erp.tellefsen.org` |
| `cloudflare_ruleset` (WAF) | Cloudflare Managed + OWASP Core Rule Set |
| `cloudflare_bot_management` | Bot Fight Mode enabled |
| `cloudflare_zone_settings_override` | SSL strict, TLS 1.2+, always HTTPS |
| `cloudflare_ruleset` (rate limit) | 100 req/min per IP on `/api/*` |

## Prerequisites

- Terraform >= 1.5.0
- A Cloudflare API token with Zone:Edit, DNS:Edit, WAF:Edit permissions
- The Cloudflare account ID
- The origin server's public IP address

## Init and plan

```bash
cd infra/cloudflare

# Set variables (use a terraform.tfvars file or env vars)
export TF_VAR_cloudflare_api_token="your-api-token"
export TF_VAR_cloudflare_account_id="your-account-id"
export TF_VAR_origin_ip="your-origin-ip"

terraform init
terraform plan
terraform apply
```

Do NOT commit `terraform.tfvars` — it contains secrets.

## Cutover steps

1. Run `terraform apply` — this creates the zone and DNS records in
   Cloudflare, but traffic will not flow through Cloudflare until the
   domain's NS records are updated.
2. Note the `nameservers` output (two Cloudflare NS hostnames).
3. Log in to your domain registrar for `tellefsen.org`.
4. Replace the existing NS records with the Cloudflare nameservers.
5. Wait for DNS propagation (typically 15 min to 48 hours).
6. Verify the orange cloud is active:
   ```bash
   dig erp.tellefsen.org +short
   # Should return Cloudflare IPs, not the origin IP
   curl -sI https://erp.tellefsen.org | grep -i cf-ray
   # Should contain a cf-ray header
   ```
7. Confirm WAF is active in the Cloudflare dashboard under Security > WAF.

## Rollback

If issues arise after cutover:

1. Log in to your domain registrar for `tellefsen.org`.
2. Revert the NS records to the previous nameservers.
3. Cloudflare will stop proxying traffic once the NS change propagates
   (within the previous TTL, typically minutes to hours).
4. The origin server (Caddy) continues serving traffic directly — no
   downtime expected during rollback.
5. Optionally run `terraform destroy` to clean up the Cloudflare zone.

## Deployment docs

JR-DEPLOYMENT.md does not currently exist at the repo root. When deployment
documentation is created, it should reference this Cloudflare configuration
and include the cutover/rollback procedures above.

# Uptime Monitoring — Terraform (BetterStack)

This directory contains Terraform configuration for provisioning uptime
monitors and a public status page via BetterStack.

## Prerequisites

- Terraform >= 1.0
- A BetterStack account with an API token (Settings > API tokens).

## Usage

### 1. Set the API token

```bash
export TF_VAR_betterstack_api_token="<your-token>"
```

Or create a `terraform.tfvars` file (**do not commit this file**):

```hcl
betterstack_api_token = "<your-token>"
```

### 2. Initialise and apply

```bash
cd infra/uptime
terraform init
terraform plan   # review the changes
terraform apply  # provision monitors + status page
```

### 3. Verify

After applying, check the BetterStack dashboard to confirm all monitors are
active and the status page is reachable at
`https://status-clauderp.betteruptime.com` (or `status.tellefsen.org` once the
CNAME is configured).

## Resources Created

| Resource                | Description                          |
|-------------------------|--------------------------------------|
| Monitor — API health    | Checks `/health` every 60 s         |
| Monitor — Web           | Checks `/` every 60 s               |
| Monitor — Portal        | Checks `/portal` every 180 s        |
| Monitor group           | Groups all monitors under "ClaudERP" |
| Status page             | Public page at `status-clauderp`     |
| Status page resources   | Exposes all 3 monitors on the page   |

## Teardown

```bash
terraform destroy
```

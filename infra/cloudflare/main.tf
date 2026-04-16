# ClaudERP — Cloudflare WAF + DDoS zone config
# Provisions a Cloudflare zone in front of erp.tellefsen.org
# with WAF managed rules, bot management, rate limiting, and TLS hardening.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# Variables
# ─────────────────────────────────────────────────────────────────────────────

variable "cloudflare_api_token" {
  type      = string
  sensitive = true
}

variable "cloudflare_account_id" {
  type      = string
  sensitive = true
}

variable "zone_name" {
  type    = string
  default = "tellefsen.org"
}

variable "origin_ip" {
  type        = string
  description = "IP address of the origin server running Caddy"
}

# ─────────────────────────────────────────────────────────────────────────────
# Provider
# ─────────────────────────────────────────────────────────────────────────────

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

# ─────────────────────────────────────────────────────────────────────────────
# Zone
# ─────────────────────────────────────────────────────────────────────────────

resource "cloudflare_zone" "main" {
  account_id = var.cloudflare_account_id
  zone       = var.zone_name
  plan       = "pro"
}

# ─────────────────────────────────────────────────────────────────────────────
# DNS Records — proxied (orange-cloud)
# ─────────────────────────────────────────────────────────────────────────────

resource "cloudflare_record" "erp" {
  zone_id = cloudflare_zone.main.id
  name    = "erp"
  content = var.origin_ip
  type    = "A"
  proxied = true
  ttl     = 1 # auto when proxied
}

# ─────────────────────────────────────────────────────────────────────────────
# WAF Managed Rules — OWASP Core Rule Set
# ─────────────────────────────────────────────────────────────────────────────

resource "cloudflare_ruleset" "waf_managed" {
  zone_id     = cloudflare_zone.main.id
  name        = "WAF Managed Rules"
  description = "OWASP CRS + Cloudflare Managed"
  kind        = "zone"
  phase       = "http_request_firewall_managed"

  rules {
    action = "execute"
    action_parameters {
      id = "efb7b8c949ac4650a09736fc376e9aee" # Cloudflare Managed Ruleset
    }
    expression  = "true"
    description = "Cloudflare Managed Ruleset"
    enabled     = true
  }

  rules {
    action = "execute"
    action_parameters {
      id = "4814384a9e5d4991b9815dcfc25d2f1f" # OWASP Core Rule Set
    }
    expression  = "true"
    description = "OWASP Core Rule Set"
    enabled     = true
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# Bot Fight Mode
# ─────────────────────────────────────────────────────────────────────────────

resource "cloudflare_bot_management" "main" {
  zone_id    = cloudflare_zone.main.id
  fight_mode = true
}

# ─────────────────────────────────────────────────────────────────────────────
# Security Level + TLS hardening
# ─────────────────────────────────────────────────────────────────────────────

resource "cloudflare_zone_settings_override" "security" {
  zone_id = cloudflare_zone.main.id
  settings {
    security_level   = "medium"
    ssl              = "strict"
    min_tls_version  = "1.2"
    always_use_https = "on"
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# Rate limiting on API endpoints
# ─────────────────────────────────────────────────────────────────────────────

resource "cloudflare_ruleset" "rate_limit" {
  zone_id     = cloudflare_zone.main.id
  name        = "API Rate Limiting"
  description = "Rate limit API endpoints"
  kind        = "zone"
  phase       = "http_ratelimit"

  rules {
    action = "block"
    ratelimit {
      characteristics     = ["ip.src"]
      period              = 60
      requests_per_period = 100
      mitigation_timeout  = 600
    }
    expression  = "(http.request.uri.path matches \"^/api/\")"
    description = "Rate limit API: 100 req/min per IP"
    enabled     = true
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# Outputs
# ─────────────────────────────────────────────────────────────────────────────

output "zone_id" {
  value = cloudflare_zone.main.id
}

output "nameservers" {
  value = cloudflare_zone.main.name_servers
}

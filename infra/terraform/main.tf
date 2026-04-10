# BPO Nexus — DigitalOcean Infrastructure
# Sprint 1: Base provider + project setup
# Sprints 3-7 will add actual resources

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}

# ─────────────────────────────────────────────────────────────────────────────
# Variables
# ─────────────────────────────────────────────────────────────────────────────

variable "do_token" {
  description = "DigitalOcean API token"
  sensitive   = true
  default     = ""  # Set via DO_TOKEN env var or terraform.tfvars
}

variable "project_name" {
  description = "DigitalOcean project name"
  default     = "bpo-nexus"
}

variable "region" {
  description = "Primary region"
  default     = "cap-1"  # Cape Town
}

variable "environments" {
  description = "Available environments"
  type        = map(string)
  default = {
    dev    = "Development"
    staging = "Staging"
    prod   = "Production"
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# Resources — Added in later sprints
# ─────────────────────────────────────────────────────────────────────────────
# Sprint 5:  Droplet for API + background workers
# Sprint 6:  Managed PostgreSQL cluster
# Sprint 6:  Managed Redis cluster
# Sprint 7:  Spaces bucket for file storage
# Sprint 9:  Load balancer for staging/prod
# ─────────────────────────────────────────────────────────────────────────────

# Placeholder to validate provider connection early
data "digitalocean droplet" "validation" {
  name = "placeholder-do-not-deploy"
}

output "terraform_version" {
  value       = terraform.version
  description = "Terraform version used"
}

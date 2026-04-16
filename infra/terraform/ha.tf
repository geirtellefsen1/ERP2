# BPO Nexus — High Availability Resources
# ADR 0002: Read replica + multi-replica API behind load balancer
# Status: PLANNED — do NOT apply without full review

# ─────────────────────────────────────────────────────────────────────────────
# Variables
# ─────────────────────────────────────────────────────────────────────────────

variable "api_replica_count" {
  description = "Number of API droplets behind the load balancer"
  type        = number
  default     = 2
}

variable "api_droplet_size" {
  description = "Droplet size for API instances"
  default     = "s-1vcpu-1gb"
}

variable "api_droplet_image" {
  description = "Image slug or ID for API droplets"
  default     = "ubuntu-22-04-x64"
}

variable "db_cluster_id" {
  description = "ID of the existing managed PostgreSQL cluster"
  type        = string
  default     = ""  # Set when managed DB cluster is provisioned
}

variable "db_replica_size" {
  description = "Size slug for the database read replica"
  default     = "db-s-1vcpu-1gb"
}

# ─────────────────────────────────────────────────────────────────────────────
# Database Read Replica
# ─────────────────────────────────────────────────────────────────────────────

resource "digitalocean_database_replica" "api_read_replica" {
  cluster_id = var.db_cluster_id
  name       = "${var.project_name}-pg-replica"
  size       = var.db_replica_size
  region     = var.region

  tags = ["${var.project_name}", "database", "replica"]
}

# ─────────────────────────────────────────────────────────────────────────────
# API Droplets (parameterized count)
# ─────────────────────────────────────────────────────────────────────────────

resource "digitalocean_droplet" "api" {
  count  = var.api_replica_count
  name   = "${var.project_name}-api-${count.index}"
  region = var.region
  size   = var.api_droplet_size
  image  = var.api_droplet_image

  tags = ["${var.project_name}", "api"]

  lifecycle {
    create_before_destroy = true
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# Load Balancer
# ─────────────────────────────────────────────────────────────────────────────

resource "digitalocean_loadbalancer" "api_lb" {
  name   = "${var.project_name}-api-lb"
  region = var.region

  forwarding_rule {
    entry_port     = 443
    entry_protocol = "https"

    target_port     = 3000
    target_protocol = "http"
  }

  forwarding_rule {
    entry_port     = 80
    entry_protocol = "http"

    target_port     = 3000
    target_protocol = "http"
  }

  healthcheck {
    port     = 3000
    protocol = "http"
    path     = "/health"

    check_interval_seconds   = 10
    response_timeout_seconds = 5
    unhealthy_threshold      = 3
    healthy_threshold        = 5
  }

  droplet_ids = digitalocean_droplet.api[*].id
}

# ─────────────────────────────────────────────────────────────────────────────
# Outputs
# ─────────────────────────────────────────────────────────────────────────────

output "api_lb_ip" {
  value       = digitalocean_loadbalancer.api_lb.ip
  description = "Public IP of the API load balancer"
}

output "api_droplet_ips" {
  value       = digitalocean_droplet.api[*].ipv4_address
  description = "Private IPs of API droplets"
}

output "db_replica_host" {
  value       = digitalocean_database_replica.api_read_replica.host
  description = "Hostname of the PostgreSQL read replica"
}

output "db_replica_port" {
  value       = digitalocean_database_replica.api_read_replica.port
  description = "Port of the PostgreSQL read replica"
}

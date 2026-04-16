terraform {
  required_providers {
    betteruptime = {
      source  = "BetterStackHQ/better-uptime"
      version = "~> 0.11"
    }
  }
}

variable "betterstack_api_token" {
  type      = string
  sensitive = true
}

provider "betteruptime" {
  api_token = var.betterstack_api_token
}

resource "betteruptime_monitor" "api_health" {
  url                 = "https://erp.tellefsen.org/health"
  monitor_type        = "status"
  check_frequency     = 60
  request_timeout     = 15
  confirmation_period = 120
  monitor_group_id    = betteruptime_monitor_group.erp.id
}

resource "betteruptime_monitor" "web" {
  url                 = "https://erp.tellefsen.org/"
  monitor_type        = "status"
  check_frequency     = 60
  request_timeout     = 15
  confirmation_period = 120
  monitor_group_id    = betteruptime_monitor_group.erp.id
}

resource "betteruptime_monitor" "portal" {
  url                 = "https://erp.tellefsen.org/portal"
  monitor_type        = "status"
  check_frequency     = 180
  request_timeout     = 15
  confirmation_period = 300
  monitor_group_id    = betteruptime_monitor_group.erp.id
}

resource "betteruptime_monitor_group" "erp" {
  name = "ClaudERP"
}

resource "betteruptime_status_page" "main" {
  company_name = "ClaudERP"
  company_url  = "https://erp.tellefsen.org"
  subdomain    = "status-clauderp"
  timezone     = "Europe/Oslo"
}

resource "betteruptime_status_page_resource" "api" {
  status_page_id = betteruptime_status_page.main.id
  resource_id    = betteruptime_monitor.api_health.id
  resource_type  = "Monitor"
  public_name    = "API"
}

resource "betteruptime_status_page_resource" "web" {
  status_page_id = betteruptime_status_page.main.id
  resource_id    = betteruptime_monitor.web.id
  resource_type  = "Monitor"
  public_name    = "Web Application"
}

resource "betteruptime_status_page_resource" "portal" {
  status_page_id = betteruptime_status_page.main.id
  resource_id    = betteruptime_monitor.portal.id
  resource_type  = "Monitor"
  public_name    = "Client Portal"
}

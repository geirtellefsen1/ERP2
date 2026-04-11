"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import {
  Users,
  FileText,
  Landmark,
  BarChart3,
  ArrowUpRight,
  Plus,
  ArrowRight,
  Clock,
  AlertTriangle,
  TrendingUp,
  Wallet,
} from "lucide-react"
import { apiGet } from "@/lib/api"
import { formatCurrency, formatDate } from "@/lib/utils"
import { MetricCard } from "@/components/ui/metric-card"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Avatar } from "@/components/ui/avatar"

interface Client {
  id: number
  name: string
  country: string
  industry: string
  is_active: boolean
  created_at: string
}

export default function DashboardPage() {
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [greeting, setGreeting] = useState("")

  useEffect(() => {
    const hour = new Date().getHours()
    if (hour < 12) setGreeting("Good morning")
    else if (hour < 18) setGreeting("Good afternoon")
    else setGreeting("Good evening")

    async function load() {
      try {
        const data: Client[] = await apiGet("/api/v1/clients")
        setClients(data)
      } catch {
        // API not available
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const activeClients = clients.filter((c) => c.is_active).length

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">{greeting}</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Here is an overview of your agency today.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" asChild>
            <Link href="/dashboard/reports">
              <BarChart3 className="h-4 w-4" />
              Reports
            </Link>
          </Button>
          <Button size="sm" asChild>
            <Link href="/dashboard/clients">
              <Plus className="h-4 w-4" />
              New Client
            </Link>
          </Button>
        </div>
      </div>

      {/* Metric Cards */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-lg" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Total Clients"
            value={clients.length.toString()}
            change={12}
            changeLabel="vs last month"
            icon={<Users />}
          />
          <MetricCard
            title="Active Clients"
            value={activeClients.toString()}
            change={activeClients > 0 ? 8 : 0}
            changeLabel="vs last month"
            icon={<TrendingUp />}
          />
          <MetricCard
            title="Outstanding"
            value={formatCurrency(0)}
            change={0}
            changeLabel="vs last month"
            icon={<Wallet />}
          />
          <MetricCard
            title="Overdue Invoices"
            value="0"
            change={0}
            changeLabel="vs last month"
            icon={<AlertTriangle />}
          />
        </div>
      )}

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Quick Actions */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1.5">
            {[
              { href: "/dashboard/invoices", label: "Create Invoice", icon: FileText, desc: "Bill a client" },
              { href: "/dashboard/expenses", label: "Log Expense", icon: Wallet, desc: "Record a cost" },
              { href: "/dashboard/banking", label: "Reconcile", icon: Landmark, desc: "Match transactions" },
              { href: "/dashboard/reports", label: "View Reports", icon: BarChart3, desc: "P&L & more" },
            ].map((action) => (
              <Link
                key={action.href}
                href={action.href}
                className="flex items-center gap-3 px-3 py-2.5 rounded-md hover:bg-accent transition-colors group"
              >
                <div className="w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center shrink-0">
                  <action.icon className="h-4 w-4 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{action.label}</p>
                  <p className="text-2xs text-muted-foreground">{action.desc}</p>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </Link>
            ))}
          </CardContent>
        </Card>

        {/* Recent Clients */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle>Recent Clients</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/dashboard/clients">
                View all
                <ArrowUpRight className="h-3.5 w-3.5" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 rounded-md" />
                ))}
              </div>
            ) : clients.length === 0 ? (
              <div className="text-center py-8">
                <Users className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">
                  No clients yet.{" "}
                  <Link
                    href="/dashboard/clients"
                    className="text-primary hover:underline"
                  >
                    Add your first client
                  </Link>
                </p>
              </div>
            ) : (
              <div className="space-y-1">
                {clients.slice(0, 6).map((client) => (
                  <div
                    key={client.id}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-md hover:bg-accent/50 transition-colors"
                  >
                    <Avatar name={client.name} size="sm" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {client.name}
                      </p>
                      <p className="text-2xs text-muted-foreground">
                        {client.industry || client.country}
                      </p>
                    </div>
                    <Badge variant={client.is_active ? "success" : "secondary"}>
                      {client.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Activity / Timeline */}
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle>Recent Activity</CardTitle>
          <Badge variant="secondary">
            <Clock className="h-3 w-3 mr-1" />
            Today
          </Badge>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Clock className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-sm font-medium">No recent activity</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Activity from your team will appear here
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

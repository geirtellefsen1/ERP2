"use client"

import {
  CreditCard,
  TrendingUp,
  Calendar,
  Download,
  CheckCircle2,
  Clock,
} from "lucide-react"
import { formatCurrency, formatDate } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card"
import { MetricCard } from "@/components/ui/metric-card"
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table"

const BILLING_HISTORY = [
  { id: 1, date: "2026-04-01", amount: 2999, status: "paid", plan: "Growth" },
  { id: 2, date: "2026-03-01", amount: 2999, status: "paid", plan: "Growth" },
  { id: 3, date: "2026-02-01", amount: 2999, status: "paid", plan: "Growth" },
  { id: 4, date: "2026-01-01", amount: 1499, status: "paid", plan: "Starter" },
]

export default function BillingPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Billing</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Manage your subscription and payment history
        </p>
      </div>

      {/* Current Plan */}
      <Card className="border-primary/20 bg-primary/[0.02]">
        <CardContent className="p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <CreditCard className="h-5 w-5 text-primary" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-semibold">Growth Plan</h3>
                  <Badge>Active</Badge>
                </div>
                <p className="text-sm text-muted-foreground mt-0.5">
                  Up to 50 clients, AI features, bank integrations, priority
                  support
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-semibold">
                R2,999<span className="text-sm text-muted-foreground font-normal">/mo</span>
              </p>
              <p className="text-xs text-muted-foreground">
                Next billing: 1 May 2026
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          title="Monthly Cost"
          value={formatCurrency(2999)}
          icon={<CreditCard />}
        />
        <MetricCard
          title="YTD Spend"
          value={formatCurrency(10496)}
          change={8}
          changeLabel="vs last year"
          icon={<TrendingUp />}
        />
        <MetricCard
          title="Next Invoice"
          value="1 May 2026"
          icon={<Calendar />}
        />
      </div>

      {/* Billing History */}
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle>Billing History</CardTitle>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4" />
            Download All
          </Button>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Plan</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {BILLING_HISTORY.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>
                    <span className="text-sm">{formatDate(item.date)}</span>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm">{item.plan}</span>
                  </TableCell>
                  <TableCell>
                    <span className="font-mono text-sm font-medium">
                      {formatCurrency(item.amount)}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Badge variant="success">
                      <CheckCircle2 className="h-3 w-3 mr-1" />
                      Paid
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Button variant="ghost" size="icon-sm">
                      <Download className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

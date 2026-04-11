"use client"

import { useState } from "react"
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Download,
  Calendar,
  FileText,
  ArrowRight,
  PieChart,
  Activity,
  DollarSign,
  Minus,
} from "lucide-react"
import { cn, formatCurrency } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Select } from "@/components/ui/select"
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card"
import { MetricCard } from "@/components/ui/metric-card"
import { Badge } from "@/components/ui/badge"

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

const REVENUE_DATA = [42000, 38000, 55000, 48000, 62000, 58000, 71000, 65000, 73000, 68000, 0, 0]
const EXPENSE_DATA = [28000, 31000, 35000, 32000, 38000, 36000, 42000, 39000, 44000, 41000, 0, 0]

export default function ReportsPage() {
  const [period, setPeriod] = useState("2026")
  const [selectedReport, setSelectedReport] = useState<string | null>(null)

  const maxVal = Math.max(...REVENUE_DATA)
  const totalRevenue = REVENUE_DATA.reduce((a, b) => a + b, 0)
  const totalExpenses = EXPENSE_DATA.reduce((a, b) => a + b, 0)
  const profit = totalRevenue - totalExpenses

  const reports = [
    {
      id: "pnl",
      title: "Profit & Loss",
      description: "Revenue, expenses, and net income breakdown",
      icon: TrendingUp,
      color: "text-emerald-600 bg-emerald-50",
    },
    {
      id: "balance",
      title: "Balance Sheet",
      description: "Assets, liabilities, and equity snapshot",
      icon: BarChart3,
      color: "text-blue-600 bg-blue-50",
    },
    {
      id: "cashflow",
      title: "Cash Flow",
      description: "Operating, investing, and financing activities",
      icon: Activity,
      color: "text-purple-600 bg-purple-50",
    },
    {
      id: "aging",
      title: "Aging Report",
      description: "Outstanding receivables by age bucket",
      icon: Calendar,
      color: "text-amber-600 bg-amber-50",
    },
  ]

  // P&L breakdown items
  const pnlItems = [
    { label: "Service Revenue", amount: totalRevenue, type: "revenue" as const },
    { label: "Salaries & Wages", amount: -280000, type: "expense" as const },
    { label: "Software & Tools", amount: -45000, type: "expense" as const },
    { label: "Office & Rent", amount: -36000, type: "expense" as const },
    { label: "Marketing", amount: -18000, type: "expense" as const },
    { label: "Other Expenses", amount: -totalExpenses + 379000, type: "expense" as const },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">Reports</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Financial insights and analytics
          </p>
        </div>
        <div className="flex gap-2">
          <Select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            options={[
              { value: "2026", label: "FY 2026" },
              { value: "2025", label: "FY 2025" },
              { value: "2024", label: "FY 2024" },
            ]}
          />
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4" />
            Export PDF
          </Button>
        </div>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          title="Revenue YTD"
          value={formatCurrency(totalRevenue)}
          change={18}
          changeLabel="vs last year"
          icon={<TrendingUp />}
        />
        <MetricCard
          title="Expenses YTD"
          value={formatCurrency(totalExpenses)}
          change={12}
          changeLabel="vs last year"
          icon={<TrendingDown />}
        />
        <MetricCard
          title="Net Profit"
          value={formatCurrency(profit)}
          change={28}
          changeLabel="vs last year"
          icon={<DollarSign />}
        />
      </div>

      {/* Revenue vs Expenses Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Revenue vs Expenses</CardTitle>
          <CardDescription>Monthly comparison for {period}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-end gap-1 h-48">
            {MONTHS.map((month, i) => {
              const rev = REVENUE_DATA[i]
              const exp = EXPENSE_DATA[i]
              const revHeight = maxVal > 0 ? (rev / maxVal) * 100 : 0
              const expHeight = maxVal > 0 ? (exp / maxVal) * 100 : 0
              return (
                <div key={month} className="flex-1 flex flex-col items-center gap-1 group">
                  <div className="w-full flex gap-0.5 items-end h-40">
                    <div
                      className="flex-1 bg-primary/80 rounded-t-sm transition-all group-hover:bg-primary"
                      style={{ height: `${revHeight}%` }}
                      title={`Revenue: ${formatCurrency(rev)}`}
                    />
                    <div
                      className="flex-1 bg-muted-foreground/20 rounded-t-sm transition-all group-hover:bg-muted-foreground/30"
                      style={{ height: `${expHeight}%` }}
                      title={`Expenses: ${formatCurrency(exp)}`}
                    />
                  </div>
                  <span className="text-2xs text-muted-foreground">{month}</span>
                </div>
              )
            })}
          </div>
          <div className="flex items-center gap-4 mt-4 pt-4 border-t">
            <div className="flex items-center gap-2 text-xs">
              <div className="w-3 h-3 rounded-sm bg-primary/80" />
              <span className="text-muted-foreground">Revenue</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <div className="w-3 h-3 rounded-sm bg-muted-foreground/20" />
              <span className="text-muted-foreground">Expenses</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Report Cards */}
      <div>
        <h2 className="text-sm font-semibold mb-3">Available Reports</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {reports.map((report) => (
            <button
              key={report.id}
              onClick={() =>
                setSelectedReport(
                  selectedReport === report.id ? null : report.id
                )
              }
              className={cn(
                "flex items-start gap-4 p-4 rounded-lg border text-left transition-all hover:shadow-soft",
                selectedReport === report.id
                  ? "border-primary bg-primary/5"
                  : "bg-card hover:bg-accent/30"
              )}
            >
              <div className={cn("rounded-lg p-2.5", report.color)}>
                <report.icon className="h-4 w-4" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">{report.title}</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {report.description}
                </p>
              </div>
              <ArrowRight className="h-4 w-4 text-muted-foreground mt-1" />
            </button>
          ))}
        </div>
      </div>

      {/* P&L Breakdown */}
      {selectedReport === "pnl" && (
        <Card className="animate-fade-in">
          <CardHeader>
            <CardTitle>Profit & Loss Statement</CardTitle>
            <CardDescription>For the period ending {period}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-medium text-muted-foreground uppercase tracking-wide px-3 py-2">
                <span>Account</span>
                <span>Amount</span>
              </div>
              {pnlItems.map((item, i) => (
                <div
                  key={i}
                  className="flex justify-between items-center px-3 py-2.5 rounded-md hover:bg-accent/50 transition-colors"
                >
                  <span className="text-sm">{item.label}</span>
                  <span
                    className={cn(
                      "text-sm font-mono font-medium",
                      item.type === "revenue"
                        ? "text-success"
                        : "text-foreground"
                    )}
                  >
                    {formatCurrency(Math.abs(item.amount))}
                  </span>
                </div>
              ))}
              <div className="flex justify-between items-center px-3 py-3 border-t mt-2 font-semibold">
                <span>Net Profit</span>
                <span
                  className={cn(
                    "font-mono",
                    profit >= 0 ? "text-success" : "text-destructive"
                  )}
                >
                  {formatCurrency(profit)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

"use client"

import { useState } from "react"
import {
  Landmark,
  ArrowLeftRight,
  Check,
  X,
  Search,
  Upload,
  Link2,
  AlertCircle,
  CheckCircle2,
  Clock,
  Sparkles,
  ArrowRight,
  CreditCard,
  Filter,
} from "lucide-react"
import { cn, formatCurrency, formatDate } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card"
import { MetricCard } from "@/components/ui/metric-card"
import { EmptyState } from "@/components/ui/empty-state"

interface BankTransaction {
  id: number
  date: string
  description: string
  amount: number
  type: "debit" | "credit"
  status: "unmatched" | "matched" | "disputed"
  matchConfidence?: number
  suggestedMatch?: string
}

const DEMO_TRANSACTIONS: BankTransaction[] = [
  {
    id: 1,
    date: "2026-04-10",
    description: "PAYMENT FROM ACME CORP",
    amount: 15000,
    type: "credit",
    status: "matched",
    matchConfidence: 98,
    suggestedMatch: "INV-001",
  },
  {
    id: 2,
    date: "2026-04-09",
    description: "ADOBE SYSTEMS",
    amount: 899,
    type: "debit",
    status: "matched",
    matchConfidence: 95,
    suggestedMatch: "Adobe Creative Cloud subscription",
  },
  {
    id: 3,
    date: "2026-04-08",
    description: "EFT PAYMENT - UNKNOWN REF",
    amount: 5200,
    type: "credit",
    status: "unmatched",
    matchConfidence: 45,
    suggestedMatch: "Possible: TechStart Ltd payment",
  },
  {
    id: 4,
    date: "2026-04-07",
    description: "UBER TRIP",
    amount: 185,
    type: "debit",
    status: "unmatched",
    matchConfidence: 72,
    suggestedMatch: "Travel expense - Uber",
  },
  {
    id: 5,
    date: "2026-04-05",
    description: "WOOLWORTHS FOOD",
    amount: 350,
    type: "debit",
    status: "unmatched",
  },
  {
    id: 6,
    date: "2026-04-04",
    description: "TRANSFER FROM BUILDRIGHT",
    amount: 22000,
    type: "credit",
    status: "matched",
    matchConfidence: 92,
    suggestedMatch: "INV-003",
  },
  {
    id: 7,
    date: "2026-04-03",
    description: "GOOGLE WORKSPACE",
    amount: 1200,
    type: "debit",
    status: "matched",
    matchConfidence: 99,
    suggestedMatch: "Software subscription",
  },
]

export default function BankingPage() {
  const [filter, setFilter] = useState("all")
  const [search, setSearch] = useState("")
  const [selectedTx, setSelectedTx] = useState<number | null>(null)

  const filtered = DEMO_TRANSACTIONS.filter((tx) => {
    const matchesFilter = filter === "all" || tx.status === filter
    const matchesSearch =
      !search ||
      tx.description.toLowerCase().includes(search.toLowerCase())
    return matchesFilter && matchesSearch
  })

  const unmatched = DEMO_TRANSACTIONS.filter(
    (t) => t.status === "unmatched"
  ).length
  const matched = DEMO_TRANSACTIONS.filter(
    (t) => t.status === "matched"
  ).length
  const totalBalance = DEMO_TRANSACTIONS.reduce(
    (sum, t) => sum + (t.type === "credit" ? t.amount : -t.amount),
    0
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">Bank Reconciliation</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Match bank transactions with your records
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Link2 className="h-4 w-4" />
            Connect Bank
          </Button>
          <Button variant="outline" size="sm">
            <Upload className="h-4 w-4" />
            Import CSV
          </Button>
          <Button size="sm">
            <Sparkles className="h-4 w-4" />
            Auto-Reconcile
          </Button>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <MetricCard
          title="Account Balance"
          value={formatCurrency(totalBalance)}
          icon={<CreditCard />}
        />
        <MetricCard
          title="Matched"
          value={`${matched}`}
          icon={<CheckCircle2 />}
        />
        <MetricCard
          title="Unmatched"
          value={`${unmatched}`}
          icon={<AlertCircle />}
        />
        <MetricCard
          title="Match Rate"
          value={`${Math.round((matched / DEMO_TRANSACTIONS.length) * 100)}%`}
          icon={<ArrowLeftRight />}
        />
      </div>

      {/* Main Split Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Transaction List */}
        <div className="lg:col-span-2 space-y-3">
          {/* Filters */}
          <div className="flex items-center gap-3">
            <div className="flex-1 max-w-xs">
              <Input
                placeholder="Search transactions..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                icon={<Search />}
              />
            </div>
            <div className="flex gap-1 bg-muted p-1 rounded-lg">
              {[
                { key: "all", label: "All" },
                { key: "unmatched", label: "Unmatched" },
                { key: "matched", label: "Matched" },
              ].map((s) => (
                <button
                  key={s.key}
                  onClick={() => setFilter(s.key)}
                  className={cn(
                    "px-3 py-1 text-xs font-medium rounded-md transition-all",
                    filter === s.key
                      ? "bg-background shadow-xs text-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* Transaction Cards */}
          <div className="space-y-1.5">
            {filtered.map((tx) => (
              <button
                key={tx.id}
                onClick={() => setSelectedTx(tx.id)}
                className={cn(
                  "w-full flex items-center gap-3 px-4 py-3 rounded-lg border text-left transition-all hover:shadow-soft",
                  selectedTx === tx.id
                    ? "border-primary bg-primary/5 shadow-soft"
                    : "bg-card"
                )}
              >
                {/* Status indicator */}
                <div
                  className={cn(
                    "w-2 h-2 rounded-full shrink-0",
                    tx.status === "matched" && "bg-success",
                    tx.status === "unmatched" && "bg-warning",
                    tx.status === "disputed" && "bg-destructive"
                  )}
                />

                {/* Amount & direction */}
                <div
                  className={cn(
                    "w-8 h-8 rounded-md flex items-center justify-center shrink-0",
                    tx.type === "credit"
                      ? "bg-success/10 text-success"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  {tx.type === "credit" ? (
                    <ArrowRight className="h-4 w-4 rotate-[-90deg]" />
                  ) : (
                    <ArrowRight className="h-4 w-4 rotate-90" />
                  )}
                </div>

                {/* Details */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">
                    {tx.description}
                  </p>
                  <p className="text-2xs text-muted-foreground">
                    {formatDate(tx.date)}
                    {tx.matchConfidence && (
                      <span className="ml-2">
                        AI confidence: {tx.matchConfidence}%
                      </span>
                    )}
                  </p>
                </div>

                {/* Amount */}
                <span
                  className={cn(
                    "text-sm font-mono font-medium",
                    tx.type === "credit" ? "text-success" : "text-foreground"
                  )}
                >
                  {tx.type === "credit" ? "+" : "-"}
                  {formatCurrency(tx.amount)}
                </span>

                {/* Status badge */}
                <Badge
                  variant={
                    tx.status === "matched"
                      ? "success"
                      : tx.status === "unmatched"
                        ? "warning"
                        : "destructive"
                  }
                >
                  {tx.status}
                </Badge>
              </button>
            ))}
          </div>
        </div>

        {/* Match Panel */}
        <div className="lg:col-span-1">
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ArrowLeftRight className="h-4 w-4" />
                Match Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              {selectedTx ? (() => {
                const tx = DEMO_TRANSACTIONS.find((t) => t.id === selectedTx)
                if (!tx) return null
                return (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">
                          Description
                        </span>
                        <span className="font-medium text-right max-w-[60%] truncate">
                          {tx.description}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Amount</span>
                        <span className="font-mono font-medium">
                          {formatCurrency(tx.amount)}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Date</span>
                        <span>{formatDate(tx.date)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Status</span>
                        <Badge
                          variant={
                            tx.status === "matched" ? "success" : "warning"
                          }
                        >
                          {tx.status}
                        </Badge>
                      </div>
                    </div>

                    {tx.suggestedMatch && (
                      <div className="rounded-lg border border-primary/20 bg-primary/5 p-3 space-y-2">
                        <div className="flex items-center gap-1.5 text-xs font-medium text-primary">
                          <Sparkles className="h-3.5 w-3.5" />
                          AI Suggested Match
                        </div>
                        <p className="text-sm">{tx.suggestedMatch}</p>
                        {tx.matchConfidence && (
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-1.5 rounded-full bg-muted">
                              <div
                                className={cn(
                                  "h-full rounded-full transition-all",
                                  tx.matchConfidence >= 80
                                    ? "bg-success"
                                    : tx.matchConfidence >= 50
                                      ? "bg-warning"
                                      : "bg-destructive"
                                )}
                                style={{
                                  width: `${tx.matchConfidence}%`,
                                }}
                              />
                            </div>
                            <span className="text-2xs font-medium">
                              {tx.matchConfidence}%
                            </span>
                          </div>
                        )}
                      </div>
                    )}

                    {tx.status === "unmatched" && (
                      <div className="flex gap-2">
                        <Button size="sm" className="flex-1" variant="default">
                          <Check className="h-4 w-4" />
                          Accept Match
                        </Button>
                        <Button size="sm" variant="outline">
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    )}
                  </div>
                )
              })() : (
                <div className="text-center py-8">
                  <ArrowLeftRight className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">
                    Select a transaction to view match details
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

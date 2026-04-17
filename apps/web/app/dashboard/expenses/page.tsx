"use client"

import { useState, useEffect, useCallback } from "react"
import {
  Plus,
  Search,
  Receipt,
  Upload,
  Tag,
  DollarSign,
  MoreHorizontal,
  Sparkles,
  Camera,
  CheckCircle2,
  Clock,
  Loader2,
  X,
} from "lucide-react"
import { cn, formatCurrency, formatDate } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { MetricCard } from "@/components/ui/metric-card"
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table"
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalContent,
  ModalFooter,
} from "@/components/ui/modal"
import { EmptyState } from "@/components/ui/empty-state"
import { useToast } from "@/components/ui/toast"
import { useClientContext } from "@/lib/client-context"
import { apiGet, apiPost } from "@/lib/api"

const CATEGORIES = [
  { value: "food_beverage", label: "Food & Beverage" },
  { value: "utilities", label: "Utilities" },
  { value: "supplies", label: "Supplies & Inventory" },
  { value: "maintenance", label: "Maintenance & Repairs" },
  { value: "rent", label: "Rent & Lease" },
  { value: "insurance", label: "Insurance" },
  { value: "marketing", label: "Marketing & Ads" },
  { value: "software", label: "Software & Subscriptions" },
  { value: "travel", label: "Travel & Transport" },
  { value: "professional", label: "Professional Services" },
  { value: "payroll", label: "Payroll & Staff" },
  { value: "other", label: "Other" },
]

const VAT_RATES = [
  { value: "25", label: "25% standard" },
  { value: "15", label: "15% food" },
  { value: "12", label: "12% room/transport" },
  { value: "0", label: "0% exempt" },
]

const categoryColors: Record<string, string> = {
  food_beverage: "bg-orange-100 text-orange-700",
  utilities: "bg-amber-100 text-amber-700",
  supplies: "bg-blue-100 text-blue-700",
  maintenance: "bg-slate-100 text-slate-700",
  rent: "bg-purple-100 text-purple-700",
  insurance: "bg-teal-100 text-teal-700",
  marketing: "bg-pink-100 text-pink-700",
  software: "bg-cyan-100 text-cyan-700",
  travel: "bg-indigo-100 text-indigo-700",
  professional: "bg-emerald-100 text-emerald-700",
  payroll: "bg-green-100 text-green-700",
  other: "bg-gray-100 text-gray-700",
}

interface ExpenseData {
  id: number
  client_id: number
  vendor_name: string
  vendor_org_number: string | null
  description: string | null
  date: string
  due_date: string | null
  amount: string
  vat_amount: string
  vat_rate: string
  currency: string
  category: string | null
  status: string
  payment_method: string | null
  notes: string | null
  created_at: string
}

export default function ExpensesPage() {
  const { selectedClient } = useClientContext()
  const [expenses, setExpenses] = useState<ExpenseData[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [search, setSearch] = useState("")
  const [categoryFilter, setCategoryFilter] = useState("all")
  const [statusFilter, setStatusFilter] = useState("all")
  const [form, setForm] = useState({
    vendor_name: "",
    vendor_org_number: "",
    description: "",
    amount: "",
    vat_rate: "25",
    date: new Date().toISOString().slice(0, 10),
    category: "other",
    payment_method: "bank_transfer",
    notes: "",
  })
  const { toast } = useToast()

  const loadExpenses = useCallback(async () => {
    setLoading(true)
    try {
      const clientParam = selectedClient ? `?client_id=${selectedClient.id}` : ""
      const data = await apiGet<ExpenseData[]>(`/api/v1/expenses${clientParam}`)
      setExpenses(data)
    } catch (e: any) {
      toast(e.message || "Failed to load expenses")
    } finally {
      setLoading(false)
    }
  }, [selectedClient, toast])

  useEffect(() => {
    loadExpenses()
  }, [loadExpenses])

  const currency = selectedClient ? "NOK" : "NOK"

  const filtered = expenses.filter((e) => {
    const matchesSearch =
      !search ||
      e.vendor_name.toLowerCase().includes(search.toLowerCase()) ||
      e.description?.toLowerCase().includes(search.toLowerCase())
    const matchesCategory = categoryFilter === "all" || e.category === categoryFilter
    const matchesStatus = statusFilter === "all" || e.status === statusFilter
    return matchesSearch && matchesCategory && matchesStatus
  })

  const totalThisMonth = expenses.reduce((sum, e) => sum + parseFloat(e.amount), 0)
  const pendingCount = expenses.filter((e) => e.status === "pending").length
  const topCategory = (() => {
    const counts: Record<string, number> = {}
    expenses.forEach((e) => {
      const cat = e.category || "other"
      counts[cat] = (counts[cat] || 0) + parseFloat(e.amount)
    })
    const sorted = Object.entries(counts).sort(([, a], [, b]) => b - a)
    return sorted[0] ? CATEGORIES.find((c) => c.value === sorted[0][0])?.label || "Other" : "—"
  })()

  function resetForm() {
    setForm({
      vendor_name: "",
      vendor_org_number: "",
      description: "",
      amount: "",
      vat_rate: "25",
      date: new Date().toISOString().slice(0, 10),
      category: "other",
      payment_method: "bank_transfer",
      notes: "",
    })
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedClient) {
      toast("Select a client from the top bar first")
      return
    }
    const amount = parseFloat(form.amount)
    if (!amount || amount <= 0) {
      toast("Enter a valid amount")
      return
    }
    setSubmitting(true)
    const vatRate = parseFloat(form.vat_rate)
    const vatAmount = Math.round((amount * vatRate) / (100 + vatRate) * 100) / 100
    try {
      await apiPost("/api/v1/expenses", {
        client_id: selectedClient.id,
        vendor_name: form.vendor_name,
        vendor_org_number: form.vendor_org_number || null,
        description: form.description || null,
        date: new Date(form.date).toISOString(),
        amount,
        vat_amount: vatAmount,
        vat_rate: vatRate,
        currency,
        category: form.category,
        payment_method: form.payment_method || null,
        notes: form.notes || null,
      })
      toast("Expense recorded")
      setShowCreate(false)
      resetForm()
      loadExpenses()
    } catch (e: any) {
      toast(e.message || "Failed to record expense")
    } finally {
      setSubmitting(false)
    }
  }

  async function approveExpense(id: number) {
    try {
      await apiPost(`/api/v1/expenses/${id}/approve`, {})
      toast("Expense approved")
      loadExpenses()
    } catch (e: any) {
      toast(e.message || "Failed to approve")
    }
  }

  if (!selectedClient) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-xl font-semibold">Expenses</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Select a client from the top bar to view and record expenses.
          </p>
        </div>
        <EmptyState
          icon={<Receipt />}
          title="No client selected"
          description="Use the client picker in the top bar to choose which client you're working on."
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">Expenses</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {selectedClient.name} — track supplier invoices and costs
          </p>
        </div>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" />
          Add Expense
        </Button>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          title="Total Expenses"
          value={formatCurrency(totalThisMonth, currency)}
          icon={<DollarSign />}
        />
        <MetricCard
          title="Pending Approval"
          value={pendingCount.toString()}
          icon={<Clock />}
        />
        <MetricCard title="Top Category" value={topCategory} icon={<Tag />} />
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex-1 max-w-xs">
          <Input
            placeholder="Search expenses..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            icon={<Search />}
          />
        </div>
        <Select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          options={[{ value: "all", label: "All Categories" }, ...CATEGORIES]}
        />
        <div className="flex gap-1 bg-muted p-1 rounded-lg">
          {["all", "pending", "approved", "paid"].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={cn(
                "px-3 py-1 text-xs font-medium rounded-md transition-all capitalize",
                statusFilter === s
                  ? "bg-background shadow-xs text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin mr-2" />
          Loading expenses...
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<Receipt />}
          title="No expenses"
          description="Start recording expenses to track spending."
          action={{ label: "Add Expense", onClick: () => setShowCreate(true) }}
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Vendor</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Date</TableHead>
              <TableHead className="text-right">Amount</TableHead>
              <TableHead className="text-right">MVA</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((exp) => (
              <TableRow key={exp.id}>
                <TableCell>
                  <div className="min-w-0">
                    <p className="font-medium text-sm truncate">{exp.vendor_name}</p>
                    {exp.vendor_org_number && (
                      <p className="text-2xs text-muted-foreground">
                        {exp.vendor_org_number}
                      </p>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <span className="text-sm text-muted-foreground truncate max-w-[200px] block">
                    {exp.description || "—"}
                  </span>
                </TableCell>
                <TableCell>
                  {exp.category && (
                    <span
                      className={cn(
                        "inline-flex items-center px-2 py-0.5 rounded-full text-2xs font-medium",
                        categoryColors[exp.category] || categoryColors.other
                      )}
                    >
                      {CATEGORIES.find((c) => c.value === exp.category)?.label || exp.category}
                    </span>
                  )}
                </TableCell>
                <TableCell>
                  <span className="text-xs text-muted-foreground">
                    {formatDate(exp.date)}
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  <span className="font-medium font-mono text-sm">
                    {formatCurrency(parseFloat(exp.amount), exp.currency)}
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  <span className="text-xs text-muted-foreground">
                    {formatCurrency(parseFloat(exp.vat_amount), exp.currency)}
                  </span>
                </TableCell>
                <TableCell>
                  <Badge
                    variant={
                      exp.status === "approved" || exp.status === "paid"
                        ? "success"
                        : exp.status === "rejected"
                          ? "destructive"
                          : "warning"
                    }
                  >
                    {exp.status === "approved" ? "Approved" : exp.status === "paid" ? "Paid" : exp.status === "pending" ? "Pending" : exp.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  {exp.status === "pending" && (
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      title="Approve"
                      onClick={() => approveExpense(exp.id)}
                    >
                      <CheckCircle2 className="h-4 w-4" />
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {/* Quick Add Modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)}>
        <ModalHeader onClose={() => setShowCreate(false)}>
          <ModalTitle>Record Expense</ModalTitle>
          <ModalDescription>
            Add a supplier invoice or cost for {selectedClient?.name}
          </ModalDescription>
        </ModalHeader>
        <form onSubmit={handleCreate}>
          <ModalContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Vendor name"
                value={form.vendor_name}
                onChange={(e) => setForm({ ...form, vendor_name: e.target.value })}
                placeholder="Tine SA, Asko, Hafslund..."
                required
              />
              <Input
                label="Org number"
                value={form.vendor_org_number}
                onChange={(e) => setForm({ ...form, vendor_org_number: e.target.value })}
                placeholder="123 456 789 MVA"
              />
            </div>
            <Input
              label="Description"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="What was this expense for?"
            />
            <div className="grid grid-cols-3 gap-4">
              <Input
                label={`Amount (${currency})`}
                type="number"
                step="0.01"
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
                placeholder="0.00"
                required
              />
              <Select
                label="MVA rate"
                value={form.vat_rate}
                onChange={(e) => setForm({ ...form, vat_rate: e.target.value })}
                options={VAT_RATES}
              />
              <Input
                label="Date"
                type="date"
                value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Select
                label="Category"
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                options={CATEGORIES}
              />
              <Select
                label="Payment method"
                value={form.payment_method}
                onChange={(e) => setForm({ ...form, payment_method: e.target.value })}
                options={[
                  { value: "bank_transfer", label: "Bank transfer" },
                  { value: "credit_card", label: "Credit card" },
                  { value: "cash", label: "Cash" },
                  { value: "ehf", label: "EHF" },
                ]}
              />
            </div>

            {/* AI hint */}
            <div className="flex items-start gap-2 rounded-lg bg-primary/5 border border-primary/10 px-3 py-2.5">
              <Sparkles className="h-4 w-4 text-primary mt-0.5 shrink-0" />
              <p className="text-xs text-muted-foreground">
                <span className="font-medium text-foreground">Tip:</span>{" "}
                Drop receipts in the{" "}
                <a href="/dashboard/inbox" className="text-primary hover:underline">
                  Inbox
                </a>{" "}
                and AI will auto-fill vendor, amount, VAT, and category.
              </p>
            </div>
          </ModalContent>
          <ModalFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => { setShowCreate(false); resetForm() }}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Receipt className="h-4 w-4" />
              )}
              Save Expense
            </Button>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  )
}

"use client"

import { useState } from "react"
import {
  Plus,
  Search,
  Receipt,
  Upload,
  Tag,
  Calendar,
  DollarSign,
  MoreHorizontal,
  Sparkles,
  Camera,
} from "lucide-react"
import { cn, formatCurrency, formatDate } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
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

const CATEGORIES = [
  { value: "office", label: "Office Supplies" },
  { value: "travel", label: "Travel & Transport" },
  { value: "software", label: "Software & Subscriptions" },
  { value: "utilities", label: "Utilities" },
  { value: "meals", label: "Meals & Entertainment" },
  { value: "professional", label: "Professional Services" },
  { value: "marketing", label: "Marketing & Ads" },
  { value: "other", label: "Other" },
]

const DEMO_EXPENSES = [
  {
    id: 1,
    description: "Adobe Creative Cloud",
    amount: 899,
    category: "software",
    date: "2026-04-08",
    status: "approved" as const,
    vendor: "Adobe Inc.",
  },
  {
    id: 2,
    description: "Client lunch - Acme Corp",
    amount: 450,
    category: "meals",
    date: "2026-04-07",
    status: "pending" as const,
    vendor: "The Kitchen",
  },
  {
    id: 3,
    description: "Uber to client meeting",
    amount: 185,
    category: "travel",
    date: "2026-04-06",
    status: "approved" as const,
    vendor: "Uber",
  },
  {
    id: 4,
    description: "Office printer paper",
    amount: 320,
    category: "office",
    date: "2026-04-05",
    status: "pending" as const,
    vendor: "Takealot",
  },
  {
    id: 5,
    description: "Google Workspace",
    amount: 1200,
    category: "software",
    date: "2026-04-01",
    status: "approved" as const,
    vendor: "Google",
  },
]

const categoryColors: Record<string, string> = {
  office: "bg-blue-100 text-blue-700",
  travel: "bg-purple-100 text-purple-700",
  software: "bg-cyan-100 text-cyan-700",
  utilities: "bg-amber-100 text-amber-700",
  meals: "bg-orange-100 text-orange-700",
  professional: "bg-emerald-100 text-emerald-700",
  marketing: "bg-pink-100 text-pink-700",
  other: "bg-gray-100 text-gray-700",
}

export default function ExpensesPage() {
  const [showCreate, setShowCreate] = useState(false)
  const [search, setSearch] = useState("")
  const [categoryFilter, setCategoryFilter] = useState("all")
  const [form, setForm] = useState({
    description: "",
    amount: "",
    category: "other",
    vendor: "",
    date: new Date().toISOString().slice(0, 10),
    notes: "",
  })
  const { toast } = useToast()

  const filtered = DEMO_EXPENSES.filter((e) => {
    const matchesSearch =
      !search ||
      e.description.toLowerCase().includes(search.toLowerCase()) ||
      e.vendor.toLowerCase().includes(search.toLowerCase())
    const matchesCategory =
      categoryFilter === "all" || e.category === categoryFilter
    return matchesSearch && matchesCategory
  })

  const totalThisMonth = DEMO_EXPENSES.reduce((sum, e) => sum + e.amount, 0)
  const pendingCount = DEMO_EXPENSES.filter(
    (e) => e.status === "pending"
  ).length

  function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    toast("Expense recorded successfully")
    setShowCreate(false)
    setForm({
      description: "",
      amount: "",
      category: "other",
      vendor: "",
      date: new Date().toISOString().slice(0, 10),
      notes: "",
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">Expenses</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Track and categorize business expenses
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Upload className="h-4 w-4" />
            Import CSV
          </Button>
          <Button size="sm" onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4" />
            Add Expense
          </Button>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          title="This Month"
          value={formatCurrency(totalThisMonth)}
          change={-5}
          changeLabel="vs last month"
          icon={<DollarSign />}
        />
        <MetricCard
          title="Pending Approval"
          value={pendingCount.toString()}
          icon={<Receipt />}
        />
        <MetricCard
          title="Top Category"
          value="Software"
          icon={<Tag />}
        />
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
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
          options={[
            { value: "all", label: "All Categories" },
            ...CATEGORIES,
          ]}
        />
      </div>

      {/* Table */}
      {filtered.length === 0 ? (
        <EmptyState
          icon={<Receipt />}
          title="No expenses"
          description="Start recording expenses to track your business spending."
          action={{ label: "Add Expense", onClick: () => setShowCreate(true) }}
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Description</TableHead>
              <TableHead>Vendor</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Date</TableHead>
              <TableHead className="text-right">Amount</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((exp) => (
              <TableRow key={exp.id}>
                <TableCell>
                  <span className="font-medium">{exp.description}</span>
                </TableCell>
                <TableCell>
                  <span className="text-muted-foreground">{exp.vendor}</span>
                </TableCell>
                <TableCell>
                  <span
                    className={cn(
                      "inline-flex items-center px-2 py-0.5 rounded-full text-2xs font-medium",
                      categoryColors[exp.category]
                    )}
                  >
                    {CATEGORIES.find((c) => c.value === exp.category)?.label}
                  </span>
                </TableCell>
                <TableCell>
                  <span className="text-xs text-muted-foreground">
                    {formatDate(exp.date)}
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  <span className="font-medium font-mono text-sm">
                    {formatCurrency(exp.amount)}
                  </span>
                </TableCell>
                <TableCell>
                  <Badge
                    variant={
                      exp.status === "approved" ? "success" : "warning"
                    }
                  >
                    {exp.status === "approved" ? "Approved" : "Pending"}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Button variant="ghost" size="icon-sm">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
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
            Add a business expense quickly
          </ModalDescription>
        </ModalHeader>
        <form onSubmit={handleCreate}>
          <ModalContent className="space-y-4">
            {/* Receipt upload zone */}
            <div className="flex items-center justify-center w-full h-24 rounded-lg border-2 border-dashed border-input hover:border-primary/50 hover:bg-accent/50 transition-colors cursor-pointer group">
              <div className="text-center">
                <Camera className="h-5 w-5 mx-auto text-muted-foreground group-hover:text-primary transition-colors" />
                <p className="text-xs text-muted-foreground mt-1">
                  Upload receipt (optional)
                </p>
              </div>
            </div>

            <Input
              label="Description"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="What was this expense for?"
              required
            />
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Amount (ZAR)"
                type="number"
                step="0.01"
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
                placeholder="0.00"
                icon={<DollarSign />}
                required
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
              <Input
                label="Vendor"
                value={form.vendor}
                onChange={(e) => setForm({ ...form, vendor: e.target.value })}
                placeholder="Company name"
              />
            </div>

            {/* AI suggestion hint */}
            <div className="flex items-start gap-2 rounded-lg bg-primary/5 border border-primary/10 px-3 py-2.5">
              <Sparkles className="h-4 w-4 text-primary mt-0.5 shrink-0" />
              <p className="text-xs text-muted-foreground">
                <span className="font-medium text-foreground">AI tip:</span>{" "}
                Upload a receipt and our AI will auto-fill the description,
                amount, vendor, and suggest a GL category.
              </p>
            </div>
          </ModalContent>
          <ModalFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowCreate(false)}
            >
              Cancel
            </Button>
            <Button type="submit">Save Expense</Button>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  )
}

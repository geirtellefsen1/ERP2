"use client"

import { useState } from "react"
import {
  Plus,
  Search,
  FileText,
  Send,
  CheckCircle2,
  Clock,
  AlertTriangle,
  MoreHorizontal,
  Download,
  Trash2,
  Eye,
  X,
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
import { Avatar } from "@/components/ui/avatar"
import { useToast } from "@/components/ui/toast"

interface InvoiceLineItem {
  description: string
  quantity: number
  unit_price: number
}

const DEMO_INVOICES = [
  {
    id: "INV-001",
    client: "Acme Corp",
    amount: 15000,
    status: "paid" as const,
    issued: "2026-03-15",
    due: "2026-04-15",
  },
  {
    id: "INV-002",
    client: "TechStart Ltd",
    amount: 8500,
    status: "sent" as const,
    issued: "2026-03-28",
    due: "2026-04-28",
  },
  {
    id: "INV-003",
    client: "BuildRight SA",
    amount: 22000,
    status: "overdue" as const,
    issued: "2026-02-10",
    due: "2026-03-10",
  },
  {
    id: "INV-004",
    client: "Green Valley",
    amount: 4200,
    status: "draft" as const,
    issued: "2026-04-10",
    due: "2026-05-10",
  },
]

const statusConfig = {
  draft: { label: "Draft", variant: "secondary" as const, icon: FileText },
  sent: { label: "Sent", variant: "default" as const, icon: Send },
  paid: { label: "Paid", variant: "success" as const, icon: CheckCircle2 },
  overdue: { label: "Overdue", variant: "destructive" as const, icon: AlertTriangle },
}

export default function InvoicesPage() {
  const [showCreate, setShowCreate] = useState(false)
  const [filter, setFilter] = useState("all")
  const [search, setSearch] = useState("")
  const [lines, setLines] = useState<InvoiceLineItem[]>([
    { description: "", quantity: 1, unit_price: 0 },
  ])
  const [invoiceForm, setInvoiceForm] = useState({
    client: "",
    due_days: "30",
    reference: "",
  })
  const { toast } = useToast()

  const filtered = DEMO_INVOICES.filter((inv) => {
    const matchesFilter = filter === "all" || inv.status === filter
    const matchesSearch =
      !search ||
      inv.client.toLowerCase().includes(search.toLowerCase()) ||
      inv.id.toLowerCase().includes(search.toLowerCase())
    return matchesFilter && matchesSearch
  })

  const totalOutstanding = DEMO_INVOICES.filter(
    (i) => i.status === "sent" || i.status === "overdue"
  ).reduce((sum, i) => sum + i.amount, 0)

  const totalOverdue = DEMO_INVOICES.filter(
    (i) => i.status === "overdue"
  ).reduce((sum, i) => sum + i.amount, 0)

  function addLine() {
    setLines([...lines, { description: "", quantity: 1, unit_price: 0 }])
  }

  function removeLine(index: number) {
    setLines(lines.filter((_, i) => i !== index))
  }

  function updateLine(
    index: number,
    field: keyof InvoiceLineItem,
    value: string | number
  ) {
    const updated = [...lines]
    updated[index] = { ...updated[index], [field]: value }
    setLines(updated)
  }

  const invoiceTotal = lines.reduce(
    (sum, l) => sum + l.quantity * l.unit_price,
    0
  )

  function handleCreateInvoice(e: React.FormEvent) {
    e.preventDefault()
    toast("Invoice created successfully")
    setShowCreate(false)
    setLines([{ description: "", quantity: 1, unit_price: 0 }])
    setInvoiceForm({ client: "", due_days: "30", reference: "" })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">Invoices</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Create and manage client invoices
          </p>
        </div>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" />
          New Invoice
        </Button>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          title="Total Outstanding"
          value={formatCurrency(totalOutstanding)}
          icon={<Clock />}
        />
        <MetricCard
          title="Overdue"
          value={formatCurrency(totalOverdue)}
          icon={<AlertTriangle />}
        />
        <MetricCard
          title="Paid This Month"
          value={formatCurrency(15000)}
          change={24}
          changeLabel="vs last month"
          icon={<CheckCircle2 />}
        />
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="flex-1 max-w-xs">
          <Input
            placeholder="Search invoices..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            icon={<Search />}
          />
        </div>
        <div className="flex gap-1 bg-muted p-1 rounded-lg">
          {["all", "draft", "sent", "paid", "overdue"].map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={cn(
                "px-3 py-1 text-xs font-medium rounded-md transition-all capitalize",
                filter === s
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
      {filtered.length === 0 ? (
        <EmptyState
          icon={<FileText />}
          title="No invoices"
          description="Create your first invoice to start billing clients."
          action={{ label: "New Invoice", onClick: () => setShowCreate(true) }}
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Invoice</TableHead>
              <TableHead>Client</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Issued</TableHead>
              <TableHead>Due</TableHead>
              <TableHead className="w-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((inv) => {
              const config = statusConfig[inv.status]
              return (
                <TableRow key={inv.id}>
                  <TableCell>
                    <span className="font-mono text-xs font-medium">
                      {inv.id}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Avatar name={inv.client} size="sm" />
                      <span className="font-medium">{inv.client}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="font-medium">
                      {formatCurrency(inv.amount)}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Badge variant={config.variant}>
                      <config.icon className="h-3 w-3 mr-1" />
                      {config.label}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <span className="text-xs text-muted-foreground">
                      {formatDate(inv.issued)}
                    </span>
                  </TableCell>
                  <TableCell>
                    <span className="text-xs text-muted-foreground">
                      {formatDate(inv.due)}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Button variant="ghost" size="icon-sm">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      )}

      {/* Create Invoice Modal */}
      <Modal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        className="max-w-2xl"
      >
        <ModalHeader onClose={() => setShowCreate(false)}>
          <ModalTitle>New Invoice</ModalTitle>
          <ModalDescription>Create and send an invoice to a client</ModalDescription>
        </ModalHeader>
        <form onSubmit={handleCreateInvoice}>
          <ModalContent className="space-y-5">
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Client"
                value={invoiceForm.client}
                onChange={(e) =>
                  setInvoiceForm({ ...invoiceForm, client: e.target.value })
                }
                placeholder="Select or type client name"
                required
              />
              <Select
                label="Payment Terms"
                value={invoiceForm.due_days}
                onChange={(e) =>
                  setInvoiceForm({ ...invoiceForm, due_days: e.target.value })
                }
                options={[
                  { value: "7", label: "Net 7" },
                  { value: "14", label: "Net 14" },
                  { value: "30", label: "Net 30" },
                  { value: "60", label: "Net 60" },
                ]}
              />
            </div>

            <Input
              label="Reference"
              value={invoiceForm.reference}
              onChange={(e) =>
                setInvoiceForm({ ...invoiceForm, reference: e.target.value })
              }
              placeholder="PO number or reference (optional)"
            />

            {/* Line Items */}
            <div className="space-y-3">
              <label className="text-sm font-medium">Line Items</label>
              <div className="rounded-lg border overflow-hidden">
                <div className="grid grid-cols-[1fr_80px_100px_32px] gap-2 px-3 py-2 bg-muted/50 text-xs font-medium text-muted-foreground">
                  <span>Description</span>
                  <span>Qty</span>
                  <span>Unit Price</span>
                  <span />
                </div>
                {lines.map((line, i) => (
                  <div
                    key={i}
                    className="grid grid-cols-[1fr_80px_100px_32px] gap-2 px-3 py-2 border-t items-center"
                  >
                    <input
                      className="h-8 w-full rounded-md border border-input bg-background px-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                      placeholder="Service description"
                      value={line.description}
                      onChange={(e) =>
                        updateLine(i, "description", e.target.value)
                      }
                      required
                    />
                    <input
                      type="number"
                      className="h-8 w-full rounded-md border border-input bg-background px-2 text-sm text-right focus:outline-none focus:ring-1 focus:ring-ring"
                      min="1"
                      value={line.quantity}
                      onChange={(e) =>
                        updateLine(i, "quantity", parseInt(e.target.value) || 1)
                      }
                    />
                    <input
                      type="number"
                      className="h-8 w-full rounded-md border border-input bg-background px-2 text-sm text-right focus:outline-none focus:ring-1 focus:ring-ring"
                      min="0"
                      step="0.01"
                      value={line.unit_price || ""}
                      onChange={(e) =>
                        updateLine(
                          i,
                          "unit_price",
                          parseFloat(e.target.value) || 0
                        )
                      }
                      placeholder="0.00"
                    />
                    <button
                      type="button"
                      onClick={() => removeLine(i)}
                      className="h-8 w-8 flex items-center justify-center text-muted-foreground hover:text-destructive rounded-md hover:bg-destructive/10 transition-colors"
                      disabled={lines.length <= 1}
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
              <Button type="button" variant="outline" size="sm" onClick={addLine}>
                <Plus className="h-3.5 w-3.5" />
                Add Line
              </Button>
            </div>

            {/* Total */}
            <div className="flex justify-end">
              <div className="w-48 space-y-1 text-sm">
                <div className="flex justify-between text-muted-foreground">
                  <span>Subtotal</span>
                  <span>{formatCurrency(invoiceTotal)}</span>
                </div>
                <div className="flex justify-between font-semibold text-base border-t pt-1">
                  <span>Total</span>
                  <span>{formatCurrency(invoiceTotal)}</span>
                </div>
              </div>
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
            <Button type="submit" variant="outline">
              <FileText className="h-4 w-4" />
              Save Draft
            </Button>
            <Button type="submit">
              <Send className="h-4 w-4" />
              Send Invoice
            </Button>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  )
}

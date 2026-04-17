"use client"

import { useState, useEffect, useCallback } from "react"
import {
  Plus,
  Search,
  FileText,
  Send,
  CheckCircle2,
  Clock,
  AlertTriangle,
  MoreHorizontal,
  X,
  Loader2,
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
import { Avatar } from "@/components/ui/avatar"
import { useToast } from "@/components/ui/toast"
import { useClientContext } from "@/lib/client-context"
import { apiGet, apiPost } from "@/lib/api"

interface InvoiceLineItem {
  description: string
  quantity: number
  unit_price: number
  vat_rate: number
}

interface InvoiceData {
  id: number
  client_id: number
  invoice_number: string
  status: string
  currency: string
  subtotal: string
  vat_amount: string
  amount: string
  customer_name: string | null
  customer_email: string | null
  customer_address: string | null
  customer_org_number: string | null
  reference: string | null
  payment_terms_days: number | null
  due_date: string | null
  issued_at: string | null
}

const statusConfig: Record<string, { label: string; variant: "secondary" | "default" | "success" | "destructive"; icon: any }> = {
  draft: { label: "Draft", variant: "secondary", icon: FileText },
  sent: { label: "Sent", variant: "default", icon: Send },
  paid: { label: "Paid", variant: "success", icon: CheckCircle2 },
  overdue: { label: "Overdue", variant: "destructive", icon: AlertTriangle },
}

const VAT_RATES = [
  { value: "25", label: "25% (standard)" },
  { value: "15", label: "15% (food)" },
  { value: "12", label: "12% (room/transport)" },
  { value: "0", label: "0% (exempt)" },
]

export default function InvoicesPage() {
  const { selectedClient } = useClientContext()
  const [invoices, setInvoices] = useState<InvoiceData[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [filter, setFilter] = useState("all")
  const [search, setSearch] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [lines, setLines] = useState<InvoiceLineItem[]>([
    { description: "", quantity: 1, unit_price: 0, vat_rate: 25 },
  ])
  const [form, setForm] = useState({
    customer_name: "",
    customer_email: "",
    customer_address: "",
    customer_org_number: "",
    payment_terms_days: "30",
    reference: "",
    notes: "",
  })
  const { toast } = useToast()

  const loadInvoices = useCallback(async () => {
    setLoading(true)
    try {
      const clientParam = selectedClient ? `?client_id=${selectedClient.id}` : ""
      const data = await apiGet<InvoiceData[]>(`/api/v1/invoices${clientParam}`)
      setInvoices(data)
    } catch (e: any) {
      toast(e.message || "Failed to load invoices")
    } finally {
      setLoading(false)
    }
  }, [selectedClient, toast])

  useEffect(() => {
    loadInvoices()
  }, [loadInvoices])

  const currency = selectedClient ? "NOK" : "NOK"

  const filtered = invoices.filter((inv) => {
    const matchesFilter = filter === "all" || inv.status === filter
    const matchesSearch =
      !search ||
      inv.customer_name?.toLowerCase().includes(search.toLowerCase()) ||
      inv.invoice_number.toLowerCase().includes(search.toLowerCase())
    return matchesFilter && matchesSearch
  })

  const totalOutstanding = invoices
    .filter((i) => i.status === "sent" || i.status === "overdue")
    .reduce((sum, i) => sum + parseFloat(i.amount), 0)

  const totalOverdue = invoices
    .filter((i) => i.status === "overdue")
    .reduce((sum, i) => sum + parseFloat(i.amount), 0)

  const totalPaid = invoices
    .filter((i) => i.status === "paid")
    .reduce((sum, i) => sum + parseFloat(i.amount), 0)

  function addLine() {
    setLines([...lines, { description: "", quantity: 1, unit_price: 0, vat_rate: 25 }])
  }

  function removeLine(index: number) {
    setLines(lines.filter((_, i) => i !== index))
  }

  function updateLine(index: number, field: keyof InvoiceLineItem, value: string | number) {
    const updated = [...lines]
    updated[index] = { ...updated[index], [field]: value }
    setLines(updated)
  }

  const invoiceSubtotal = lines.reduce((sum, l) => sum + l.quantity * l.unit_price, 0)
  const invoiceVat = lines.reduce(
    (sum, l) => sum + (l.quantity * l.unit_price * l.vat_rate) / 100,
    0
  )

  function resetForm() {
    setLines([{ description: "", quantity: 1, unit_price: 0, vat_rate: 25 }])
    setForm({
      customer_name: "",
      customer_email: "",
      customer_address: "",
      customer_org_number: "",
      payment_terms_days: "30",
      reference: "",
      notes: "",
    })
  }

  async function handleCreateInvoice(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedClient) {
      toast("Select a client from the top bar first")
      return
    }
    if (lines.every((l) => !l.description || l.unit_price <= 0)) {
      toast("Add at least one line item")
      return
    }
    setSubmitting(true)
    try {
      await apiPost("/api/v1/invoices", {
        client_id: selectedClient.id,
        customer_name: form.customer_name,
        customer_email: form.customer_email || null,
        customer_address: form.customer_address || null,
        customer_org_number: form.customer_org_number || null,
        payment_terms_days: parseInt(form.payment_terms_days),
        reference: form.reference || null,
        notes: form.notes || null,
        currency,
        line_items: lines
          .filter((l) => l.description && l.unit_price > 0)
          .map((l) => ({
            description: l.description,
            quantity: l.quantity,
            unit_price: l.unit_price,
            vat_rate: l.vat_rate,
          })),
      })
      toast("Invoice created")
      setShowCreate(false)
      resetForm()
      loadInvoices()
    } catch (e: any) {
      toast(e.message || "Failed to create invoice")
    } finally {
      setSubmitting(false)
    }
  }

  async function sendInvoice(id: number) {
    try {
      await apiPost(`/api/v1/invoices/${id}/send`, {})
      toast("Invoice sent")
      loadInvoices()
    } catch (e: any) {
      toast(e.message || "Failed to send invoice")
    }
  }

  if (!selectedClient) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-xl font-semibold">Invoices</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Select a client from the top bar to view and create invoices.
          </p>
        </div>
        <EmptyState
          icon={<FileText />}
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
          <h1 className="text-xl font-semibold">Invoices</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {selectedClient.name} — create and manage sales invoices
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
          title="Outstanding"
          value={formatCurrency(totalOutstanding, currency)}
          icon={<Clock />}
        />
        <MetricCard
          title="Overdue"
          value={formatCurrency(totalOverdue, currency)}
          icon={<AlertTriangle />}
        />
        <MetricCard
          title="Paid"
          value={formatCurrency(totalPaid, currency)}
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
      {loading ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin mr-2" />
          Loading invoices...
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<FileText />}
          title="No invoices"
          description="Create your first invoice to start billing."
          action={{ label: "New Invoice", onClick: () => setShowCreate(true) }}
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Invoice</TableHead>
              <TableHead>Customer</TableHead>
              <TableHead className="text-right">Subtotal</TableHead>
              <TableHead className="text-right">VAT</TableHead>
              <TableHead className="text-right">Total</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Due</TableHead>
              <TableHead className="w-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((inv) => {
              const config = statusConfig[inv.status] || statusConfig.draft
              const Icon = config.icon
              return (
                <TableRow key={inv.id}>
                  <TableCell>
                    <span className="font-mono text-xs font-medium">
                      {inv.invoice_number}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Avatar name={inv.customer_name || "?"} size="sm" />
                      <div className="min-w-0">
                        <p className="font-medium text-sm truncate">
                          {inv.customer_name || "—"}
                        </p>
                        {inv.customer_org_number && (
                          <p className="text-2xs text-muted-foreground">
                            Org: {inv.customer_org_number}
                          </p>
                        )}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <span className="text-sm text-muted-foreground">
                      {formatCurrency(parseFloat(inv.subtotal), inv.currency)}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <span className="text-xs text-muted-foreground">
                      {formatCurrency(parseFloat(inv.vat_amount), inv.currency)}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <span className="font-medium">
                      {formatCurrency(parseFloat(inv.amount), inv.currency)}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Badge variant={config.variant}>
                      <Icon className="h-3 w-3 mr-1" />
                      {config.label}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <span className="text-xs text-muted-foreground">
                      {inv.due_date ? formatDate(inv.due_date) : "—"}
                    </span>
                  </TableCell>
                  <TableCell>
                    {inv.status === "draft" && (
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        title="Send invoice"
                        onClick={() => sendInvoice(inv.id)}
                      >
                        <Send className="h-4 w-4" />
                      </Button>
                    )}
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
          <ModalDescription>
            Create a sales invoice for {selectedClient?.name}
          </ModalDescription>
        </ModalHeader>
        <form onSubmit={handleCreateInvoice}>
          <ModalContent className="space-y-5">
            {/* Customer info */}
            <div className="space-y-3">
              <p className="text-sm font-medium">Customer details</p>
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Customer name"
                  value={form.customer_name}
                  onChange={(e) => setForm({ ...form, customer_name: e.target.value })}
                  placeholder="Company or person name"
                  required
                />
                <Input
                  label="Org number"
                  value={form.customer_org_number}
                  onChange={(e) => setForm({ ...form, customer_org_number: e.target.value })}
                  placeholder="123 456 789 MVA"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Email"
                  type="email"
                  value={form.customer_email}
                  onChange={(e) => setForm({ ...form, customer_email: e.target.value })}
                  placeholder="invoice@customer.no"
                />
                <Input
                  label="Address"
                  value={form.customer_address}
                  onChange={(e) => setForm({ ...form, customer_address: e.target.value })}
                  placeholder="Street, City, Postal code"
                />
              </div>
            </div>

            {/* Terms */}
            <div className="grid grid-cols-2 gap-4">
              <Select
                label="Payment Terms"
                value={form.payment_terms_days}
                onChange={(e) => setForm({ ...form, payment_terms_days: e.target.value })}
                options={[
                  { value: "7", label: "Net 7" },
                  { value: "14", label: "Net 14" },
                  { value: "30", label: "Net 30" },
                  { value: "60", label: "Net 60" },
                ]}
              />
              <Input
                label="Reference / PO"
                value={form.reference}
                onChange={(e) => setForm({ ...form, reference: e.target.value })}
                placeholder="PO-12345"
              />
            </div>

            {/* Line Items */}
            <div className="space-y-3">
              <label className="text-sm font-medium">Line Items</label>
              <div className="rounded-lg border overflow-hidden">
                <div className="grid grid-cols-[1fr_60px_90px_90px_32px] gap-2 px-3 py-2 bg-muted/50 text-xs font-medium text-muted-foreground">
                  <span>Description</span>
                  <span>Qty</span>
                  <span>Unit Price</span>
                  <span>MVA %</span>
                  <span />
                </div>
                {lines.map((line, i) => (
                  <div
                    key={i}
                    className="grid grid-cols-[1fr_60px_90px_90px_32px] gap-2 px-3 py-2 border-t items-center"
                  >
                    <input
                      className="h-8 w-full rounded-md border border-input bg-background px-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                      placeholder="Service description"
                      value={line.description}
                      onChange={(e) => updateLine(i, "description", e.target.value)}
                      required
                    />
                    <input
                      type="number"
                      className="h-8 w-full rounded-md border border-input bg-background px-2 text-sm text-right focus:outline-none focus:ring-1 focus:ring-ring"
                      min="1"
                      value={line.quantity}
                      onChange={(e) => updateLine(i, "quantity", parseInt(e.target.value) || 1)}
                    />
                    <input
                      type="number"
                      className="h-8 w-full rounded-md border border-input bg-background px-2 text-sm text-right focus:outline-none focus:ring-1 focus:ring-ring"
                      min="0"
                      step="0.01"
                      value={line.unit_price || ""}
                      onChange={(e) => updateLine(i, "unit_price", parseFloat(e.target.value) || 0)}
                      placeholder="0.00"
                    />
                    <select
                      className="h-8 w-full rounded-md border border-input bg-background px-1 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                      value={line.vat_rate}
                      onChange={(e) => updateLine(i, "vat_rate", parseFloat(e.target.value))}
                    >
                      {VAT_RATES.map((r) => (
                        <option key={r.value} value={r.value}>
                          {r.label}
                        </option>
                      ))}
                    </select>
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

            {/* Notes */}
            <Input
              label="Notes"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              placeholder="Payment instructions, thank you note..."
            />

            {/* Totals */}
            <div className="flex justify-end">
              <div className="w-56 space-y-1 text-sm">
                <div className="flex justify-between text-muted-foreground">
                  <span>Subtotal</span>
                  <span>{formatCurrency(invoiceSubtotal, currency)}</span>
                </div>
                <div className="flex justify-between text-muted-foreground">
                  <span>MVA</span>
                  <span>{formatCurrency(invoiceVat, currency)}</span>
                </div>
                <div className="flex justify-between font-semibold text-base border-t pt-1">
                  <span>Total</span>
                  <span>{formatCurrency(invoiceSubtotal + invoiceVat, currency)}</span>
                </div>
              </div>
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
                <FileText className="h-4 w-4" />
              )}
              Create Invoice
            </Button>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  )
}

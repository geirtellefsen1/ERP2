"use client"

import { useState, useCallback, useRef } from "react"
import {
  Upload,
  FileText,
  Download,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  BookOpen,
  TrendingUp,
  DollarSign,
  Building2,
  BarChart3,
  X,
} from "lucide-react"
import { cn, formatCurrency } from "@/lib/utils"
import { Button } from "@/components/ui/button"
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
import { useToast } from "@/components/ui/toast"
import { useClientContext } from "@/lib/client-context"
import { apiGet, apiPost } from "@/lib/api"
import { EmptyState } from "@/components/ui/empty-state"

interface ParsedLine {
  description: string
  quantity: string
  unit_price: string
  line_amount: string
  vat_rate: string
  vat_amount: string
  suggested_account: string
}

interface ParsedInvoice {
  invoice_number: string
  issue_date: string
  due_date: string
  supplier_name: string
  supplier_org_number: string
  currency: string
  subtotal: string
  total_vat: string
  total: string
  lines: ParsedLine[]
}

interface BookingResult {
  invoice_number: string
  journal_entry_id: number
  lines_posted: number
  total_debit: string
  total_credit: string
}

interface ImportResult {
  invoices_parsed: number
  invoices_booked: number
  journal_entries: BookingResult[]
  errors: string[]
  notices?: string[]
}

interface ReportLine {
  account_code: string
  account_name: string
  debit_balance: string
  credit_balance: string
  net_balance: string
}

interface TrialBalance {
  lines: ReportLine[]
  totals: { total_debit: string; total_credit: string }
}

interface PLReport {
  revenue: { lines: any[]; total: number }
  expenses: { lines: any[]; total: number }
  net_profit: number
}

interface BSReport {
  assets: { lines: any[]; total: number }
  liabilities: { lines: any[]; total: number }
  equity: { lines: any[]; total: number }
  check: string
}

type Step = "upload" | "preview" | "booked" | "reports"

export default function ImportPage() {
  const { selectedClient } = useClientContext()
  const [step, setStep] = useState<Step>("upload")
  const [dragOver, setDragOver] = useState(false)
  const [files, setFiles] = useState<File[]>([])
  const [parsing, setParsing] = useState(false)
  const [parsed, setParsed] = useState<ParsedInvoice[]>([])
  const [booking, setBooking] = useState(false)
  const [bookResult, setBookResult] = useState<ImportResult | null>(null)
  const [loadingSamples, setLoadingSamples] = useState(false)
  const [loadingBaseline, setLoadingBaseline] = useState(false)
  const [trialBalance, setTrialBalance] = useState<TrialBalance | null>(null)
  const [plReport, setPLReport] = useState<PLReport | null>(null)
  const [bsReport, setBSReport] = useState<BSReport | null>(null)
  const [loadingReports, setLoadingReports] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const dropped = Array.from(e.dataTransfer.files).filter(
      (f) => f.name.endsWith(".xml") || f.type === "text/xml" || f.type === "application/xml"
    )
    if (dropped.length === 0) {
      toast("Please drop EHF XML files (.xml)")
      return
    }
    setFiles(dropped)
    parseFiles(dropped)
  }, [toast])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files || [])
    if (selected.length > 0) {
      setFiles(selected)
      parseFiles(selected)
    }
  }, [])

  async function parseFiles(fileList: File[]) {
    setParsing(true)
    try {
      const formData = new FormData()
      fileList.forEach((f) => formData.append("files", f))
      const token = localStorage.getItem("bpo_token")
      const res = await fetch("/api/v1/ehf/parse", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      })
      if (!res.ok) {
        const d = await res.json().catch(() => ({ detail: "Parse failed" }))
        throw new Error(d.detail || "Parse failed")
      }
      const data: ParsedInvoice[] = await res.json()
      setParsed(data)
      setStep("preview")
    } catch (e: any) {
      toast(e.message || "Failed to parse EHF files", "error")
    } finally {
      setParsing(false)
    }
  }

  async function loadSampleInvoices() {
    setLoadingSamples(true)
    try {
      const data = await apiGet<ParsedInvoice[]>("/api/v1/ehf/sample-invoices")
      setParsed(data)
      setStep("preview")
    } catch (e: any) {
      toast(e.message || "Failed to load samples", "error")
    } finally {
      setLoadingSamples(false)
    }
  }

  async function loadDemoBaseline() {
    if (!selectedClient) {
      toast("Select a client first", "error")
      return
    }
    setLoadingBaseline(true)
    try {
      const result = await apiPost<{
        seeded: number
        entries: number
        period: string
        hotel_name: string
        reason: string
        coa_notice: string
      }>(`/api/v1/ehf/demo-baseline?client_id=${selectedClient.id}`, {})
      if (result.seeded > 0) {
        toast(
          `Seeded ${result.entries} journal entries for ${result.hotel_name} (${result.period})`,
          "success"
        )
      } else {
        toast(
          result.reason
            ? `Skipped: ${result.reason}`
            : "Baseline already loaded",
          "error"
        )
      }
    } catch (e: any) {
      toast(e.message || "Failed to load baseline", "error")
    } finally {
      setLoadingBaseline(false)
    }
  }

  async function downloadSamples() {
    const token = localStorage.getItem("bpo_token")
    const res = await fetch("/api/v1/ehf/sample-invoices/download", {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) {
      toast("Download failed", "error")
      return
    }
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "ehf-sample-invoices.zip"
    a.click()
    URL.revokeObjectURL(url)
  }

  async function bookInvoices() {
    if (!selectedClient) {
      toast("Select a client first")
      return
    }
    setBooking(true)
    try {
      if (files.length > 0) {
        const formData = new FormData()
        files.forEach((f) => formData.append("files", f))
        const token = localStorage.getItem("bpo_token")
        const res = await fetch(
          `/api/v1/ehf/import?client_id=${selectedClient.id}`,
          {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
            body: formData,
          }
        )
        if (!res.ok) {
          const d = await res.json().catch(() => ({ detail: "Import failed" }))
          throw new Error(d.detail || "Import failed")
        }
        const result: ImportResult = await res.json()
        setBookResult(result)
      } else {
        const result = await apiPost<ImportResult>(
          `/api/v1/ehf/import-samples?client_id=${selectedClient.id}`,
          {}
        )
        setBookResult(result)
      }
      setStep("booked")
      toast("Invoices booked to general ledger")
    } catch (e: any) {
      toast(e.message || "Booking failed", "error")
    } finally {
      setBooking(false)
    }
  }

  async function loadReports() {
    if (!selectedClient) return
    setLoadingReports(true)
    try {
      const [tb, pl, bs] = await Promise.all([
        apiGet<TrialBalance>(
          `/api/v1/journal/reports/trial-balance?client_id=${selectedClient.id}`
        ),
        apiGet<PLReport>(
          `/api/v1/reports/profit-and-loss?client_id=${selectedClient.id}&year=2026`
        ),
        apiGet<BSReport>(
          `/api/v1/reports/balance-sheet?client_id=${selectedClient.id}`
        ),
      ])
      setTrialBalance(tb)
      setPLReport(pl)
      setBSReport(bs)
      setStep("reports")
    } catch (e: any) {
      toast(e.message || "Failed to load reports", "error")
    } finally {
      setLoadingReports(false)
    }
  }

  function reset() {
    setStep("upload")
    setFiles([])
    setParsed([])
    setBookResult(null)
    setTrialBalance(null)
    setPLReport(null)
    setBSReport(null)
  }

  const totalNet = parsed.reduce((s, inv) => s + parseFloat(inv.subtotal), 0)
  const totalVat = parsed.reduce((s, inv) => s + parseFloat(inv.total_vat), 0)
  const totalGross = parsed.reduce((s, inv) => s + parseFloat(inv.total), 0)

  if (!selectedClient) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-xl font-semibold">EHF Import</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Import Norwegian EHF invoices and auto-book to the general ledger.
          </p>
        </div>
        <EmptyState
          icon={<FileText />}
          title="No client selected"
          description="Select a client from the top bar to import invoices."
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">EHF Invoice Import</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {selectedClient.name} — Upload EHF XML invoices, auto-book to GL, view impact on P&L and Balance Sheet
          </p>
        </div>
        {step !== "upload" && (
          <Button variant="outline" size="sm" onClick={reset}>
            Start Over
          </Button>
        )}
      </div>

      {/* Step indicators */}
      <div className="flex items-center gap-2 text-sm">
        {(["upload", "preview", "booked", "reports"] as Step[]).map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            {i > 0 && <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />}
            <span
              className={cn(
                "px-3 py-1 rounded-full text-xs font-medium transition-colors",
                step === s
                  ? "bg-primary text-primary-foreground"
                  : (["upload", "preview", "booked", "reports"].indexOf(step) > i)
                    ? "bg-green-100 text-green-700"
                    : "bg-muted text-muted-foreground"
              )}
            >
              {s === "upload" && "1. Upload"}
              {s === "preview" && "2. Preview"}
              {s === "booked" && "3. Booked"}
              {s === "reports" && "4. Reports"}
            </span>
          </div>
        ))}
      </div>

      {/* STEP 1: Upload */}
      {step === "upload" && (
        <div className="space-y-4">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileRef.current?.click()}
            className={cn(
              "border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all",
              dragOver
                ? "border-primary bg-primary/5 scale-[1.01]"
                : "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/50"
            )}
          >
            <input
              ref={fileRef}
              type="file"
              accept=".xml"
              multiple
              className="hidden"
              onChange={handleFileSelect}
            />
            {parsing ? (
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="h-10 w-10 animate-spin text-primary" />
                <p className="text-sm font-medium">Parsing EHF invoices...</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <Upload className="h-10 w-10 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Drop EHF XML files here or click to browse</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Norwegian EHF Billing 3.0 / PEPPOL BIS format
                  </p>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            <div className="flex-1 border-t" />
            <span className="text-xs text-muted-foreground">or use demo data</span>
            <div className="flex-1 border-t" />
          </div>

          <div className="rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/30 p-4">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div className="flex-1 min-w-[260px]">
                <h4 className="text-sm font-medium text-amber-900 dark:text-amber-200">
                  Hotel Q1 baseline (recommended for demo)
                </h4>
                <p className="text-xs text-amber-800/80 dark:text-amber-200/80 mt-1 leading-relaxed">
                  Seeds a legacy Norwegian hotel: opening balance
                  (bygg, inventar, pantelån, egenkapital) plus 3 months of
                  revenue (rom 12%, mat 15%, alkohol/minibar/konferanse 25%)
                  and typical Q1 expenses. Load this first — then run the
                  EHF import to see April's supplier invoices land on top.
                </p>
              </div>
              <Button
                variant="outline"
                onClick={loadDemoBaseline}
                loading={loadingBaseline}
                disabled={!selectedClient}
              >
                <Building2 className="h-4 w-4" />
                Load Q1 Baseline
              </Button>
            </div>
          </div>

          <div className="flex gap-3 justify-center">
            <Button
              variant="outline"
              onClick={loadSampleInvoices}
              loading={loadingSamples}
            >
              <FileText className="h-4 w-4" />
              Load 10 Sample Invoices
            </Button>
            <Button variant="ghost" onClick={downloadSamples}>
              <Download className="h-4 w-4" />
              Download as ZIP
            </Button>
          </div>
        </div>
      )}

      {/* STEP 2: Preview parsed invoices */}
      {step === "preview" && parsed.length > 0 && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <MetricCard
              title="Invoices"
              value={`${parsed.length}`}
              icon={<FileText />}
            />
            <MetricCard
              title="Total ex. VAT"
              value={formatCurrency(totalNet, "NOK")}
              icon={<DollarSign />}
            />
            <MetricCard
              title="Total VAT"
              value={formatCurrency(totalVat, "NOK")}
              icon={<TrendingUp />}
            />
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Invoice #</TableHead>
                <TableHead>Supplier</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Lines</TableHead>
                <TableHead className="text-right">Net</TableHead>
                <TableHead className="text-right">VAT</TableHead>
                <TableHead className="text-right">Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {parsed.map((inv) => (
                <TableRow key={inv.invoice_number}>
                  <TableCell>
                    <span className="font-mono text-xs">{inv.invoice_number}</span>
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="font-medium text-sm">{inv.supplier_name}</p>
                      <p className="text-2xs text-muted-foreground">
                        Org: {inv.supplier_org_number}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell className="text-xs">{inv.issue_date}</TableCell>
                  <TableCell>
                    <div className="space-y-0.5">
                      {inv.lines.map((l, i) => (
                        <div key={i} className="flex items-center gap-2 text-xs">
                          <Badge variant="secondary" className="font-mono text-2xs px-1.5">
                            {l.suggested_account}
                          </Badge>
                          <span className="truncate max-w-[200px]">{l.description}</span>
                          <span className="text-muted-foreground ml-auto">
                            MVA {l.vat_rate}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {formatCurrency(parseFloat(inv.subtotal), "NOK")}
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs text-muted-foreground">
                    {formatCurrency(parseFloat(inv.total_vat), "NOK")}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm font-medium">
                    {formatCurrency(parseFloat(inv.total), "NOK")}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <div className="flex items-center justify-between pt-2 border-t">
            <p className="text-sm text-muted-foreground">
              {parsed.length} invoices ready — booking will create journal entries per NS 4102
            </p>
            <div className="flex gap-3">
              <Button variant="outline" onClick={reset}>
                Cancel
              </Button>
              <Button onClick={bookInvoices} loading={booking}>
                <BookOpen className="h-4 w-4" />
                Book to General Ledger
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* STEP 3: Booking results */}
      {step === "booked" && bookResult && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <MetricCard
              title="Invoices Booked"
              value={`${bookResult.invoices_booked} / ${bookResult.invoices_parsed}`}
              icon={<CheckCircle2 />}
            />
            <MetricCard
              title="Journal Entries"
              value={`${bookResult.journal_entries.length}`}
              icon={<BookOpen />}
            />
            <MetricCard
              title="Total Posted"
              value={formatCurrency(
                bookResult.journal_entries.reduce(
                  (s, j) => s + parseFloat(j.total_debit),
                  0
                ),
                "NOK"
              )}
              icon={<DollarSign />}
            />
          </div>

          {bookResult.notices && bookResult.notices.length > 0 && (
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
              <p className="text-sm font-medium text-blue-700 dark:text-blue-400 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4" />
                {bookResult.notices.length} notice(s):
              </p>
              <ul className="text-sm text-blue-700/80 dark:text-blue-400/80 mt-2 space-y-1 list-disc list-inside">
                {bookResult.notices.map((n, i) => (
                  <li key={i}>{n}</li>
                ))}
              </ul>
            </div>
          )}

          {bookResult.errors.length > 0 && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
              <p className="text-sm font-medium text-destructive flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                {bookResult.errors.length} error(s):
              </p>
              <ul className="text-sm text-destructive/80 mt-2 space-y-1 list-disc list-inside">
                {bookResult.errors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            </div>
          )}

          <div>
            <h3 className="text-sm font-medium mb-2">Journal Entry Ledger</h3>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Entry ID</TableHead>
                  <TableHead>Invoice</TableHead>
                  <TableHead>Lines</TableHead>
                  <TableHead className="text-right">Total Debit</TableHead>
                  <TableHead className="text-right">Total Credit</TableHead>
                  <TableHead>Balance</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {bookResult.journal_entries.map((j) => {
                  const balanced =
                    Math.abs(parseFloat(j.total_debit) - parseFloat(j.total_credit)) < 0.01
                  return (
                    <TableRow key={j.journal_entry_id}>
                      <TableCell>
                        <span className="font-mono text-xs">JE-{j.journal_entry_id}</span>
                      </TableCell>
                      <TableCell>
                        <span className="font-mono text-xs">{j.invoice_number}</span>
                      </TableCell>
                      <TableCell>{j.lines_posted} lines</TableCell>
                      <TableCell className="text-right font-mono text-sm">
                        {formatCurrency(parseFloat(j.total_debit), "NOK")}
                      </TableCell>
                      <TableCell className="text-right font-mono text-sm">
                        {formatCurrency(parseFloat(j.total_credit), "NOK")}
                      </TableCell>
                      <TableCell>
                        <Badge variant={balanced ? "success" : "destructive"}>
                          {balanced ? "Balanced" : "Unbalanced"}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </div>

          <div className="flex justify-end pt-2 border-t">
            <Button onClick={loadReports} loading={loadingReports}>
              <BarChart3 className="h-4 w-4" />
              View Updated Reports
            </Button>
          </div>
        </div>
      )}

      {/* STEP 4: Reports (P&L + Balance Sheet) */}
      {step === "reports" && (
        <div className="space-y-6">
          {/* P&L */}
          {plReport && (
            <div className="border rounded-lg overflow-hidden">
              <div className="bg-muted/50 px-4 py-3 border-b">
                <h3 className="text-sm font-semibold flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Profit & Loss — {selectedClient.name} — 2026
                </h3>
              </div>
              <div className="divide-y">
                <div className="px-4 py-2">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                    Revenue (3xxx)
                  </p>
                  {plReport.revenue.lines.length > 0 ? (
                    plReport.revenue.lines.map((l: any, i: number) => (
                      <div key={i} className="flex justify-between py-1 text-sm">
                        <span>
                          <span className="font-mono text-xs text-muted-foreground mr-2">
                            {l.code}
                          </span>
                          {l.name}
                        </span>
                        <span className="font-mono">{formatCurrency(l.amount, "NOK")}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-muted-foreground py-1">No revenue entries</p>
                  )}
                  <div className="flex justify-between py-1 text-sm font-semibold border-t mt-1">
                    <span>Total Revenue</span>
                    <span className="font-mono">
                      {formatCurrency(plReport.revenue.total, "NOK")}
                    </span>
                  </div>
                </div>

                <div className="px-4 py-2">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                    Expenses (4xxx–7xxx)
                  </p>
                  {plReport.expenses.lines.length > 0 ? (
                    plReport.expenses.lines.map((l: any, i: number) => (
                      <div key={i} className="flex justify-between py-1 text-sm">
                        <span>
                          <span className="font-mono text-xs text-muted-foreground mr-2">
                            {l.code}
                          </span>
                          {l.name}
                        </span>
                        <span className="font-mono">{formatCurrency(l.amount, "NOK")}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-muted-foreground py-1">No expense entries</p>
                  )}
                  <div className="flex justify-between py-1 text-sm font-semibold border-t mt-1">
                    <span>Total Expenses</span>
                    <span className="font-mono">
                      {formatCurrency(plReport.expenses.total, "NOK")}
                    </span>
                  </div>
                </div>

                <div className="px-4 py-3 bg-muted/30">
                  <div className="flex justify-between text-base font-bold">
                    <span>Net Profit / (Loss)</span>
                    <span
                      className={cn(
                        "font-mono",
                        plReport.net_profit >= 0 ? "text-green-600" : "text-red-600"
                      )}
                    >
                      {formatCurrency(plReport.net_profit, "NOK")}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Balance Sheet */}
          {bsReport && (
            <div className="border rounded-lg overflow-hidden">
              <div className="bg-muted/50 px-4 py-3 border-b">
                <h3 className="text-sm font-semibold flex items-center gap-2">
                  <Building2 className="h-4 w-4" />
                  Balance Sheet — {selectedClient.name}
                </h3>
              </div>
              <div className="divide-y">
                {(["assets", "liabilities", "equity"] as const).map((section) => (
                  <div key={section} className="px-4 py-2">
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                      {section === "assets"
                        ? "Assets (1xxx)"
                        : section === "liabilities"
                          ? "Liabilities (2xxx)"
                          : "Equity"}
                    </p>
                    {bsReport[section].lines.length > 0 ? (
                      bsReport[section].lines.map((l: any, i: number) => (
                        <div key={i} className="flex justify-between py-1 text-sm">
                          <span>
                            <span className="font-mono text-xs text-muted-foreground mr-2">
                              {l.code}
                            </span>
                            {l.name}
                          </span>
                          <span className="font-mono">
                            {formatCurrency(Math.abs(l.amount), "NOK")}
                          </span>
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-muted-foreground py-1">
                        No {section} entries
                      </p>
                    )}
                    <div className="flex justify-between py-1 text-sm font-semibold border-t mt-1">
                      <span>Total {section.charAt(0).toUpperCase() + section.slice(1)}</span>
                      <span className="font-mono">
                        {formatCurrency(Math.abs(bsReport[section].total), "NOK")}
                      </span>
                    </div>
                  </div>
                ))}

                <div className="px-4 py-3 bg-muted/30">
                  <div className="flex justify-between text-sm font-bold">
                    <span>Balance Check</span>
                    <Badge variant={bsReport.check ? "success" : "destructive"}>
                      {bsReport.check ? "Balanced" : "Not Balanced"}
                    </Badge>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="flex justify-end">
            <Button variant="outline" onClick={reset}>
              Import More Invoices
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

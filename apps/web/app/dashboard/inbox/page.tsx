"use client"

import { useEffect, useState, useRef, DragEvent } from "react"
import {
  Upload,
  FileText,
  CheckCircle2,
  XCircle,
  Loader2,
  Mail,
  Smartphone,
  FileInput,
  Sparkles,
  Inbox as InboxIcon,
  AlertCircle,
} from "lucide-react"
import { apiGet, apiPost } from "@/lib/api"
import { cn } from "@/lib/utils"
import { useClientContext } from "@/lib/client-context"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useToast } from "@/components/ui/toast"

interface InboxItem {
  id: number
  client_id: number | null
  source: string
  original_filename: string | null
  status: string
  extracted_vendor: string | null
  extracted_date: string | null
  extracted_amount_minor: number | null
  extracted_vat_minor: number | null
  extracted_currency: string | null
  extracted_invoice_number: string | null
  suggested_account_code: string | null
  suggested_account_name: string | null
  ai_confidence: number | null
  ai_reasoning: string | null
  approved_at: string | null
  rejected_at: string | null
  rejection_reason: string | null
  created_at: string
}

const STATUS_TABS = [
  { key: "all", label: "All" },
  { key: "pending", label: "Pending" },
  { key: "extracted", label: "Awaiting review" },
  { key: "approved", label: "Approved" },
  { key: "rejected", label: "Rejected" },
] as const

type StatusKey = (typeof STATUS_TABS)[number]["key"]

function fmtMinor(minor: number | null, currency: string | null): string {
  if (minor === null) return "—"
  const formatter = new Intl.NumberFormat("nb-NO", {
    style: "currency",
    currency: currency || "NOK",
    maximumFractionDigits: 2,
  })
  return formatter.format(minor / 100)
}

function fmtRelative(iso: string): string {
  const minutes = Math.floor((Date.now() - new Date(iso).getTime()) / 60_000)
  if (minutes < 1) return "just now"
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

function sourceIcon(source: string) {
  if (source === "email") return <Mail className="h-3.5 w-3.5" />
  if (source === "mobile") return <Smartphone className="h-3.5 w-3.5" />
  if (source === "ehf") return <FileInput className="h-3.5 w-3.5" />
  return <Upload className="h-3.5 w-3.5" />
}

function confidenceBadge(c: number | null) {
  if (c === null) return null
  const pct = Math.round(c * 100)
  let variant: "success" | "secondary" | "destructive" = "secondary"
  if (c >= 0.9) variant = "success"
  else if (c < 0.5) variant = "destructive"
  return (
    <Badge variant={variant} className="text-xs">
      <Sparkles className="h-3 w-3 mr-1" />
      {pct}%
    </Badge>
  )
}

export default function InboxPage() {
  const { selectedClient } = useClientContext()
  const { toast } = useToast()
  const dropRef = useRef<HTMLDivElement>(null)

  const [items, setItems] = useState<InboxItem[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<StatusKey>("all")
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [busyItem, setBusyItem] = useState<number | null>(null)

  const load = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ limit: "100" })
      if (selectedClient) params.set("client_id", selectedClient.id.toString())
      const data = await apiGet<InboxItem[]>(`/api/v1/inbox?${params}`)
      setItems(data)
    } catch (e: any) {
      toast(e.message || "Failed to load inbox")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedClient?.id])

  const filtered = items.filter((i) => tab === "all" || i.status === tab)

  // Counts per tab
  const counts: Record<StatusKey, number> = {
    all: items.length,
    pending: items.filter((i) => i.status === "pending").length,
    extracted: items.filter((i) => i.status === "extracted").length,
    approved: items.filter((i) => i.status === "approved").length,
    rejected: items.filter((i) => i.status === "rejected").length,
  }

  const handleUpload = async (filename: string) => {
    if (!selectedClient) {
      toast("Pick a client in the top bar first")
      return
    }
    setUploading(true)
    try {
      await apiPost("/api/v1/inbox/upload", {
        client_id: selectedClient.id,
        filename,
        source: "upload",
      })
      toast(`Uploaded ${filename}`)
      await load()
    } catch (e: any) {
      toast(e.message || "Upload failed")
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = async (e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragging(false)
    const files = Array.from(e.dataTransfer.files)
    if (files.length === 0) return
    for (const f of files) {
      await handleUpload(f.name)
    }
  }

  const handleApprove = async (id: number) => {
    setBusyItem(id)
    try {
      await apiPost(`/api/v1/inbox/${id}/approve`, {})
      toast("Approved — Transaction created")
      await load()
    } catch (e: any) {
      toast(e.message || "Approval failed")
    } finally {
      setBusyItem(null)
    }
  }

  const handleReject = async (id: number) => {
    const reason = window.prompt("Why are you rejecting this item?")
    if (!reason) return
    setBusyItem(id)
    try {
      await apiPost(`/api/v1/inbox/${id}/reject`, { reason })
      toast("Rejected")
      await load()
    } catch (e: any) {
      toast(e.message || "Rejection failed")
    } finally {
      setBusyItem(null)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold flex items-center gap-2">
            <InboxIcon className="h-5 w-5" />
            Inbox
            {selectedClient && (
              <span className="text-sm font-normal text-muted-foreground">
                · {selectedClient.name}
              </span>
            )}
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Receipts, invoices and bank statements. AI extracts the details
            — you approve or reject.
          </p>
        </div>
      </div>

      {/* Drop zone + intake channels */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card
          className={cn(
            "md:col-span-2 cursor-pointer transition-colors border-2 border-dashed",
            dragging
              ? "border-primary bg-primary/5"
              : "border-border hover:border-primary/40"
          )}
          ref={dropRef as any}
          onDragEnter={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
        >
          <CardContent className="py-10 text-center">
            <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
            <p className="text-sm font-medium">
              {uploading
                ? "Uploading..."
                : "Drop receipts, invoices, or bank statements here"}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {selectedClient
                ? `Will be assigned to ${selectedClient.name}`
                : "Select a client in the top bar before uploading"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Other intake channels</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs">
            <div className="flex items-center gap-2">
              <Mail className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-muted-foreground">Forward to:</span>
            </div>
            <code className="block bg-muted px-2 py-1.5 rounded text-2xs break-all">
              receipts-{selectedClient?.id || "{client}"}@inbox.claud-erp.com
            </code>
            <div className="flex items-center gap-2 pt-1">
              <Smartphone className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-muted-foreground">Mobile app:</span>
              <Badge variant="secondary">iOS / Android</Badge>
            </div>
            <div className="flex items-center gap-2">
              <FileInput className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-muted-foreground">EHF (Norway B2G):</span>
              <Badge variant="success">enabled</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Status tabs */}
      <div className="border-b border-border flex gap-1">
        {STATUS_TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              "px-3 py-2 text-sm font-medium border-b-2 transition-colors -mb-px",
              tab === t.key
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            {t.label}
            {counts[t.key] > 0 && (
              <Badge variant="secondary" className="ml-1.5 text-2xs">
                {counts[t.key]}
              </Badge>
            )}
          </button>
        ))}
      </div>

      {/* Items list */}
      {loading ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin mr-2" />
          Loading inbox...
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">
              {tab === "all"
                ? "Inbox is empty."
                : `No items with status "${tab}".`}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {filtered.map((item) => (
            <Card key={item.id}>
              <CardContent className="py-4">
                <div className="flex items-start gap-4">
                  <FileText className="h-5 w-5 mt-0.5 text-muted-foreground shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="font-medium text-sm truncate">
                          {item.extracted_vendor || (
                            <span className="text-muted-foreground italic">
                              Unrecognized vendor
                            </span>
                          )}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {item.original_filename}
                        </p>
                      </div>
                      <div className="flex items-center gap-1.5 shrink-0">
                        {confidenceBadge(item.ai_confidence)}
                        <Badge
                          variant={
                            item.status === "approved"
                              ? "success"
                              : item.status === "rejected"
                                ? "destructive"
                                : "secondary"
                          }
                        >
                          {item.status}
                        </Badge>
                      </div>
                    </div>

                    {/* Extracted details grid */}
                    <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                      <div>
                        <p className="text-muted-foreground">Date</p>
                        <p className="font-medium">
                          {item.extracted_date
                            ? new Date(item.extracted_date).toLocaleDateString(
                                "nb-NO"
                              )
                            : "—"}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Amount</p>
                        <p className="font-medium">
                          {fmtMinor(
                            item.extracted_amount_minor,
                            item.extracted_currency
                          )}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">VAT</p>
                        <p className="font-medium">
                          {fmtMinor(
                            item.extracted_vat_minor,
                            item.extracted_currency
                          )}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Account</p>
                        <p className="font-medium">
                          {item.suggested_account_code ? (
                            <>
                              {item.suggested_account_code}
                              <span className="text-muted-foreground ml-1">
                                {item.suggested_account_name}
                              </span>
                            </>
                          ) : (
                            "—"
                          )}
                        </p>
                      </div>
                    </div>

                    {item.ai_reasoning && (
                      <p className="text-2xs text-muted-foreground mt-2 italic">
                        AI: {item.ai_reasoning}
                      </p>
                    )}

                    {item.rejection_reason && (
                      <div className="mt-2 flex items-start gap-1.5 text-xs text-destructive">
                        <AlertCircle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                        <p>{item.rejection_reason}</p>
                      </div>
                    )}

                    {/* Footer: source + actions */}
                    <div className="flex items-center justify-between mt-3">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        {sourceIcon(item.source)}
                        <span className="capitalize">{item.source}</span>
                        <span>·</span>
                        <span>{fmtRelative(item.created_at)}</span>
                      </div>

                      {(item.status === "pending" ||
                        item.status === "extracted") && (
                        <div className="flex gap-1.5">
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={busyItem === item.id}
                            onClick={() => handleReject(item.id)}
                          >
                            <XCircle className="h-3.5 w-3.5 mr-1" />
                            Reject
                          </Button>
                          <Button
                            size="sm"
                            disabled={busyItem === item.id}
                            onClick={() => handleApprove(item.id)}
                          >
                            {busyItem === item.id ? (
                              <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
                            ) : (
                              <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                            )}
                            Approve
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

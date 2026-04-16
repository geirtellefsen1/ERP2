"use client"

import { useEffect, useState } from "react"
import { Plus, ShieldCheck } from "lucide-react"
import { apiGet, apiPost } from "@/lib/api"
import { cn, formatDate } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { Modal, ModalHeader, ModalTitle, ModalDescription, ModalContent, ModalFooter } from "@/components/ui/modal"
import { useToast } from "@/components/ui/toast"

interface DSR {
  id: number
  subject_email: string
  subject_name: string | null
  request_type: "access" | "erasure" | "portability" | "rectification"
  status: "pending" | "in_progress" | "completed" | "rejected"
  notes: string | null
  created_at: string
  deadline: string | null
}

const BADGE_MAP: Record<DSR["status"], { label: string; variant: "warning" | "default" | "success" | "destructive" }> = {
  pending: { label: "Pending", variant: "warning" },
  in_progress: { label: "In Progress", variant: "default" },
  completed: { label: "Completed", variant: "success" },
  rejected: { label: "Rejected", variant: "destructive" },
}

const TYPES = [
  { value: "access", label: "Access" },
  { value: "erasure", label: "Erasure" },
  { value: "portability", label: "Portability" },
  { value: "rectification", label: "Rectification" },
]

const FILTERS = [
  { key: "all", label: "All" },
  { key: "pending", label: "Pending" },
  { key: "in_progress", label: "In Progress" },
  { key: "completed", label: "Completed" },
]

const INIT_FORM = { subject_email: "", subject_name: "", request_type: "access", notes: "" }

export default function DSRPage() {
  const [items, setItems] = useState<DSR[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState("all")
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState(INIT_FORM)
  const [saving, setSaving] = useState(false)
  const [processingId, setProcessingId] = useState<number | null>(null)
  const { toast } = useToast()

  async function load() {
    try { setItems(await apiGet<DSR[]>("/api/v1/dsr")) }
    catch { toast("Failed to load DSR requests", "error") }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const body: Record<string, string> = { subject_email: form.subject_email, request_type: form.request_type }
      if (form.subject_name) body.subject_name = form.subject_name
      if (form.notes) body.notes = form.notes
      await apiPost("/api/v1/dsr", body)
      setShowModal(false)
      setForm(INIT_FORM)
      toast("DSR request created successfully")
      load()
    } catch (err: any) { toast(err.message, "error") }
    finally { setSaving(false) }
  }

  async function handleProcess(id: number) {
    setProcessingId(id)
    try {
      await apiPost(`/api/v1/dsr/${id}/process`, {})
      toast("DSR request processed")
      load()
    } catch (err: any) { toast(err.message, "error") }
    finally { setProcessingId(null) }
  }

  const filtered = filter === "all" ? items : items.filter((r) => r.status === filter)
  const countFor = (s: string) => s === "all" ? items.length : items.filter((r) => r.status === s).length
  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }))

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">Data Subject Requests</h1>
          <p className="text-sm text-muted-foreground mt-0.5">GDPR data subject rights management</p>
        </div>
        <Button onClick={() => setShowModal(true)} size="sm">
          <Plus className="h-4 w-4" /> New DSR Request
        </Button>
      </div>

      {/* Status filter tabs */}
      <div className="flex gap-1 bg-muted p-1 rounded-lg w-fit">
        {FILTERS.map((s) => (
          <button
            key={s.key}
            onClick={() => setFilter(s.key)}
            className={cn(
              "px-3 py-1 text-xs font-medium rounded-md transition-all",
              filter === s.key ? "bg-background shadow-xs text-foreground" : "text-muted-foreground hover:text-foreground"
            )}
          >
            {s.label} ({countFor(s.key)})
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-14 rounded-lg" />)}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<ShieldCheck />}
          title={items.length === 0 ? "No DSR requests yet" : "No matching requests"}
          description={items.length === 0
            ? "Create your first data subject request to start tracking GDPR compliance."
            : "No requests match the selected filter."}
          action={items.length === 0 ? { label: "New DSR Request", onClick: () => setShowModal(true) } : undefined}
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Subject Email</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Received</TableHead>
              <TableHead>Deadline</TableHead>
              <TableHead className="w-24">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((r) => {
              const b = BADGE_MAP[r.status]
              return (
                <TableRow key={r.id}>
                  <TableCell>
                    <span className="font-medium">{r.subject_email}</span>
                    {r.subject_name && <span className="block text-xs text-muted-foreground">{r.subject_name}</span>}
                  </TableCell>
                  <TableCell className="text-muted-foreground capitalize">{r.request_type}</TableCell>
                  <TableCell><Badge variant={b.variant}>{b.label}</Badge></TableCell>
                  <TableCell className="text-muted-foreground text-xs">{formatDate(r.created_at)}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">{r.deadline ? formatDate(r.deadline) : "--"}</TableCell>
                  <TableCell>
                    {(r.status === "pending" || r.status === "in_progress") && (
                      <Button size="sm" variant="outline" onClick={() => handleProcess(r.id)} loading={processingId === r.id}>
                        Process
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      )}

      {/* New DSR Modal */}
      <Modal open={showModal} onClose={() => setShowModal(false)}>
        <ModalHeader onClose={() => setShowModal(false)}>
          <ModalTitle>New DSR Request</ModalTitle>
          <ModalDescription>Submit a GDPR data subject rights request</ModalDescription>
        </ModalHeader>
        <form onSubmit={handleCreate}>
          <ModalContent className="space-y-4">
            <Input label="Subject Email" type="email" value={form.subject_email}
              onChange={(e) => set("subject_email", e.target.value)} placeholder="user@example.com" required />
            <Input label="Subject Name" value={form.subject_name}
              onChange={(e) => set("subject_name", e.target.value)} placeholder="Optional" hint="Full name of the data subject" />
            <Select label="Request Type" value={form.request_type}
              onChange={(e) => set("request_type", e.target.value)} options={TYPES} />
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">Notes</label>
              <textarea
                className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm transition-colors placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1 focus:ring-offset-background"
                rows={3} value={form.notes} onChange={(e) => set("notes", e.target.value)} placeholder="Additional context..." />
            </div>
          </ModalContent>
          <ModalFooter>
            <Button type="button" variant="outline" onClick={() => setShowModal(false)}>Cancel</Button>
            <Button type="submit" loading={saving}>Submit Request</Button>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  )
}

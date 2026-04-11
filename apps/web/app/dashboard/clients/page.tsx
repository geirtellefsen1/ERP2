"use client"

import { useEffect, useState } from "react"
import {
  Plus,
  Search,
  MoreHorizontal,
  Building2,
  Globe,
  Hash,
  Filter,
} from "lucide-react"
import { apiGet, apiPost } from "@/lib/api"
import { formatDate } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Avatar } from "@/components/ui/avatar"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
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
import { useToast } from "@/components/ui/toast"

interface Client {
  id: number
  name: string
  country: string
  industry: string
  registration_number: string | null
  is_active: boolean
  created_at: string
}

const COUNTRIES = [
  { value: "ZA", label: "South Africa" },
  { value: "NO", label: "Norway" },
  { value: "UK", label: "United Kingdom" },
  { value: "EU", label: "European Union" },
]

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [form, setForm] = useState({
    name: "",
    country: "ZA",
    industry: "",
    registration_number: "",
  })
  const [saving, setSaving] = useState(false)
  const { toast } = useToast()

  async function load() {
    try {
      const data: Client[] = await apiGet("/api/v1/clients")
      setClients(data)
    } catch {
      toast("Failed to load clients", "error")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      await apiPost("/api/v1/clients", form)
      setShowModal(false)
      setForm({ name: "", country: "ZA", industry: "", registration_number: "" })
      toast("Client created successfully")
      load()
    } catch (err: any) {
      toast(err.message, "error")
    } finally {
      setSaving(false)
    }
  }

  const filtered = clients.filter((c) => {
    const matchesSearch =
      !search ||
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.industry?.toLowerCase().includes(search.toLowerCase())
    const matchesStatus =
      statusFilter === "all" ||
      (statusFilter === "active" && c.is_active) ||
      (statusFilter === "inactive" && !c.is_active)
    return matchesSearch && matchesStatus
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">Clients</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {clients.length} client{clients.length !== 1 ? "s" : ""} total
          </p>
        </div>
        <Button onClick={() => setShowModal(true)} size="sm">
          <Plus className="h-4 w-4" />
          Add Client
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="flex-1 max-w-xs">
          <Input
            placeholder="Search clients..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            icon={<Search />}
          />
        </div>
        <Select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          options={[
            { value: "all", label: "All Status" },
            { value: "active", label: "Active" },
            { value: "inactive", label: "Inactive" },
          ]}
        />
      </div>

      {/* Table */}
      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-14 rounded-lg" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        clients.length === 0 ? (
          <EmptyState
            icon={<Building2 />}
            title="No clients yet"
            description="Add your first client to start managing their accounts, invoices, and reports."
            action={{
              label: "Add Client",
              onClick: () => setShowModal(true),
            }}
          />
        ) : (
          <EmptyState
            icon={<Search />}
            title="No results"
            description="No clients match your current filters. Try adjusting your search."
          />
        )
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Client</TableHead>
              <TableHead>Country</TableHead>
              <TableHead>Industry</TableHead>
              <TableHead>Reg. Number</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="w-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((c) => (
              <TableRow key={c.id}>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <Avatar name={c.name} size="sm" />
                    <span className="font-medium">{c.name}</span>
                  </div>
                </TableCell>
                <TableCell>
                  <span className="text-muted-foreground">
                    {COUNTRIES.find((co) => co.value === c.country)?.label ||
                      c.country}
                  </span>
                </TableCell>
                <TableCell>
                  <span className="text-muted-foreground">
                    {c.industry || "--"}
                  </span>
                </TableCell>
                <TableCell>
                  <span className="font-mono text-xs text-muted-foreground">
                    {c.registration_number || "--"}
                  </span>
                </TableCell>
                <TableCell>
                  <Badge variant={c.is_active ? "success" : "secondary"}>
                    {c.is_active ? "Active" : "Inactive"}
                  </Badge>
                </TableCell>
                <TableCell>
                  <span className="text-muted-foreground text-xs">
                    {c.created_at ? formatDate(c.created_at) : "--"}
                  </span>
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

      {/* Add Client Modal */}
      <Modal open={showModal} onClose={() => setShowModal(false)}>
        <ModalHeader onClose={() => setShowModal(false)}>
          <ModalTitle>Add New Client</ModalTitle>
          <ModalDescription>
            Add a company to start managing their books
          </ModalDescription>
        </ModalHeader>
        <form onSubmit={handleCreate}>
          <ModalContent className="space-y-4">
            <Input
              label="Company Name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Acme Corporation"
              icon={<Building2 />}
              required
            />
            <Select
              label="Country"
              value={form.country}
              onChange={(e) => setForm({ ...form, country: e.target.value })}
              options={COUNTRIES}
            />
            <Input
              label="Industry"
              value={form.industry}
              onChange={(e) => setForm({ ...form, industry: e.target.value })}
              placeholder="e.g. Hospitality, Retail, Construction"
            />
            <Input
              label="Registration Number"
              value={form.registration_number}
              onChange={(e) =>
                setForm({ ...form, registration_number: e.target.value })
              }
              placeholder="CIPC / Companies House"
              icon={<Hash />}
              hint="Optional company registration number"
            />
          </ModalContent>
          <ModalFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowModal(false)}
            >
              Cancel
            </Button>
            <Button type="submit" loading={saving}>
              Add Client
            </Button>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  )
}

"use client"

import { useEffect, useState, useCallback } from "react"
import {
  Plus,
  Search,
  MoreHorizontal,
  Building2,
  Globe,
  Hash,
  Pencil,
  Loader2,
  CheckCircle2,
  XCircle,
  MapPin,
  Phone,
  Mail,
  CreditCard,
} from "lucide-react"
import { apiGet, apiPost, apiPatch } from "@/lib/api"
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
  industry: string | null
  registration_number: string | null
  vat_number: string | null
  address: string | null
  city: string | null
  postal_code: string | null
  email: string | null
  phone: string | null
  default_currency: string
  is_active: boolean
  created_at: string
}

const COUNTRIES = [
  { value: "NO", label: "Norway" },
  { value: "SE", label: "Sweden" },
  { value: "FI", label: "Finland" },
  { value: "UK", label: "United Kingdom" },
  { value: "EU", label: "European Union" },
  { value: "ZA", label: "South Africa" },
]

const INDUSTRIES = [
  { value: "hospitality", label: "Hospitality" },
  { value: "restaurant", label: "Restaurant / F&B" },
  { value: "retail", label: "Retail" },
  { value: "construction", label: "Construction" },
  { value: "professional_services", label: "Professional Services" },
  { value: "real_estate", label: "Real Estate" },
  { value: "technology", label: "Technology" },
  { value: "healthcare", label: "Healthcare" },
  { value: "transport", label: "Transport & Logistics" },
  { value: "other", label: "Other" },
]

const CURRENCIES: Record<string, string> = {
  NO: "NOK",
  SE: "SEK",
  FI: "EUR",
  UK: "GBP",
  EU: "EUR",
  ZA: "ZAR",
}

const EMPTY_FORM = {
  name: "",
  country: "NO",
  industry: "",
  registration_number: "",
  vat_number: "",
  address: "",
  city: "",
  postal_code: "",
  email: "",
  phone: "",
  default_currency: "NOK",
}

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingClient, setEditingClient] = useState<Client | null>(null)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [countryFilter, setCountryFilter] = useState("all")
  const [form, setForm] = useState({ ...EMPTY_FORM })
  const [saving, setSaving] = useState(false)
  const [orgValidation, setOrgValidation] = useState<{
    valid: boolean
    formatted: string
    error: string | null
  } | null>(null)
  const [validating, setValidating] = useState(false)
  const { toast } = useToast()

  const load = useCallback(async () => {
    try {
      const data: Client[] = await apiGet("/api/v1/clients")
      setClients(data)
    } catch {
      toast("Failed to load clients", "error")
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    load()
  }, [load])

  function openCreate() {
    setEditingClient(null)
    setForm({ ...EMPTY_FORM })
    setOrgValidation(null)
    setShowModal(true)
  }

  function openEdit(client: Client) {
    setEditingClient(client)
    setForm({
      name: client.name,
      country: client.country,
      industry: client.industry || "",
      registration_number: client.registration_number || "",
      vat_number: client.vat_number || "",
      address: client.address || "",
      city: client.city || "",
      postal_code: client.postal_code || "",
      email: client.email || "",
      phone: client.phone || "",
      default_currency: client.default_currency || CURRENCIES[client.country] || "NOK",
    })
    setOrgValidation(null)
    setShowModal(true)
  }

  function handleCountryChange(country: string) {
    setForm({
      ...form,
      country,
      default_currency: CURRENCIES[country] || "NOK",
    })
    setOrgValidation(null)
  }

  async function validateOrgNumber() {
    if (!form.registration_number.trim()) return
    setValidating(true)
    try {
      const result = await apiPost<{
        valid: boolean
        formatted: string
        error: string | null
      }>("/api/v1/nordic/validate-org-number", {
        org_number: form.registration_number,
        country: form.country,
      })
      setOrgValidation(result)
      if (result.valid) {
        setForm({ ...form, registration_number: result.formatted })
      }
    } catch {
      setOrgValidation(null)
    } finally {
      setValidating(false)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = {
        name: form.name,
        country: form.country,
        industry: form.industry || null,
        registration_number: form.registration_number || null,
        vat_number: form.vat_number || null,
        address: form.address || null,
        city: form.city || null,
        postal_code: form.postal_code || null,
        email: form.email || null,
        phone: form.phone || null,
        default_currency: form.default_currency,
      }

      if (editingClient) {
        await apiPatch(`/api/v1/clients/${editingClient.id}`, payload)
        toast("Client updated")
      } else {
        await apiPost("/api/v1/clients", payload)
        toast("Client created — chart of accounts seeded")
      }
      setShowModal(false)
      setForm({ ...EMPTY_FORM })
      setEditingClient(null)
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
      c.industry?.toLowerCase().includes(search.toLowerCase()) ||
      c.registration_number?.includes(search) ||
      c.email?.toLowerCase().includes(search.toLowerCase())
    const matchesStatus =
      statusFilter === "all" ||
      (statusFilter === "active" && c.is_active) ||
      (statusFilter === "inactive" && !c.is_active)
    const matchesCountry = countryFilter === "all" || c.country === countryFilter
    return matchesSearch && matchesStatus && matchesCountry
  })

  const orgPlaceholder =
    form.country === "NO"
      ? "123 456 789"
      : form.country === "SE"
        ? "556677-8899"
        : "Company reg. number"

  const orgHint =
    form.country === "NO"
      ? "9-digit organisasjonsnummer"
      : form.country === "SE"
        ? "10-digit organisationsnummer"
        : "Company registration number"

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">Clients</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {clients.length} client{clients.length !== 1 ? "s" : ""} total
          </p>
        </div>
        <Button onClick={openCreate} size="sm">
          <Plus className="h-4 w-4" />
          Add Client
        </Button>
      </div>

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
        <Select
          value={countryFilter}
          onChange={(e) => setCountryFilter(e.target.value)}
          options={[
            { value: "all", label: "All Countries" },
            ...COUNTRIES,
          ]}
        />
      </div>

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
            action={{ label: "Add Client", onClick: openCreate }}
          />
        ) : (
          <EmptyState
            icon={<Search />}
            title="No results"
            description="No clients match your current filters."
          />
        )
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Client</TableHead>
              <TableHead>Country</TableHead>
              <TableHead>Industry</TableHead>
              <TableHead>Org. Number</TableHead>
              <TableHead>Currency</TableHead>
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
                    <div>
                      <span className="font-medium">{c.name}</span>
                      {c.email && (
                        <p className="text-2xs text-muted-foreground">{c.email}</p>
                      )}
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="secondary">
                    {COUNTRIES.find((co) => co.value === c.country)?.label || c.country}
                  </Badge>
                </TableCell>
                <TableCell>
                  <span className="text-muted-foreground capitalize">
                    {c.industry?.replace(/_/g, " ") || "—"}
                  </span>
                </TableCell>
                <TableCell>
                  <span className="font-mono text-xs text-muted-foreground">
                    {c.registration_number || "—"}
                  </span>
                </TableCell>
                <TableCell>
                  <span className="text-xs font-medium">{c.default_currency}</span>
                </TableCell>
                <TableCell>
                  <Badge variant={c.is_active ? "success" : "secondary"}>
                    {c.is_active ? "Active" : "Inactive"}
                  </Badge>
                </TableCell>
                <TableCell>
                  <span className="text-muted-foreground text-xs">
                    {c.created_at ? formatDate(c.created_at) : "—"}
                  </span>
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => openEdit(c)}
                    title="Edit client"
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <Modal open={showModal} onClose={() => setShowModal(false)} className="max-w-2xl">
        <ModalHeader onClose={() => setShowModal(false)}>
          <ModalTitle>
            {editingClient ? `Edit ${editingClient.name}` : "Add New Client"}
          </ModalTitle>
          <ModalDescription>
            {editingClient
              ? "Update company details and contact information"
              : "Add a company — chart of accounts will be auto-seeded based on country"}
          </ModalDescription>
        </ModalHeader>
        <form onSubmit={handleSubmit}>
          <ModalContent className="space-y-5">
            <div className="space-y-3">
              <p className="text-sm font-medium text-muted-foreground">Company details</p>
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Company Name"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Fjordvik Hotell AS"
                  icon={<Building2 />}
                  required
                />
                <Select
                  label="Country"
                  value={form.country}
                  onChange={(e) => handleCountryChange(e.target.value)}
                  options={COUNTRIES}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Select
                  label="Industry"
                  value={form.industry}
                  onChange={(e) => setForm({ ...form, industry: e.target.value })}
                  options={[{ value: "", label: "Select industry..." }, ...INDUSTRIES]}
                />
                <Select
                  label="Default Currency"
                  value={form.default_currency}
                  onChange={(e) => setForm({ ...form, default_currency: e.target.value })}
                  options={[
                    { value: "NOK", label: "NOK — Norwegian Krone" },
                    { value: "SEK", label: "SEK — Swedish Krona" },
                    { value: "EUR", label: "EUR — Euro" },
                    { value: "GBP", label: "GBP — British Pound" },
                    { value: "USD", label: "USD — US Dollar" },
                  ]}
                />
              </div>
            </div>

            <div className="space-y-3">
              <p className="text-sm font-medium text-muted-foreground">Registration</p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Input
                    label="Org. Number"
                    value={form.registration_number}
                    onChange={(e) => {
                      setForm({ ...form, registration_number: e.target.value })
                      setOrgValidation(null)
                    }}
                    onBlur={validateOrgNumber}
                    placeholder={orgPlaceholder}
                    icon={<Hash />}
                    hint={orgHint}
                  />
                  {validating && (
                    <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                      <Loader2 className="h-3 w-3 animate-spin" /> Validating...
                    </p>
                  )}
                  {orgValidation && !validating && (
                    <p
                      className={`text-xs mt-1 flex items-center gap-1 ${
                        orgValidation.valid ? "text-green-600" : "text-red-500"
                      }`}
                    >
                      {orgValidation.valid ? (
                        <>
                          <CheckCircle2 className="h-3 w-3" /> Valid: {orgValidation.formatted}
                        </>
                      ) : (
                        <>
                          <XCircle className="h-3 w-3" /> {orgValidation.error}
                        </>
                      )}
                    </p>
                  )}
                </div>
                <Input
                  label="VAT Number"
                  value={form.vat_number}
                  onChange={(e) => setForm({ ...form, vat_number: e.target.value })}
                  placeholder={
                    form.country === "NO"
                      ? "123456789MVA"
                      : form.country === "SE"
                        ? "SE5566778899 01"
                        : "VAT number"
                  }
                  icon={<CreditCard />}
                  hint={
                    form.country === "NO"
                      ? "MVA-nummer for registered businesses"
                      : form.country === "SE"
                        ? "SE + org.nr + 01"
                        : "VAT registration number"
                  }
                />
              </div>
            </div>

            <div className="space-y-3">
              <p className="text-sm font-medium text-muted-foreground">Contact & address</p>
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Email"
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  placeholder="post@fjordvik.no"
                  icon={<Mail />}
                />
                <Input
                  label="Phone"
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  placeholder={form.country === "NO" ? "+47 400 00 000" : "+46 70 000 00 00"}
                  icon={<Phone />}
                />
              </div>
              <Input
                label="Address"
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
                placeholder="Strandveien 1"
                icon={<MapPin />}
              />
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="City"
                  value={form.city}
                  onChange={(e) => setForm({ ...form, city: e.target.value })}
                  placeholder={form.country === "NO" ? "Tromsø" : "Stockholm"}
                />
                <Input
                  label="Postal Code"
                  value={form.postal_code}
                  onChange={(e) => setForm({ ...form, postal_code: e.target.value })}
                  placeholder={form.country === "NO" ? "9008" : "111 22"}
                />
              </div>
            </div>
          </ModalContent>
          <ModalFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setShowModal(false)
                setEditingClient(null)
              }}
            >
              Cancel
            </Button>
            <Button type="submit" loading={saving}>
              {editingClient ? "Save Changes" : "Add Client"}
            </Button>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  )
}

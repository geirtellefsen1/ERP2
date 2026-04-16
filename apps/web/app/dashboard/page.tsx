"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import {
  Users,
  FileText,
  Inbox,
  Building2,
  AlertTriangle,
  Sparkles,
  Clock,
  ArrowRight,
  Hotel,
  Loader2,
  CheckCircle2,
} from "lucide-react"
import { apiGet, apiPost } from "@/lib/api"
import { cn } from "@/lib/utils"
import { useClientContext } from "@/lib/client-context"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Avatar } from "@/components/ui/avatar"
import { useToast } from "@/components/ui/toast"

// --- Types -------------------------------------------------------------------

interface ClientSummary {
  id: number
  name: string
  country: string
  industry: string
  is_active: boolean
}

interface AiActivityItem {
  id: number
  client_id: number | null
  category: string
  severity: "info" | "warning" | "critical"
  title: string
  detail: string | null
  source_kind: string | null
  requires_review: boolean
  reviewed_at: string | null
  created_at: string
}

interface InboxItem {
  id: number
  client_id: number | null
  status: string
  extracted_vendor: string | null
  extracted_amount_minor: number | null
  ai_confidence: number | null
  created_at: string
}

interface PropertySummary {
  id: number
  client_id: number
  name: string
  total_rooms: number
}

// --- Helpers -----------------------------------------------------------------

function fmtRelative(iso: string): string {
  const minutes = Math.floor((Date.now() - new Date(iso).getTime()) / 60_000)
  if (minutes < 1) return "just now"
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

function severityClasses(sev: string): string {
  if (sev === "critical") return "border-red-300 bg-red-50 text-red-900"
  if (sev === "warning") return "border-amber-300 bg-amber-50 text-amber-900"
  return "border-blue-200 bg-blue-50 text-blue-900"
}

// --- Page --------------------------------------------------------------------

export default function DashboardPage() {
  const { selectedClient, clients, loading: clientsLoading } = useClientContext()

  if (clientsLoading) {
    return (
      <div className="flex items-center justify-center py-16 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin mr-2" />
        Loading...
      </div>
    )
  }

  if (selectedClient) {
    return <ClientFocusedDashboard clientId={selectedClient.id} clientName={selectedClient.name} />
  }

  return <AgencyOverviewDashboard clients={clients} />
}

// --- Agency overview (no client selected) ----------------------------------

function AgencyOverviewDashboard({ clients }: { clients: ClientSummary[] }) {
  const greeting = (() => {
    const h = new Date().getHours()
    if (h < 12) return "Good morning"
    if (h < 18) return "Good afternoon"
    return "Good evening"
  })()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">{greeting}</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Pick a client from the top bar to focus, or browse your portfolio below.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Your client portfolio
            <Badge variant="secondary" className="ml-1">
              {clients.length}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {clients.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4">
              No clients yet.{" "}
              <Link href="/dashboard/clients" className="text-primary hover:underline">
                Add your first client
              </Link>
              .
            </p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
              {clients.map((c) => (
                <Link
                  key={c.id}
                  href={`/dashboard?client=${c.id}`}
                  onClick={(e) => {
                    // Setting via context is handled in the TopBar — fall through
                  }}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-md hover:bg-accent transition-colors border border-transparent hover:border-border"
                >
                  <Avatar name={c.name} size="sm" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{c.name}</p>
                    <p className="text-2xs text-muted-foreground">
                      {c.industry || c.country}
                    </p>
                  </div>
                  <Badge variant={c.is_active ? "success" : "secondary"}>
                    {c.is_active ? "Active" : "Inactive"}
                  </Badge>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// --- Client-focused dashboard ----------------------------------------------

function ClientFocusedDashboard({
  clientId,
  clientName,
}: {
  clientId: number
  clientName: string
}) {
  const [activity, setActivity] = useState<AiActivityItem[]>([])
  const [inbox, setInbox] = useState<InboxItem[]>([])
  const [properties, setProperties] = useState<PropertySummary[]>([])
  const [loading, setLoading] = useState(true)
  const [approving, setApproving] = useState<number | null>(null)
  const { toast } = useToast()

  const load = async () => {
    try {
      const [act, inb, props] = await Promise.all([
        apiGet<AiActivityItem[]>(
          `/api/v1/hospitality/ai-activity?since_hours=72&client_id=${clientId}&limit=20`
        ),
        apiGet<InboxItem[]>(`/api/v1/inbox?client_id=${clientId}&limit=10`),
        apiGet<PropertySummary[]>(
          `/api/v1/hospitality/properties?client_id=${clientId}`
        ),
      ])
      setActivity(act)
      setInbox(inb)
      setProperties(props)
    } catch (e: any) {
      toast(e.message || "Failed to load dashboard")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clientId])

  const approveActivity = async (id: number) => {
    setApproving(id)
    try {
      await apiPost(`/api/v1/hospitality/ai-activity/${id}/approve`, {})
      setActivity((items) =>
        items.map((i) =>
          i.id === id ? { ...i, reviewed_at: new Date().toISOString() } : i
        )
      )
      toast("Approved")
    } catch (e: any) {
      toast(e.message || "Approval failed")
    } finally {
      setApproving(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin mr-2" />
        Loading {clientName}...
      </div>
    )
  }

  const pending = activity.filter((a) => a.requires_review && !a.reviewed_at)
  const completed = activity.filter((a) => !a.requires_review)
  const inboxPending = inbox.filter((i) => i.status === "pending" || i.status === "extracted")

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">
            Working on
          </p>
          <h1 className="text-xl font-semibold mt-0.5">{clientName}</h1>
        </div>
        <div className="flex gap-2">
          {properties.length > 0 && (
            <Button variant="outline" size="sm" asChild>
              <Link href={`/dashboard/hospitality/${properties[0].id}`}>
                <Hotel className="h-4 w-4" />
                Hospitality dashboard
              </Link>
            </Button>
          )}
          <Button size="sm" asChild>
            <Link href="/dashboard/inbox">
              <Inbox className="h-4 w-4" />
              Open inbox
              {inboxPending.length > 0 && (
                <Badge variant="destructive" className="ml-1.5">
                  {inboxPending.length}
                </Badge>
              )}
            </Link>
          </Button>
        </div>
      </div>

      {/* Two-column inbox: needs attention + AI did this */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              Needs your attention
              {pending.length > 0 && (
                <Badge variant="destructive" className="ml-1">
                  {pending.length}
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {pending.length === 0 && (
              <p className="text-sm text-muted-foreground">
                All caught up — nothing to approve right now.
              </p>
            )}
            {pending.map((item) => (
              <div
                key={item.id}
                className={cn("border rounded-md p-3", severityClasses(item.severity))}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="font-medium text-sm">{item.title}</p>
                    {item.detail && (
                      <p className="text-xs mt-1 opacity-80">{item.detail}</p>
                    )}
                    <p className="text-xs mt-2 opacity-60 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {fmtRelative(item.created_at)}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={approving === item.id}
                    onClick={() => approveActivity(item.id)}
                  >
                    {approving === item.id ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <CheckCircle2 className="h-3.5 w-3.5" />
                    )}
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              AI did this since you were last here
              {completed.length > 0 && (
                <Badge variant="secondary" className="ml-1">
                  {completed.length}
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {completed.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No completed AI activity in the last 72 hours.
              </p>
            )}
            {completed.map((item) => (
              <div key={item.id} className="border rounded-md p-3 bg-muted/30">
                <p className="font-medium text-sm">{item.title}</p>
                {item.detail && (
                  <p className="text-xs mt-1 text-muted-foreground">
                    {item.detail}
                  </p>
                )}
                <p className="text-xs mt-2 text-muted-foreground flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {fmtRelative(item.created_at)}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Inbox preview */}
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="flex items-center gap-2">
            <Inbox className="h-4 w-4" />
            Inbox
            {inboxPending.length > 0 && (
              <Badge variant="destructive" className="ml-1">
                {inboxPending.length} pending
              </Badge>
            )}
          </CardTitle>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/dashboard/inbox">
              View all <ArrowRight className="h-3.5 w-3.5 ml-1" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {inbox.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4">
              Inbox is empty. Drop receipts at <Link href="/dashboard/inbox" className="text-primary hover:underline">/dashboard/inbox</Link> or forward them by email.
            </p>
          ) : (
            <div className="space-y-1.5">
              {inbox.slice(0, 5).map((i) => (
                <div
                  key={i.id}
                  className="flex items-center gap-3 px-2 py-2 rounded-md hover:bg-accent/50"
                >
                  <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {i.extracted_vendor || "Awaiting extraction"}
                    </p>
                    <p className="text-2xs text-muted-foreground">
                      {fmtRelative(i.created_at)}
                      {i.ai_confidence != null &&
                        ` · ${Math.round(i.ai_confidence * 100)}% confidence`}
                    </p>
                  </div>
                  <Badge
                    variant={
                      i.status === "approved"
                        ? "success"
                        : i.status === "rejected"
                          ? "destructive"
                          : "secondary"
                    }
                  >
                    {i.status}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

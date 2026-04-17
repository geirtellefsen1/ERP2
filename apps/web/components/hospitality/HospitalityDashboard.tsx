"use client"

import { useEffect, useState } from "react"
import {
  Bed,
  Banknote,
  TrendingUp,
  Utensils,
  Wine,
  AlertTriangle,
  Sparkles,
  CheckCircle2,
  Clock,
  Loader2,
} from "lucide-react"
import { apiGet, apiPost } from "@/lib/api"
import { cn } from "@/lib/utils"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { MetricCard } from "@/components/ui/metric-card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useToast } from "@/components/ui/toast"

interface DaySnapshot {
  snapshot_date: string
  rooms_sold: number
  rooms_available: number
  occupancy_pct: number
  adr_minor: number | null
  revpar_minor: number
  food_revenue_minor: number
  beverage_revenue_minor: number
  food_covers: number
  rooms_revenue_minor: number
  total_revenue_minor: number
  currency: string
}

interface TrendPoint {
  point_date: string
  occupancy_pct: number
  revpar_minor: number
  total_revenue_minor: number
}

interface Alert {
  severity: "info" | "warning" | "critical"
  title: string
  detail: string
  metric: string
  current_value: number
  baseline_value: number
  delta_pct: number
}

interface RoomCategoryOut {
  id: number
  code: string
  label: string
  room_count: number
  base_rate_minor: number
  currency: string
}

interface OutletOut {
  id: number
  name: string
  outlet_type: string
}

interface DashboardResponse {
  property_id: number
  property_name: string
  country: string
  currency: string
  today: DaySnapshot | null
  yesterday: DaySnapshot | null
  trend_30d: TrendPoint[]
  alerts: Alert[]
  room_categories: RoomCategoryOut[]
  outlets: OutletOut[]
}

interface AiActivityItem {
  id: number
  category: string
  severity: "info" | "warning" | "critical"
  title: string
  detail: string | null
  requires_review: boolean
  reviewed_at: string | null
  created_at: string
}

function fmtMinor(minor: number | null, currency: string): string {
  if (minor === null) return "—"
  return new Intl.NumberFormat("nb-NO", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(minor / 100)
}

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

function TrendChart({ points }: { points: TrendPoint[] }) {
  if (points.length === 0) {
    return (
      <div className="text-sm text-muted-foreground py-8 text-center">
        No data yet
      </div>
    )
  }
  const w = 600
  const h = 140
  const pad = 8
  const max = Math.max(...points.map((p) => p.occupancy_pct), 100)
  const xs = (i: number) =>
    pad + (i / Math.max(1, points.length - 1)) * (w - 2 * pad)
  const ys = (v: number) => h - pad - (v / max) * (h - 2 * pad)
  const path = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${xs(i)} ${ys(p.occupancy_pct)}`)
    .join(" ")
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-auto">
      <path d={path} fill="none" stroke="currentColor" strokeWidth={2} />
      {points.map((p, i) => (
        <circle
          key={p.point_date}
          cx={xs(i)}
          cy={ys(p.occupancy_pct)}
          r={2}
          fill="currentColor"
        />
      ))}
    </svg>
  )
}

interface HospitalityDashboardProps {
  propertyId: number | string
  clientId?: number | string
  showAiActivity?: boolean
}

export default function HospitalityDashboard({
  propertyId,
  clientId,
  showAiActivity = true,
}: HospitalityDashboardProps) {
  const { toast } = useToast()
  const [data, setData] = useState<DashboardResponse | null>(null)
  const [activity, setActivity] = useState<AiActivityItem[]>([])
  const [loading, setLoading] = useState(true)
  const [approving, setApproving] = useState<number | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const fetches: Promise<any>[] = [
          apiGet<DashboardResponse>(
            `/api/v1/hospitality/properties/${propertyId}/dashboard`
          ),
        ]
        if (showAiActivity) {
          const clientParam = clientId ? `&client_id=${clientId}` : ""
          fetches.push(
            apiGet<AiActivityItem[]>(
              `/api/v1/hospitality/ai-activity?since_hours=72&limit=20${clientParam}`
            )
          )
        }
        const results = await Promise.all(fetches)
        setData(results[0])
        if (results[1]) setActivity(results[1])
      } catch (e: any) {
        toast(e.message || "Failed to load hospitality dashboard")
      } finally {
        setLoading(false)
      }
    }
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [propertyId, clientId])

  const handleApprove = async (id: number) => {
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
        Loading hospitality dashboard...
      </div>
    )
  }

  if (!data) {
    return (
      <div className="text-sm text-muted-foreground py-8 text-center">
        No data available for this property.
      </div>
    )
  }

  const today = data.today
  const yesterday = data.yesterday
  const occChange =
    today && yesterday
      ? Math.round((today.occupancy_pct - yesterday.occupancy_pct) * 10) / 10
      : undefined
  const revparChange =
    today && yesterday && yesterday.revpar_minor > 0
      ? Math.round(
          ((today.revpar_minor - yesterday.revpar_minor) /
            yesterday.revpar_minor) *
            1000
        ) / 10
      : undefined

  const pendingReview = activity.filter(
    (a) => a.requires_review && !a.reviewed_at
  )
  const completed = activity.filter((a) => !a.requires_review)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <p className="text-xs uppercase tracking-wide text-muted-foreground">
          Hospitality · {data.country}
        </p>
        <h1 className="text-2xl font-semibold mt-0.5">{data.property_name}</h1>
        <p className="text-sm text-muted-foreground mt-1">
          {data.room_categories.reduce((acc, c) => acc + c.room_count, 0)} rooms
          · {data.outlets.length} outlets · {data.currency}
        </p>
      </div>

      {/* KPI tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Occupancy"
          value={today ? `${today.occupancy_pct.toFixed(0)}%` : "—"}
          change={occChange}
          changeLabel="vs yesterday"
          icon={<Bed />}
        />
        <MetricCard
          title="ADR"
          value={today ? fmtMinor(today.adr_minor, data.currency) : "—"}
          icon={<Banknote />}
        />
        <MetricCard
          title="RevPAR"
          value={today ? fmtMinor(today.revpar_minor, data.currency) : "—"}
          change={revparChange}
          changeLabel="vs yesterday"
          icon={<TrendingUp />}
        />
        <MetricCard
          title="Food covers"
          value={today ? today.food_covers.toString() : "—"}
          icon={<Utensils />}
        />
      </div>

      {/* F&B revenue split */}
      {today && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MetricCard
            title="Rooms revenue (today)"
            value={fmtMinor(today.rooms_revenue_minor, data.currency)}
            icon={<Bed />}
          />
          <MetricCard
            title="Food revenue (today)"
            value={fmtMinor(today.food_revenue_minor, data.currency)}
            icon={<Utensils />}
          />
          <MetricCard
            title="Bar revenue (today)"
            value={fmtMinor(today.beverage_revenue_minor, data.currency)}
            icon={<Wine />}
          />
        </div>
      )}

      {/* Trend + Alerts */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              30-day occupancy trend
            </CardTitle>
          </CardHeader>
          <CardContent className="text-primary">
            <TrendChart points={data.trend_30d} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              Active alerts
              {data.alerts.length > 0 && (
                <Badge variant="destructive" className="ml-1">
                  {data.alerts.length}
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {data.alerts.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No anomalies detected.
              </p>
            )}
            {data.alerts.map((a, i) => (
              <div
                key={`${a.metric}-${i}`}
                className={cn(
                  "border rounded-md p-3 text-sm",
                  severityClasses(a.severity)
                )}
              >
                <p className="font-medium">{a.title}</p>
                <p className="text-xs mt-1 opacity-80">{a.detail}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* AI activity feed */}
      {showAiActivity && activity.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                Needs your attention
                {pendingReview.length > 0 && (
                  <Badge variant="destructive" className="ml-1">
                    {pendingReview.length}
                  </Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {pendingReview.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  Nothing to approve right now.
                </p>
              )}
              {pendingReview.map((item) => (
                <div
                  key={item.id}
                  className={cn(
                    "border rounded-md p-3",
                    severityClasses(item.severity)
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-medium text-sm">{item.title}</p>
                      <p className="text-xs mt-1 opacity-80">{item.detail}</p>
                      <p className="text-xs mt-2 opacity-60 flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {fmtRelative(item.created_at)}
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={approving === item.id}
                      onClick={() => handleApprove(item.id)}
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
                AI activity
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
                <div
                  key={item.id}
                  className="border rounded-md p-3 bg-muted/30"
                >
                  <p className="font-medium text-sm">{item.title}</p>
                  <p className="text-xs mt-1 text-muted-foreground">
                    {item.detail}
                  </p>
                  <p className="text-xs mt-2 text-muted-foreground flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {fmtRelative(item.created_at)}
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Room categories + outlets */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Room categories</CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead className="text-muted-foreground border-b">
                <tr>
                  <th className="text-left font-medium py-2">Category</th>
                  <th className="text-right font-medium py-2">Rooms</th>
                  <th className="text-right font-medium py-2">Base rate</th>
                </tr>
              </thead>
              <tbody>
                {data.room_categories.map((c) => (
                  <tr key={c.id} className="border-b last:border-0">
                    <td className="py-2">{c.label}</td>
                    <td className="py-2 text-right">{c.room_count}</td>
                    <td className="py-2 text-right">
                      {fmtMinor(c.base_rate_minor, c.currency)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Outlets</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {data.outlets.map((o) => (
              <div
                key={o.id}
                className="flex items-center justify-between py-1.5 border-b last:border-0"
              >
                <span className="text-sm">{o.name}</span>
                <Badge variant="secondary" className="text-xs">
                  {o.outlet_type}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

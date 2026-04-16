"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Building2, Loader2, ArrowRight } from "lucide-react"
import { apiGet } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/components/ui/toast"

interface PropertySummary {
  id: number
  client_id: number
  name: string
  country: string
  total_rooms: number
  timezone: string
}

export default function HospitalityIndexPage() {
  const [properties, setProperties] = useState<PropertySummary[]>([])
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    apiGet<PropertySummary[]>("/api/v1/hospitality/properties")
      .then((data) => setProperties(data))
      .catch((e) => toast(e.message || "Failed to load properties"))
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin mr-2" />
        Loading hospitality properties...
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Hospitality properties</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Hotels, restaurants, and venues across your client portfolio
        </p>
      </div>

      {properties.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <Building2 className="h-10 w-10 mx-auto mb-3 opacity-50" />
            <p className="text-sm">No hospitality properties yet.</p>
            <p className="text-xs mt-2">
              Run <code>python scripts/seed_hospitality.py</code> in the API
              container to load the Fjordvik Hotel demo.
            </p>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {properties.map((p) => (
          <Link key={p.id} href={`/dashboard/hospitality/${p.id}`}>
            <Card className="hover:border-primary/40 transition-colors cursor-pointer">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Building2 className="h-4 w-4 text-primary" />
                      {p.name}
                    </CardTitle>
                    <p className="text-sm text-muted-foreground mt-1">
                      {p.total_rooms} rooms · {p.timezone}
                    </p>
                  </div>
                  <Badge variant="secondary">{p.country}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-end text-sm text-primary">
                  Open dashboard <ArrowRight className="h-4 w-4 ml-1" />
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}

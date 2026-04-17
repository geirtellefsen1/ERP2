"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import {
  FileText,
  Upload,
  BarChart3,
  Loader2,
  Hotel,
} from "lucide-react"
import { apiGet } from "@/lib/api"
import HospitalityDashboard from "@/components/hospitality/HospitalityDashboard"

interface PropertySummary {
  id: number
  client_id: number
  name: string
  total_rooms: number
}

export default function PortalClientPage() {
  const params = useParams()
  const clientId = params.clientId as string
  const [properties, setProperties] = useState<PropertySummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiGet<PropertySummary[]>(
      `/api/v1/hospitality/properties?client_id=${clientId}`
    )
      .then(setProperties)
      .catch(() => setProperties([]))
      .finally(() => setLoading(false))
  }, [clientId])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-slate-400">
        <Loader2 className="h-5 w-5 animate-spin mr-2" />
        Loading...
      </div>
    )
  }

  const property = properties[0]

  return (
    <div className="max-w-7xl mx-auto px-6 py-6 space-y-8">
      {/* Quick nav */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <Link
          href={`/portal/${clientId}/documents`}
          className="flex items-center gap-3 p-4 rounded-xl border border-slate-200 bg-white hover:bg-blue-50 hover:border-blue-200 transition-colors"
        >
          <Upload className="h-5 w-5 text-blue-600" />
          <div>
            <p className="font-medium text-sm text-slate-900">Upload documents</p>
            <p className="text-xs text-slate-500">Receipts, invoices, statements</p>
          </div>
        </Link>
        <Link
          href={`/portal/invoices`}
          className="flex items-center gap-3 p-4 rounded-xl border border-slate-200 bg-white hover:bg-amber-50 hover:border-amber-200 transition-colors"
        >
          <FileText className="h-5 w-5 text-amber-600" />
          <div>
            <p className="font-medium text-sm text-slate-900">Invoices</p>
            <p className="text-xs text-slate-500">View and pay invoices</p>
          </div>
        </Link>
        <Link
          href={`/portal/reports`}
          className="flex items-center gap-3 p-4 rounded-xl border border-slate-200 bg-white hover:bg-purple-50 hover:border-purple-200 transition-colors"
        >
          <BarChart3 className="h-5 w-5 text-purple-600" />
          <div>
            <p className="font-medium text-sm text-slate-900">Reports</p>
            <p className="text-xs text-slate-500">Financial reports & KPIs</p>
          </div>
        </Link>
      </div>

      {/* Hospitality dashboard */}
      {property ? (
        <HospitalityDashboard
          propertyId={property.id}
          clientId={clientId}
          showAiActivity={false}
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
          <Hotel className="h-8 w-8 text-slate-300 mx-auto mb-3" />
          <h2 className="font-semibold text-slate-900">Welcome to your portal</h2>
          <p className="text-sm text-slate-500 mt-1">
            Your accountant is setting up your dashboard. Upload documents or
            check invoices using the links above.
          </p>
        </div>
      )}
    </div>
  )
}

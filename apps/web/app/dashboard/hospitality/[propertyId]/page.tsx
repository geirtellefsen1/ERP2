"use client"

import { useParams } from "next/navigation"
import { ToastProvider } from "@/components/ui/toast"
import HospitalityDashboard from "@/components/hospitality/HospitalityDashboard"

export default function HospitalityDashboardPage() {
  const params = useParams<{ propertyId: string }>()

  return (
    <HospitalityDashboard
      propertyId={params.propertyId}
      showAiActivity={true}
    />
  )
}

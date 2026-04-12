"use client"

import { useEffect, useState, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Loader2, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"

function CallbackInner() {
  const router = useRouter()
  const params = useSearchParams()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const token = params.get("token")
    const userB64 = params.get("user")
    const next = params.get("next") || "/dashboard"
    const errParam = params.get("error")

    if (errParam) {
      try {
        // base64url decode
        const padded = errParam + "=".repeat((4 - (errParam.length % 4)) % 4)
        const decoded = atob(padded.replace(/-/g, "+").replace(/_/g, "/"))
        setError(decoded)
      } catch {
        setError(errParam)
      }
      return
    }

    if (!token || !userB64) {
      setError("Missing authentication token. Please try signing in again.")
      return
    }

    try {
      const padded = userB64 + "=".repeat((4 - (userB64.length % 4)) % 4)
      const userJson = atob(padded.replace(/-/g, "+").replace(/_/g, "/"))
      const user = JSON.parse(userJson)

      localStorage.setItem("bpo_token", token)
      localStorage.setItem("bpo_user", JSON.stringify(user))

      // Hard navigate so the dashboard layout re-reads localStorage cleanly
      window.location.href = next
    } catch (e: any) {
      setError(`Failed to process login: ${e.message || "unknown error"}`)
    }
  }, [params, router])

  if (error) {
    return (
      <main className="min-h-screen flex items-center justify-center p-8">
        <div className="w-full max-w-sm space-y-6 text-center">
          <div className="w-12 h-12 rounded-full bg-destructive/10 flex items-center justify-center mx-auto">
            <AlertCircle className="h-6 w-6 text-destructive" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">Sign-in failed</h1>
            <p className="text-sm text-muted-foreground mt-2 break-words">
              {error}
            </p>
          </div>
          <Button
            onClick={() => router.push("/login")}
            variant="outline"
            className="w-full"
          >
            Back to sign in
          </Button>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen flex items-center justify-center">
      <div className="text-center space-y-3">
        <Loader2 className="h-6 w-6 animate-spin text-primary mx-auto" />
        <p className="text-sm text-muted-foreground">Signing you in...</p>
      </div>
    </main>
  )
}

export default function CallbackPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen flex items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </main>
      }
    >
      <CallbackInner />
    </Suspense>
  )
}

"use client"

import { useState } from "react"
import { LogIn, Mail, Lock, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { API_BASE } from "@/lib/utils"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError("")
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      })
      if (!res.ok) {
        const d = await res.json()
        setError(d.detail || "Invalid email or password")
        return
      }
      const data = await res.json()
      localStorage.setItem("bpo_token", data.access_token)
      localStorage.setItem("bpo_user", JSON.stringify(data.user))
      window.location.href = "/dashboard"
    } catch {
      setError("Cannot connect to server. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen flex">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-primary relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary to-primary/80" />
        <div className="relative z-10 flex flex-col justify-between p-12 text-primary-foreground">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center font-bold text-lg">
                N
              </div>
              <span className="text-xl font-semibold">BPO Nexus</span>
            </div>
          </div>
          <div className="space-y-4">
            <h2 className="text-3xl font-bold leading-tight">
              AI-powered accounting
              <br />
              for modern agencies
            </h2>
            <p className="text-primary-foreground/70 max-w-md">
              Manage clients, automate bookkeeping, and generate insights
              — all from a single platform.
            </p>
          </div>
          <p className="text-sm text-primary-foreground/50">
            Saga Advisory AS
          </p>
        </div>
        {/* Decorative circles */}
        <div className="absolute -bottom-32 -right-32 w-96 h-96 rounded-full bg-white/5" />
        <div className="absolute -top-16 -right-16 w-64 h-64 rounded-full bg-white/5" />
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm space-y-8">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-4">
            <div className="w-9 h-9 rounded-lg bg-primary text-primary-foreground flex items-center justify-center font-bold text-sm">
              N
            </div>
            <span className="text-lg font-semibold">BPO Nexus</span>
          </div>

          <div>
            <h1 className="text-xl font-semibold">Welcome back</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Sign in to your agency dashboard
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              icon={<Mail />}
              required
            />

            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              icon={<Lock />}
              required
            />

            {error && (
              <div className="flex items-center gap-2 rounded-lg bg-destructive/10 text-destructive text-sm px-3 py-2.5">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {error}
              </div>
            )}

            <Button type="submit" className="w-full" size="lg" loading={loading}>
              <LogIn className="h-4 w-4" />
              Sign In
            </Button>
          </form>

          <p className="text-center text-xs text-muted-foreground">
            Secured with enterprise-grade encryption
          </p>
        </div>
      </div>
    </main>
  )
}

"use client"

import Link from "next/link"
import {
  ArrowRight,
  BarChart3,
  Shield,
  Sparkles,
  Landmark,
  FileText,
  Users,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { GoogleIcon, MicrosoftIcon } from "@/components/ui/brand-icons"
import { Logo } from "@/components/ui/logo"
import { API_BASE } from "@/lib/utils"

export default function HomePage() {
  function startOAuth(provider: "google" | "microsoft") {
    window.location.href = `${API_BASE}/api/v1/auth/${provider}/login`
  }

  return (
    <main className="min-h-screen">
      {/* Nav */}
      <header className="border-b">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <Logo size="sm" href="/" />
          <nav className="flex items-center gap-1">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/demo">Demos</Link>
            </Button>
            <Button size="sm" asChild>
              <Link href="/login">
                Sign In
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </Button>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-5xl mx-auto px-6 pt-24 pb-16">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs text-muted-foreground mb-6">
            <Sparkles className="h-3 w-3 text-primary" />
            AI-powered accounting platform
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight leading-[1.1] mb-4">
            Modern accounting
            <br />
            for BPO agencies
          </h1>
          <p className="text-lg text-muted-foreground mb-8 max-w-lg">
            Manage clients, automate bookkeeping, reconcile bank transactions,
            and generate insights — all powered by AI.
          </p>
          <div className="flex flex-wrap gap-3 mb-6">
            <Button size="lg" asChild>
              <Link href="/login">
                Get Started
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button size="lg" variant="outline">
              Learn More
            </Button>
          </div>

          {/* Quick OAuth sign-in — no registration form needed */}
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-xs text-muted-foreground">
              Or sign in instantly with
            </span>
            <button
              onClick={() => startOAuth("google")}
              className="flex items-center gap-2 h-9 px-4 rounded-md border bg-card text-sm font-medium hover:bg-accent transition-colors"
            >
              <GoogleIcon className="h-4 w-4" />
              Google
            </button>
            <button
              onClick={() => startOAuth("microsoft")}
              className="flex items-center gap-2 h-9 px-4 rounded-md border bg-card text-sm font-medium hover:bg-accent transition-colors"
            >
              <MicrosoftIcon className="h-4 w-4" />
              Microsoft
            </button>
          </div>
        </div>
      </section>

      {/* Trust badge */}
      <section className="border-t border-b bg-muted/30">
        <div className="max-w-5xl mx-auto px-6 py-8">
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6 sm:gap-10">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Works seamlessly with
            </p>
            <div className="flex items-center gap-6 sm:gap-10">
              <div className="flex items-center gap-2.5 text-sm text-muted-foreground">
                <GoogleIcon className="h-5 w-5" />
                <span className="font-medium">Google Workspace</span>
              </div>
              <div className="w-px h-6 bg-border" />
              <div className="flex items-center gap-2.5 text-sm text-muted-foreground">
                <MicrosoftIcon className="h-5 w-5" />
                <span className="font-medium">Microsoft 365</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="bg-background">
        <div className="max-w-5xl mx-auto px-6 py-16">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-8">
            Everything you need
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                icon: Users,
                title: "Client Management",
                desc: "Multi-tenant client portal with document upload, invoicing, and reporting.",
              },
              {
                icon: FileText,
                title: "Invoicing & Expenses",
                desc: "Create professional invoices, track expenses, and manage cash flow.",
              },
              {
                icon: Landmark,
                title: "Bank Reconciliation",
                desc: "AI-powered transaction matching with Open Banking integration.",
              },
              {
                icon: BarChart3,
                title: "Financial Reports",
                desc: "P&L, Balance Sheet, Cash Flow reports with PDF export.",
              },
              {
                icon: Sparkles,
                title: "AI Assistant",
                desc: "Ask questions about your finances in plain language.",
              },
              {
                icon: Shield,
                title: "Enterprise Security",
                desc: "SSO with Google + Microsoft, encrypted at rest, JWT-based auth.",
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className="p-5 rounded-lg border bg-card"
              >
                <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center mb-3">
                  <feature.icon className="h-4 w-4 text-primary" />
                </div>
                <h3 className="text-sm font-semibold mb-1">{feature.title}</h3>
                <p className="text-sm text-muted-foreground">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t">
        <div className="max-w-5xl mx-auto px-6 py-6 flex items-center justify-between text-xs text-muted-foreground">
          <span>Saga Advisory AS</span>
          <span>ClaudERP v1.4.0</span>
        </div>
      </footer>
    </main>
  )
}

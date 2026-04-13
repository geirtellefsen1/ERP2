"use client"

import Link from "next/link"
import {
  ArrowRight,
  ArrowLeft,
  Globe,
  FileScan,
  LineChart,
  Clock,
  Wallet,
  Landmark,
  FileBarChart,
  Sparkles,
  MessageCircle,
  Receipt,
  Coins,
  type LucideIcon,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Logo } from "@/components/ui/logo"

interface Demo {
  id: string
  title: string
  description: string
  icon: LucideIcon
  duration: string
  audience: string
  topics: string[]
  accent: string
}

const DEMOS: Demo[] = [
  {
    id: "nordic-overview",
    title: "Nordic Platform Overview",
    description:
      "See how one platform handles Norwegian, Swedish, and Finnish compliance simultaneously — pluggable jurisdiction engine, country-aware VAT rates, localised UI, and consolidated reporting in any base currency.",
    icon: Globe,
    duration: "20 min",
    audience: "BPO agency owners",
    topics: ["Jurisdiction engine", "Multi-country", "Consolidated reports"],
    accent: "text-blue-600 bg-blue-50",
  },
  {
    id: "ai-documents",
    title: "AI Document Pipeline",
    description:
      "Upload a Norwegian supplier invoice, watch Claude Vision extract every field, detect the VAT rate, auto-suggest the GL code, and flag potential duplicates — all before a human touches it.",
    icon: FileScan,
    duration: "10 min",
    audience: "Accountants",
    topics: ["Claude Vision", "OCR", "GL coding", "Fraud detection"],
    accent: "text-purple-600 bg-purple-50",
  },
  {
    id: "cashflow-forecast",
    title: "13-Week Cashflow Forecast",
    description:
      "Generate a rolling 13-week forecast with threshold alerts and a Claude-written narrative in the client's language. See exactly which week cash dips below the safety line.",
    icon: LineChart,
    duration: "15 min",
    audience: "CFOs, advisors",
    topics: ["Forecasting", "AI narratives", "Multi-language"],
    accent: "text-emerald-600 bg-emerald-50",
  },
  {
    id: "payroll-norway",
    title: "Payroll — Norway (A-melding)",
    description:
      "Run a full Norwegian payroll cycle including AGA zones, OTP pension, holiday pay accrual, Skatteetaten tax tables, and A-melding XML submission to Altinn.",
    icon: Wallet,
    duration: "20 min",
    audience: "Payroll specialists",
    topics: ["AGA zones", "OTP", "A-melding", "Altinn"],
    accent: "text-red-600 bg-red-50",
  },
  {
    id: "payroll-finland",
    title: "Payroll — Finland (Tulorekisteri)",
    description:
      "Run payroll for a Finnish employee and watch the real-time Tulorekisteri submission fire within seconds of payment — the strictest payroll reporting requirement in the Nordics, fully automated.",
    icon: Clock,
    duration: "20 min",
    audience: "Payroll specialists",
    topics: ["TyEL", "Tulorekisteri", "Real-time 5-day reporting"],
    accent: "text-sky-600 bg-sky-50",
  },
  {
    id: "payroll-sweden",
    title: "Payroll — Sweden (AGD + ITP1)",
    description:
      "See age-banded arbetsgivaravgifter (31.42% standard, 10.21% under-23 and over-65), ITP1 occupational pension, karensdag handling, and monthly AGD submission to Skatteverket.",
    icon: Wallet,
    duration: "20 min",
    audience: "Payroll specialists",
    topics: ["Arbetsgivaravgifter", "ITP1", "AGD", "Skatteverket"],
    accent: "text-amber-600 bg-amber-50",
  },
  {
    id: "bank-reconciliation",
    title: "Bank Reconciliation with AI matching",
    description:
      "Import a bank statement via Aiia or upload a CSV, watch AI auto-match transactions with confidence scores, and resolve the rest with a keyboard-driven review queue.",
    icon: Landmark,
    duration: "15 min",
    audience: "Bookkeepers",
    topics: ["Open banking", "AI matching", "Keyboard shortcuts"],
    accent: "text-indigo-600 bg-indigo-50",
  },
  {
    id: "vat-returns",
    title: "VAT Returns — All Three Countries",
    description:
      "Generate a bimonthly Norwegian MVA-melding, a monthly Swedish momsdeklaration, and a Finnish ALV — all from the same underlying journal data, with the correct schema for each tax authority.",
    icon: Receipt,
    duration: "15 min",
    audience: "Accountants",
    topics: ["MVA-melding", "Momsdeklaration", "ALV/OmaVero"],
    accent: "text-orange-600 bg-orange-50",
  },
  {
    id: "month-end-report",
    title: "Month-End Report with AI Commentary",
    description:
      "Generate a full month-end management report — P&L, balance sheet, variances vs. prior period, and a Claude-written commentary in the client's language. Delivered as PDF on a monthly schedule.",
    icon: FileBarChart,
    duration: "15 min",
    audience: "CFOs, owners",
    topics: ["PDF reports", "AI narratives", "Scheduled delivery"],
    accent: "text-teal-600 bg-teal-50",
  },
  {
    id: "ai-agent-chat",
    title: "AI Agent Chat",
    description:
      "Ask a natural-language question about any client\u2019s financials \u2014 \u201cwhat is Bj\u00f6rn\u2019s VAT liability for Q1?\u201d \u2014 and get an answer with source citations to specific transactions and journal lines.",
    icon: Sparkles,
    duration: "10 min",
    audience: "Agency staff",
    topics: ["Claude tool use", "Natural language", "Citations"],
    accent: "text-pink-600 bg-pink-50",
  },
  {
    id: "whatsapp-portal",
    title: "WhatsApp Client Portal (OpenClaw)",
    description:
      "Send a receipt photo to ClaudERP's WhatsApp number, see it auto-processed, coded, and posted to the right GL account — without the client ever opening a web browser. Works in Norwegian, Swedish, and Finnish.",
    icon: MessageCircle,
    duration: "10 min",
    audience: "End clients",
    topics: ["OpenClaw", "Multi-language", "Mobile-first"],
    accent: "text-green-600 bg-green-50",
  },
  {
    id: "multi-currency",
    title: "Multi-currency Consolidated Reporting",
    description:
      "See a group P&L combining a Norwegian parent (NOK), a Swedish subsidiary (SEK), and a Finnish subsidiary (EUR), with ECB-driven FX translation and intercompany elimination.",
    icon: Coins,
    duration: "20 min",
    audience: "Group CFOs",
    topics: ["Multi-currency", "FX translation", "Consolidation"],
    accent: "text-violet-600 bg-violet-50",
  },
]

export default function DemoPage() {
  return (
    <main className="min-h-screen">
      {/* Nav — same shell as the landing page */}
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
      <section className="border-b bg-muted/30">
        <div className="max-w-5xl mx-auto px-6 pt-16 pb-12">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors mb-6"
          >
            <ArrowLeft className="h-3 w-3" />
            Back to home
          </Link>
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-1.5 rounded-full border bg-background px-3 py-1 text-xs text-muted-foreground mb-6">
              <Sparkles className="h-3 w-3 text-primary" />
              Live demos
            </div>
            <h1 className="text-4xl font-bold tracking-tight leading-[1.15] mb-4">
              See ClaudERP in action
            </h1>
            <p className="text-lg text-muted-foreground max-w-lg">
              {DEMOS.length} focused walkthroughs covering everything from
              multi-country compliance to AI-powered document processing.
              Pick one and we&rsquo;ll book a live session.
            </p>
          </div>
        </div>
      </section>

      {/* Demo grid */}
      <section>
        <div className="max-w-5xl mx-auto px-6 py-12">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {DEMOS.map((demo) => (
              <Card
                key={demo.id}
                className="p-5 flex flex-col h-full hover:-translate-y-0.5 transition-transform"
              >
                <div className="flex items-start gap-3 mb-3">
                  <div
                    className={`rounded-lg p-2.5 shrink-0 ${demo.accent}`}
                  >
                    <demo.icon className="h-5 w-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold leading-tight">
                      {demo.title}
                    </h3>
                    <div className="flex gap-2 mt-1.5">
                      <Badge variant="secondary" className="text-2xs">
                        {demo.duration}
                      </Badge>
                    </div>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed mb-4 flex-1">
                  {demo.description}
                </p>
                <div className="space-y-3">
                  <div>
                    <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5">
                      Best for
                    </p>
                    <p className="text-xs">{demo.audience}</p>
                  </div>
                  <div>
                    <p className="text-2xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5">
                      Covers
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {demo.topics.map((topic) => (
                        <span
                          key={topic}
                          className="inline-flex items-center rounded-md bg-muted px-1.5 py-0.5 text-2xs text-muted-foreground"
                        >
                          {topic}
                        </span>
                      ))}
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full mt-2"
                    asChild
                  >
                    <a
                      href={`mailto:demo@saga-advisory.com?subject=Demo request: ${encodeURIComponent(
                        demo.title
                      )}`}
                    >
                      Book this demo
                      <ArrowRight className="h-3.5 w-3.5" />
                    </a>
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA band */}
      <section className="border-t bg-muted/30">
        <div className="max-w-5xl mx-auto px-6 py-12 text-center">
          <h2 className="text-2xl font-bold tracking-tight mb-2">
            Can&rsquo;t find what you need?
          </h2>
          <p className="text-muted-foreground mb-6 max-w-md mx-auto">
            We&rsquo;ll tailor a session to your exact use case — send us a
            note and we&rsquo;ll scope it within one business day.
          </p>
          <Button size="lg" asChild>
            <a href="mailto:demo@saga-advisory.com?subject=Custom demo request">
              Request a custom demo
              <ArrowRight className="h-4 w-4" />
            </a>
          </Button>
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

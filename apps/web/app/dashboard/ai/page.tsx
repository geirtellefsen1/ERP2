"use client"

import { useState, useRef, useEffect } from "react"
import {
  Send,
  Sparkles,
  User,
  Bot,
  Loader2,
  FileText,
  BarChart3,
  Database,
  Lightbulb,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  toolsUsed?: string[]
}

const SUGGESTIONS = [
  {
    label: "Revenue summary",
    prompt: "What was our total revenue last month?",
    icon: BarChart3,
  },
  {
    label: "Client overview",
    prompt: "Show me a summary of all active clients",
    icon: FileText,
  },
  {
    label: "Anomalies",
    prompt: "Are there any unusual transactions this week?",
    icon: Lightbulb,
  },
  {
    label: "Cash flow",
    prompt: "Generate a cash flow analysis for Q1 2026",
    icon: Database,
  },
]

export default function AIPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isThinking, setIsThinking] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  function handleSend(text?: string) {
    const message = text || input.trim()
    if (!message) return

    const userMsg: Message = {
      id: Math.random().toString(36).slice(2),
      role: "user",
      content: message,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMsg])
    setInput("")
    setIsThinking(true)

    // Simulate AI response
    setTimeout(() => {
      const aiMsg: Message = {
        id: Math.random().toString(36).slice(2),
        role: "assistant",
        content: getSimulatedResponse(message),
        timestamp: new Date(),
        toolsUsed: ["sql_query", "get_client_summary"],
      }
      setMessages((prev) => [...prev, aiMsg])
      setIsThinking(false)
    }, 1500)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    handleSend()
  }

  return (
    <div className="flex flex-col h-[calc(100vh-theme(spacing.12))]">
      {/* Header */}
      <div className="shrink-0 pb-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
            <Sparkles className="h-4 w-4 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-semibold">AI Assistant</h1>
            <p className="text-sm text-muted-foreground">
              Ask questions about your financial data in natural language
            </p>
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-4 pb-4"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
              <Sparkles className="h-6 w-6 text-primary" />
            </div>
            <h2 className="text-base font-semibold mb-1">
              Ask me anything about your finances
            </h2>
            <p className="text-sm text-muted-foreground mb-6 text-center max-w-md">
              I can query your database, generate reports, detect anomalies,
              and explain financial data in plain language.
            </p>
            <div className="grid grid-cols-2 gap-2 max-w-lg w-full">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s.label}
                  onClick={() => handleSend(s.prompt)}
                  className="flex items-center gap-2.5 p-3 rounded-lg border bg-card hover:bg-accent/50 hover:shadow-soft text-left transition-all"
                >
                  <s.icon className="h-4 w-4 text-muted-foreground shrink-0" />
                  <span className="text-sm">{s.label}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={cn(
                "flex gap-3 animate-fade-in",
                msg.role === "user" && "justify-end"
              )}
            >
              {msg.role === "assistant" && (
                <div className="w-7 h-7 rounded-md bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
              )}
              <div
                className={cn(
                  "max-w-[75%] rounded-lg px-4 py-3 text-sm",
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-card border"
                )}
              >
                <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                {msg.toolsUsed && msg.toolsUsed.length > 0 && (
                  <div className="flex gap-1.5 mt-2 pt-2 border-t border-border/50">
                    {msg.toolsUsed.map((tool) => (
                      <Badge
                        key={tool}
                        variant="secondary"
                        className="text-2xs"
                      >
                        <Database className="h-2.5 w-2.5 mr-0.5" />
                        {tool}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
              {msg.role === "user" && (
                <div className="w-7 h-7 rounded-md bg-muted flex items-center justify-center shrink-0 mt-0.5">
                  <User className="h-4 w-4 text-muted-foreground" />
                </div>
              )}
            </div>
          ))
        )}

        {isThinking && (
          <div className="flex gap-3 animate-fade-in">
            <div className="w-7 h-7 rounded-md bg-primary/10 flex items-center justify-center shrink-0">
              <Bot className="h-4 w-4 text-primary" />
            </div>
            <div className="bg-card border rounded-lg px-4 py-3">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Analyzing your data...
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="shrink-0 pt-2">
        <form onSubmit={handleSubmit} className="relative">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about revenue, expenses, clients, anomalies..."
            className="w-full h-11 rounded-lg border bg-card px-4 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1"
            disabled={isThinking}
          />
          <Button
            type="submit"
            size="icon-sm"
            variant="ghost"
            className="absolute right-2 top-1/2 -translate-y-1/2"
            disabled={!input.trim() || isThinking}
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
        <p className="text-center text-2xs text-muted-foreground mt-2">
          AI responses are generated from your financial data. Always verify critical numbers.
        </p>
      </div>
    </div>
  )
}

function getSimulatedResponse(query: string): string {
  const q = query.toLowerCase()
  if (q.includes("revenue") || q.includes("income")) {
    return "Based on your financial data for March 2026:\n\n- Total Revenue: R73,000\n- Growth vs February: +11.4%\n- Top client by revenue: Acme Corp (R22,000)\n- Service revenue makes up 100% of total income\n\nRevenue has been trending upward consistently over the past 3 months."
  }
  if (q.includes("client") || q.includes("active")) {
    return "Here is your active client summary:\n\n- Total clients: 4\n- Active: 3\n- Inactive: 1\n\nActive clients:\n1. Acme Corp (Hospitality, ZA) - Active since Jan 2026\n2. TechStart Ltd (Technology, UK) - Active since Feb 2026\n3. BuildRight SA (Construction, ZA) - Active since Jan 2026"
  }
  if (q.includes("anomal") || q.includes("unusual")) {
    return "I scanned your recent transactions and found 2 items worth reviewing:\n\n1. Duplicate charge: WOOLWORTHS FOOD on Apr 5 (R350) - appears twice within 24 hours\n2. Unusual amount: EFT PAYMENT from unknown reference (R5,200) on Apr 8 - 340% above average incoming EFT\n\nRecommendation: Review the unmatched EFT payment in Bank Reconciliation."
  }
  if (q.includes("cash flow") || q.includes("cashflow")) {
    return "Cash Flow Analysis - Q1 2026:\n\nOperating Activities:\n- Cash from clients: R580,000\n- Cash paid to suppliers: -(R346,000)\n- Net operating cash flow: R234,000\n\nInvesting Activities:\n- Equipment purchases: -(R15,000)\n\nFinancing Activities:\n- Loan repayment: -(R12,000)\n\nNet cash change: R207,000\nClosing balance: R1,245,000"
  }
  return "I analyzed your financial data to answer your question. Based on the current records in your database, here is what I found:\n\nYour agency currently manages 4 client accounts with a combined monthly revenue of approximately R73,000. All accounts are in good standing with no overdue balances exceeding 60 days.\n\nWould you like me to drill into any specific area?"
}

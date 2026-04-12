"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  Users,
  FileText,
  BarChart3,
  Landmark,
  Receipt,
  Wallet,
  Settings,
  LogOut,
  ChevronLeft,
  Search,
  Sparkles,
  ChevronsUpDown,
} from "lucide-react"
import { cn, getInitials } from "@/lib/utils"
import { useState, useEffect } from "react"
import { Avatar } from "./ui/avatar"

const NAV_SECTIONS = [
  {
    label: "Overview",
    items: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/dashboard/clients", label: "Clients", icon: Users },
    ],
  },
  {
    label: "Finance",
    items: [
      { href: "/dashboard/invoices", label: "Invoices", icon: FileText },
      { href: "/dashboard/expenses", label: "Expenses", icon: Receipt },
      { href: "/dashboard/banking", label: "Bank Reconciliation", icon: Landmark },
    ],
  },
  {
    label: "Insights",
    items: [
      { href: "/dashboard/reports", label: "Reports", icon: BarChart3 },
      { href: "/dashboard/ai", label: "AI Assistant", icon: Sparkles },
    ],
  },
]

const BOTTOM_NAV = [
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
]

function getUser() {
  if (typeof window === "undefined") return null
  try {
    const u = localStorage.getItem("bpo_user")
    return u ? JSON.parse(u) : null
  } catch {
    return null
  }
}

export default function Sidebar() {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    setUser(getUser())
  }, [])

  const isActive = (href: string) =>
    pathname === href || (href !== "/dashboard" && pathname.startsWith(href + "/"))

  return (
    <aside
      className={cn(
        "flex flex-col h-screen bg-sidebar border-r border-sidebar-border transition-all duration-200 ease-in-out",
        collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Header / Workspace Switcher */}
      <div className="flex items-center gap-2 px-3 py-3 border-b border-sidebar-border">
        <div className="flex items-center justify-center h-8 w-8 shrink-0">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/logo.svg" alt="ClaudERP" className="h-7 w-auto" />
        </div>
        {!collapsed && (
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold truncate">ClaudERP</p>
            <p className="text-2xs text-muted-foreground truncate">
              {user?.agency_id || "Workspace"}
            </p>
          </div>
        )}
        {!collapsed && (
          <button
            onClick={() => setCollapsed(true)}
            className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-sidebar-accent transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Search Trigger */}
      {!collapsed && (
        <div className="px-3 pt-3">
          <button className="flex items-center gap-2 w-full h-8 px-2.5 rounded-md border border-sidebar-border bg-background text-muted-foreground text-xs hover:bg-sidebar-accent transition-colors">
            <Search className="h-3.5 w-3.5" />
            <span>Search...</span>
            <kbd className="ml-auto text-2xs bg-muted px-1.5 py-0.5 rounded font-mono">
              /
            </kbd>
          </button>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-4">
        {NAV_SECTIONS.map((section) => (
          <div key={section.label}>
            {!collapsed && (
              <p className="px-2 mb-1 text-2xs font-medium text-muted-foreground uppercase tracking-wider">
                {section.label}
              </p>
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const active = isActive(item.href)
                const Icon = item.icon
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    title={collapsed ? item.label : undefined}
                    className={cn(
                      "flex items-center gap-2.5 rounded-md text-sm font-medium transition-all duration-100",
                      collapsed
                        ? "justify-center w-10 h-9 mx-auto"
                        : "px-2.5 py-1.5",
                      active
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:text-foreground hover:bg-sidebar-accent"
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    {!collapsed && <span>{item.label}</span>}
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Bottom Actions */}
      <div className="px-2 pb-1 space-y-0.5">
        {BOTTOM_NAV.map((item) => {
          const active = isActive(item.href)
          const Icon = item.icon
          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.label : undefined}
              className={cn(
                "flex items-center gap-2.5 rounded-md text-sm font-medium transition-all duration-100",
                collapsed
                  ? "justify-center w-10 h-9 mx-auto"
                  : "px-2.5 py-1.5",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground hover:bg-sidebar-accent"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          )
        })}
      </div>

      {/* User / Account */}
      <div className="border-t border-sidebar-border px-2 py-2">
        {collapsed ? (
          <button
            onClick={() => setCollapsed(false)}
            className="flex items-center justify-center w-10 h-9 mx-auto rounded-md text-muted-foreground hover:bg-sidebar-accent transition-colors"
          >
            <Avatar name={user?.email || "U"} size="sm" />
          </button>
        ) : (
          <div className="flex items-center gap-2.5 px-2 py-1.5 rounded-md hover:bg-sidebar-accent transition-colors group">
            <Avatar name={user?.email || "User"} size="sm" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">
                {user?.email?.split("@")[0] || "User"}
              </p>
              <p className="text-2xs text-muted-foreground capitalize">
                {user?.role || "Agent"}
              </p>
            </div>
            <button
              onClick={() => {
                localStorage.removeItem("bpo_token")
                localStorage.removeItem("bpo_user")
                window.location.href = "/login"
              }}
              title="Sign out"
              className="p-1 rounded-md text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-all"
            >
              <LogOut className="h-3.5 w-3.5" />
            </button>
          </div>
        )}
      </div>
    </aside>
  )
}

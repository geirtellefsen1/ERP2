"use client"

import { useState } from "react"
import {
  CheckCircle2,
  Circle,
  Clock,
  Plus,
  Filter,
  AlertTriangle,
  User,
} from "lucide-react"
import { cn, formatDate } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { EmptyState } from "@/components/ui/empty-state"

interface Task {
  id: number
  title: string
  client: string
  priority: "high" | "medium" | "low"
  status: "todo" | "in_progress" | "done"
  due: string
  assignee: string
}

const DEMO_TASKS: Task[] = [
  {
    id: 1,
    title: "Monthly VAT return - Acme Corp",
    client: "Acme Corp",
    priority: "high",
    status: "in_progress",
    due: "2026-04-15",
    assignee: "Sarah",
  },
  {
    id: 2,
    title: "Q1 financial statements",
    client: "BuildRight SA",
    priority: "high",
    status: "todo",
    due: "2026-04-20",
    assignee: "James",
  },
  {
    id: 3,
    title: "Payroll processing - March",
    client: "TechStart Ltd",
    priority: "medium",
    status: "done",
    due: "2026-04-05",
    assignee: "Sarah",
  },
  {
    id: 4,
    title: "Bank reconciliation",
    client: "Green Valley",
    priority: "low",
    status: "todo",
    due: "2026-04-25",
    assignee: "James",
  },
  {
    id: 5,
    title: "Annual tax filing",
    client: "Acme Corp",
    priority: "medium",
    status: "todo",
    due: "2026-05-01",
    assignee: "Sarah",
  },
]

const priorityConfig = {
  high: { color: "text-destructive", bg: "bg-destructive/10" },
  medium: { color: "text-warning", bg: "bg-warning/10" },
  low: { color: "text-muted-foreground", bg: "bg-muted" },
}

export default function TasksPage() {
  const [filter, setFilter] = useState("all")
  const [tasks, setTasks] = useState(DEMO_TASKS)

  const toggleStatus = (id: number) => {
    setTasks(
      tasks.map((t) => {
        if (t.id !== id) return t
        const next =
          t.status === "todo"
            ? "in_progress"
            : t.status === "in_progress"
              ? "done"
              : "todo"
        return { ...t, status: next as Task["status"] }
      })
    )
  }

  const filtered = tasks.filter((t) => {
    if (filter === "all") return true
    return t.status === filter
  })

  const counts = {
    todo: tasks.filter((t) => t.status === "todo").length,
    in_progress: tasks.filter((t) => t.status === "in_progress").length,
    done: tasks.filter((t) => t.status === "done").length,
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">Tasks</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {tasks.length} tasks across all clients
          </p>
        </div>
        <Button size="sm">
          <Plus className="h-4 w-4" />
          New Task
        </Button>
      </div>

      {/* Status filters */}
      <div className="flex gap-1 bg-muted p-1 rounded-lg w-fit">
        {[
          { key: "all", label: `All (${tasks.length})` },
          { key: "todo", label: `To Do (${counts.todo})` },
          { key: "in_progress", label: `In Progress (${counts.in_progress})` },
          { key: "done", label: `Done (${counts.done})` },
        ].map((s) => (
          <button
            key={s.key}
            onClick={() => setFilter(s.key)}
            className={cn(
              "px-3 py-1 text-xs font-medium rounded-md transition-all",
              filter === s.key
                ? "bg-background shadow-xs text-foreground"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Task List */}
      <div className="space-y-1.5">
        {filtered.map((task) => (
          <div
            key={task.id}
            className={cn(
              "flex items-center gap-3 px-4 py-3 rounded-lg border bg-card hover:shadow-soft transition-all",
              task.status === "done" && "opacity-60"
            )}
          >
            <button
              onClick={() => toggleStatus(task.id)}
              className="shrink-0"
            >
              {task.status === "done" ? (
                <CheckCircle2 className="h-5 w-5 text-success" />
              ) : task.status === "in_progress" ? (
                <Clock className="h-5 w-5 text-primary" />
              ) : (
                <Circle className="h-5 w-5 text-muted-foreground" />
              )}
            </button>
            <div className="flex-1 min-w-0">
              <p
                className={cn(
                  "text-sm font-medium",
                  task.status === "done" && "line-through"
                )}
              >
                {task.title}
              </p>
              <p className="text-2xs text-muted-foreground">
                {task.client} &middot; Due {formatDate(task.due)}
              </p>
            </div>
            <Badge
              variant="secondary"
              className={cn("text-2xs", priorityConfig[task.priority].color)}
            >
              {task.priority}
            </Badge>
            <div className="flex items-center gap-1 text-2xs text-muted-foreground">
              <User className="h-3 w-3" />
              {task.assignee}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

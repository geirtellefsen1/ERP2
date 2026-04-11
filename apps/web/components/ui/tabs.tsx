"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface TabsProps {
  value: string
  onValueChange: (value: string) => void
  children: React.ReactNode
  className?: string
}

function Tabs({ value, onValueChange, children, className }: TabsProps) {
  return (
    <div className={cn("space-y-4", className)} data-value={value}>
      {React.Children.map(children, (child) =>
        React.isValidElement(child)
          ? React.cloneElement(child as React.ReactElement<any>, {
              value,
              onValueChange,
            })
          : child
      )}
    </div>
  )
}

interface TabsListProps {
  children: React.ReactNode
  className?: string
  value?: string
  onValueChange?: (value: string) => void
}

function TabsList({ children, className, value, onValueChange }: TabsListProps) {
  return (
    <div
      className={cn(
        "inline-flex h-9 items-center justify-start gap-1 rounded-lg bg-muted p-1",
        className
      )}
    >
      {React.Children.map(children, (child) =>
        React.isValidElement(child)
          ? React.cloneElement(child as React.ReactElement<any>, {
              active: value === (child as React.ReactElement<any>).props["data-value"],
              onClick: () =>
                onValueChange?.((child as React.ReactElement<any>).props["data-value"]),
            })
          : child
      )}
    </div>
  )
}

interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  "data-value": string
  active?: boolean
}

function TabsTrigger({
  className,
  active,
  children,
  ...props
}: TabsTriggerProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1 text-sm font-medium transition-all",
        active
          ? "bg-background text-foreground shadow-xs"
          : "text-muted-foreground hover:text-foreground",
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}

interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  tabValue: string
  value?: string
}

function TabsContent({
  className,
  tabValue,
  value,
  children,
  ...props
}: TabsContentProps) {
  if (value !== tabValue) return null
  return (
    <div className={cn("animate-fade-in", className)} {...props}>
      {children}
    </div>
  )
}

export { Tabs, TabsList, TabsTrigger, TabsContent }

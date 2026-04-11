import { cn } from "@/lib/utils"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"
import { Card } from "./card"

interface MetricCardProps {
  title: string
  value: string
  change?: number
  changeLabel?: string
  icon?: React.ReactNode
  className?: string
}

export function MetricCard({
  title,
  value,
  change,
  changeLabel,
  icon,
  className,
}: MetricCardProps) {
  const trend =
    change === undefined || change === 0
      ? "neutral"
      : change > 0
        ? "up"
        : "down"

  return (
    <Card className={cn("p-5", className)}>
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            {title}
          </p>
          <p className="text-2xl font-semibold tracking-tight">{value}</p>
        </div>
        {icon && (
          <div className="rounded-lg bg-primary/10 p-2.5 [&_svg]:h-4 [&_svg]:w-4 [&_svg]:text-primary">
            {icon}
          </div>
        )}
      </div>
      {change !== undefined && (
        <div className="mt-3 flex items-center gap-1.5">
          <div
            className={cn(
              "flex items-center gap-0.5 text-xs font-medium",
              trend === "up" && "text-success",
              trend === "down" && "text-destructive",
              trend === "neutral" && "text-muted-foreground"
            )}
          >
            {trend === "up" && <TrendingUp className="h-3.5 w-3.5" />}
            {trend === "down" && <TrendingDown className="h-3.5 w-3.5" />}
            {trend === "neutral" && <Minus className="h-3.5 w-3.5" />}
            {change > 0 && "+"}
            {change}%
          </div>
          {changeLabel && (
            <span className="text-xs text-muted-foreground">
              {changeLabel}
            </span>
          )}
        </div>
      )}
    </Card>
  )
}

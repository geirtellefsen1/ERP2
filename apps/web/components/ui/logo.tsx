import Link from "next/link"
import { cn } from "@/lib/utils"

interface LogoProps {
  /** Size preset — sm=28px, md=36px, lg=48px, xl=64px */
  size?: "sm" | "md" | "lg" | "xl"
  /** Show the "ClaudERP" wordmark alongside the icon. Default: true */
  showWordmark?: boolean
  /** Wrap the logo in a <Link> pointing at this href */
  href?: string
  /** Force a background for the icon mark (useful on colored surfaces) */
  markBackground?: "none" | "white" | "tint"
  className?: string
}

const sizeMap = {
  sm: {
    icon: "h-7",
    text: "text-sm",
    gap: "gap-2",
    pad: "p-1.5",
  },
  md: {
    icon: "h-9",
    text: "text-base",
    gap: "gap-2.5",
    pad: "p-2",
  },
  lg: {
    icon: "h-12",
    text: "text-lg",
    gap: "gap-3",
    pad: "p-2.5",
  },
  xl: {
    icon: "h-16",
    text: "text-xl",
    gap: "gap-3.5",
    pad: "p-3",
  },
}

export function Logo({
  size = "md",
  showWordmark = true,
  href,
  markBackground = "none",
  className,
}: LogoProps) {
  const s = sizeMap[size]

  const mark = (
    <div
      className={cn(
        "flex items-center justify-center shrink-0",
        markBackground === "white" && "bg-white rounded-xl shadow-xs",
        markBackground === "tint" && "bg-primary/10 rounded-xl",
        markBackground !== "none" && s.pad
      )}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/logo.svg"
        alt="ClaudERP"
        className={cn("w-auto", s.icon)}
      />
    </div>
  )

  const content = (
    <div className={cn("flex items-center", s.gap, className)}>
      {mark}
      {showWordmark && (
        <span className={cn("font-semibold tracking-tight", s.text)}>
          ClaudERP
        </span>
      )}
    </div>
  )

  if (href) {
    return (
      <Link href={href} className="hover:opacity-90 transition-opacity">
        {content}
      </Link>
    )
  }
  return content
}

/**
 * Icon-only variant for tight spaces like the collapsed sidebar.
 * Always renders the mark without the wordmark.
 */
export function LogoIcon({
  size = "md",
  className,
  markBackground = "none",
}: Omit<LogoProps, "showWordmark" | "href">) {
  return (
    <Logo
      size={size}
      showWordmark={false}
      markBackground={markBackground}
      className={className}
    />
  )
}

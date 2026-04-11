import { cn, getInitials } from "@/lib/utils"

interface AvatarProps {
  name: string
  src?: string
  size?: "sm" | "md" | "lg"
  className?: string
}

const sizeMap = {
  sm: "h-7 w-7 text-2xs",
  md: "h-8 w-8 text-xs",
  lg: "h-10 w-10 text-sm",
}

export function Avatar({ name, src, size = "md", className }: AvatarProps) {
  if (src) {
    return (
      <img
        src={src}
        alt={name}
        className={cn("rounded-full object-cover", sizeMap[size], className)}
      />
    )
  }

  return (
    <div
      className={cn(
        "rounded-full bg-primary/10 text-primary font-medium flex items-center justify-center",
        sizeMap[size],
        className
      )}
    >
      {getInitials(name)}
    </div>
  )
}

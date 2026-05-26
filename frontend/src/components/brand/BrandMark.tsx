import { WheelIcon } from "@/components/icons/WheelIcon"
import { brandAssets } from "@/components/brand/brandAssets"
import { cn } from "@/lib/utils"

interface BrandMarkProps {
  compact?: boolean
  variant?: "header" | "hero"
  className?: string
}

function TypographicHero({ className }: { className?: string }) {
  return (
    <div
      className={cn("flex flex-col items-center gap-4 text-center", className)}
      aria-label="Wheel of Fish — Playlist Manager"
    >
      <WheelIcon className="size-28 sm:size-32" />
      <div className="flex flex-col items-center gap-1">
        <span className="font-heading text-4xl leading-none tracking-wide sm:text-5xl">
          <span className="bg-gradient-to-b from-wof-yellow to-wof-orange bg-clip-text text-transparent [text-shadow:0_1px_0_rgba(0,0,0,0.15)]">
            WHEEL
          </span>
        </span>
        <span className="font-heading text-2xl leading-none tracking-wide text-wof-teal sm:text-3xl">
          of FISH
        </span>
      </div>
      <p className="text-xs font-medium uppercase tracking-[0.28em] text-muted-foreground">
        Playlist Manager
      </p>
    </div>
  )
}

function TypographicHeader({ compact, className }: { compact?: boolean; className?: string }) {
  return (
    <div
      className={cn("flex items-center gap-2.5", className)}
      aria-label="Wheel of Fish TV"
    >
      <WheelIcon className={cn(compact ? "size-7" : "size-8")} />
      <span
        className={cn(
          "font-heading leading-none tracking-wide text-foreground",
          compact ? "text-sm" : "text-base sm:text-lg",
        )}
      >
        Wheel of Fish
      </span>
    </div>
  )
}

export function BrandMark({
  compact = false,
  variant = "header",
  className,
}: BrandMarkProps) {
  if (variant === "hero") {
    if (brandAssets.heroLogoSrc) {
      return (
        <img
          src={brandAssets.heroLogoSrc}
          alt="Wheel of Fish — Playlist Manager"
          className={cn("h-auto w-full max-w-md", className)}
        />
      )
    }
    return <TypographicHero className={className} />
  }

  if (brandAssets.headerLogoSrc) {
    return (
      <img
        src={brandAssets.headerLogoSrc}
        alt="Wheel of Fish TV"
        className={cn(
          "block h-auto w-auto shrink-0 object-contain object-left",
          compact ? "h-14 w-auto sm:h-16 md:h-[4.75rem]" : "h-24 w-auto sm:h-28 md:h-32",
          className,
        )}
      />
    )
  }

  return <TypographicHeader compact={compact} className={className} />
}

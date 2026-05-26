import { WheelIcon } from "@/components/icons/WheelIcon"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface RebuildButtonProps {
  onClick: () => void
  spinning?: boolean
  className?: string
}

export function RebuildButton({
  onClick,
  spinning = false,
  className,
}: RebuildButtonProps) {
  const label = spinning ? "Rebuilding…" : "Rebuild"

  return (
    <Button
      type="button"
      variant="outline"
      onClick={onClick}
      disabled={spinning}
      aria-busy={spinning}
      aria-label={label}
      className={cn(
        "h-auto min-w-[4.75rem] flex-col gap-1.5 px-3 py-2.5",
        className,
      )}
    >
      <WheelIcon spinning={spinning} className="size-10" />
      <span className="text-[0.65rem] font-semibold uppercase tracking-[0.12em]">
        {label}
      </span>
    </Button>
  )
}

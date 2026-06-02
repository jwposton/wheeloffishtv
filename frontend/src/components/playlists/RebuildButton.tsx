import { WheelIcon } from "@/components/icons/WheelIcon"
import {
  playlistActionButtonClass,
  playlistActionIconFrameClass,
  playlistActionLabelClass,
} from "@/components/playlists/playlistActionButton"
import { Button } from "@/components/ui/button"

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
      className={playlistActionButtonClass(className)}
    >
      <span className={playlistActionIconFrameClass}>
        <WheelIcon spinning={spinning} className="size-full" />
      </span>
      <span className={playlistActionLabelClass}>{label}</span>
    </Button>
  )
}

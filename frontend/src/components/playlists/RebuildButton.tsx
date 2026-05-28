import { RebuildWheelIcon } from "@/components/playlists/RebuildWheelIcon"
import {
  playlistActionButtonClass,
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
      <RebuildWheelIcon spinning={spinning} />
      <span className={playlistActionLabelClass}>{label}</span>
    </Button>
  )
}

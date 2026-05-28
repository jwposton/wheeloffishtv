import rebuildPointer from "@/assets/playlists/rebuild-pointer.png"
import rebuildWheel from "@/assets/playlists/rebuild-wheel.png"
import { playlistActionIconFrameClass } from "@/components/playlists/playlistActionButton"
import { cn } from "@/lib/utils"

interface RebuildWheelIconProps {
  spinning?: boolean
  className?: string
}

/** Wheel spins; pointer stays fixed (polished two-layer rebuild art). */
export function RebuildWheelIcon({ spinning = false, className }: RebuildWheelIconProps) {
  return (
    <span
      data-testid="wheel-icon"
      data-spinning={spinning ? "true" : "false"}
      className={cn(playlistActionIconFrameClass, className)}
    >
      <img
        src={rebuildWheel}
        alt=""
        className={cn(
          "size-full object-contain",
          spinning && "motion-safe:animate-[spin_1.1s_linear_infinite]",
        )}
      />
      <img
        src={rebuildPointer}
        alt=""
        className="pointer-events-none absolute top-0 left-1/2 z-10 w-[34%] -translate-x-1/2 object-contain drop-shadow-sm"
      />
    </span>
  )
}

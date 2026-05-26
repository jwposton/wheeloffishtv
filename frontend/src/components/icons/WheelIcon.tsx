import { brandAssets } from "@/components/brand/brandAssets"
import { cn } from "@/lib/utils"

const SEGMENTS = ["#f07c2f", "#26a69a", "#fbc02d", "#66bb6a"] as const
const RIM = "#0d4a6e"
const POINTER = "#fbc02d"
const OUTLINE = "#1a1a2e"

function polar(cx: number, cy: number, radius: number, degrees: number): [number, number] {
  const radians = ((degrees - 90) * Math.PI) / 180
  return [cx + radius * Math.cos(radians), cy + radius * Math.sin(radians)]
}

function wedgePath(
  cx: number,
  cy: number,
  innerRadius: number,
  outerRadius: number,
  startDegrees: number,
  endDegrees: number,
): string {
  const [ox1, oy1] = polar(cx, cy, outerRadius, startDegrees)
  const [ox2, oy2] = polar(cx, cy, outerRadius, endDegrees)
  const [ix2, iy2] = polar(cx, cy, innerRadius, endDegrees)
  const [ix1, iy1] = polar(cx, cy, innerRadius, startDegrees)
  const largeArc = endDegrees - startDegrees > 180 ? 1 : 0

  return [
    `M ${ox1} ${oy1}`,
    `A ${outerRadius} ${outerRadius} 0 ${largeArc} 1 ${ox2} ${oy2}`,
    `L ${ix2} ${iy2}`,
    `A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${ix1} ${iy1}`,
    "Z",
  ].join(" ")
}

interface WheelIconProps {
  spinning?: boolean
  className?: string
}

/** Wheel mark — painted PNG when set, otherwise SVG fallback. */
export function WheelIcon({ spinning = false, className }: WheelIconProps) {
  if (brandAssets.wheelIconSrc) {
    return (
      <img
        src={brandAssets.wheelIconSrc}
        alt=""
        aria-hidden="true"
        data-testid="wheel-icon"
        data-spinning={spinning ? "true" : "false"}
        className={cn(
          "size-4 shrink-0 object-contain",
          spinning && "motion-safe:animate-spin",
          className,
        )}
      />
    )
  }

  return (
    <svg
      viewBox="0 0 64 64"
      aria-hidden="true"
      data-testid="wheel-icon"
      data-spinning={spinning ? "true" : "false"}
      className={cn(
        "size-4 shrink-0",
        spinning && "motion-safe:animate-spin",
        className,
      )}
    >
      <circle cx="32" cy="32" r="30" fill={RIM} />
      {Array.from({ length: 8 }, (_, index) => {
        const start = index * 45
        const end = start + 45
        return (
          <path
            key={index}
            d={wedgePath(32, 32, 9, 26, start, end)}
            fill={SEGMENTS[index % SEGMENTS.length]}
            stroke={OUTLINE}
            strokeWidth="0.6"
            strokeLinejoin="round"
          />
        )
      })}
      {Array.from({ length: 12 }, (_, index) => {
        const [x, y] = polar(32, 32, 28, index * 30)
        return <circle key={index} cx={x} cy={y} r="1.3" fill="#fff8dc" opacity="0.95" />
      })}
      <polygon
        points="32,3 37,13 27,13"
        fill={POINTER}
        stroke={OUTLINE}
        strokeWidth="0.6"
        strokeLinejoin="round"
      />
      <circle cx="32" cy="32" r="6" fill="#1e88e5" stroke={OUTLINE} strokeWidth="0.6" />
      <circle cx="32" cy="32" r="2.5" fill="#e3f2fd" />
    </svg>
  )
}

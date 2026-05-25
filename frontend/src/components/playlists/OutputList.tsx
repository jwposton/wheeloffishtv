import type { SnapshotEpisode } from "@/api/playlists"

interface OutputListProps {
  episodes: SnapshotEpisode[]
}

export function OutputList({ episodes }: OutputListProps) {
  if (episodes.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-4 text-center">
        No output yet — rebuild to generate the episode list.
      </p>
    )
  }

  return (
    <ol className="flex flex-col divide-y">
      {episodes.map((ep) => (
        <li
          key={ep.slot_index}
          className="flex items-start gap-3 py-2.5"
        >
          <span className="min-w-[2rem] text-right text-sm text-muted-foreground tabular-nums">
            {ep.slot_index + 1}.
          </span>
          <div className="flex-1 min-w-0">
            <p className="truncate text-sm font-medium">{ep.title}</p>
            {ep.series_title && (
              <p className="truncate text-xs text-muted-foreground">{ep.series_title}</p>
            )}
          </div>
        </li>
      ))}
    </ol>
  )
}

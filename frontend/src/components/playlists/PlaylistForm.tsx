import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { SeriesPicker, type SeriesRow } from "@/components/playlists/SeriesPicker"
import {
  SLOT_ALLOCATION_LABELS,
  useCreatePlaylist,
  useUpdatePlaylist,
  type PlaylistCreatePayload,
  type PlaylistDetailResponse,
  type SlotAllocation,
  type CompletionPolicy,
} from "@/api/playlists"
import type { RefreshCadence } from "@/api/types"

const SLOT_ALLOCATION_OPTIONS: SlotAllocation[] = ["wild", "balanced", "round_robin"]

const COMPLETION_POLICY_LABELS: Record<CompletionPolicy, string> = {
  remove: "Remove when done",
  restart: "Restart",
  disordered: "Switch to random",
}

const DOW_OPTIONS = [
  { value: 0, label: "Monday" },
  { value: 1, label: "Tuesday" },
  { value: 2, label: "Wednesday" },
  { value: 3, label: "Thursday" },
  { value: 4, label: "Friday" },
  { value: 5, label: "Saturday" },
  { value: 6, label: "Sunday" },
]

interface PlaylistFormProps {
  mode: "create" | "edit"
  playlist?: PlaylistDetailResponse
}

export function PlaylistForm({ mode, playlist }: PlaylistFormProps) {
  const navigate = useNavigate()
  const createMutation = useCreatePlaylist()
  const updateMutation = useUpdatePlaylist()

  const [name, setName] = useState(playlist?.name ?? "")
  const [episodeCount, setEpisodeCount] = useState(playlist?.episode_count ?? 20)
  const [slotAllocation, setSlotAllocation] = useState<SlotAllocation>(
    playlist?.slot_allocation ?? "wild",
  )
  const [defaultCompletionPolicy, setDefaultCompletionPolicy] =
    useState<CompletionPolicy>(playlist?.default_completion_policy ?? "remove")
  const [cadence, setCadence] = useState<RefreshCadence>(
    playlist?.refresh_cadence ?? "daily",
  )
  const [dow, setDow] = useState<number>(playlist?.refresh_day_of_week ?? 0)

  const [rows, setRows] = useState<SeriesRow[]>(
    playlist?.rows.map((r) => ({
      series_id: r.series_id,
      series_title: r.series_title ?? r.series_id,
      thumb_url: null,
      mode: r.mode,
      completion_policy: r.completion_policy,
    })) ?? [],
  )

  const [errors, setErrors] = useState<Record<string, string>>({})

  function validate(): boolean {
    const errs: Record<string, string> = {}
    if (!name.trim()) errs.name = "Name is required."
    if (episodeCount < 1) errs.episode_count = "Episode count must be at least 1."
    if (cadence === "weekly" && dow == null) errs.dow = "Day of week is required for weekly cadence."
    if (rows.length === 0) errs.rows = "Add at least one series."
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validate()) return

    const payload: PlaylistCreatePayload = {
      name: name.trim(),
      episode_count: episodeCount,
      slot_allocation: slotAllocation,
      default_completion_policy: defaultCompletionPolicy,
      refresh_cadence: cadence,
      refresh_day_of_week: cadence === "weekly" ? dow : null,
      rows: rows.map((r) => ({
        series_id: r.series_id,
        mode: r.mode,
        completion_policy: r.completion_policy,
      })),
    }

    try {
      if (mode === "create") {
        const result = await createMutation.mutateAsync(payload)
        toast.success("Playlist created")
        navigate(`/playlists/${result.id}`)
      } else if (playlist) {
        await updateMutation.mutateAsync({ id: playlist.id, payload })
        toast.success("Playlist saved")
        navigate(`/playlists/${playlist.id}`)
      }
    } catch {
      toast.error(mode === "create" ? "Failed to create playlist" : "Failed to save playlist")
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <form onSubmit={(e) => void handleSubmit(e)} className="flex flex-col gap-6">
      {/* Section 1: Basics */}
      <section className="flex flex-col gap-4 rounded-xl border bg-card p-4">
        <h3 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">Basics</h3>

        <div className="flex flex-col gap-1">
          <Label htmlFor="playlist-name">Name</Label>
          <Input
            id="playlist-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="My Playlist"
            aria-invalid={Boolean(errors.name)}
          />
          {errors.name && <p className="text-xs text-destructive">{errors.name}</p>}
        </div>

        <div className="flex flex-col gap-1">
          <Label htmlFor="episode-count">Episode count</Label>
          <Input
            id="episode-count"
            type="number"
            min={1}
            value={episodeCount}
            onChange={(e) => setEpisodeCount(Number(e.target.value))}
            className="w-24"
            aria-invalid={Boolean(errors.episode_count)}
          />
          {errors.episode_count && (
            <p className="text-xs text-destructive">{errors.episode_count}</p>
          )}
        </div>

        <div className="flex flex-col gap-1">
          <Label htmlFor="slot-allocation">Slot allocation</Label>
          <select
            id="slot-allocation"
            value={slotAllocation}
            onChange={(e) => setSlotAllocation(e.target.value as SlotAllocation)}
            className="h-8 w-fit rounded-lg border border-input bg-transparent px-2.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {SLOT_ALLOCATION_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>
                {SLOT_ALLOCATION_LABELS[opt]}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <Label htmlFor="default-completion">Default completion policy</Label>
          <select
            id="default-completion"
            value={defaultCompletionPolicy}
            onChange={(e) =>
              setDefaultCompletionPolicy(e.target.value as CompletionPolicy)
            }
            className="h-8 w-fit rounded-lg border border-input bg-transparent px-2.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {(Object.keys(COMPLETION_POLICY_LABELS) as CompletionPolicy[]).map((k) => (
              <option key={k} value={k}>
                {COMPLETION_POLICY_LABELS[k]}
              </option>
            ))}
          </select>
        </div>
      </section>

      {/* Section 2: Schedule */}
      <section className="flex flex-col gap-4 rounded-xl border bg-card p-4">
        <h3 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">Schedule</h3>

        <div className="flex items-center gap-4" role="radiogroup" aria-label="Refresh cadence">
          <label className="flex items-center gap-2 cursor-pointer text-sm">
            <input
              type="radio"
              name="cadence"
              value="daily"
              checked={cadence === "daily"}
              onChange={() => setCadence("daily")}
              className="accent-primary"
            />
            Daily
          </label>
          <label className="flex items-center gap-2 cursor-pointer text-sm">
            <input
              type="radio"
              name="cadence"
              value="weekly"
              checked={cadence === "weekly"}
              onChange={() => setCadence("weekly")}
              className="accent-primary"
            />
            Weekly
          </label>
        </div>

        {cadence === "weekly" && (
          <div className="flex flex-col gap-1">
            <Label htmlFor="day-of-week">Day of week</Label>
            <select
              id="day-of-week"
              value={dow}
              onChange={(e) => setDow(Number(e.target.value))}
              className="h-8 w-fit rounded-lg border border-input bg-transparent px-2.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-invalid={Boolean(errors.dow)}
            >
              {DOW_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            {errors.dow && <p className="text-xs text-destructive">{errors.dow}</p>}
          </div>
        )}
      </section>

      {/* Section 3: Series rows */}
      <section className="flex flex-col gap-4 rounded-xl border bg-card p-4">
        <h3 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">Series</h3>

        <SeriesPicker
          rows={rows}
          onAdd={(row) => setRows((prev) => [...prev, row])}
          onRemove={(id) => setRows((prev) => prev.filter((r) => r.series_id !== id))}
          onUpdateRow={(id, updates) =>
            setRows((prev) =>
              prev.map((r) => (r.series_id === id ? { ...r, ...updates } : r)),
            )
          }
        />
        {errors.rows && <p className="text-xs text-destructive">{errors.rows}</p>}
      </section>

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={isPending}>
          {isPending ? "Saving…" : "Save playlist"}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => navigate(playlist ? `/playlists/${playlist.id}` : "/playlists")}
        >
          Cancel
        </Button>
      </div>
    </form>
  )
}

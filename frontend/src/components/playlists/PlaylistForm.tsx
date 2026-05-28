import { useEffect, useMemo, useRef, useState } from "react"

import { useRemoveConfirmSession } from "@/hooks/useRemoveConfirmSession"
import { useAuth } from "@/hooks/useAuth"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  TwoPanePicker,
  type SeriesRow,
} from "@/components/playlists/TwoPanePicker"
import {
  SLOT_ALLOCATION_LABELS,
  formatRefreshScheduleHelp,
  useCreatePlaylist,
  usePlaylist,
  useUpdatePlaylist,
  type PlaylistCreatePayload,
  type PlaylistDetailResponse,
  type PlaylistUpdatePayload,
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

interface PlaylistSettingsState {
  name: string
  episodeCountInput: string
  slotAllocation: SlotAllocation
  defaultCompletionPolicy: CompletionPolicy
  cadence: RefreshCadence
  dow: number
}

function settingsFromPlaylist(playlist: PlaylistDetailResponse): PlaylistSettingsState {
  return {
    name: playlist.name,
    episodeCountInput: String(playlist.episode_count),
    slotAllocation: playlist.slot_allocation,
    defaultCompletionPolicy: playlist.default_completion_policy,
    cadence: playlist.refresh_cadence,
    dow: playlist.refresh_day_of_week ?? 0,
  }
}

function rowsFromPlaylist(playlist: PlaylistDetailResponse): SeriesRow[] {
  return playlist.rows.map((r) => ({
    series_id: r.series_id,
    series_title: r.series_title ?? r.series_id,
    thumb_url: r.thumb_url ?? null,
    mode: r.mode,
    completion_policy: r.completion_policy,
  }))
}

function FieldHelp({ children }: { children: string }) {
  return <p className="text-xs text-muted-foreground">{children}</p>
}

interface PlaylistFormProps {
  mode: "create" | "edit"
  playlist?: PlaylistDetailResponse
  initialRows?: SeriesRow[]
}

export function PlaylistForm({ mode, playlist, initialRows }: PlaylistFormProps) {
  const navigate = useNavigate()
  const { user } = useAuth()
  const createMutation = useCreatePlaylist()
  const updateMutation = useUpdatePlaylist()
  const { data: livePlaylist } = usePlaylist(playlist?.id ?? "", {
    enabled: mode === "edit" && Boolean(playlist?.id),
  })

  const baselineRef = useRef<PlaylistSettingsState | null>(
    playlist ? settingsFromPlaylist(playlist) : null,
  )

  const [settings, setSettings] = useState<PlaylistSettingsState>(() =>
    playlist
      ? settingsFromPlaylist(playlist)
      : {
          name: "",
          episodeCountInput: "20",
          slotAllocation: "wild",
          defaultCompletionPolicy: "remove",
          cadence: "daily",
          dow: 0,
        },
  )

  const [createRows, setCreateRows] = useState<SeriesRow[]>(
    playlist?.rows.map((r) => ({
      series_id: r.series_id,
      series_title: r.series_title ?? r.series_id,
      thumb_url: r.thumb_url ?? null,
      mode: r.mode,
      completion_policy: r.completion_policy,
    })) ??
      initialRows ??
      [],
  )

  const [errors, setErrors] = useState<Record<string, string>>({})
  const [rowMutationsPending, setRowMutationsPending] = useState(false)
  const {
    skipRemoveConfirm,
    enableSkipRemoveConfirm,
    resetSkipRemoveConfirm,
  } = useRemoveConfirmSession()

  const activePlaylist = livePlaylist ?? playlist
  const editMemberRows = useMemo(
    () => (activePlaylist ? rowsFromPlaylist(activePlaylist) : []),
    [activePlaylist],
  )

  useEffect(() => {
    if (!playlist) {
      return
    }
    const next = settingsFromPlaylist(playlist)
    baselineRef.current = next
    setSettings(next)
  }, [playlist?.id, playlist?.name, playlist?.episode_count])

  function parsedEpisodeCount(): number {
    const parsed = Number.parseInt(settings.episodeCountInput, 10)
    return Number.isFinite(parsed) && parsed >= 1 ? parsed : 1
  }

  function validateSettings(): boolean {
    const errs: Record<string, string> = {}
    if (!settings.name.trim()) errs.name = "Name is required."
    if (parsedEpisodeCount() < 1) errs.episode_count = "Episode count must be at least 1."
    if (settings.cadence === "weekly" && settings.dow == null) {
      errs.dow = "Day of week is required for weekly cadence."
    }
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  function validateCreate(): boolean {
    if (!validateSettings()) {
      return false
    }
    if (createRows.length === 0) {
      setErrors((previous) => ({ ...previous, rows: "Add at least one series." }))
      return false
    }
    return true
  }

  function handleCancelSettings() {
    if (baselineRef.current) {
      setSettings({ ...baselineRef.current })
    }
    setErrors({})
  }

  async function handleSaveSettings() {
    if (!validateSettings() || !playlist) {
      return
    }

    const payload: PlaylistUpdatePayload = {
      name: settings.name.trim(),
      episode_count: parsedEpisodeCount(),
      slot_allocation: settings.slotAllocation,
      default_completion_policy: settings.defaultCompletionPolicy,
      refresh_cadence: settings.cadence,
      refresh_day_of_week: settings.cadence === "weekly" ? settings.dow : null,
    }

    try {
      const updated = await updateMutation.mutateAsync({ id: playlist.id, payload })
      const nextSettings = settingsFromPlaylist(updated)
      baselineRef.current = nextSettings
      setSettings(nextSettings)
      toast.success("Playlist settings saved")
    } catch {
      toast.error("Failed to save playlist settings")
    }
  }

  async function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validateCreate()) {
      return
    }

    const payload: PlaylistCreatePayload = {
      name: settings.name.trim(),
      episode_count: parsedEpisodeCount(),
      slot_allocation: settings.slotAllocation,
      default_completion_policy: settings.defaultCompletionPolicy,
      refresh_cadence: settings.cadence,
      refresh_day_of_week: settings.cadence === "weekly" ? settings.dow : null,
      rows: createRows.map((r) => ({
        series_id: r.series_id,
        mode: r.mode,
        completion_policy: r.completion_policy,
      })),
    }

    try {
      const result = await createMutation.mutateAsync(payload)
      resetSkipRemoveConfirm()
      toast.success("Playlist created")
      navigate(`/playlists/${result.id}`)
    } catch {
      toast.error("Failed to create playlist")
    }
  }

  const installSchedule = user?.install_schedule ?? {
    install_timezone: "UTC",
    rebuild_cron: "04:00",
  }

  const refreshHelp = formatRefreshScheduleHelp(
    {
      refresh_cadence: settings.cadence,
      refresh_day_of_week: settings.cadence === "weekly" ? settings.dow : null,
    },
    installSchedule,
  )

  const settingsPending = updateMutation.isPending
  const createPending = createMutation.isPending

  return (
    <form
      onSubmit={mode === "create" ? (e) => void handleCreateSubmit(e) : (e) => e.preventDefault()}
      className="flex flex-col gap-6 pb-20"
    >
      <section className="flex flex-col gap-4 rounded-xl border bg-card p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
            Playlist settings
          </h3>
          {mode === "edit" ? (
            <div className="flex items-center gap-2">
              <Button
                type="button"
                size="sm"
                onClick={() => void handleSaveSettings()}
                disabled={settingsPending || rowMutationsPending}
              >
                {settingsPending ? "Saving…" : "Save Settings"}
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={handleCancelSettings}
                disabled={settingsPending}
              >
                Cancel
              </Button>
            </div>
          ) : null}
        </div>

        <div className="grid gap-4">
          <div className="flex flex-col gap-1">
            <Label htmlFor="playlist-name">Name</Label>
            <FieldHelp>Display name for this playlist in Wheel of Fish and on your media server.</FieldHelp>
            <Input
              id="playlist-name"
              value={settings.name}
              onChange={(e) => setSettings((s) => ({ ...s, name: e.target.value }))}
              placeholder="My Playlist"
              aria-invalid={Boolean(errors.name)}
            />
            {errors.name && <p className="text-xs text-destructive">{errors.name}</p>}
          </div>

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <div className="flex flex-col gap-1">
              <Label htmlFor="episode-count">Episode count</Label>
              <FieldHelp>How many episodes each rebuild should try to fill.</FieldHelp>
              <Input
                id="episode-count"
                type="text"
                inputMode="numeric"
                autoComplete="off"
                value={settings.episodeCountInput}
                onChange={(e) => {
                  const next = e.target.value.replace(/\D/g, "")
                  setSettings((s) => ({ ...s, episodeCountInput: next }))
                }}
                onBlur={() => {
                  setSettings((s) => ({
                    ...s,
                    episodeCountInput: String(parsedEpisodeCount()),
                  }))
                }}
                className="w-full max-w-none"
                aria-invalid={Boolean(errors.episode_count)}
              />
              {errors.episode_count && (
                <p className="text-xs text-destructive">{errors.episode_count}</p>
              )}
            </div>

            <div className="flex flex-col gap-1">
              <Label htmlFor="slot-allocation">Slot allocation</Label>
              <FieldHelp>How episodes are distributed across shows when rebuilding.</FieldHelp>
              <select
                id="slot-allocation"
                value={settings.slotAllocation}
                onChange={(e) =>
                  setSettings((s) => ({
                    ...s,
                    slotAllocation: e.target.value as SlotAllocation,
                  }))
                }
                className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {SLOT_ALLOCATION_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {SLOT_ALLOCATION_LABELS[opt]}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1 sm:col-span-2 xl:col-span-1">
              <Label htmlFor="default-completion">Default completion policy</Label>
              <FieldHelp>What happens to a show when you finish every episode in it.</FieldHelp>
              <select
                id="default-completion"
                value={settings.defaultCompletionPolicy}
                onChange={(e) =>
                  setSettings((s) => ({
                    ...s,
                    defaultCompletionPolicy: e.target.value as CompletionPolicy,
                  }))
                }
                className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {(Object.keys(COMPLETION_POLICY_LABELS) as CompletionPolicy[]).map((k) => (
                  <option key={k} value={k}>
                    {COMPLETION_POLICY_LABELS[k]}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-3 border-t pt-4 lg:flex-row lg:flex-wrap lg:items-end lg:gap-6">
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-4" role="radiogroup" aria-label="Refresh cadence">
              <span className="text-sm font-medium">Refresh</span>
              <label className="flex items-center gap-2 cursor-pointer text-sm">
                <input
                  type="radio"
                  name="cadence"
                  value="daily"
                  checked={settings.cadence === "daily"}
                  onChange={() => setSettings((s) => ({ ...s, cadence: "daily" }))}
                  className="accent-primary"
                />
                Daily
              </label>
              <label className="flex items-center gap-2 cursor-pointer text-sm">
                <input
                  type="radio"
                  name="cadence"
                  value="weekly"
                  checked={settings.cadence === "weekly"}
                  onChange={() => setSettings((s) => ({ ...s, cadence: "weekly" }))}
                  className="accent-primary"
                />
                Weekly
              </label>
            </div>
            <FieldHelp>{refreshHelp}</FieldHelp>
          </div>

          {settings.cadence === "weekly" && (
            <div className="flex flex-col gap-1 lg:min-w-[180px]">
              <Label htmlFor="day-of-week">Day of week</Label>
              <FieldHelp>Weekly rebuilds run on this day when the playlist is due.</FieldHelp>
              <select
                id="day-of-week"
                value={settings.dow}
                onChange={(e) =>
                  setSettings((s) => ({ ...s, dow: Number(e.target.value) }))
                }
                className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
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
        </div>
      </section>

      <section className="flex flex-col gap-4 rounded-xl border bg-card p-4">
        <h3 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">Series</h3>
        <FieldHelp>
          Adding or removing shows saves immediately. Use Save Settings above for name, episode
          count, allocation, completion policy, and refresh schedule.
        </FieldHelp>

        {mode === "edit" && playlist ? (
          <TwoPanePicker
            rows={editMemberRows}
            onRowsChange={() => {
              /* membership updates via immediate API + query invalidation */
            }}
            playlistId={playlist.id}
            onRowMutationsPendingChange={setRowMutationsPending}
            skipRemoveConfirm={skipRemoveConfirm}
            onEnableSkipRemoveConfirm={enableSkipRemoveConfirm}
          />
        ) : (
          <TwoPanePicker
            rows={createRows}
            onRowsChange={setCreateRows}
            onRowMutationsPendingChange={setRowMutationsPending}
            skipRemoveConfirm={skipRemoveConfirm}
            onEnableSkipRemoveConfirm={enableSkipRemoveConfirm}
          />
        )}
        {errors.rows && <p className="text-xs text-destructive">{errors.rows}</p>}
      </section>

      {mode === "create" ? (
        <div className="sticky bottom-0 z-10 -mx-4 mt-4 flex items-center gap-3 border-t bg-background/95 px-4 py-3 backdrop-blur supports-[backdrop-filter]:bg-background/80">
          <Button type="submit" disabled={createPending}>
            {createPending ? "Creating…" : "Create playlist"}
          </Button>
          <Button type="button" variant="outline" onClick={() => navigate("/playlists")}>
            Cancel
          </Button>
        </div>
      ) : (
        <div className="flex justify-end">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate(playlist ? `/playlists/${playlist.id}` : "/playlists")}
          >
            Back to playlist
          </Button>
        </div>
      )}
    </form>
  )
}

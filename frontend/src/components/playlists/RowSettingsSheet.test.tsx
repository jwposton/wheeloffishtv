import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { RowSettingsSheet, type SeriesRow } from "@/components/playlists/RowSettingsSheet"

const SAMPLE_ROW: SeriesRow = {
  series_id: "series-1",
  series_title: "Sample Show",
  thumb_url: null,
  mode: "ordered",
  completion_policy: "remove",
}

describe("RowSettingsSheet", () => {
  it("renders toggle and select when open", () => {
    render(
      <RowSettingsSheet
        open
        onOpenChange={() => {}}
        row={SAMPLE_ROW}
        seriesTitle="Sample Show"
        onSave={vi.fn()}
        onRemove={vi.fn()}
      />,
    )

    expect(screen.getByText("Sample Show — row settings")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Ordered" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Random" })).toBeInTheDocument()
    expect(screen.getByLabelText("Completion policy")).toBeInTheDocument()
  })

  it("calls onSave with updated mode when Random is selected and saved", () => {
    const onSave = vi.fn()
    render(
      <RowSettingsSheet
        open
        onOpenChange={() => {}}
        row={SAMPLE_ROW}
        seriesTitle="Sample Show"
        onSave={onSave}
        onRemove={vi.fn()}
      />,
    )

    fireEvent.click(screen.getByRole("button", { name: "Random" }))
    fireEvent.click(screen.getByRole("button", { name: "Save" }))

    expect(onSave).toHaveBeenCalledWith({
      ...SAMPLE_ROW,
      mode: "disordered",
    })
  })
})

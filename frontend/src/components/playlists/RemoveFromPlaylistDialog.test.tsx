import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { RemoveFromPlaylistDialog } from "@/components/playlists/RemoveFromPlaylistDialog"

describe("RemoveFromPlaylistDialog", () => {
  it("toggles don't ask again and confirms remove", () => {
    const onConfirm = vi.fn()
    const onDontAskAgainChange = vi.fn()

    render(
      <RemoveFromPlaylistDialog
        open
        onOpenChange={vi.fn()}
        seriesTitle="Test Show"
        dontAskAgain={false}
        onDontAskAgainChange={onDontAskAgainChange}
        onConfirm={onConfirm}
      />,
    )

    fireEvent.click(screen.getByRole("checkbox", { name: "Don't ask again" }))
    expect(onDontAskAgainChange).toHaveBeenCalledWith(true)

    fireEvent.click(screen.getByRole("button", { name: "Remove" }))
    expect(onConfirm).toHaveBeenCalledTimes(1)
  })
})

import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { WritebackStatus } from "./WritebackStatus"

describe("WritebackStatus", () => {
  it("renders status badge without episode or info lists on detail", () => {
    render(
      <WritebackStatus
        status="partial"
        warnings={[
          { episode_id: "ep-1", reason: "No metadata found" },
          { episode_id: null, reason: "Playlist was recreated" },
        ]}
        openUrl="https://plex.example/playlist"
        providerKind="plex"
      />,
    )

    expect(screen.getByText("Partial sync")).toBeInTheDocument()
    expect(
      screen.getByText("Some episodes could not be synced to your media server."),
    ).toBeInTheDocument()
    expect(screen.queryByRole("list", { name: "Sync warnings" })).not.toBeInTheDocument()
    expect(screen.queryByRole("list", { name: "Sync notes" })).not.toBeInTheDocument()
    expect(screen.queryByText("The Pilot")).not.toBeInTheDocument()
    expect(screen.queryByText("Playlist was recreated")).not.toBeInTheDocument()
  })

  it("renders failed one-line summary without bullet list on detail", () => {
    render(
      <WritebackStatus
        status="failed"
        error="Connection refused"
        warnings={[{ episode_id: "ep-1", reason: "Sync error" }]}
      />,
    )

    expect(screen.getByText("Sync failed")).toBeInTheDocument()
    expect(screen.getByText("Sync failed: Connection refused")).toBeInTheDocument()
    expect(screen.queryByRole("list", { name: "Sync warnings" })).not.toBeInTheDocument()
  })

  it("renders badge only in compact mode", () => {
    render(
      <WritebackStatus
        status="partial"
        compact
        warnings={[{ episode_id: "ep-1", reason: "Missing guid" }]}
        openUrl="https://plex.example/playlist"
        providerKind="plex"
      />,
    )

    expect(screen.getByText("Partial sync")).toBeInTheDocument()
    expect(
      screen.queryByText("Some episodes could not be synced to your media server."),
    ).not.toBeInTheDocument()
    expect(screen.queryByRole("list", { name: "Sync warnings" })).not.toBeInTheDocument()
  })
})

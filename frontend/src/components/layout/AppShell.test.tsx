import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, within } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { beforeEach, describe, expect, it, vi } from "vitest"

import type { AuthMeResponse } from "@/api/types"

import { AppShell } from "./AppShell"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/hooks/useSessionCatalogRefresh", () => ({
  useSessionCatalogRefresh: vi.fn(),
}))

import { useAuth } from "@/hooks/useAuth"

const mockUseAuth = vi.mocked(useAuth)

const baseUser: AuthMeResponse = {
  app_user_id: "user-1",
  provider_user_id: "plex-123",
  provider_username: "operator",
  connection: null,
  has_media_link: true,
  libraries_scoped: true,
  install_schedule: { install_timezone: "UTC", rebuild_cron: "04:00" },
}

function renderAppShell(initialPath = "/browse") {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/browse" element={<div>Browse page</div>} />
            <Route path="/settings" element={<div>Settings page</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("AppShell navigation", () => {
  beforeEach(() => {
    mockUseAuth.mockReturnValue({
      user: baseUser,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    })

    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify({}), { status: 200 })),
    )
  })

  it("renders mobile and desktop nav with Library and Playlists", () => {
    renderAppShell()

    const navs = screen.getAllByRole("navigation", { name: "Main" })
    expect(navs).toHaveLength(2)

    for (const nav of navs) {
      expect(within(nav).getByRole("link", { name: "Library" })).toBeInTheDocument()
      expect(within(nav).getByRole("link", { name: "Playlists" })).toBeInTheDocument()
    }
  })

  it("hides Settings when user has no media link", () => {
    mockUseAuth.mockReturnValue({
      user: { ...baseUser, has_media_link: false },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    })

    renderAppShell()

    expect(screen.queryByRole("link", { name: "Settings" })).not.toBeInTheDocument()
  })

  it("shows Settings for linked users", () => {
    renderAppShell()

    expect(screen.getAllByRole("link", { name: "Settings" })).toHaveLength(2)
  })
})

import { render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { beforeEach, describe, expect, it, vi } from "vitest"

import type { AuthMeResponse } from "@/api/types"

import { AdminRoute } from "./AdminRoute"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

import { useAuth } from "@/hooks/useAuth"

const mockUseAuth = vi.mocked(useAuth)

const baseUser: AuthMeResponse = {
  app_user_id: "user-1",
  provider_user_id: "plex-123",
  provider_username: "operator",
  is_admin: false,
  setup_mode: false,
  connection: null,
  has_media_link: true,
  libraries_scoped: true,
  install_libraries_configured: true,
}

function renderAdminRoute(initialPath = "/settings") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/" element={<div>Home page</div>} />
        <Route element={<AdminRoute />}>
          <Route path="/settings" element={<div>Settings page</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

describe("AdminRoute", () => {
  beforeEach(() => {
    mockUseAuth.mockReset()
  })

  it("redirects non-admin users away from settings", () => {
    mockUseAuth.mockReturnValue({
      user: baseUser,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    })

    renderAdminRoute()

    expect(screen.getByText("Home page")).toBeInTheDocument()
    expect(screen.queryByText("Settings page")).not.toBeInTheDocument()
  })

  it("allows admin users to access settings", () => {
    mockUseAuth.mockReturnValue({
      user: { ...baseUser, is_admin: true },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    })

    renderAdminRoute()

    expect(screen.getByText("Settings page")).toBeInTheDocument()
  })
})

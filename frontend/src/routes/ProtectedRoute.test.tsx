import { render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { beforeEach, describe, expect, it, vi } from "vitest"

import type { AuthMeResponse } from "@/api/types"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

import { useAuth } from "@/hooks/useAuth"
import { ProtectedRoute } from "./ProtectedRoute"

const mockUseAuth = vi.mocked(useAuth)

const authenticatedUser: AuthMeResponse = {
  app_user_id: "user-1",
  provider_user_id: "plex-123",
  provider_username: "operator",
  is_admin: false,
  setup_mode: false,
  connection: null,
  has_media_link: true,
  libraries_scoped: false,
}

function renderProtected(initialPath = "/") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/login" element={<div>Login Page</div>} />
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<div>Protected Content</div>} />
          <Route path="/browse" element={<div>Browse Content</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

describe("ProtectedRoute", () => {
  beforeEach(() => {
    mockUseAuth.mockReset()
  })

  it("redirects to /login when useAuth returns isLoading=false and user=null", () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      isError: true,
      error: new Error("unauthenticated"),
      refetch: vi.fn(),
    })

    renderProtected("/browse")

    expect(screen.getByText("Login Page")).toBeInTheDocument()
    expect(screen.queryByText("Browse Content")).not.toBeInTheDocument()
  })

  it("renders children when user present", () => {
    mockUseAuth.mockReturnValue({
      user: authenticatedUser,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    })

    renderProtected()

    expect(screen.getByText("Protected Content")).toBeInTheDocument()
  })
})

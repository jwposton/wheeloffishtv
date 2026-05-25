import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { ThemeProvider } from "@/components/layout/ThemeProvider"
import App from "./App"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
  authQueryKey: ["auth", "me"],
}))

import { useAuth } from "@/hooks/useAuth"

const mockUseAuth = vi.mocked(useAuth)

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
})

describe("App", () => {
  beforeEach(() => {
    queryClient.clear()
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      isError: true,
      error: new Error("unauthenticated"),
      refetch: vi.fn(),
    })

    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
        const url =
          typeof input === "string"
            ? input
            : input instanceof URL
              ? input.href
              : input.url
        if (url.includes("/auth/bootstrap-session")) {
          return new Response(JSON.stringify({ status: "ok" }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          })
        }
        if (url.includes("/meta/providers")) {
          return new Response(
            JSON.stringify({
              provider: "plex",
              oauth_callback_base: "http://localhost:5173",
            }),
            {
              status: 200,
              headers: { "Content-Type": "application/json" },
            },
          )
        }
        return new Response("not found", { status: 404 })
      }),
    )
  })

  it("renders login when visiting the login route", async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/login"]}>
          <ThemeProvider>
            <App />
          </ThemeProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    )

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Wheel of Fish TV" }),
      ).toBeInTheDocument()
      expect(screen.getByText("Sign in")).toBeInTheDocument()
      expect(
        screen.getByRole("button", { name: "Sign in with Plex" }),
      ).toBeInTheDocument()
    })
  })
})

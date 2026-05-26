import { useMutation, useQueryClient } from "@tanstack/react-query"
import { LogOutIcon } from "lucide-react"
import { Link, Navigate, Outlet, useLocation, useNavigate } from "react-router-dom"

import { fetchJson } from "@/api/client"
import { BrandMark } from "@/components/brand/BrandMark"
import { ThemeToggle } from "@/components/layout/ThemeToggle"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { useAuth } from "@/hooks/useAuth"
import { useSessionCatalogRefresh } from "@/hooks/useSessionCatalogRefresh"
import { cn } from "@/lib/utils"

function SetupModeGate() {
  const { user } = useAuth()
  const location = useLocation()

  if (!user?.setup_mode) {
    return null
  }

  const allowedPaths = ["/setup/admin"]
  if (user.libraries_scoped || user.install_libraries_configured) {
    allowedPaths.push("/browse")
  }

  const isAllowed = allowedPaths.some(
    (path) =>
      location.pathname === path ||
      location.pathname.startsWith(`${path}/`),
  )

  if (isAllowed) {
    return null
  }

  return <Navigate to="/setup/admin" replace />
}

export function AppShell() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const location = useLocation()
  const { user } = useAuth()

  useSessionCatalogRefresh()

  const logout = useMutation({
    mutationFn: () => fetchJson("/auth/logout", { method: "POST" }),
    onSuccess: async () => {
      queryClient.clear()
      navigate("/login", { replace: true })
    },
  })

  const showSettingsNav = Boolean(user?.is_admin && !user?.setup_mode)

  const navLinkClass = (path: string) => {
    const active =
      location.pathname === path || location.pathname.startsWith(`${path}/`)

    return cn(
      "wof-nav-link text-sm",
      active
        ? "wof-nav-link-active font-medium"
        : "text-muted-foreground hover:text-foreground",
    )
  }

  const navLinks = (
    <>
      <Link to="/browse" className={navLinkClass("/browse")}>
        Library
      </Link>
      <Link to="/playlists" className={navLinkClass("/playlists")}>
        Playlists
      </Link>
      {showSettingsNav ? (
        <Link to="/settings" className={navLinkClass("/settings")}>
          Settings
        </Link>
      ) : null}
    </>
  )

  return (
    <div className="flex min-h-svh flex-col">
      <header className="border-b border-border/70 bg-card/50 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-2 sm:py-3">
          <div className="flex min-w-0 items-center gap-3 sm:gap-4">
            <Link
              to="/"
              className="shrink-0 rounded-lg transition-opacity hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <BrandMark compact variant="header" />
            </Link>
            <Separator orientation="vertical" className="hidden h-14 sm:block md:h-16" />
            <nav
              aria-label="Main"
              className="hidden items-center gap-5 sm:flex"
            >
              {navLinks}
            </nav>
          </div>
          <div className="flex items-center gap-2">
            {user?.setup_mode ? (
              <Button variant="outline" size="sm" render={<Link to="/setup/admin" />}>
                Admin setup
              </Button>
            ) : null}
            <ThemeToggle />
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={logout.isPending}
              onClick={() => logout.mutate()}
            >
              <LogOutIcon />
              Log out
            </Button>
          </div>
        </div>
        <nav
          aria-label="Main"
          className="mx-auto flex max-w-6xl gap-5 border-t border-border/60 px-4 py-2.5 sm:hidden"
        >
          {navLinks}
        </nav>
      </header>

      <main className="flex-1 px-4 py-6">
        <SetupModeGate />
        <Outlet />
      </main>
    </div>
  )
}

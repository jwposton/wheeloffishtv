import { useMutation, useQueryClient } from "@tanstack/react-query"
import { LogOutIcon } from "lucide-react"
import { Link, Navigate, Outlet, useLocation, useNavigate } from "react-router-dom"

import { fetchJson } from "@/api/client"
import { ThemeToggle } from "@/components/layout/ThemeToggle"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { useAuth } from "@/hooks/useAuth"

function SetupModeGate() {
  const { user } = useAuth()
  const location = useLocation()

  if (!user?.setup_mode) {
    return null
  }

  const allowedPaths = ["/setup/admin"]
  if (user.libraries_scoped) {
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

  const logout = useMutation({
    mutationFn: () => fetchJson("/auth/logout", { method: "POST" }),
    onSuccess: async () => {
      queryClient.clear()
      navigate("/login", { replace: true })
    },
  })

  const navLinkClass = (path: string) =>
    location.pathname === path || location.pathname.startsWith(`${path}/`)
      ? "text-foreground font-medium"
      : "text-muted-foreground hover:text-foreground"

  return (
    <div className="flex min-h-svh flex-col">
      <header className="border-b">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3">
          <div className="flex items-center gap-4">
            <Link to="/" className="font-semibold tracking-tight">
              Wheel of Fish TV
            </Link>
            <Separator orientation="vertical" className="hidden h-5 sm:block" />
            <nav className="hidden items-center gap-4 text-sm sm:flex">
              <Link to="/browse" className={navLinkClass("/browse")}>
                Browse
              </Link>
              <Link to="/settings" className={navLinkClass("/settings")}>
                Settings
              </Link>
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
      </header>

      <main className="flex-1 px-4 py-6">
        <SetupModeGate />
        <Outlet />
      </main>
    </div>
  )
}

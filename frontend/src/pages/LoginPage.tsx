import { useQuery } from "@tanstack/react-query"
import { useEffect } from "react"
import { Navigate, useSearchParams } from "react-router-dom"

import { fetchJson } from "@/api/client"
import type { ProvidersMetaResponse } from "@/api/types"
import { JellyfinLoginForm } from "@/components/auth/JellyfinLoginForm"
import { PlexLoginButton } from "@/components/auth/PlexLoginButton"
import { BrandMark } from "@/components/brand/BrandMark"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { ThemeToggle } from "@/components/layout/ThemeToggle"
import { VersionBadge } from "@/components/layout/VersionBadge"
import { useAuth } from "@/hooks/useAuth"

export function LoginPage() {
  const { user, isLoading: authLoading } = useAuth()
  const [searchParams] = useSearchParams()

  useEffect(() => {
    void fetchJson("/auth/bootstrap-session", { method: "POST" })
  }, [])

  const providersQuery = useQuery({
    queryKey: ["meta", "providers"],
    queryFn: () => fetchJson<ProvidersMetaResponse>("/meta/providers"),
  })

  if (authLoading) {
    return (
      <main className="mx-auto flex min-h-svh max-w-md flex-col justify-center gap-4 p-8">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-40 w-full" />
      </main>
    )
  }

  if (user?.has_media_link) {
    const returnUrl = searchParams.get("returnUrl")
    return (
      <Navigate
        to={returnUrl ? decodeURIComponent(returnUrl) : "/browse"}
        replace
      />
    )
  }

  const provider = providersQuery.data?.provider

  return (
    <main className="mx-auto flex min-h-svh max-w-md flex-col justify-center gap-6 p-8">
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-3">
          <BrandMark variant="hero" className="max-w-xs" />
          <p className="text-sm text-muted-foreground">
            Sign in with your household media server account.
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <VersionBadge />
          <ThemeToggle />
        </div>
      </div>

      <Card className="wof-panel">
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
          <CardDescription>
            Use your household media server account. Server connection is
            configured by your operator — nothing to set up here.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {providersQuery.isLoading ? (
            <div className="flex flex-col gap-3">
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-4 w-full" />
            </div>
          ) : providersQuery.isError ? (
            <p className="text-destructive text-sm">
              Could not load sign-in options. Refresh and try again.
            </p>
          ) : provider === "plex" ? (
            <PlexLoginButton />
          ) : provider === "jellyfin" ? (
            <JellyfinLoginForm />
          ) : (
            <p className="text-destructive text-sm">
              Unknown media provider configured for this install.
            </p>
          )}
        </CardContent>
      </Card>
    </main>
  )
}

import { Navigate, Outlet, useLocation } from "react-router-dom"

import { ApiError } from "@/api/client"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/hooks/useAuth"

export function ProtectedRoute() {
  const { user, isLoading, isError, error } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="flex min-h-svh flex-col gap-4 p-8">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-full max-w-md" />
        <Skeleton className="h-4 w-full max-w-sm" />
      </div>
    )
  }

  const isUnauthorized =
    !user ||
    isError ||
    (error instanceof ApiError && error.status === 401)

  if (isUnauthorized) {
    const returnUrl = encodeURIComponent(
      `${location.pathname}${location.search}`,
    )
    return <Navigate to={`/login?returnUrl=${returnUrl}`} replace />
  }

  return <Outlet />
}

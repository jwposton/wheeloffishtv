import { Navigate, Outlet, useLocation } from "react-router-dom"

import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/hooks/useAuth"

export function AdminRoute() {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4 p-8">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-full max-w-md" />
      </div>
    )
  }

  if (!user?.is_admin || user.setup_mode) {
    return <Navigate to="/" replace state={{ from: location }} />
  }

  return <Outlet />
}

import { Navigate, Outlet } from "react-router-dom"

import { HoldingPage } from "@/pages/HoldingPage"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/hooks/useAuth"

export function LibraryScopeGuard() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4 p-8">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-full max-w-md" />
      </div>
    )
  }

  const canBrowse =
    user?.libraries_scoped ||
    user?.install_libraries_configured ||
    (Boolean(user?.has_media_link) && !user?.is_admin)

  if (canBrowse) {
    return <Outlet />
  }

  if (user?.is_admin && !user.setup_mode) {
    return <Navigate to="/setup/libraries" replace />
  }

  return <HoldingPage />
}

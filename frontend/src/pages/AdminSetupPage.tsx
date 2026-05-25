import { Navigate } from "react-router-dom"

import { AdminSetupPanel } from "@/components/auth/AdminSetupPanel"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/hooks/useAuth"

export function AdminSetupPage() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="mx-auto flex max-w-2xl flex-col gap-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (!user.setup_mode) {
    return <Navigate to="/" replace />
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <div>
        <h2 className="text-xl font-semibold">Operator admin setup</h2>
        <p className="text-muted-foreground text-sm">
          Until an admin user ID is configured, library scoping and other admin
          actions stay disabled.
        </p>
      </div>
      <AdminSetupPanel user={user} />
    </div>
  )
}

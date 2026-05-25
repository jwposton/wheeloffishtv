import { Link } from "react-router-dom"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/hooks/useAuth"

export function SettingsPage() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="mx-auto flex max-w-2xl flex-col gap-4">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  const connection = user?.connection

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <div>
        <h2 className="text-xl font-semibold">Settings</h2>
        <p className="text-muted-foreground text-sm">
          Household preferences and connection details.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Connection</CardTitle>
          <CardDescription>
            Read-only view of the media server configured at install time.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {connection ? (
            <p className="text-sm">
              Connected to{" "}
              <span className="font-medium">{connection.base_url}</span> (
              {connection.display_name})
            </p>
          ) : (
            <p className="text-muted-foreground text-sm">
              No connection details available.
            </p>
          )}
          <p className="text-muted-foreground text-sm">
            To change the server URL or provider, edit your{" "}
            <code className="text-foreground">.env</code> file and restart the
            container.
          </p>
        </CardContent>
      </Card>

      {user?.is_admin && !user.setup_mode ? (
        <Card>
          <CardHeader>
            <CardTitle>Libraries</CardTitle>
            <CardDescription>
              Choose which TV libraries appear in Browse for your household.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link
              to="/settings/libraries"
              className="text-primary text-sm font-medium hover:underline"
            >
              Manage library scope →
            </Link>
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}

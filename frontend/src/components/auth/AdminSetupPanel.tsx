import { CheckIcon, CopyIcon } from "lucide-react"
import { useState } from "react"
import { Link } from "react-router-dom"

import type { AuthMeResponse } from "@/api/types"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

interface AdminSetupPanelProps {
  user: AuthMeResponse
}

export function AdminSetupPanel({ user }: AdminSetupPanelProps) {
  const [copied, setCopied] = useState(false)

  async function copyProviderUserId() {
    await navigator.clipboard.writeText(user.provider_user_id)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Admin setup required</CardTitle>
        <CardDescription>
          Copy your media-server user ID into the operator environment, then
          restart the container.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">Provider user ID</p>
          <div className="flex items-center gap-2">
            <code className="bg-muted flex-1 rounded-md px-3 py-2 font-mono text-sm break-all">
              {user.provider_user_id}
            </code>
            <Button
              type="button"
              variant="outline"
              size="icon"
              aria-label="Copy provider user ID"
              onClick={() => {
                void copyProviderUserId()
              }}
            >
              {copied ? <CheckIcon /> : <CopyIcon />}
            </Button>
          </div>
        </div>

        {user.provider_username ? (
          <div className="flex flex-col gap-1">
            <p className="text-sm font-medium">Signed in as</p>
            <p className="text-muted-foreground text-sm">
              {user.provider_username}
            </p>
          </div>
        ) : null}

        <ol className="text-muted-foreground list-decimal space-y-2 pl-5 text-sm">
          <li>
            Add{" "}
            <code className="text-foreground">
              WOF_ADMIN_PROVIDER_USER_ID={user.provider_user_id}
            </code>{" "}
            to your <code className="text-foreground">.env</code> file.
          </li>
          <li>Restart the Wheel of Fish container.</li>
          <li>Sign in again after restart to unlock admin actions.</li>
        </ol>

        {user.libraries_scoped ? (
          <Button variant="outline" nativeButton={false} render={<Link to="/browse" />}>
            Continue to browse
          </Button>
        ) : null}
      </CardContent>
    </Card>
  )
}

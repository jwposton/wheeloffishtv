import { useMutation } from "@tanstack/react-query"
import { Loader2Icon } from "lucide-react"
import { useState } from "react"

import { ApiError, fetchJson } from "@/api/client"
import type { PlexOAuthStartResponse } from "@/api/types"
import { Button } from "@/components/ui/button"

export function PlexLoginButton() {
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const startOAuth = useMutation({
    mutationFn: () =>
      fetchJson<PlexOAuthStartResponse>("/connections/plex/oauth/start", {
        method: "POST",
        body: JSON.stringify({}),
      }),
    onSuccess: (data) => {
      window.location.assign(data.auth_url)
    },
    onError: (error) => {
      if (error instanceof ApiError) {
        setErrorMessage("Could not start Plex sign-in. Try again.")
      } else {
        setErrorMessage("Could not start Plex sign-in. Try again.")
      }
    },
  })

  return (
    <div className="flex flex-col gap-2">
      <Button
        type="button"
        size="lg"
        className="w-full"
        disabled={startOAuth.isPending}
        onClick={() => {
          setErrorMessage(null)
          startOAuth.mutate()
        }}
      >
        {startOAuth.isPending ? (
          <>
            <Loader2Icon className="animate-spin" />
            Connecting…
          </>
        ) : (
          "Sign in with Plex"
        )}
      </Button>
      {errorMessage ? (
        <p className="text-destructive text-sm">{errorMessage}</p>
      ) : null}
      <p className="text-muted-foreground text-xs">
        Opens Plex in this window. Return here after approving access.
      </p>
    </div>
  )
}

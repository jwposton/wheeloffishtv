import { useMutation } from "@tanstack/react-query"
import { Loader2Icon } from "lucide-react"
import { useState, type FormEvent } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"

import { ApiError, fetchJson } from "@/api/client"
import type { JellyfinAuthResponse } from "@/api/types"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { authQueryKey } from "@/hooks/useAuth"
import { useQueryClient } from "@tanstack/react-query"

export function JellyfinLoginForm() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const login = useMutation({
    mutationFn: (credentials: { username: string; password: string }) =>
      fetchJson<JellyfinAuthResponse>("/connections/jellyfin/auth", {
        method: "POST",
        body: JSON.stringify(credentials),
      }),
    onSuccess: async () => {
      setPassword("")
      await queryClient.invalidateQueries({ queryKey: authQueryKey })
      const returnUrl = searchParams.get("returnUrl")
      navigate(returnUrl ? decodeURIComponent(returnUrl) : "/", { replace: true })
    },
    onError: (error) => {
      setPassword("")
      if (error instanceof ApiError && error.status === 422) {
        setErrorMessage("Invalid Jellyfin username or password.")
      } else {
        setErrorMessage("Could not sign in to Jellyfin. Try again.")
      }
    },
  })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage(null)
    login.mutate({ username, password })
    setPassword("")
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
      <p className="text-muted-foreground text-sm">
        Sign in with the same username and password you use on your Jellyfin
        server. Credentials are sent to your Wheel of Fish instance only.
      </p>
      <div className="flex flex-col gap-2">
        <Label htmlFor="jellyfin-username">Username</Label>
        <Input
          id="jellyfin-username"
          name="username"
          autoComplete="username"
          required
          value={username}
          onChange={(event) => setUsername(event.target.value)}
        />
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor="jellyfin-password">Password</Label>
        <Input
          id="jellyfin-password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
      </div>
      {errorMessage ? (
        <p className="text-destructive text-sm">{errorMessage}</p>
      ) : null}
      <Button type="submit" size="lg" disabled={login.isPending}>
        {login.isPending ? (
          <>
            <Loader2Icon className="animate-spin" />
            Signing in…
          </>
        ) : (
          "Sign in with Jellyfin"
        )}
      </Button>
    </form>
  )
}

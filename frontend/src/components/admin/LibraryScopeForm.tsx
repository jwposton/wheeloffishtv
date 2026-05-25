import { Loader2Icon } from "lucide-react"
import { useEffect, useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/hooks/useAuth"
import { useLibraryScope } from "@/hooks/useLibraryScope"

interface LibraryScopeFormProps {
  onSaveSuccess?: (selectedCount: number) => void
}

export function LibraryScopeForm({ onSaveSuccess }: LibraryScopeFormProps) {
  const { user } = useAuth()
  const connectionId = user?.connection?.id
  const { libraries, isLoading, saveScope, formatSaveError } =
    useLibraryScope(connectionId)

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [initialized, setInitialized] = useState(false)

  useEffect(() => {
    if (libraries.length > 0 && !initialized) {
      setSelectedIds(
        new Set(
          libraries.filter((library) => library.in_scope).map((l) => l.native_id),
        ),
      )
      setInitialized(true)
    }
  }, [libraries, initialized])

  if (!user?.is_admin || user.setup_mode) {
    return null
  }

  function toggleLibrary(nativeId: string, checked: boolean) {
    setSelectedIds((current) => {
      const next = new Set(current)
      if (checked) {
        next.add(nativeId)
      } else {
        next.delete(nativeId)
      }
      return next
    })
  }

  function handleSave() {
    saveScope.mutate(
      { in_scope_library_native_ids: [...selectedIds] },
      {
        onSuccess: () => {
          const count = selectedIds.size
          toast.success(
            count > 0
              ? `Saved ${count} ${count === 1 ? "library" : "libraries"} in scope.`
              : "Library scope saved.",
          )
          onSaveSuccess?.(count)
        },
        onError: (error) => {
          toast.error(formatSaveError(error))
        },
      },
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>TV libraries in scope</CardTitle>
        <CardDescription>
          Choose which TV libraries appear in Browse for everyone in your
          household. Only selected libraries are synced and searchable.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {isLoading ? (
          <div className="flex flex-col gap-3">
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-5 w-2/3" />
          </div>
        ) : libraries.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            No TV libraries found on your media server yet. Run a catalog sync
            or check your server libraries, then refresh this page.
          </p>
        ) : (
          <ul className="flex flex-col gap-3">
            {libraries.map((library) => (
              <li key={library.native_id} className="flex items-center gap-3">
                <Checkbox
                  id={`library-${library.native_id}`}
                  checked={selectedIds.has(library.native_id)}
                  onCheckedChange={(checked) =>
                    toggleLibrary(library.native_id, checked === true)
                  }
                />
                <Label
                  htmlFor={`library-${library.native_id}`}
                  className="cursor-pointer font-normal"
                >
                  {library.title}
                </Label>
              </li>
            ))}
          </ul>
        )}

        <Button
          type="button"
          disabled={saveScope.isPending || isLoading || libraries.length === 0}
          onClick={handleSave}
        >
          {saveScope.isPending ? (
            <>
              <Loader2Icon className="animate-spin" />
              Saving…
            </>
          ) : (
            "Save library scope"
          )}
        </Button>
      </CardContent>
    </Card>
  )
}

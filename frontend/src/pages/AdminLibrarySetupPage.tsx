import { useState } from "react"
import { Link } from "react-router-dom"

import { LibraryScopeForm } from "@/components/admin/LibraryScopeForm"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/hooks/useAuth"

export function AdminLibrarySetupPage() {
  const { user, isLoading } = useAuth()
  const [savedWithSelection, setSavedWithSelection] = useState(
    () => user?.libraries_scoped ?? false,
  )

  if (isLoading) {
    return (
      <div className="mx-auto flex max-w-2xl flex-col gap-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <div>
        <h2 className="text-xl font-semibold">Pick TV libraries</h2>
        <p className="text-muted-foreground text-sm">
          Before anyone can browse, choose which TV libraries belong in your
          household catalog. You can change this later under Settings →
          Libraries.
        </p>
      </div>

      <ol className="text-muted-foreground list-decimal space-y-1 pl-5 text-sm">
        <li>Select one or more TV libraries from your media server.</li>
        <li>Save your selections.</li>
        <li>Continue to Browse when ready.</li>
      </ol>

      <LibraryScopeForm
        onSaveSuccess={(selectedCount) => {
          setSavedWithSelection(selectedCount > 0)
        }}
      />

      <Button
        nativeButton={false}
        disabled={!savedWithSelection}
        render={<Link to="/browse" />}
      >
        Continue to Browse
      </Button>
    </div>
  )
}

import { LibraryScopeForm } from "@/components/admin/LibraryScopeForm"

export function SettingsLibrariesPage() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <div>
        <h2 className="text-xl font-semibold">Libraries</h2>
        <p className="text-muted-foreground text-sm">
          Update which TV libraries are in scope for Browse. Changes apply to
          everyone in your household.
        </p>
      </div>

      <LibraryScopeForm />
    </div>
  )
}

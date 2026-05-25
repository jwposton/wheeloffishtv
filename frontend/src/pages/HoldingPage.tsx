export function HoldingPage() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-3 py-8">
      <h2 className="text-xl font-semibold">Setup in progress</h2>
      <p className="text-muted-foreground text-sm">
        Admin hasn&apos;t finished setup. Your operator needs to pick which TV
        libraries are in scope before Browse is available.
      </p>
      <p className="text-muted-foreground text-sm">
        Check back after library scope is configured.
      </p>
    </div>
  )
}

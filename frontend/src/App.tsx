import { ThemeToggle } from "@/components/layout/ThemeToggle"

function App() {
  return (
    <main className="mx-auto flex min-h-svh max-w-3xl flex-col items-center justify-center gap-6 p-8">
      <div className="flex w-full items-center justify-between gap-4">
        <h1 className="text-3xl font-semibold tracking-tight">Wheel of Fish TV</h1>
        <ThemeToggle />
      </div>
      <p className="text-muted-foreground text-center text-sm">
        Operator SPA shell — auth and browse views ship in upcoming plans.
      </p>
    </main>
  )
}

export default App

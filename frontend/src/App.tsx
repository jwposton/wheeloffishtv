import { Navigate, Route, Routes } from "react-router-dom"

import { AppShell } from "@/components/layout/AppShell"
import { AdminLibrarySetupPage } from "@/pages/AdminLibrarySetupPage"
import { AdminSetupPage } from "@/pages/AdminSetupPage"
import { BrowsePage } from "@/pages/BrowsePage"
import { LoginPage } from "@/pages/LoginPage"
import { SettingsLibrariesPage } from "@/pages/SettingsLibrariesPage"
import { SettingsPage } from "@/pages/SettingsPage"
import { AdminRoute } from "@/routes/AdminRoute"
import { LibraryScopeGuard } from "@/routes/LibraryScopeGuard"
import { ProtectedRoute } from "@/routes/ProtectedRoute"

function HomePage() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-2">
      <h2 className="text-xl font-semibold">Home</h2>
      <p className="text-muted-foreground text-sm">
        Series browse and playlists ship in upcoming plans.
      </p>
    </div>
  )
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<HomePage />} />
          <Route element={<LibraryScopeGuard />}>
            <Route path="/browse" element={<BrowsePage />} />
          </Route>
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/setup/admin" element={<AdminSetupPage />} />
          <Route element={<AdminRoute />}>
            <Route path="/setup/libraries" element={<AdminLibrarySetupPage />} />
            <Route path="/settings/libraries" element={<SettingsLibrariesPage />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App

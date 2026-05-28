import { Navigate, Route, Routes } from "react-router-dom"

import { AppShell } from "@/components/layout/AppShell"
import { WatchStateProgressBanner } from "@/components/ui/watch-state-progress"
import { BrowsePage } from "@/pages/BrowsePage"
import { SeriesDetailPage } from "@/pages/SeriesDetailPage"
import { LoginPage } from "@/pages/LoginPage"
import { PlaylistsPage } from "@/pages/PlaylistsPage"
import { PlaylistFormPage } from "@/pages/PlaylistFormPage"
import { PlaylistDetailPage } from "@/pages/PlaylistDetailPage"
import { SettingsLibrariesPage } from "@/pages/SettingsLibrariesPage"
import { SettingsPage } from "@/pages/SettingsPage"
import { LibraryScopeGuard } from "@/routes/LibraryScopeGuard"
import { PlaylistEditRedirect } from "@/routes/PlaylistEditRedirect"
import { ProtectedRoute } from "@/routes/ProtectedRoute"

import { HomePage } from "@/pages/HomePage"

function App() {
  return (
    <>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/settings/libraries" element={<SettingsLibrariesPage />} />
            <Route element={<LibraryScopeGuard />}>
              <Route path="/browse" element={<BrowsePage />} />
              <Route path="/series" element={<SeriesDetailPage />} />
              <Route path="/series/:seriesId" element={<SeriesDetailPage />} />
              <Route path="/playlists" element={<PlaylistsPage />} />
              <Route path="/playlists/new" element={<PlaylistFormPage />} />
              <Route path="/playlists/:id/edit" element={<PlaylistEditRedirect />} />
              <Route path="/playlists/:id" element={<PlaylistDetailPage />} />
            </Route>
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <WatchStateProgressBanner />
    </>
  )
}

export default App

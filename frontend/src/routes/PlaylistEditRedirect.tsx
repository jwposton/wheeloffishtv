import { Navigate, useParams } from "react-router-dom"

/** Legacy `/playlists/:id/edit` URLs → unified playlist page. */
export function PlaylistEditRedirect() {
  const { id } = useParams<{ id: string }>()
  if (!id) {
    return <Navigate to="/playlists" replace />
  }
  return <Navigate to={`/playlists/${id}`} replace />
}

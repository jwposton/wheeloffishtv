import { Link } from "react-router-dom"

import { BrandMark } from "@/components/brand/BrandMark"
import { Button } from "@/components/ui/button"

export function HomePage() {
  return (
    <div className="mx-auto flex max-w-3xl flex-col items-center gap-8 py-4">
      <BrandMark variant="hero" className="max-w-xl" />

      <div className="wof-panel flex w-full max-w-xl flex-col items-center gap-5 px-6 py-8 text-center">
        <p className="text-base leading-relaxed text-foreground">
          Build mixed TV playlists from your Plex or Jellyfin library. Add shows,
          set how often they refresh, and rebuild when you want a new mix.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Button render={<Link to="/browse" />}>Browse library</Button>
          <Button variant="outline" render={<Link to="/playlists" />}>
            My playlists
          </Button>
        </div>
      </div>
    </div>
  )
}

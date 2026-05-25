import type { Ref } from "react"

import type { Series, SeriesProviderMetadata } from "@/api/types"
import { SeriesPoster } from "@/components/browse/SeriesPoster"
import { Badge } from "@/components/ui/badge"

function metadataFor(series: Series): SeriesProviderMetadata {
  return series.provider_metadata ?? {}
}

interface SeriesMetadataHeroProps {
  series: Series
  headingRef?: Ref<HTMLHeadingElement>
}

export function SeriesMetadataHero({ series, headingRef }: SeriesMetadataHeroProps) {
  const metadata = metadataFor(series)
  const genres = metadata.genres?.filter(Boolean) ?? []

  return (
    <div className="flex flex-col gap-4 md:flex-row md:gap-6">
      <div className="aspect-[2/3] w-40 shrink-0 overflow-hidden rounded-md border bg-white">
        <SeriesPoster title={series.title} thumbUrl={series.thumb_url} compact />
      </div>
      <div className="flex min-w-0 flex-1 flex-col gap-2">
        <h2
          ref={headingRef}
          tabIndex={-1}
          className="text-2xl font-semibold outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          {series.title}
        </h2>
        {series.year ? (
          <p className="text-muted-foreground text-sm">{series.year}</p>
        ) : null}
        {metadata.contentRating || genres.length > 0 ? (
          <div className="flex flex-wrap items-center gap-2">
            {metadata.contentRating ? (
              <Badge variant="outline" className="text-xs">
                {metadata.contentRating}
              </Badge>
            ) : null}
            {genres.map((genre) => (
              <Badge key={genre} variant="secondary">
                {genre}
              </Badge>
            ))}
          </div>
        ) : null}
        {metadata.studio ? (
          <p className="text-muted-foreground text-sm">{metadata.studio}</p>
        ) : null}
        {metadata.summary ? (
          <p className="line-clamp-4 text-sm">{metadata.summary}</p>
        ) : null}
      </div>
    </div>
  )
}

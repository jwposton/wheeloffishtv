import heroLogo from "@/assets/brand/logo-hero.png"
import headerLogo from "@/assets/brand/logo-header.png"

/** Bundled PNGs — imported so Vite emits /assets/* URLs (avoids ad-blockers on /brand/* paths). */
export const brandAssets = {
  heroLogoSrc: heroLogo,
  headerLogoSrc: headerLogo,
  wheelIconSrc: null as string | null,
} as const

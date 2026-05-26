# Brand assets (production)

| File | Use |
|------|-----|
| `logo-hero.png` | Home + login hero (`brandAssets.heroLogoSrc`) |
| `logo-header.png` | Title bar (`brandAssets.headerLogoSrc`) |

Imported in `brandAssets.ts` so Vite bundles them under `/assets/` (plain `/brand/*.png` URLs are often blocked by ad/privacy extensions).

Source artwork:
- `reference_assets/main_logo.png` → `logo-hero.png`
- `reference_assets/header.png` → `logo-header.png`

Typography + SVG wheel remain the fallback when a path in `brandAssets.ts` is `null`.

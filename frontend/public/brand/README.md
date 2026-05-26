# Brand assets (production)

| File | Use |
|------|-----|
| `logo-hero.png` | Home + login hero (`brandAssets.heroLogoSrc`) |
| `logo-header.png` | Title bar (`brandAssets.headerLogoSrc`) — from `reference_assets/header.png` |
| `wheel-icon.png` | Optional rebuild wheel override — SVG used until set |

Source artwork:
- `reference_assets/main_logo.png` → `logo-hero.png`
- `reference_assets/header.png` → `logo-header.png`

Typography + SVG wheel remain the fallback when a path in `brandAssets.ts` is `null`.

## Reference only

`reference_assets/02.png` is the style guide — not shipped directly.  
`scripts/extract-brand-assets.py` writes preview crops to `_reference-preview/` for design comparison.

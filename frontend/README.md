# Wheel of Fish TV — Frontend

React operator SPA for Wheel of Fish TV (Phase 3).

## Stack

- Vite + React + TypeScript
- Tailwind CSS v4 + shadcn/ui
- TanStack Query + React Router
- next-themes (light/dark, system default)

## Development

Start the backend on port 8000, then:

```bash
npm install
npm run dev
```

The dev server proxies `/api` to `http://localhost:8000`.

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Vite dev server (default port 5173) |
| `npm run build` | Production build to `dist/` |
| `npm run test` | Vitest unit/component tests |
| `npm run preview` | Preview production build locally |

## Production

The backend Docker image builds this frontend and serves `dist/` via `SPAStaticFiles` at `/`.

For local backend testing without Docker, build the frontend and point the backend at the output:

```bash
npm run build
# optional: SPA_DIST_DIR=../frontend/dist when running the backend locally
```

## API client

`src/api/client.ts` calls `/api/v1` with `credentials: "include"` for session cookies.

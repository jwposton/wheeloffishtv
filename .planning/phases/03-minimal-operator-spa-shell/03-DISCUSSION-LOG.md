# Phase 3: Minimal operator SPA shell - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-25
**Phase:** 3-minimal-operator-spa-shell
**Areas discussed:** Local auth & admin bootstrap, Connection & onboarding, Series browser UX, Design system kickoff

---

## Local auth & admin bootstrap

| Option | Description | Selected |
|--------|-------------|----------|
| Local username/password accounts | Env-seeded or open registration with separate app login | |
| Media-server OAuth only | Sign in = Plex or Jellyfin OAuth; no standalone passwords | ✓ |
| Both providers on one install | Plex and Jellyfin simultaneously | |
| Single provider per install | Operator picks `WOF_PROVIDER=plex` or `jellyfin` | ✓ |

**User's choice:** Media-server OAuth as the only login; one provider per install; admin via `WOF_ADMIN_PROVIDER_USER_ID` discovered on first-login setup screen (copy ID → edit env → restart). Setup mode before admin env: browse allowed, admin actions blocked. `WOF_SESSION_DAYS` unset = long-lived session.

**Notes:** User rejected standalone local accounts — without media-server login there is no app account. Apple Sign-In to Plex makes username unreliable; provider user ID is primary. Admin username/email match optional secondary only.

---

## Connection & media-link onboarding

| Option | Description | Selected |
|--------|-------------|----------|
| Hybrid env + UI connection config | Env seeds URL; wizard can change; DB canonical after setup | |
| Env-only connection config | URL/provider/SSL in `.env` only; DB syncs on boot | ✓ |
| Library scope in env only | `WOF_SCOPED_LIBRARY_IDS` | |
| Library scope in UI | Admin checkboxes; maintained in app | ✓ |
| Login wall | No server setup wizard; env configured before use | ✓ |
| First-run admin library checklist + Settings | Both forced step and permanent page | ✓ |
| Non-admin holding page | Block browse until admin scopes libraries | ✓ |

**User's choice:** Env-only for connection (version controlled, no duplicate definition). Library scope is the exception — UI-managed. Login wall only. Admin gets first-run library checklist plus Settings → Libraries. Non-admins see holding page if scope not set.

**Notes:** User explicitly rejected hybrid after learning DB would win over stale env — wanted single source of truth outside container for connection config.

---

## Series browser UX

| Option | Description | Selected |
|--------|-------------|----------|
| Poster grid only | Cards with artwork | |
| Grid + list toggle | Default grid; compact list option; persisted | ✓ |
| Pagination controls | Prev/next pages | |
| Infinite scroll | Load next page on scroll | ✓ |
| Full-page spinner during sync | Block until sync completes | |
| Top banner + stale list | Non-blocking sync indicator | ✓ |
| List only (no detail) | Browse/search only | |
| Detail with up-next preview | Resume/on-deck from API | ✓ |

**User's choice:** Grid + list toggle; infinite scroll; debounced title search (substring, not fuzzy); top banner during sync; detail drawer/page with up-next episode preview.

**Notes:** User asked whether search is fuzzy — clarified API uses `ILIKE` substring match. User assumed detail shows on-deck — confirmed via `GET …/series/{id}/resume` and Phase 2 hybrid resume rule.

---

## Design system kickoff

| Option | Description | Selected |
|--------|-------------|----------|
| shadcn/ui + Radix + Tailwind | Recommended for modern responsive a11y baseline | ✓ (advice accepted) |
| Light only until Phase 7 | Defer dark mode | |
| Light + dark from day one | Toggle + prefers-color-scheme | ✓ |
| Storybook stub in Phase 3 | Component catalog / visual regression prep | |
| Skip Storybook Phase 3 | Defer to Phase 7 | ✓ (advice accepted) |
| Clean utilitarian tone | Neutral functional shell; polish later | ✓ |

**User's choice:** Accept shadcn/ui stack recommendation; dark + light themes day one; utilitarian visual tone Phase 3 (adjustable via tokens later); skip Storybook until Phase 7 after explanation.

**Notes:** User asked if utilitarian tone is easy to change later — yes, via Tailwind theme tokens and CSS variables. Storybook explained as isolated component workshop for docs/testing/visual regression — not needed for Phase 3 MVP shell.

---

## Claude's Discretion

- Env var naming for connection fields, session cookie details, SPA static serve mechanics, drawer vs routed detail page, search debounce timing.

## Deferred Ideas

- Hybrid env/UI connection configuration (rejected)
- Dual Plex + Jellyfin single install (superseded)
- Fuzzy search, Storybook CI, cinematic Plex-like polish (Phase 7 or later)

# JobPilot Frontend — Progress

> ## ⚠️ Design reference warning
>
> **`frontend/UI Design/` screenshots and HTML are desktop-only Stitch exports (1440px mockups).**  
> They are **visual reference**, not copy-paste targets.
>
> We are building a **responsive website** that works on phone, tablet, and desktop.  
> Do **not** ship fixed 2560px layouts, hard-coded pixel widths, or desktop-only navigation.
>
> **Use from Stitch:** colors, typography, component style, content hierarchy, tone.  
> **Adapt for the web:** layout, breakpoints, touch targets, navigation pattern, spacing.

**Phase 1 scope (locked):** Welcome, Profile, Search only.  
**Backend:** FastAPI profile API at `localhost:8000` (Vite proxies `/api`).  
**Design tokens:** `.stitch/DESIGN.md` (palette + components; layout rules overridden below)

---

## Status legend

| Mark | Meaning |
|------|---------|
| `[x]` | **Complete** — done and meets web UI rules + design intent |
| `[o]` | **In progress** — actively being built or reviewed |
| `[ ]` | **Not started** — not begun yet |

Update this file whenever an item changes state.

---

## Web UI rules (apply to every screen)

Universal website standards. Stitch desktop mocks must be **adapted**, not cloned.

### Responsive layout

| Breakpoint | Width | Shell behavior |
|------------|-------|----------------|
| Mobile | `< 640px` | No fixed sidebar. Top bar + hamburger or bottom nav. Full-width content, `16px` page padding |
| Tablet | `640px – 1023px` | Collapsed icon sidebar **or** drawer nav. Content uses full width minus gutters |
| Desktop | `≥ 1024px` | Persistent sidebar (~`240px`) + main area. Content `max-w-3xl` (`960px`) centered |

- Use **fluid widths** (`%`, `rem`, `max-w-*`) — never lock the app to `1440px`.
- Cards and forms: full width on mobile; `max-w-lg` / `max-w-xl` on larger screens where appropriate.
- Test at **375px** (phone), **768px** (tablet), **1280px** (desktop).

### Navigation

| Viewport | Pattern |
|----------|---------|
| Desktop | Left sidebar: Profile, Search, Applications (disabled Phase 1), Settings (Phase 2) |
| Mobile / tablet | Same links in **drawer** or **bottom tab bar**; disabled items still visible but greyed |
| All | Active route clearly indicated; disabled nav not clickable |

### Touch & interaction

- Minimum tap target: **44×44px** (buttons, nav items, chip remove).
- Visible **focus rings** for keyboard users (`focus-visible`).
- Hover states on desktop only; don’t rely on hover for critical info on mobile.
- Form inputs: **16px+ font size** on mobile to avoid iOS zoom-on-focus.

### Typography & spacing

- Keep **Inter** and token colors from `.stitch/DESIGN.md`.
- Scale headings down on mobile (e.g. `text-2xl` → `text-xl` for page titles).
- Vertical rhythm: `16px` / `24px` spacing scale; avoid cramped mobile layouts.

### Accessibility (WCAG-oriented)

| Rule | Requirement |
|------|-------------|
| Color contrast | Text ≥ 4.5:1; large text ≥ 3:1 |
| Semantics | One `<h1>` per page; labels tied to inputs; buttons vs links used correctly |
| Images / icons | Decorative icons `aria-hidden`; meaningful icons get `aria-label` |
| Forms | Errors announced; required fields marked; file upload has keyboard path |
| Motion | Respect `prefers-reduced-motion` |

### Performance & web basics

- Semantic HTML first; React components on top.
- Lazy-load routes when the app grows.
- `viewport` meta tag; no horizontal scroll on any breakpoint.
- Meta title + description per route (can be minimal in Phase 1).

### Stitch → website mapping

| Stitch (desktop reference) | Website implementation |
|----------------------------|-------------------------|
| Fixed 240px sidebar always visible | Sidebar desktop only; drawer/tabs on small screens |
| 960px centered column | `max-w-3xl mx-auto w-full px-4 sm:px-6` |
| Dense desktop forms | Stack fields vertically on mobile |
| Static screenshot text | Real state-driven copy (profile gate, counts) |

---

## Phase 1 — Locked screens

These three screens are **in scope**. Do not implement screens 4–8 until Phase 2.

| # | Screen | Route | React page | Design ref | Status |
|---|--------|-------|------------|------------|--------|
| 1 | Welcome / setup gate | `/` | `WelcomePage` | `UI Design/01-welcome/` | `[x]` |
| 2 | Profile setup | `/profile` | `ProfilePage` | `UI Design/02-profile/` | `[x]` |
| 3 | New search | `/search` | `SearchPage` | `UI Design/03-search/` | `[x]` |

---

## Foundation (required for all 3 screens)

| Task | Status |
|------|--------|
| Vite + React + TypeScript + Tailwind scaffold in `frontend/` | `[x]` |
| Tailwind breakpoints + design tokens (colors, fonts from `.stitch/DESIGN.md`) | `[x]` |
| Responsive `AppShell` — sidebar desktop / drawer or bottom nav mobile | `[x]` |
| React Router: `/`, `/profile`, `/search` | `[x]` |
| `ProfileContext` / store (CV, skills, projects) | `[x]` |
| Gmail strip | `[x]` removed — cancelled (LinkedIn/Indeed in-platform apply) |
| Profile gate: Search nav disabled until CV + ≥3 skills + ≥1 project | `[x]` |
| Mock API layer (localStorage; swap to backend later) | `[x]` removed — real backend API only |
| API fetch layer (FastAPI only; no localStorage mock) | `[x]` |
| Responsive + a11y pass on shell (focus, contrast, tap targets) | `[x]` |

---

## Screen 1 — Welcome (`/`)

| Task | Status |
|------|--------|
| Hero: logo, tagline, subtext | `[x]` |
| Setup checklist card (3 required rows) | `[x]` |
| Progress: “X of 3 required steps” | `[x]` |
| CTA: “Set up your profile” → `/profile` | `[x]` |
| Nav: Profile context; Search + Applications disabled | `[x]` |
| Responsive: stacked layout mobile; centered card desktop | `[x]` |

---

## Screen 2 — Profile (`/profile`)

| Task | Status |
|------|--------|
| Profile completeness progress bar | `[x]` |
| CV: drag-drop, filename, preview, re-upload | `[x]` |
| Skills: read-only chips from CV (`SkillsFromCv`) | `[x]` |
| Target roles: chip input (add/remove) | `[x]` |
| Projects: repeatable cards (name, description, add/remove) | `[x]` |
| GitHub: OAuth connect + repo import modal | `[x]` |
| Login / signup screens | `[ ]` next phase |
| Save profile (persist via API / SQLite) | `[x]` |
| Continue to Search (enabled when gate rules pass) | `[x]` |
| Responsive: single-column mobile; full-width cards | `[x]` |

---

## Screen 3 — Search (`/search`)

| Task | Status |
|------|--------|
| Route guard: redirect if profile incomplete | `[x]` |
| Target role dropdown from profile | `[x]` |
| Platform radio: LinkedIn / Indeed | `[x]` |
| Summary line from profile (resume · skills · projects) | `[x]` |
| Start search button (`POST /api/search` + status/jobs fetch) | `[x]` stub-wired |
| Nav: Search active | `[x]` |
| Responsive: form card full width mobile; constrained desktop | `[x]` |

---

## Phase 2 — Deferred (locked out)

Not in scope until backend + Phase 1 is complete. **Do not build yet.**

| # | Screen | Route | Status |
|---|--------|-------|--------|
| 4 | Run in progress | `/runs/:runId` | `[ ]` locked |
| 5 | Job results list | `/runs/:runId/jobs` | `[ ]` locked |
| 6 | Job detail HITL | `/jobs/:id` | `[ ]` locked |
| 7 | Applications | `/applications` | `[ ]` locked |
| 8 | Settings | `/settings` | `[ ]` locked |

---

## Summary

| Area | Complete | In progress | Not started |
|------|----------|-------------|-------------|
| Locked screens (1–3) | 3 / 3 | 0 / 3 | 0 / 3 |
| Foundation | 9 / 9 | 0 / 9 | 0 / 9 |

**Last updated:** 2026-06-29

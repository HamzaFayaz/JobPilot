## JobPilot overrides (authoritative)
- Colors, sidebar, cards: .stitch/DESIGN.md (primary #0D9488, sidebar #0F172A)
- Typography: Inter (not skill-recommended fonts)
- Layout/nav: frontend/progress.md
- Icons: @heroicons/react
- Skill output below is reference only for UX patterns, not brand tokens.

---

# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/jobpilot/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** JobPilot
**Generated:** 2026-06-29
**Category:** Job Board/Recruitment

---

## Global Rules (Stitch tokens — use these, not skill blues below)

| Role | Hex | Usage |
|------|-----|-------|
| Primary | `#0D9488` | Buttons, active nav, accents (teal) |
| Secondary | `#1E40AF` | Links, secondary actions |
| Background | `#F8FAFC` | Main content area |
| Sidebar | `#0F172A` | Left navigation |
| Text primary | `#0F172A` | Headings, body |
| Text secondary | `#64748B` | Captions, meta |
| Border | `#E2E8F0` | Cards, dividers |
| Success | `#16A34A` | Checkmarks, high scores |
| Warning | `#D97706` | HITL banner accent |
| Error | `#DC2626` | Errors, low scores |
| HITL banner bg | `#FEF3C7` | Amber banner |
| HITL banner text | `#92400E` | Amber banner text |
| Chip bg | `#CCFBF1` | Skill/role chips |

### Typography

- **Font:** Inter (400, 600, 700)
- **Google Fonts:** `https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap`

### Spacing & interaction (from ui-ux-pro-max)

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | `4px` | Tight gaps |
| `--space-sm` | `8px` | Icon gaps |
| `--space-md` | `16px` | Standard padding |
| `--space-lg` | `24px` | Section padding |
| `--space-xl` | `32px` | Large gaps |

- Hover transitions: 150–300ms
- Touch targets: ≥44px
- `cursor-pointer` on all clickables
- Visible `focus-visible` rings
- Respect `prefers-reduced-motion`

---

## Skill reference (UX patterns only — do NOT use skill colors/fonts)

See `design-system/jobpilot/MASTER.md` for full ui-ux-pro-max persist output.
Use its **checklists and anti-patterns** only. Stitch tokens above override skill palette.

### Pre-Delivery Checklist

- [ ] No emojis used as icons (Heroicons only)
- [ ] `cursor-pointer` on all clickable elements
- [ ] Hover states with smooth transitions (150-300ms)
- [ ] Light mode: text contrast 4.5:1 minimum
- [ ] Focus states visible for keyboard navigation
- [ ] `prefers-reduced-motion` respected
- [ ] Responsive: 375px, 768px, 1024px, 1280px
- [ ] No content hidden behind fixed navbars
- [ ] No horizontal scroll on mobile

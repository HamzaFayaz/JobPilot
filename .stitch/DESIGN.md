# JobPilot Design System

## Product

- **Name:** JobPilot
- **Tagline:** Your AI job application copilot
- **Audience:** Developers job searching who want AI-assisted applications with human approval before anything is sent
- **Platform:** Desktop web app (1440px)
- **Tone:** Professional, calm, trustworthy

## Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| Primary | `#0D9488` | Primary buttons, active nav, accents (teal) |
| Secondary | `#1E40AF` | Links, secondary actions (blue) |
| Background | `#F8FAFC` | Main content area |
| Sidebar | `#0F172A` | Left navigation sidebar |
| Text primary | `#0F172A` | Headings, body |
| Text secondary | `#64748B` | Captions, meta |
| Border | `#E2E8F0` | Cards, dividers |
| Success / score high | `#16A34A` | Match score 70+ |
| Warning / score mid | `#D97706` | Match score 50–69, HITL banner |
| Error / score low | `#DC2626` | Match score below 50 |
| HITL banner bg | `#FEF3C7` | Amber banner background |
| HITL banner text | `#92400E` | Amber banner text |

## Typography (Inter)

| Level | Size | Weight | Usage |
|-------|------|--------|-------|
| h1 | 32px | 700 | Page titles |
| h2 | 24px | 600 | Section headings |
| h3 | 18px | 600 | Card titles |
| h4 | 16px | 600 | Subsection labels |
| body | 14px | 400 | Default text |
| caption | 12px | 400 | Meta, helper text |

## Layout

- **Shell:** Fixed left sidebar (240px, dark `#0F172A`) + main content area (`#F8FAFC`)
- **Sidebar nav items:** Profile, Search, Applications, Settings (icon + label)
- **Active nav:** Teal accent bar + lighter text
- **Disabled nav:** Greyed out, reduced opacity
- **Content max-width:** 960px centered in main area
- **Card style:** White background, 8px border-radius, subtle shadow, 1px `#E2E8F0` border

## Components

### Buttons
- **Primary:** Teal `#0D9488` bg, white text, 8px radius, hover darken
- **Secondary:** White bg, teal border, teal text
- **Ghost:** Transparent, grey text, hover light grey bg
- **Disabled:** Grey bg `#CBD5E1`, grey text, no pointer

### Score Badge
- Large circular or pill badge with percentage
- Red `<50`, amber `50–69`, green `70+`

### Chips / Tags
- Rounded pill, light teal bg `#CCFBF1`, teal text
- Removable with × icon for skill input

### Progress Bar
- Track: `#E2E8F0`, fill: teal `#0D9488`
- Label above: "X of Y" or percentage

### Status Pills
- Running: blue bg, Done: green, Failed: red, Ready: teal

### Tabs
- Underline style, active tab teal underline + bold
- Inactive: grey text

### HITL Banner
- Amber background `#FEF3C7`, text `#92400E`
- Shield/check icon, text: "You approve before anything is sent"

### Empty States
- Centered icon, heading, subtext, optional CTA
- Muted grey illustration style

## Stitch Prompt Snippets

Use these phrases in screen prompts for consistency:

- "Left sidebar nav with dark background #0F172A, JobPilot logo at top"
- "Sidebar nav item active state with teal #0D9488 accent"
- "Disabled/greyed sidebar nav items for locked sections"
- "Match score badge green for 82%, amber for 65%, red for 42%"
- "Amber HITL banner: You approve before anything is sent"
- "White card on light grey #F8FAFC background with subtle shadow"
- "Teal primary button, professional calm developer tool aesthetic"
- "Inter font, clear typographic hierarchy"

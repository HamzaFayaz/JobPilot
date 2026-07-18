# Premcrest Van Sales

**Professional van sales & stock app for Premcrest Ltd** — field orders, stock checks, invoices, credit notes, end-of-day reporting, and van P&L analysis.

**Branch:** `main` · **v7 changes 1–13:** built · **Device QA:** [in progress](./docs/testing/MANUAL-TEST-CHECKLIST.md)

Full documentation: [`docs/README.md`](./docs/README.md) · Feature guide: [`docs/user-guides/FEATURES.md`](./docs/user-guides/FEATURES.md)

---

## What it does

- **Sales** — Customer → scan → checkout (Cash / Card / Credit, per-line discounts, optional returns) → A4 PDF + 70mm thermal receipt.
- **Credit notes** — Free stock and refunds (from **Orders** tab).
- **Van & stock** — Select van daily; route name + start mileage; stock per van; opening/closing shift checks.
- **End of day** — Daily PDFs/Excel, **cash overview**, shift mileage on reports, **OneDrive** upload (`Upload Data`).
- **Analysis manager** (admin) — Route analysis, **Van P&L** (daily + summary xlsx), generated reports library.
- **Products** — CSV import with **buy price Ex/Inc** (no manual add product).
- **Offline-first** — Orders, products, and customers on device (SQLite + AsyncStorage).

---

## Tabs

**Home** | **Orders** | **Products** | **Stock** | **EOD** | **Profile**

---

## Quick start (developers)

```bash
cd "E:\EARL OF ETON\Premcrest-Van-Sales"
npm install
npm start                    # Expo dev server
npx expo run:android         # Dev build (recommended — OneDrive, SQLite, MSAL)
```

First launch: **Setup** (rep name, phone, invoice sequence, machine number) → **Profile** (add/select van, route + mileage, connect OneDrive).

| Doc | Purpose |
|-----|---------|
| [`docs/developer/SETUP.md`](./docs/developer/SETUP.md) | Install details |
| [`docs/developer/TESTING.md`](./docs/developer/TESTING.md) | Jest + Maestro |
| [`docs/testing/MANUAL-TEST-CHECKLIST.md`](./docs/testing/MANUAL-TEST-CHECKLIST.md) | Test failure log (IN PROGRESS) |
| [`docs/cloud-storage/setuponedrive.md`](./docs/cloud-storage/setuponedrive.md) | OneDrive setup |
| [`docs/developer/GITHUB-ACTIONS-BUILD.md`](./docs/developer/GITHUB-ACTIONS-BUILD.md) | APK build on GitHub Actions |

---

## Tech stack

| Layer | Choice |
|-------|--------|
| Framework | Expo SDK ~54, React Native 0.81 |
| Persistence | SQLite (`expo-sqlite`) + AsyncStorage |
| State | React Context (`Van`, `Products`, `Orders`, `Customers`, `Theme`, …) |
| PDF / print | `expo-print`, HTML builders in `src/utils/*Pdf.js` |
| Cloud | **OneDrive** via MSAL + Microsoft Graph |
| Scanning | `expo-camera` + hardware keyboard wedge |

---

## Project structure

```
Premcrest-Van-Sales/
├── App.js                 # Providers → Setup or MainTabs
├── src/
│   ├── screens/           # Tabs + Analysis manager, Van P&L, EOD cash overview, …
│   ├── components/        # TabBar, modals, ProfileVanSection, …
│   ├── context/           # Van, Products, Orders, Customers, Db, Theme
│   ├── db/                # SQLite schema, migrations, repositories
│   └── utils/             # PDFs, OneDrive, P&L, CSV, stock, mileage
├── docs/                  # All documentation (see docs/README.md)
├── data/                  # Reference CSV + DISTRIBUTION P&L xlsx templates
├── tests/                 # Jest (213 tests) + Maestro E2E + manual guides
└── assets/                # Logo, icons
```

---

## Documentation map

| Audience | Start here |
|----------|------------|
| **Device testing (now)** | [`docs/testing/MANUAL-TEST-CHECKLIST.md`](./docs/testing/MANUAL-TEST-CHECKLIST.md) |
| Drivers / office | [`docs/user-guides/FEATURES.md`](./docs/user-guides/FEATURES.md) |
| Feature → code files | [`docs/code-map/FEATURE-TO-FILES.md`](./docs/code-map/FEATURE-TO-FILES.md) |
| v7 release (changes 1–13) | [`docs/continuous-changes/NEW-CHANGES-V7.md`](./docs/continuous-changes/NEW-CHANGES-V7.md) |
| Build status | [`docs/continuous-changes/PROGRESS-OF-CHANGES.md`](./docs/continuous-changes/PROGRESS-OF-CHANGES.md) |
| UI / design | [`docs/design/UI_DESIGN.md`](./docs/design/UI_DESIGN.md) |
| Developers | [`docs/developer/PROJECT-OVERVIEW.md`](./docs/developer/PROJECT-OVERVIEW.md) |

**Thermal receipts:** 70mm (`invoiceReceipt78Pdf.js`); legacy `*58*` names in docs only — see [`docs/pdf-and-receipts/THERMAL-RECEIPT.md`](./docs/pdf-and-receipts/THERMAL-RECEIPT.md).

---

## v7 highlights (all built on `main`)

| # | Feature |
|---|---------|
| 1 | Shift start/end mileage + pence per mile on EOD |
| 2 | Route analysis (stock recommendations) |
| 3–4 | OneDrive reports by van / van-first folder layout |
| 5–6 | New thermal logo; receipt module rename 58→78 |
| 7 | Sales Breakdown sheet layout (EOD Excel) |
| 8 | Delete customer data (date range, admin) |
| 9 | EOD cash overview screen |
| 10 | Upload button renamed **Upload Data** |
| 11 | SALES Totals Sheet 1 — Inc VAT columns |
| 12 | Remove scan line at qty zero |
| 13 | Analysis manager · Van P&L · generated reports · CSV buy prices |

---

## Not implemented

- In-app **Linnworks order upload** (placeholder “Coming soon”).
- Stock restore on checkout returns (deferred).

See [`docs/continuous-changes/NOT-CODED-YET.md`](./docs/continuous-changes/NOT-CODED-YET.md).

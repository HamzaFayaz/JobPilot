import {
  ArrowLeftIcon,
  CheckCircleIcon,
  ComputerDesktopIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline'
import { Link } from 'react-router-dom'
import { SearchHelperSetupCard } from '../components/settings/SearchHelperSetupCard'

export function SearchHelperGuidePage() {
  return (
    <div className="space-y-6 pb-6 sm:space-y-8">
      <header className="relative overflow-hidden rounded-[1.75rem] border border-border bg-surface px-6 py-7 shadow-surface sm:px-8 sm:py-9">
        <div className="pointer-events-none absolute -right-16 -top-16 h-52 w-52 rounded-full bg-primary/10 blur-3xl" />
        <div className="relative">
          <Link to="/settings" className="inline-flex items-center gap-2 text-sm font-bold text-primary hover:text-primary-hover hover:underline">
            <ArrowLeftIcon className="h-4 w-4" aria-hidden="true" />
            Back to Settings
          </Link>
          <p className="jp-eyebrow mt-6">Search Helper guide</p>
          <h1 className="jp-display mt-2 text-3xl font-extrabold tracking-tight text-text-primary sm:text-4xl">
            Set up your first LinkedIn search.
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
            Follow the checklist once on this computer. The connection remains under your control and JobPilot never submits an application for you.
          </p>
        </div>
      </header>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(280px,0.8fr)]">
        <SearchHelperSetupCard />

        <aside className="space-y-5">
          <section className="rounded-[1.5rem] border border-sidebar/10 bg-sidebar p-5 text-white shadow-lg shadow-slate-950/10 sm:p-6">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/20 text-teal-100">
              <ShieldCheckIcon className="h-5 w-5" aria-hidden="true" />
            </span>
            <p className="jp-eyebrow mt-5 !text-teal-200">Connection rules</p>
            <h2 className="jp-display mt-2 text-xl font-extrabold tracking-tight">Keep your job search in your hands.</h2>
            <ul className="mt-5 space-y-4 text-sm leading-6 text-slate-300">
              {[
                'Use the exact Chrome profile where you are signed in to LinkedIn.',
                'Keep your pairing code private and enter it only in your own Search Helper.',
                'Keep the Helper running only while you want JobPilot to search.',
                'Review every recommendation and choose whether to apply yourself.',
              ].map((rule) => (
                <li key={rule} className="flex gap-2.5">
                  <CheckCircleIcon className="mt-1 h-4 w-4 shrink-0 text-teal-200" aria-hidden="true" />
                  {rule}
                </li>
              ))}
            </ul>
          </section>

          <section className="jp-surface rounded-[1.5rem] p-5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-secondary-soft text-secondary">
              <ComputerDesktopIcon className="h-5 w-5" aria-hidden="true" />
            </span>
            <h2 className="jp-display mt-4 text-lg font-extrabold tracking-tight text-text-primary">Why this helper exists</h2>
            <p className="mt-2 text-sm leading-6 text-text-secondary">
              LinkedIn browsing happens in your own Chrome session. The desktop Helper only connects that session to JobPilot so it can surface relevant posts for your review.
            </p>
          </section>
        </aside>
      </div>
    </div>
  )
}

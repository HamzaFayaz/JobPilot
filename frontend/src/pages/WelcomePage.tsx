import { Navigate } from 'react-router-dom'
import {
  ArrowRightIcon,
  ArrowUpTrayIcon,
  BoltIcon,
  CheckCircleIcon,
  CodeBracketIcon,
  HandRaisedIcon,
  LockClosedIcon,
  RocketLaunchIcon,
  ShieldCheckIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'
import { Link } from 'react-router-dom'
import { useProfile } from '../context/ProfileContext'

interface ChecklistItem {
  key: string
  title: string
  description: string
  done: boolean
  icon: typeof ArrowUpTrayIcon
}

export function WelcomePage() {
  const { gate, loading } = useProfile()

  if (!loading && gate.isComplete) {
    return <Navigate to="/applications" replace />
  }

  const items: ChecklistItem[] = [
    {
      key: 'cv',
      title: 'Upload CV',
      description: '.docx only. Skills are extracted automatically.',
      done: gate.hasCv,
      icon: ArrowUpTrayIcon,
    },
    {
      key: 'skills',
      title: 'Skills from CV',
      description: 'At least 3 skills extracted from your resume.',
      done: gate.hasMinSkills,
      icon: CodeBracketIcon,
    },
    {
      key: 'projects',
      title: 'At least one project',
      description: 'Import from GitHub on Profile or add in Settings.',
      done: gate.hasProject,
      icon: RocketLaunchIcon,
    },
  ]

  const completeness = Math.round((gate.requiredComplete / gate.requiredTotal) * 100)

  return (
    <div className="space-y-6 pb-5 sm:space-y-8">
      <section className="jp-surface relative overflow-hidden rounded-[1.75rem] p-6 sm:p-8 lg:p-10">
        <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-secondary/10 blur-3xl" />
        <div className="pointer-events-none absolute bottom-0 left-[35%] h-48 w-80 rounded-full bg-primary/10 blur-3xl" />
        <div className="relative grid gap-8 lg:grid-cols-[1.25fr_0.75fr] lg:items-end">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/15 bg-primary-soft px-3 py-1.5 text-xs font-semibold text-primary">
              <SparklesIcon className="h-4 w-4" aria-hidden="true" />
              JobPilot is ready when you are
            </div>
            <h1 className="jp-display mt-5 max-w-2xl text-3xl font-extrabold tracking-tight text-text-primary sm:text-4xl lg:text-[2.7rem] lg:leading-[1.08]">
              Turn your experience into your next opportunity.
            </h1>
            <p className="mt-4 max-w-xl text-sm leading-6 text-text-secondary sm:text-base sm:leading-7">
              Build your career signal once. JobPilot then scouts LinkedIn Posts from your own
              browser, explains each match, and leaves every decision with you.
            </p>
            <div className="mt-7 flex flex-wrap gap-3 text-xs font-medium text-text-secondary">
              <span className="inline-flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-primary" />
                Real browser search
              </span>
              <span className="inline-flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-secondary" />
                Evidence-backed fit
              </span>
              <span className="inline-flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-success" />
                You decide what happens next
              </span>
            </div>
          </div>

          <div className="rounded-2xl border border-sidebar/8 bg-sidebar p-5 text-white shadow-xl shadow-slate-950/10">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[11px] font-bold uppercase tracking-[0.15em] text-slate-400">
                  Career readiness
                </p>
                <p className="jp-display mt-1 text-2xl font-extrabold">{completeness}%</p>
                <p className="mt-1 text-xs text-slate-400">
                  {gate.requiredComplete} of {gate.requiredTotal} launch steps complete
                </p>
              </div>
              <div
                className="flex h-16 w-16 items-center justify-center rounded-full"
                style={{
                  background: `conic-gradient(#14b8a6 ${completeness * 3.6}deg, rgba(255,255,255,0.12) 0deg)`,
                }}
                aria-label={`${completeness}% profile readiness`}
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-sidebar text-xs font-bold text-teal-100">
                  {gate.requiredComplete}/{gate.requiredTotal}
                </div>
              </div>
            </div>
            <div className="mt-5 h-px bg-white/10" />
            <p className="mt-4 flex items-start gap-2 text-xs leading-5 text-slate-300">
              <ShieldCheckIcon className="mt-0.5 h-4 w-4 shrink-0 text-teal-200" aria-hidden="true" />
              Your master CV stays untouched. JobPilot only prepares suggestions for you to review.
            </p>
          </div>
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
        <section className="jp-surface rounded-[1.5rem] p-5 sm:p-7">
          <div className="flex flex-col gap-4 border-b border-border pb-5 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="jp-eyebrow">Launch sequence</p>
              <h2 className="jp-display mt-2 text-xl font-extrabold tracking-tight text-text-primary">
                Build your search-ready profile
              </h2>
              <p className="mt-1 text-sm text-text-secondary">
                Three quick steps unlock your first focused search.
              </p>
            </div>
            <Link
              to="/profile"
              className="inline-flex min-h-11 shrink-0 items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-primary/20 transition-all duration-200 hover:-translate-y-0.5 hover:bg-primary-hover hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            >
              Continue setup
              <ArrowRightIcon className="h-4 w-4" aria-hidden="true" />
            </Link>
          </div>

          <ol className="mt-3 divide-y divide-border">
            {items.map((item, index) => {
              const Icon = item.icon
              return (
                <li key={item.key} className="flex items-center gap-4 py-4 sm:gap-5">
                  <span
                    className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-sm font-bold ${
                      item.done
                        ? 'bg-success-soft text-success'
                        : 'border border-border bg-surface-muted text-text-secondary'
                    }`}
                    aria-hidden="true"
                  >
                    {item.done ? <CheckCircleIcon className="h-5 w-5" /> : `0${index + 1}`}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-semibold text-text-primary">{item.title}</span>
                      {item.done ? (
                        <span className="rounded-full bg-success-soft px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-success">
                          Ready
                        </span>
                      ) : null}
                    </span>
                    <span className="mt-1 block text-xs leading-5 text-text-secondary">{item.description}</span>
                  </span>
                  <Icon className="hidden h-5 w-5 shrink-0 text-text-tertiary sm:block" aria-hidden="true" />
                </li>
              )
            })}
          </ol>
        </section>

        <aside className="rounded-[1.5rem] bg-sidebar p-6 text-white shadow-lg shadow-slate-950/10 sm:p-7">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/20 text-teal-100">
            <RocketLaunchIcon className="h-5 w-5" aria-hidden="true" />
          </div>
          <p className="jp-eyebrow mt-6 !text-teal-200">Why JobPilot</p>
          <h2 className="jp-display mt-2 text-xl font-extrabold tracking-tight">
            More signal. Less job-search drag.
          </h2>
          <div className="mt-6 space-y-5">
            {[
              { icon: LockClosedIcon, title: 'Private by design', text: 'Your profile powers your own search only.' },
              { icon: BoltIcon, title: 'Built for momentum', text: 'The agent handles repetitive scouting and analysis.' },
              { icon: HandRaisedIcon, title: 'Human decision point', text: 'You decide which opportunities deserve action.' },
            ].map((card) => {
              const Icon = card.icon
              return (
                <div key={card.title} className="flex gap-3">
                  <Icon className="mt-0.5 h-5 w-5 shrink-0 text-teal-200" aria-hidden="true" />
                  <div>
                    <h3 className="text-sm font-semibold text-white">{card.title}</h3>
                    <p className="mt-1 text-xs leading-5 text-slate-400">{card.text}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </aside>
      </div>
    </div>
  )
}

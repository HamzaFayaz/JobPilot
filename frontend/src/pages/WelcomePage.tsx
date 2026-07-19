import { Navigate } from 'react-router-dom'
import {
  ArrowUpTrayIcon,
  BoltIcon,
  CheckCircleIcon,
  CodeBracketIcon,
  HandRaisedIcon,
  LockClosedIcon,
  RocketLaunchIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline'
import { Link } from 'react-router-dom'
import { useProfile } from '../context/ProfileContext'
import { Button } from '../components/ui/Button'
import { ProgressBar } from '../components/ui/ProgressBar'

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
    <div className="mx-auto max-w-3xl space-y-8">
      <header className="text-center">
        <div className="mb-4 flex justify-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-white shadow-lg shadow-primary/25">
            <RocketLaunchIcon className="h-7 w-7" aria-hidden="true" />
          </div>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
          Welcome to JobPilot
        </h1>
        <p className="mx-auto mt-3 max-w-lg text-sm text-text-secondary sm:text-base">
          Set up your profile once, then run AI-powered job searches from your own browser.
        </p>
      </header>

      <div className="flex items-start gap-3 rounded-xl border border-warning/25 bg-hitl-bg/80 p-4">
        <ShieldCheckIcon className="mt-0.5 h-5 w-5 shrink-0 text-warning" aria-hidden="true" />
        <p className="text-sm text-hitl-text">
          <span className="font-semibold">You stay in control.</span> Nothing is sent without your
          approval.
        </p>
      </div>

      <section className="rounded-xl border border-border bg-surface p-6 shadow-sm sm:p-8">
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-text-primary">Getting started</h2>
            <p className="mt-1 text-sm text-text-secondary">
              {gate.requiredComplete} of {gate.requiredTotal} steps complete
            </p>
          </div>
          <div className="w-full sm:w-44">
            <ProgressBar value={gate.requiredComplete} max={gate.requiredTotal} label={`${completeness}%`} />
          </div>
        </div>

        <ul className="space-y-3">
          {items.map((item) => {
            const Icon = item.icon
            return (
              <li
                key={item.key}
                className="flex items-center gap-4 rounded-lg border border-border bg-background/50 px-4 py-3.5"
              >
                {item.done ? (
                  <CheckCircleIcon className="h-6 w-6 shrink-0 text-success" aria-hidden="true" />
                ) : (
                  <span className="block h-6 w-6 shrink-0 rounded-full border-2 border-disabled" />
                )}
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-text-primary">{item.title}</p>
                  <p className="text-xs text-text-secondary">{item.description}</p>
                </div>
                <Icon className="hidden h-5 w-5 shrink-0 text-text-secondary sm:block" aria-hidden="true" />
              </li>
            )
          })}
        </ul>

        <div className="mt-8 flex justify-end border-t border-border pt-6">
          <Link to="/profile">
            <Button>Continue setup</Button>
          </Link>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {[
          { icon: LockClosedIcon, title: 'Privacy first', text: 'Your data personalizes searches only.' },
          { icon: BoltIcon, title: 'Fast drafts', text: 'AI handles repetition; you approve output.' },
          { icon: HandRaisedIcon, title: 'Human in the loop', text: 'Built for developers, not spam.' },
        ].map((card) => {
          const Icon = card.icon
          return (
            <div key={card.title} className="rounded-xl border border-border bg-surface p-5">
              <Icon className="mb-2 h-5 w-5 text-primary" aria-hidden="true" />
              <h3 className="text-sm font-semibold">{card.title}</h3>
              <p className="mt-1 text-xs text-text-secondary">{card.text}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

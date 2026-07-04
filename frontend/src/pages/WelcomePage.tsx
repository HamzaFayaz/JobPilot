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
  optional?: boolean
  icon: typeof ArrowUpTrayIcon
}

export function WelcomePage() {
  const { gate } = useProfile()

  const items: ChecklistItem[] = [
    {
      key: 'cv',
      title: 'Upload CV',
      description: '.docx only, required for AI parsing.',
      done: gate.hasCv,
      icon: ArrowUpTrayIcon,
    },
    {
      key: 'skills',
      title: 'Skills from CV',
      description: 'Auto-extracted from your CV (minimum 3 skills).',
      done: gate.hasMinSkills,
      icon: CodeBracketIcon,
    },
    {
      key: 'projects',
      title: 'Projects ready',
      description: 'Import from GitHub on Profile or add in Settings (minimum 1).',
      done: gate.hasProject,
      icon: RocketLaunchIcon,
    },
  ]

  return (
    <div className="space-y-8">
      <header className="text-center">
        <div className="mb-4 flex justify-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-primary text-white shadow-md">
            <RocketLaunchIcon className="h-8 w-8" aria-hidden="true" />
          </div>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
          Your AI job application copilot
        </h1>
        <p className="mx-auto mt-3 max-w-2xl text-sm text-text-secondary sm:text-base">
          Your browser-based assistant for finding developer roles with human approval
          before anything is sent.
        </p>
      </header>

      <div className="flex items-center gap-3 rounded-lg border border-warning/30 bg-hitl-bg p-4 text-hitl-text">
        <ShieldCheckIcon className="h-6 w-6 shrink-0 text-warning" aria-hidden="true" />
        <p className="text-sm font-semibold">
          HITL Control: You approve every cover letter and email before the AI hits send.
        </p>
      </div>

      <section className="rounded-lg border border-border bg-surface p-6 shadow-sm">
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-text-primary">Getting Started</h2>
            <p className="mt-1 text-sm text-text-secondary">
              Complete these steps to unlock the application automator.
            </p>
          </div>
          <div className="w-full sm:w-40">
            <ProgressBar
              value={gate.requiredComplete}
              max={gate.requiredTotal}
              label={`${Math.round((gate.requiredComplete / gate.requiredTotal) * 100)}%`}
            />
          </div>
        </div>

        <ul className="space-y-3">
          {items.map((item) => {
            const Icon = item.icon
            return (
              <li
                key={item.key}
                className="flex items-center gap-4 rounded-lg border border-border p-4 transition-colors duration-200 hover:border-primary/30 hover:bg-chip-bg/20"
              >
                <div className="shrink-0">
                  {item.done ? (
                    <CheckCircleIcon className="h-6 w-6 text-success" aria-hidden="true" />
                  ) : (
                    <span className="block h-6 w-6 rounded-full border-2 border-disabled" />
                  )}
                </div>
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-sm font-semibold text-text-primary">{item.title}</h3>
                    {item.optional ? (
                      <span className="rounded bg-background px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-text-secondary">
                        Optional
                      </span>
                    ) : null}
                  </div>
                  <p className="text-xs text-text-secondary">{item.description}</p>
                </div>
                <Icon className="h-5 w-5 shrink-0 text-text-secondary" aria-hidden="true" />
              </li>
            )
          })}
        </ul>

        <div className="mt-8 flex flex-col gap-4 border-t border-border pt-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-text-secondary">
            <span className="font-semibold text-text-primary">
              {gate.requiredComplete} of {gate.requiredTotal}
            </span>{' '}
            required steps completed
          </p>
          <Link to="/profile" className="w-full sm:w-auto">
            <Button className="w-full">Set up your profile</Button>
          </Link>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-border bg-surface p-5 text-center">
          <LockClosedIcon className="mx-auto mb-2 h-6 w-6 text-primary" aria-hidden="true" />
          <h3 className="text-sm font-semibold">Privacy First</h3>
          <p className="mt-1 text-xs text-text-secondary">
            Your data is only used to personalize your job search and draft applications.
          </p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-5 text-center">
          <BoltIcon className="mx-auto mb-2 h-6 w-6 text-primary" aria-hidden="true" />
          <h3 className="text-sm font-semibold">Speed + Quality</h3>
          <p className="mt-1 text-xs text-text-secondary">
            AI handles the tedious drafting; you handle the final personal touches.
          </p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-5 text-center">
          <HandRaisedIcon className="mx-auto mb-2 h-6 w-6 text-primary" aria-hidden="true" />
          <h3 className="text-sm font-semibold">Human Centric</h3>
          <p className="mt-1 text-xs text-text-secondary">
            Built to empower developers, not to spam hiring managers.
          </p>
        </div>
      </div>
    </div>
  )
}

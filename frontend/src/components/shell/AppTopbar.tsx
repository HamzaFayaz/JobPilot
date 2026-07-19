import { CheckCircleIcon, SparklesIcon } from '@heroicons/react/24/outline'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useProfile } from '../../context/ProfileContext'

const pageContext: Record<string, { eyebrow: string; title: string }> = {
  '/': { eyebrow: 'Pilot desk', title: 'Career command center' },
  '/profile': { eyebrow: 'Profile intelligence', title: 'Your career signal' },
  '/search': { eyebrow: 'Search mission', title: 'Configure your next scout run' },
  '/applications': { eyebrow: 'Review queue', title: 'Your opportunity inbox' },
  '/settings': { eyebrow: 'Workspace', title: 'Connections & preferences' },
  '/settings/search-helper-guide': { eyebrow: 'Setup guide', title: 'Connect your Search Helper' },
  '/settings/projects': { eyebrow: 'Profile evidence', title: 'Manage project cards' },
  '/settings/skills': { eyebrow: 'CV intelligence', title: 'Your skill library' },
}

export function AppTopbar() {
  const { pathname } = useLocation()
  const { gate } = useProfile()
  const { user } = useAuth()
  const context = pageContext[pathname] ?? pageContext['/']
  const initial = user?.email?.slice(0, 1).toUpperCase() ?? 'J'

  return (
    <header className="mb-7 hidden items-center justify-between gap-6 lg:flex">
      <div>
        <p className="jp-eyebrow">{context.eyebrow}</p>
        <p className="jp-display mt-1 text-lg font-bold tracking-tight text-text-primary">
          {context.title}
        </p>
      </div>

      <div className="flex items-center gap-3">
        <div
          className={`flex items-center gap-2 rounded-full border px-3 py-2 text-xs font-semibold ${
            gate.isComplete
              ? 'border-success/20 bg-success-soft text-success'
              : 'border-warning/20 bg-warning-soft text-warning'
          }`}
          title={
            gate.isComplete
              ? 'Your profile is ready for JobPilot searches'
              : `${gate.requiredComplete} of ${gate.requiredTotal} profile steps complete`
          }
        >
          {gate.isComplete ? (
            <CheckCircleIcon className="h-4 w-4" aria-hidden="true" />
          ) : (
            <SparklesIcon className="h-4 w-4" aria-hidden="true" />
          )}
          {gate.isComplete
            ? 'Profile ready'
            : `${gate.requiredComplete}/${gate.requiredTotal} setup steps`}
        </div>
        <div
          className="flex h-9 w-9 items-center justify-center rounded-full border border-border bg-surface text-xs font-bold text-primary shadow-sm"
          title={user?.email ?? 'JobPilot account'}
          aria-label={user?.email ?? 'JobPilot account'}
        >
          {initial}
        </div>
      </div>
    </header>
  )
}

import {
  ArrowRightIcon,
  CheckCircleIcon,
  CodeBracketIcon,
  DocumentTextIcon,
  RocketLaunchIcon,
} from '@heroicons/react/24/outline'
import { useEffect } from 'react'
import { useSearchParams, Link as RouterLink } from 'react-router-dom'
import { CvUpload } from '../components/profile/CvUpload'
import { GitHubImport } from '../components/profile/GitHubImport'
import { RolesInput } from '../components/profile/RolesInput'
import { SearchPreferencesFields } from '../components/search/SearchPreferencesFields'
import { ProgressBar } from '../components/ui/ProgressBar'
import { useProfile } from '../context/ProfileContext'

export function ProfilePage() {
  const { gate, refreshProfile, profile, updateProfile } = useProfile()
  const [searchParams] = useSearchParams()
  const completeness = Math.round((gate.requiredComplete / gate.requiredTotal) * 100)

  useEffect(() => {
    if (searchParams.get('github') === 'connected') {
      void refreshProfile()
      window.history.replaceState({}, '', '/profile')
    }
  }, [searchParams, refreshProfile])

  const readinessCards = [
    {
      icon: DocumentTextIcon,
      label: 'Career evidence',
      text: gate.hasCv ? profile.cvFilename ?? 'CV uploaded' : 'Upload your .docx CV',
      ready: gate.hasCv,
    },
    {
      icon: CodeBracketIcon,
      label: 'Skills signal',
      text: gate.hasMinSkills ? `${profile.skills.length} skills extracted` : 'At least 3 verified skills',
      ready: gate.hasMinSkills,
    },
    {
      icon: RocketLaunchIcon,
      label: 'Project proof',
      text:
        profile.projectsIndexingStatus === 'pending'
          ? 'Preparing project evidence...'
          : gate.hasProject
            ? `${profile.projects.length} project${profile.projects.length === 1 ? '' : 's'} ready`
            : 'Add or import a project',
      ready: gate.hasProject,
    },
  ]

  return (
    <div className="space-y-6 pb-6 sm:space-y-8">
      <header className="relative overflow-hidden rounded-[1.75rem] border border-border bg-surface px-6 py-7 shadow-surface sm:px-8 sm:py-9">
        <div className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-primary/10 blur-3xl" />
        <div className="relative grid gap-7 lg:grid-cols-[1fr_260px] lg:items-end">
          <div>
            <p className="jp-eyebrow">Career signal</p>
            <h1 className="jp-display mt-3 text-3xl font-extrabold tracking-tight text-text-primary sm:text-4xl">
              {gate.isComplete ? 'Your profile is search-ready.' : 'Make your experience searchable.'}
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
              {gate.isComplete
                ? 'Your CV, skills, and projects give JobPilot the evidence it needs to surface stronger opportunities.'
                : 'Add the proof behind your experience once. JobPilot uses it to explain why a role fits, not just assign a score.'}
            </p>
          </div>

          <div className="rounded-2xl border border-primary/15 bg-primary-soft/60 p-4">
            <div className="flex items-end justify-between gap-3">
              <div>
                <p className="text-xs font-semibold text-primary">Profile readiness</p>
                <p className="jp-display mt-1 text-3xl font-extrabold text-text-primary">{completeness}%</p>
              </div>
              {gate.isComplete ? (
                <CheckCircleIcon className="h-9 w-9 text-success" aria-label="Profile complete" />
              ) : (
                <RocketLaunchIcon className="h-9 w-9 text-primary" aria-hidden="true" />
              )}
            </div>
            <div className="mt-3">
              <ProgressBar value={gate.requiredComplete} max={gate.requiredTotal} />
            </div>
            <p className="mt-3 text-xs leading-5 text-text-secondary">
              {gate.isComplete
                ? 'Everything JobPilot needs is in place.'
                : `${gate.requiredTotal - gate.requiredComplete} launch step${gate.requiredTotal - gate.requiredComplete === 1 ? '' : 's'} remaining.`}
            </p>
          </div>
        </div>
      </header>

      <section className="grid gap-3 sm:grid-cols-3" aria-label="Profile readiness">
        {readinessCards.map((item) => {
          const Icon = item.icon
          return (
            <div
              key={item.label}
              className={`rounded-2xl border p-4 transition-colors ${
                item.ready
                  ? 'border-success/18 bg-success-soft/55'
                  : 'border-border bg-surface shadow-sm'
              }`}
            >
              <div className="flex items-start gap-3">
                <span
                  className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${
                    item.ready ? 'bg-success/10 text-success' : 'bg-surface-muted text-text-secondary'
                  }`}
                >
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </span>
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-text-primary">{item.label}</p>
                  <p className="mt-1 truncate text-xs text-text-secondary" title={item.text}>
                    {item.text}
                  </p>
                </div>
              </div>
            </div>
          )
        })}
      </section>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(330px,0.85fr)]">
        <div className="space-y-6">
          <CvUpload />
          <RolesInput />
          <GitHubImport />
        </div>

        <aside className="space-y-6">
          <section className="jp-surface rounded-[1.5rem] p-5 sm:p-6">
            <p className="jp-eyebrow">Default search brief</p>
            <h2 className="jp-display mt-2 text-xl font-extrabold tracking-tight text-text-primary">
              Set your search guardrails
            </h2>
            <p className="mt-2 text-sm leading-6 text-text-secondary">
              Saved to your JobPilot profile and used when you launch a focused search.
            </p>
            <div className="mt-6">
              <SearchPreferencesFields
                profile={profile}
                onChange={(patch) => {
                  void updateProfile(patch)
                }}
              />
            </div>
          </section>

          <section className="rounded-[1.5rem] border border-sidebar/10 bg-sidebar p-5 text-white shadow-lg shadow-slate-950/10 sm:p-6">
            <p className="jp-eyebrow !text-teal-200">Your next move</p>
            <h2 className="jp-display mt-2 text-xl font-extrabold">
              {gate.isComplete ? 'Your pilot desk is ready.' : 'Complete the launch sequence.'}
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-300">
              {gate.isComplete
                ? 'Connect your Search Helper when you are ready, then let JobPilot scout LinkedIn Posts from your browser.'
                : 'Every step adds evidence JobPilot can use to make its recommendations transparent.'}
            </p>
            {gate.isComplete ? (
              <RouterLink
                to="/search"
                className="mt-5 inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-black/20 transition-all hover:-translate-y-0.5 hover:bg-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-200 focus-visible:ring-offset-2 focus-visible:ring-offset-sidebar"
              >
                Configure a search
                <ArrowRightIcon className="h-4 w-4" aria-hidden="true" />
              </RouterLink>
            ) : (
              <p className="mt-5 rounded-xl border border-white/10 bg-white/5 px-3 py-3 text-xs leading-5 text-slate-300">
                Search unlocks after your CV, skills, and at least one project are ready.
              </p>
            )}
          </section>
        </aside>
      </div>

      {!gate.hasProject ? (
        <p className="rounded-xl border border-dashed border-border-strong bg-surface/70 px-4 py-3 text-sm text-text-secondary">
          Need project proof? Import repositories above or{' '}
          <RouterLink to="/settings" className="font-semibold text-primary hover:text-primary-hover hover:underline">
            add a project in Settings
          </RouterLink>
          .
        </p>
      ) : null}
    </div>
  )
}

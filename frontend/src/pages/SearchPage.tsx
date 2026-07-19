import {
  ArrowPathIcon,
  ArrowRightIcon,
  BoltIcon,
  CheckCircleIcon,
  ComputerDesktopIcon,
  LightBulbIcon,
  LinkIcon,
  MagnifyingGlassIcon,
  MapPinIcon,
  ShieldCheckIcon,
  PlusIcon,
  SignalIcon,
} from '@heroicons/react/24/outline'
import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  getLatestRun,
  getRunStatus,
  listRunJobs,
  startSearch,
  type JobPackage,
  type SearchRunStatusResponse,
} from '../api/search'
import { Button } from '../components/ui/Button'
import { SearchHelperHint } from '../components/search/SearchHelperHint'
import { SearchPreferencesFields } from '../components/search/SearchPreferencesFields'
import { useProfile } from '../context/ProfileContext'
import type { SearchPlatform } from '../types/profile'

export function SearchPage() {
  const navigate = useNavigate()
  const { profile, gate, loading: profileLoading, updateProfile } = useProfile()
  const [role, setRole] = useState(profile.searchRole ?? profile.targetRoles[0] ?? '')
  const [platform, setPlatform] = useState<SearchPlatform>(profile.searchPlatform)
  const [toast, setToast] = useState<string | null>(null)
  const [activeRunId, setActiveRunId] = useState<number | null>(null)
  const [runStatus, setRunStatus] = useState<SearchRunStatusResponse | null>(null)
  const [jobs, setJobs] = useState<JobPackage[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [pollError, setPollError] = useState<string | null>(null)
  const [helperReady, setHelperReady] = useState(false)
  const [restoringRun, setRestoringRun] = useState(true)

  const showToast = useCallback((message: string) => {
    setToast(message)
    window.setTimeout(() => setToast(null), 3000)
  }, [])

  const refreshRun = useCallback(async (runId: number) => {
    const [status, nextJobs] = await Promise.all([getRunStatus(runId), listRunJobs(runId)])
    setRunStatus(status)
    setJobs(nextJobs)
    setPollError(null)
  }, [])

  useEffect(() => {
    let cancelled = false

    void (async () => {
      try {
        const latest = await getLatestRun()
        if (cancelled || !latest) return
        setActiveRunId(latest.runId)
        setRunStatus(latest)
        const nextJobs = await listRunJobs(latest.runId)
        if (!cancelled) setJobs(nextJobs)
      } catch (error: unknown) {
        if (!cancelled) {
          setPollError(error instanceof Error ? error.message : 'Failed to load latest search run')
        }
      } finally {
        if (!cancelled) setRestoringRun(false)
      }
    })()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (profileLoading || !gate.isComplete) return
    if (profile.targetRoles.length === 0) {
      setRole('')
      return
    }

    const nextRole =
      profile.searchRole && profile.targetRoles.includes(profile.searchRole)
        ? profile.searchRole
        : profile.targetRoles[0]

    setRole(nextRole)
    if (profile.searchRole !== nextRole) {
      void updateProfile({ searchRole: nextRole })
    }
  }, [
    gate.isComplete,
    profile.searchRole,
    profile.targetRoles,
    profileLoading,
    updateProfile,
  ])

  useEffect(() => {
    // Indeed is coming soon. Keep searches on LinkedIn.
    if (profile.searchPlatform === 'indeed') {
      setPlatform('linkedin')
      void updateProfile({ searchPlatform: 'linkedin' })
      return
    }
    setPlatform(profile.searchPlatform)
  }, [profile.searchPlatform, updateProfile])

  useEffect(() => {
    if (!activeRunId || !runStatus) return
    if (runStatus.status === 'completed' || runStatus.status === 'failed') {
      if (!jobs.some((job) => job.status === 'analyzing')) return
    }

    const timer = window.setInterval(() => {
      void refreshRun(activeRunId).catch((error: unknown) => {
        setPollError(error instanceof Error ? error.message : 'Failed to refresh run status')
      })
    }, 3000)

    return () => window.clearInterval(timer)
  }, [activeRunId, jobs, refreshRun, runStatus])

  if (profileLoading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-sm text-text-secondary">
        Loading your pilot desk...
      </div>
    )
  }

  if (profile.projectsIndexingStatus === 'pending') {
    return (
      <div className="jp-surface mx-auto max-w-xl rounded-[1.5rem] px-6 py-9 text-center sm:px-8">
        <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-secondary-soft text-secondary">
          <ArrowPathIcon className="h-6 w-6 animate-spin" aria-hidden="true" />
        </span>
        <p className="jp-eyebrow mt-5">Preparing your signal</p>
        <h1 className="jp-display mt-2 text-2xl font-extrabold tracking-tight text-text-primary">
          Project evidence is being prepared.
        </h1>
        <p className="mt-3 text-sm leading-6 text-text-secondary">
          JobPilot is building project overviews and evidence. You can set up your Search Helper while this finishes.
        </p>
        <Link
          to="/settings"
          className="mt-6 inline-flex min-h-11 items-center justify-center rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          Open Search Helper setup
        </Link>
      </div>
    )
  }

  if (!gate.isComplete) {
    return (
      <div className="jp-surface mx-auto max-w-xl rounded-[1.5rem] px-6 py-9 text-center sm:px-8">
        <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-warning-soft text-warning">
          <ShieldCheckIcon className="h-6 w-6" aria-hidden="true" />
        </span>
        <p className="jp-eyebrow mt-5">Launch sequence incomplete</p>
        <h1 className="jp-display mt-2 text-2xl font-extrabold tracking-tight text-text-primary">
          Build your profile before searching.
        </h1>
        <p className="mt-3 text-sm leading-6 text-text-secondary">
          A CV, verified skills, and at least one project let JobPilot explain its recommendations with real evidence.
        </p>
        <Link
          to="/profile"
          className="mt-6 inline-flex min-h-11 items-center justify-center rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          Complete your profile
        </Link>
      </div>
    )
  }

  const summaryParts = [
    profile.cvFilename ?? 'No CV',
    `${profile.skills.length} skills`,
    `${profile.projects.length} projects`,
  ]
  const runActive =
    runStatus?.status === 'pending' ||
    runStatus?.status === 'running' ||
    jobs.some((job) => job.status === 'analyzing')

  const searchBlockers: string[] = []
  if (!profile.targetRoles.length) {
    searchBlockers.push('Add at least one target role on your profile.')
  }
  if (!profile.searchCountry) {
    searchBlockers.push('Select a country in search preferences below.')
  }
  if (!helperReady) {
    searchBlockers.push('Connect Search Helper and open Chrome with WebBridge.')
  }
  if (runActive) {
    searchBlockers.push('A search or analysis is already running. Open Applications to follow it.')
  }

  const canStartSearch = searchBlockers.length === 0 && !submitting
  const analyzingCount = jobs.filter((job) => job.status === 'analyzing').length
  const readyCount = jobs.filter((job) => job.status === 'ready').length

  const runMessage =
    runStatus?.status === 'pending'
      ? 'Queued for your connected Search Helper'
      : analyzingCount > 0
        ? `Analyzing ${analyzingCount} match${analyzingCount === 1 ? '' : 'es'} against your evidence`
        : runStatus?.status === 'running'
          ? 'Scouting LinkedIn Posts in your browser'
          : runStatus?.status === 'failed'
            ? 'This search needs attention'
            : 'Search complete'

  return (
    <div className="space-y-6 pb-6 sm:space-y-8">
      <header className="relative overflow-hidden rounded-[1.75rem] border border-border bg-surface px-6 py-7 shadow-surface sm:px-8 sm:py-9">
        <div className="pointer-events-none absolute -right-20 top-0 h-64 w-64 rounded-full bg-secondary/10 blur-3xl" />
        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="jp-eyebrow">Search mission</p>
            <h1 className="jp-display mt-3 text-3xl font-extrabold tracking-tight text-text-primary sm:text-4xl">
              Give JobPilot a focused brief.
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
              JobPilot scouts real LinkedIn Posts from your browser, then turns each opportunity into an explainable review decision.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 self-start rounded-full border border-warning/20 bg-warning-soft px-3 py-2 text-xs font-semibold text-warning lg:self-auto">
            <ShieldCheckIcon className="h-4 w-4" aria-hidden="true" />
            Nothing is submitted automatically
          </div>
        </div>
      </header>

      <SearchHelperHint onReadyChange={setHelperReady} />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(300px,0.85fr)]">
        <section className="jp-surface rounded-[1.5rem] p-5 sm:p-7">
          <div className="mb-7 flex flex-wrap items-start justify-between gap-4 border-b border-border pb-5">
            <div>
              <p className="jp-eyebrow">Mission brief</p>
              <h2 className="jp-display mt-2 text-xl font-extrabold tracking-tight text-text-primary">
                What should JobPilot scout?
              </h2>
            </div>
            <span className="rounded-full border border-secondary/12 bg-secondary-soft px-3 py-1.5 text-xs font-semibold text-secondary">
              LinkedIn Posts
            </span>
          </div>

          <form
            className="space-y-7"
            onSubmit={async (event) => {
              event.preventDefault()
              setSubmitting(true)
              setPollError(null)
              try {
                const started = await startSearch()
                setActiveRunId(started.runId)
                await refreshRun(started.runId)
                showToast(`Search run #${started.runNumber} started.`)
                navigate('/applications')
              } catch (error: unknown) {
                const message = error instanceof Error ? error.message : 'Failed to start search run'
                setPollError(message)
                showToast(message)
              } finally {
                setSubmitting(false)
              }
            }}
          >
            <div>
              <label htmlFor="target-role" className="mb-2 block text-sm font-semibold text-text-primary">
                Target role
              </label>
              {profile.targetRoles.length === 0 ? (
                <p className="rounded-xl bg-surface-muted px-3.5 py-3 text-sm text-text-secondary">
                  Add target roles on your profile first.
                </p>
              ) : (
                <select
                  id="target-role"
                  value={role}
                  onChange={(event) => {
                    const nextRole = event.target.value
                    setRole(nextRole)
                    void updateProfile({ searchRole: nextRole })
                  }}
                  disabled={runActive}
                  className="jp-input w-full cursor-pointer px-3.5 py-2.5 text-base disabled:cursor-not-allowed disabled:opacity-60 sm:text-sm"
                >
                  {profile.targetRoles.map((targetRole) => (
                    <option key={targetRole} value={targetRole}>
                      {targetRole}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <fieldset disabled={runActive}>
              <legend className="mb-3 text-sm font-semibold text-text-primary">Search source</legend>
              <div className="grid gap-3 sm:grid-cols-2">
                <label
                  className={`flex min-h-20 cursor-pointer items-center justify-between rounded-2xl border p-4 transition-all duration-200 ${
                    platform === 'linkedin'
                      ? 'border-primary/45 bg-primary-soft/65 shadow-sm'
                      : 'border-border bg-surface hover:border-primary/35'
                  } ${runActive ? 'cursor-not-allowed opacity-60' : ''}`}
                >
                  <span className="flex items-center gap-3">
                    <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#0A66C2] text-sm font-extrabold text-white">
                      in
                    </span>
                    <span>
                      <span className="block text-sm font-semibold text-text-primary">LinkedIn Posts</span>
                      <span className="mt-0.5 block text-xs text-text-secondary">Live in your Chrome</span>
                    </span>
                  </span>
                  <input
                    type="radio"
                    name="platform"
                    value="linkedin"
                    checked={platform === 'linkedin'}
                    onChange={() => {
                      setPlatform('linkedin')
                      void updateProfile({ searchPlatform: 'linkedin' })
                    }}
                    className="h-4 w-4 cursor-pointer accent-primary"
                  />
                </label>
                <button
                  type="button"
                  disabled={runActive}
                  onClick={() => showToast('More sources will be added based on JobPilot user demand.')}
                  className="flex min-h-20 items-center justify-between rounded-2xl border border-border bg-surface p-4 text-left transition-colors duration-200 hover:border-secondary/35 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <span className="flex items-center gap-3">
                    <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-secondary-soft text-secondary">
                      <PlusIcon className="h-5 w-5" aria-hidden="true" />
                    </span>
                    <span>
                      <span className="block text-sm font-semibold text-text-primary">More sources</span>
                      <span className="mt-0.5 block text-xs text-text-secondary">Planned from user demand</span>
                    </span>
                  </span>
                  <span className="rounded-full bg-surface-muted px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-text-secondary">
                    Soon
                  </span>
                </button>
              </div>
            </fieldset>

            <div className="rounded-2xl border border-border bg-surface-muted/45 p-4 sm:p-5">
              <p className="mb-5 text-sm font-semibold text-text-primary">Search guardrails</p>
              <SearchPreferencesFields
                profile={profile}
                onChange={(patch) => {
                  void updateProfile(patch)
                }}
                compact
              />
            </div>

            <div className="flex items-center gap-2 rounded-xl bg-surface-muted px-3.5 py-3 text-xs text-text-secondary">
              <MagnifyingGlassIcon className="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
              <span className="truncate">Using: {summaryParts.join(' • ')}</span>
            </div>

            {searchBlockers.length > 0 ? (
              <div className="rounded-2xl border border-warning/20 bg-warning-soft px-4 py-3.5 text-sm text-hitl-text">
                <p className="font-semibold">Preflight check</p>
                <ul className="mt-2 space-y-1.5 text-xs leading-5">
                  {searchBlockers.map((item) => (
                    <li key={item} className="flex gap-2">
                      <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-warning" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {pollError ? (
              <div className="rounded-2xl border border-error/20 bg-error-soft px-4 py-3 text-sm text-error" role="alert">
                {pollError}
              </div>
            ) : null}

            <Button type="submit" className="w-full" disabled={!canStartSearch}>
              {submitting
                ? 'Starting your scout run...'
                : runActive
                  ? 'Search already in progress'
                  : !profile.searchCountry
                    ? 'Select a country to search'
                    : !helperReady
                      ? 'Set up Search Helper to continue'
                      : 'Start focused search'}
              {!submitting && !runActive && helperReady ? (
                <ArrowRightIcon className="ml-2 h-4 w-4" aria-hidden="true" />
              ) : null}
            </Button>
          </form>
        </section>

        <aside className="space-y-5">
          <section className="rounded-[1.5rem] border border-sidebar/10 bg-sidebar p-5 text-white shadow-lg shadow-slate-950/10 sm:p-6">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/20 text-teal-100">
                <SignalIcon className="h-5 w-5" aria-hidden="true" />
              </span>
              <div>
                <p className="jp-eyebrow !text-teal-200">Ready check</p>
                <h2 className="jp-display mt-1 text-lg font-extrabold">Your search preflight</h2>
              </div>
            </div>
            <ul className="mt-6 space-y-4">
              {[
                {
                  icon: CheckCircleIcon,
                  title: 'Career profile',
                  detail: `${profile.skills.length} skills and ${profile.projects.length} project${profile.projects.length === 1 ? '' : 's'} ready`,
                  ready: true,
                },
                {
                  icon: ComputerDesktopIcon,
                  title: 'Search Helper',
                  detail: helperReady ? 'Connected and browser-ready' : 'Needs connection in Settings',
                  ready: helperReady,
                },
                {
                  icon: MapPinIcon,
                  title: 'Search scope',
                  detail: `${profile.searchCountry ?? 'Pakistan'} • ${profile.searchMaxListings} listings maximum`,
                  ready: Boolean(profile.searchCountry),
                },
              ].map((item) => {
                const Icon = item.icon
                return (
                  <li key={item.title} className="flex gap-3">
                    <span
                      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ${
                        item.ready ? 'bg-primary/20 text-teal-100' : 'bg-white/8 text-slate-400'
                      }`}
                    >
                      <Icon className="h-4 w-4" aria-hidden="true" />
                    </span>
                    <span>
                      <span className="block text-sm font-semibold text-white">{item.title}</span>
                      <span className="mt-0.5 block text-xs leading-5 text-slate-400">{item.detail}</span>
                    </span>
                  </li>
                )
              })}
            </ul>
          </section>

          <section className="jp-surface rounded-[1.5rem] p-5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-secondary-soft text-secondary">
              <LightBulbIcon className="h-5 w-5" aria-hidden="true" />
            </div>
            <h2 className="jp-display mt-4 text-lg font-extrabold tracking-tight text-text-primary">
              A focused title gets better matches.
            </h2>
            <p className="mt-2 text-sm leading-6 text-text-secondary">
              Specific roles such as “Senior Backend Engineer” give JobPilot a cleaner brief than broad labels.
            </p>
          </section>
        </aside>
      </div>

      {restoringRun ? (
        <section className="jp-surface rounded-[1.5rem] p-6">
          <p className="flex items-center gap-2 text-sm text-text-secondary">
            <ArrowPathIcon className="h-4 w-4 animate-spin text-secondary" aria-hidden="true" />
            Restoring your latest search run...
          </p>
        </section>
      ) : activeRunId ? (
        <section className="relative overflow-hidden rounded-[1.5rem] border border-secondary/15 bg-secondary-soft/60 p-5 sm:p-6">
          <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-secondary/12 blur-3xl" />
          <div className="relative grid gap-5 lg:grid-cols-[1fr_auto] lg:items-center">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className={`h-2 w-2 rounded-full ${runActive ? 'animate-pulse bg-secondary' : 'bg-success'}`} />
                <p className="text-xs font-bold uppercase tracking-[0.12em] text-secondary">
                  Run #{runStatus?.runNumber ?? activeRunId}
                </p>
              </div>
              <h2 className="jp-display mt-2 text-xl font-extrabold tracking-tight text-text-primary">
                {runMessage}
              </h2>
              <p className="mt-2 text-sm text-text-secondary">
                {jobs.length} job{jobs.length === 1 ? '' : 's'} discovered • {readyCount} ready for review
              </p>
              {runStatus?.error ? <p className="mt-3 text-sm text-error">{runStatus.error}</p> : null}
            </div>
            <div className="flex flex-col gap-2 sm:flex-row lg:flex-col">
              <Button type="button" variant="secondary" onClick={() => void refreshRun(activeRunId)}>
                <ArrowPathIcon className="mr-2 h-4 w-4" aria-hidden="true" />
                Refresh status
              </Button>
              <Link
                to="/applications"
                className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              >
                Open review queue
                <ArrowRightIcon className="h-4 w-4" aria-hidden="true" />
              </Link>
            </div>
          </div>
        </section>
      ) : null}

      <section className="grid gap-3 sm:grid-cols-2">
        <article className="rounded-2xl border border-border bg-surface/75 p-4">
          <BoltIcon className="h-5 w-5 text-primary" aria-hidden="true" />
          <h2 className="mt-3 text-sm font-semibold text-text-primary">Live in your browser</h2>
          <p className="mt-1 text-xs leading-5 text-text-secondary">
            JobPilot works with your connected Chrome session, not a datacenter bot.
          </p>
        </article>
        <article className="rounded-2xl border border-border bg-surface/75 p-4">
          <LinkIcon className="h-5 w-5 text-secondary" aria-hidden="true" />
          <h2 className="mt-3 text-sm font-semibold text-text-primary">Transparent recommendations</h2>
          <p className="mt-1 text-xs leading-5 text-text-secondary">
            Review the source post, fit evidence, and CV suggestions before you take action.
          </p>
        </article>
      </section>

      {toast ? (
        <div
          role="status"
          className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-xl bg-sidebar px-4 py-3 text-sm font-medium text-white shadow-float"
        >
          {toast}
        </div>
      ) : null}
    </div>
  )
}

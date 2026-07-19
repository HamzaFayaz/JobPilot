import {
  LightBulbIcon,
  MagnifyingGlassIcon,
  ShieldCheckIcon,
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
        if (cancelled || !latest) {
          return
        }
        setActiveRunId(latest.runId)
        setRunStatus(latest)
        const nextJobs = await listRunJobs(latest.runId)
        if (!cancelled) {
          setJobs(nextJobs)
        }
      } catch (error: unknown) {
        if (!cancelled) {
          setPollError(error instanceof Error ? error.message : 'Failed to load latest search run')
        }
      } finally {
        if (!cancelled) {
          setRestoringRun(false)
        }
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
    // Indeed is coming soon — keep searches on LinkedIn.
    if (profile.searchPlatform === 'indeed') {
      setPlatform('linkedin')
      void updateProfile({ searchPlatform: 'linkedin' })
      return
    }
    setPlatform(profile.searchPlatform)
  }, [profile.searchPlatform, updateProfile])

  useEffect(() => {
    if (!activeRunId || !runStatus) {
      return
    }
    if (runStatus.status === 'completed' || runStatus.status === 'failed') {
      if (!jobs.some((job) => job.status === 'analyzing')) {
        return
      }
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
        Loading…
      </div>
    )
  }

  if (profile.projectsIndexingStatus === 'pending') {
    return (
      <div className="mx-auto max-w-lg space-y-4 rounded-xl border border-border bg-surface px-6 py-8 text-center shadow-sm">
        <h1 className="text-xl font-bold text-text-primary">Preparing your profile</h1>
        <p className="text-sm text-text-secondary">
          The system is building project overviews and evidence. This can take a few minutes.
          You can connect Search Helper in Settings while you wait.
        </p>
        <Link
          to="/settings"
          className="inline-flex min-h-10 items-center justify-center rounded-lg bg-primary px-4 text-sm font-semibold text-white hover:bg-primary-hover"
        >
          Open Settings
        </Link>
      </div>
    )
  }

  if (!gate.isComplete) {
    return (
      <div className="mx-auto max-w-lg space-y-4 rounded-xl border border-border bg-surface px-6 py-8 text-center shadow-sm">
        <h1 className="text-xl font-bold text-text-primary">Finish your profile first</h1>
        <p className="text-sm text-text-secondary">
          Search needs a complete profile. Stay on this page URL — finish setup, then return here.
        </p>
        <Link
          to="/profile"
          className="inline-flex min-h-10 items-center justify-center rounded-lg bg-primary px-4 text-sm font-semibold text-white hover:bg-primary-hover"
        >
          Go to Profile
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
  if (profile.projectsIndexingStatus === 'pending') {
    searchBlockers.push('Projects are still being prepared. Please wait a few minutes.')
  }
  if (!profile.targetRoles.length) {
    searchBlockers.push('Add at least one target role on your profile.')
  }
  if (!profile.searchCountry) {
    searchBlockers.push('Select a country in search preferences below.')
  }
  if (!helperReady) {
    searchBlockers.push('Connect Search Helper in Settings and open Chrome with WebBridge.')
  }
  if (runActive) {
    searchBlockers.push('A search or analysis is already running. Open Applications to follow it.')
  }

  const canStartSearch = searchBlockers.length === 0 && !submitting

  const analyzingCount = jobs.filter((job) => job.status === 'analyzing').length
  const readyCount = jobs.filter((job) => job.status === 'ready').length

  return (
    <div className="space-y-8">
      <header>
        <p className="text-sm font-medium text-primary">Search</p>
        <h1 className="mt-1 text-2xl font-bold text-text-primary sm:text-3xl">New search</h1>
        <p className="mt-2 text-sm text-text-secondary">
          Start a LinkedIn Posts search. Job analysis opens in Applications as results arrive.
        </p>
      </header>

      <div className="mx-auto max-w-xl space-y-4">
        <SearchHelperHint onReadyChange={setHelperReady} />

        <div className="rounded-lg border border-border bg-surface p-6 shadow-sm">
          <div className="mb-6 flex items-start gap-3 rounded-lg bg-hitl-bg p-4 text-hitl-text">
            <ShieldCheckIcon className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
            <p className="text-sm">
              <span className="font-semibold">Human-in-the-loop:</span> You approve before
              anything is sent.
            </p>
          </div>

          <form
            className="space-y-6"
            onSubmit={async (e) => {
              e.preventDefault()
              setSubmitting(true)
              setPollError(null)
              try {
                const started = await startSearch()
                setActiveRunId(started.runId)
                await refreshRun(started.runId)
                showToast(`Search run #${started.runNumber} started.`)
                navigate('/applications')
              } catch (error: unknown) {
                const message =
                  error instanceof Error ? error.message : 'Failed to start search run'
                setPollError(message)
                showToast(message)
              } finally {
                setSubmitting(false)
              }
            }}
          >
            <div>
              <label htmlFor="target-role" className="mb-2 block text-sm font-semibold">
                Target role
              </label>
              {profile.targetRoles.length === 0 ? (
                <p className="text-sm text-text-secondary">
                  Add target roles on your profile first.
                </p>
              ) : (
                <select
                  id="target-role"
                  value={role}
                  onChange={(e) => {
                    const nextRole = e.target.value
                    setRole(nextRole)
                    void updateProfile({ searchRole: nextRole })
                  }}
                  disabled={runActive}
                  className="w-full cursor-pointer rounded-lg border border-border bg-surface px-3 py-3 text-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-60 sm:text-sm"
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
              <legend className="mb-2 text-sm font-semibold text-text-primary">Platform</legend>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <label
                  className={`flex cursor-pointer items-center justify-between rounded-lg border p-4 transition-colors duration-200 ${
                    platform === 'linkedin'
                      ? 'border-primary bg-chip-bg/40'
                      : 'border-border hover:border-primary/40'
                  } ${runActive ? 'cursor-not-allowed opacity-60' : ''}`}
                >
                  <span className="flex items-center gap-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded bg-[#0A66C2] text-sm font-bold text-white">
                      in
                    </span>
                    <span className="text-sm font-medium">LinkedIn</span>
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
                  onClick={() => showToast('Indeed — coming soon')}
                  className={`flex items-center justify-between rounded-lg border border-border p-4 text-left transition-colors duration-200 hover:border-primary/40 disabled:cursor-not-allowed disabled:opacity-60`}
                >
                  <span className="flex items-center gap-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded bg-[#2164f3] text-sm font-bold text-white">
                      i
                    </span>
                    <span className="text-sm font-medium">Indeed</span>
                  </span>
                  <span className="rounded-full bg-background px-2 py-0.5 text-[11px] font-semibold uppercase text-text-secondary">
                    Coming soon
                  </span>
                </button>
              </div>
            </fieldset>

            <SearchPreferencesFields
              profile={profile}
              onChange={(patch) => {
                void updateProfile(patch)
              }}
              compact
            />

            <p className="flex items-center gap-2 text-sm text-text-secondary">
              <MagnifyingGlassIcon className="h-4 w-4" aria-hidden="true" />
              {summaryParts.join(' · ')}
            </p>

            {searchBlockers.length > 0 ? (
              <div className="rounded-lg border border-warning/30 bg-hitl-bg/60 px-4 py-3 text-sm text-hitl-text">
                <p className="font-semibold">Before you can search:</p>
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {searchBlockers.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {pollError ? (
              <div className="rounded-lg border border-error/30 bg-error/5 px-4 py-3 text-sm text-error">
                {pollError}
              </div>
            ) : null}

            <Button type="submit" className="w-full" disabled={!canStartSearch}>
              {submitting
                ? 'Starting search...'
                : runActive
                  ? 'Search in progress…'
                  : !profile.searchCountry
                    ? 'Select a country to search'
                    : !helperReady
                      ? 'Set up Search Helper in Settings'
                      : 'Start search'}
            </Button>
          </form>
        </div>
      </div>

      {restoringRun ? (
        <section className="mx-auto max-w-xl rounded-lg border border-border bg-surface p-6 shadow-sm">
          <p className="text-sm text-text-secondary">Loading your latest search run…</p>
        </section>
      ) : activeRunId ? (
        <section className="mx-auto max-w-xl rounded-lg border border-border bg-surface p-6 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-base font-semibold text-text-primary">Current run</h2>
              <p className="mt-1 text-sm text-text-secondary">
                Run #{runStatus?.runNumber ?? activeRunId}
              </p>
            </div>
            <Button type="button" variant="ghost" onClick={() => void refreshRun(activeRunId)}>
              Refresh
            </Button>
          </div>

          <div className="mt-4 space-y-2 text-sm text-text-secondary">
            <p>
              <span className="font-semibold text-text-primary">Status:</span>{' '}
              {runActive ? (
                <span className="inline-flex items-center gap-2">
                  <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-primary" />
                  {runStatus?.status === 'pending'
                    ? 'Starting…'
                    : analyzingCount > 0
                      ? `Analyzing ${analyzingCount} job${analyzingCount === 1 ? '' : 's'}…`
                      : 'Searching on your PC…'}
                </span>
              ) : (
                (runStatus?.status ?? 'pending')
              )}
            </p>
            <p>
              <span className="font-semibold text-text-primary">Jobs found:</span> {jobs.length}
            </p>
            <p>
              <span className="font-semibold text-text-primary">Ready to review:</span> {readyCount}
            </p>
            {runStatus?.error ? (
              <p className="text-red-600">
                <span className="font-semibold">Run error:</span> {runStatus.error}
              </p>
            ) : null}
          </div>

          <div className="mt-6">
            <Link to="/applications">
              <Button type="button" className="w-full">
                Open Applications inbox
              </Button>
            </Link>
            <p className="mt-2 text-center text-xs text-text-secondary">
              Job details, scores, and apply decisions live in Applications.
            </p>
          </div>
        </section>
      ) : null}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <article className="rounded-lg border border-border bg-surface p-5">
          <LightBulbIcon className="mb-2 h-6 w-6 text-primary" aria-hidden="true" />
          <h2 className="text-sm font-semibold">Tip: Be specific with roles</h2>
          <p className="mt-1 text-xs text-text-secondary">
            Narrow titles like &quot;Senior Backend Engineer&quot; produce better matches than
            generic labels.
          </p>
        </article>
        <article className="rounded-lg border border-border bg-surface p-5">
          <ShieldCheckIcon className="mb-2 h-6 w-6 text-primary" aria-hidden="true" />
          <h2 className="text-sm font-semibold">You stay in control</h2>
          <p className="mt-1 text-xs text-text-secondary">
            Mark I applied or Not applying in Applications. Nothing sends automatically.
          </p>
        </article>
      </div>

      {toast ? (
        <div
          role="status"
          className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-lg bg-sidebar px-4 py-3 text-sm text-white shadow-lg"
        >
          {toast}
        </div>
      ) : null}
    </div>
  )
}

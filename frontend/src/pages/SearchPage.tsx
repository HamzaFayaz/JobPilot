import {
  LightBulbIcon,
  MagnifyingGlassIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline'
import { useCallback, useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { getRunStatus, listRunJobs, startSearch, type JobPackage, type SearchRunStatusResponse } from '../api/search'
import { Button } from '../components/ui/Button'
import { SearchHelperHint } from '../components/search/SearchHelperHint'
import { SearchPreferencesFields } from '../components/search/SearchPreferencesFields'
import { useProfile } from '../context/ProfileContext'
import type { SearchPlatform } from '../types/profile'

export function SearchPage() {
  const { profile, gate, updateProfile } = useProfile()
  const [role, setRole] = useState(profile.searchRole ?? profile.targetRoles[0] ?? '')
  const [platform, setPlatform] = useState<SearchPlatform>(profile.searchPlatform)
  const [toast, setToast] = useState<string | null>(null)
  const [activeRunId, setActiveRunId] = useState<number | null>(null)
  const [runStatus, setRunStatus] = useState<SearchRunStatusResponse | null>(null)
  const [jobs, setJobs] = useState<JobPackage[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [pollError, setPollError] = useState<string | null>(null)
  const [helperReady, setHelperReady] = useState(false)

  useEffect(() => {
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
  }, [profile.searchRole, profile.targetRoles, updateProfile])

  useEffect(() => {
    setPlatform(profile.searchPlatform)
  }, [profile.searchPlatform])

  if (!gate.isComplete) {
    return <Navigate to="/profile" replace />
  }

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

  const summaryParts = [
    profile.cvFilename ?? 'No CV',
    `${profile.skills.length} skills`,
    `${profile.projects.length} projects`,
  ]

  const searchBlockers: string[] = []
  if (!profile.targetRoles.length) {
    searchBlockers.push('Add at least one target role on your profile.')
  }
  if (!profile.searchCountry) {
    searchBlockers.push('Select a country in search preferences below.')
  }
  if (!helperReady) {
    searchBlockers.push('Connect Search Helper in Settings and open Chrome with WebBridge.')
  }

  const canStartSearch = searchBlockers.length === 0 && !submitting

  useEffect(() => {
    if (!activeRunId || !runStatus) {
      return
    }
    if (runStatus.status === 'completed' || runStatus.status === 'failed') {
      return
    }

    const timer = window.setInterval(() => {
      void refreshRun(activeRunId).catch((error: unknown) => {
        setPollError(error instanceof Error ? error.message : 'Failed to refresh run status')
      })
    }, 3000)

    return () => window.clearInterval(timer)
  }, [activeRunId, refreshRun, runStatus])

  return (
    <div className="space-y-8">
      <header>
        <p className="text-sm font-medium text-primary">Search</p>
        <h1 className="mt-1 text-2xl font-bold text-text-primary sm:text-3xl">New search</h1>
        <p className="mt-2 text-sm text-text-secondary">
          Configure your agent to find and score jobs on LinkedIn or Indeed.
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
                showToast(`Search run #${started.runId} started.`)
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
                  className="w-full cursor-pointer rounded-lg border border-border bg-surface px-3 py-3 text-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary sm:text-sm"
                >
                  {profile.targetRoles.map((targetRole) => (
                    <option key={targetRole} value={targetRole}>
                      {targetRole}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <fieldset>
              <legend className="mb-2 text-sm font-semibold text-text-primary">Platform</legend>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {([
                  { id: 'linkedin' as const, label: 'LinkedIn', badge: 'in', color: 'bg-[#0A66C2]' },
                  { id: 'indeed' as const, label: 'Indeed', badge: 'i', color: 'bg-[#2164f3]' },
                ]).map((item) => (
                  <label
                    key={item.id}
                    className={`flex cursor-pointer items-center justify-between rounded-lg border p-4 transition-colors duration-200 ${
                      platform === item.id
                        ? 'border-primary bg-chip-bg/40'
                        : 'border-border hover:border-primary/40'
                    }`}
                  >
                    <span className="flex items-center gap-3">
                      <span
                        className={`flex h-8 w-8 items-center justify-center rounded text-sm font-bold text-white ${item.color}`}
                      >
                        {item.badge}
                      </span>
                      <span className="text-sm font-medium">{item.label}</span>
                    </span>
                    <input
                      type="radio"
                      name="platform"
                      value={item.id}
                      checked={platform === item.id}
                      onChange={() => {
                        setPlatform(item.id)
                        void updateProfile({ searchPlatform: item.id })
                      }}
                      className="h-4 w-4 cursor-pointer accent-primary"
                    />
                  </label>
                ))}
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

            <Button
              type="submit"
              className="w-full"
              disabled={!canStartSearch}
            >
              {submitting
                ? 'Starting search...'
                : !profile.searchCountry
                  ? 'Select a country to search'
                  : !helperReady
                    ? 'Set up Search Helper in Settings'
                    : 'Start search'}
            </Button>
          </form>
        </div>
      </div>

      {activeRunId ? (
        <section className="mx-auto max-w-xl rounded-lg border border-border bg-surface p-6 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-base font-semibold text-text-primary">Current run</h2>
              <p className="mt-1 text-sm text-text-secondary">Run #{activeRunId}</p>
            </div>
            <Button type="button" variant="ghost" onClick={() => void refreshRun(activeRunId)}>
              Refresh
            </Button>
          </div>

          <div className="mt-4 space-y-2 text-sm text-text-secondary">
            <p>
              <span className="font-semibold text-text-primary">Status:</span>{' '}
              {runStatus?.status === 'running' || runStatus?.status === 'pending' ? (
                <span className="inline-flex items-center gap-2">
                  <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-primary" />
                  {runStatus.status === 'pending' ? 'Starting…' : 'Searching on your PC…'}
                </span>
              ) : (
                runStatus?.status ?? 'pending'
              )}
            </p>
            <p>
              <span className="font-semibold text-text-primary">Jobs ready:</span>{' '}
              {runStatus?.status === 'running' || runStatus?.status === 'pending'
                ? '—'
                : (runStatus?.jobsReadyCount ?? 0)}
            </p>
            {runStatus?.error ? (
              <p className="text-red-600">
                <span className="font-semibold">Run error:</span> {runStatus.error}
              </p>
            ) : null}
            {pollError ? (
              <p className="text-red-600">
                <span className="font-semibold">Refresh error:</span> {pollError}
              </p>
            ) : null}
          </div>

          <div className="mt-6 space-y-3">
            {runStatus?.status === 'running' || runStatus?.status === 'pending' ? (
              <div className="rounded-lg border border-dashed border-primary/40 bg-chip-bg/30 p-4 text-sm text-text-secondary">
                <p className="font-medium text-text-primary">Search in progress</p>
                <p className="mt-1">
                  Your Search Helper is working on this run. Keep the worker running and Chrome open
                  with the Kimi WebBridge extension connected.
                </p>
              </div>
            ) : jobs.length === 0 ? (
              <p className="text-sm text-text-secondary">
                {runStatus?.status === 'failed'
                  ? 'Search failed before any jobs were saved.'
                  : 'No matching jobs were found for this run.'}
              </p>
            ) : (
              jobs.map((job) => (
                <article key={job.id ?? `${job.url}-${job.title}`} className="rounded-lg border border-border p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-semibold text-text-primary">{job.title}</h3>
                      <p className="text-sm text-text-secondary">{job.company}</p>
                    </div>
                    <span className="rounded-full bg-chip-bg px-2 py-1 text-xs font-medium text-text-primary">
                      {job.status}
                    </span>
                  </div>
                  {job.matchScore !== null ? (
                    <p className="mt-2 text-sm text-text-secondary">Match score: {job.matchScore}</p>
                  ) : null}
                  {job.summary ? <p className="mt-2 text-sm text-text-secondary">{job.summary}</p> : null}
                  {job.descriptionText ? (
                    <p className="mt-2 line-clamp-3 text-sm text-text-secondary">{job.descriptionText}</p>
                  ) : null}
                  {job.url ? (
                    <a
                      href={job.url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 inline-block text-sm font-medium text-primary hover:underline"
                    >
                      View listing
                    </a>
                  ) : null}
                  {job.error ? <p className="mt-2 text-sm text-red-600">{job.error}</p> : null}
                </article>
              ))
            )}
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
            Search results will feed into a human-approved application flow. Nothing sends
            automatically.
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

import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import {
  extractFitMessage,
  extractProjectDecisions,
  getLatestRun,
  listJobs,
  setJobDecision,
  type JobPackage,
  type JobPackageStatus,
  type SearchRunStatusResponse,
} from '../api/search'
import { Button } from '../components/ui/Button'
import { useProfile } from '../context/ProfileContext'

type FilterKey = 'all' | 'analyzing' | 'ready' | 'applied' | 'skipped' | 'failed'

const FILTERS: { key: FilterKey; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'analyzing', label: 'Analyzing' },
  { key: 'ready', label: 'Ready' },
  { key: 'applied', label: 'Applied' },
  { key: 'skipped', label: 'Skipped' },
  { key: 'failed', label: 'Failed' },
]

const LINK_RE = /(https?:\/\/[^\s<>"']+|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g

function statusLabel(status: JobPackageStatus): string {
  switch (status) {
    case 'analyzing':
      return 'Analyzing'
    case 'ready':
      return 'Ready'
    case 'applied':
      return 'Applied'
    case 'skipped':
      return 'Skipped'
    case 'failed':
      return 'Failed'
    default:
      return status
  }
}

function statusClasses(status: JobPackageStatus): string {
  switch (status) {
    case 'analyzing':
      return 'bg-secondary/10 text-secondary'
    case 'ready':
      return 'bg-chip-bg text-primary'
    case 'applied':
      return 'bg-success/10 text-success'
    case 'skipped':
      return 'bg-border text-text-secondary'
    case 'failed':
      return 'bg-error/10 text-error'
    default:
      return 'bg-border text-text-secondary'
  }
}

function splitPostDescription(text: string): { applyBlock: string | null; body: string } {
  const trimmed = text.trim()
  if (!trimmed.toLowerCase().startsWith('how to apply')) {
    return { applyBlock: null, body: trimmed }
  }
  const parts = trimmed.split(/\n\n+/)
  return {
    applyBlock: parts[0] ?? trimmed,
    body: parts.slice(1).join('\n\n').trim(),
  }
}

function scoreTone(score: number | null | undefined): string {
  if (score == null) return 'text-text-secondary'
  if (score >= 75) return 'text-success'
  if (score >= 45) return 'text-warning'
  return 'text-error'
}

function ScoreMeter({
  label,
  score,
  emphasize,
}: {
  label: string
  score: number | null | undefined
  emphasize?: boolean
}) {
  const width = score == null ? 0 : Math.max(0, Math.min(100, score))
  return (
    <div
      className={`rounded-xl border border-border px-4 py-3 ${
        emphasize ? 'bg-chip-bg/40' : 'bg-surface'
      }`}
    >
      <div className="flex items-baseline justify-between gap-2">
        <p className="text-xs font-medium uppercase tracking-wide text-text-secondary">{label}</p>
        <p className={`text-2xl font-bold tabular-nums ${scoreTone(score)}`}>
          {score != null ? score : '—'}
        </p>
      </div>
      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-border/80">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            score == null
              ? 'bg-border'
              : score >= 75
                ? 'bg-success'
                : score >= 45
                  ? 'bg-warning'
                  : 'bg-error'
          }`}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  )
}

function LinkedText({ text }: { text: string }) {
  const nodes: ReactNode[] = []
  let last = 0
  let match: RegExpExecArray | null
  const re = new RegExp(LINK_RE.source, 'g')
  while ((match = re.exec(text)) !== null) {
    if (match.index > last) {
      nodes.push(text.slice(last, match.index))
    }
    const token = match[0]
    const href = token.includes('@') ? `mailto:${token}` : token.replace(/[),.;]+$/, '')
    const display = token.replace(/[),.;]+$/, '')
    nodes.push(
      <a
        key={`${match.index}-${display}`}
        href={href}
        target={token.includes('@') ? undefined : '_blank'}
        rel={token.includes('@') ? undefined : 'noreferrer'}
        className="font-medium text-primary underline decoration-primary/30 underline-offset-2 hover:decoration-primary"
      >
        {display}
      </a>,
    )
    last = match.index + token.length
  }
  if (last < text.length) nodes.push(text.slice(last))
  return <>{nodes}</>
}

function JobListItem({
  job,
  selected,
  onSelect,
}: {
  job: JobPackage
  selected: boolean
  onSelect: () => void
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full cursor-pointer border-b border-border px-4 py-3.5 text-left transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-primary ${
        selected ? 'border-l-2 border-l-primary bg-chip-bg/45' : 'bg-surface hover:bg-background'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-text-primary">{job.title}</p>
          <p className="mt-0.5 truncate text-xs text-text-secondary">{job.company}</p>
        </div>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium ${statusClasses(job.status)}`}
        >
          {statusLabel(job.status)}
        </span>
      </div>
      {job.status === 'analyzing' ? (
        <p className="mt-2 flex items-center gap-2 text-xs text-text-secondary">
          <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-primary" />
          Scoring against your CV…
        </p>
      ) : job.currentCvScore != null ? (
        <p className={`mt-2 text-xs font-medium ${scoreTone(job.currentCvScore)}`}>
          {job.currentCvScore}
          {job.suggestedCvScore != null && job.suggestedCvScore !== job.currentCvScore
            ? ` → ${job.suggestedCvScore}`
            : ''}{' '}
          fit
        </p>
      ) : null}
    </button>
  )
}

function JobDetailPanel({
  job,
  onDecision,
  busy,
}: {
  job: JobPackage
  onDecision: (decision: 'applied' | 'skipped') => void
  busy: boolean
}) {
  const decisions = extractProjectDecisions(job)
  const fitMessage = extractFitMessage(job)
  const analyzing = job.status === 'analyzing'
  const { applyBlock, body } = splitPostDescription(job.descriptionText || '')
  const applyLines = (applyBlock || '')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(1)

  return (
    <div className="flex h-full flex-col">
      <header className="relative overflow-hidden border-b border-border px-4 py-5 sm:px-6">
        <div
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(13,148,136,0.12),_transparent_55%)]"
          aria-hidden="true"
        />
        <div className="relative flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-primary">
              {job.company}
            </p>
            <h2 className="mt-1 text-xl font-bold leading-snug text-text-primary sm:text-2xl">
              {job.title}
            </h2>
            {job.url && !job.url.startsWith('linkedin-post://') ? (
              <a
                href={job.url}
                target="_blank"
                rel="noreferrer"
                className="mt-2 inline-flex text-xs font-medium text-primary hover:underline"
              >
                Open listing
              </a>
            ) : (
              <p className="mt-2 text-xs text-text-secondary">
                LinkedIn post — use apply info below (no direct post URL).
              </p>
            )}
          </div>
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold ${statusClasses(job.status)}`}
          >
            {statusLabel(job.status)}
          </span>
        </div>
      </header>

      <div className="flex-1 space-y-5 overflow-y-auto px-4 py-5 sm:px-6">
        {analyzing ? (
          <div className="rounded-xl border border-dashed border-primary/40 bg-chip-bg/30 px-4 py-3 text-sm text-text-secondary">
            <p className="font-medium text-text-primary">Analysis in progress</p>
            <p className="mt-1">
              Scores and project suggestions appear below when ready. The post text is available
              now.
            </p>
          </div>
        ) : null}

        {applyLines.length > 0 ? (
          <section className="rounded-xl border border-primary/25 bg-gradient-to-br from-chip-bg/70 to-surface px-4 py-4 shadow-sm">
            <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-primary">
              How to apply
            </p>
            <div className="mt-2 space-y-1.5 text-sm leading-relaxed text-text-primary">
              {applyLines.map((line) => (
                <p key={line}>
                  <LinkedText text={line} />
                </p>
              ))}
            </div>
          </section>
        ) : null}

        <section className="space-y-2">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-semibold text-text-primary">Job post</h3>
            <span className="text-[11px] text-text-secondary">Source listing</span>
          </div>
          <div className="rounded-xl border border-border bg-surface px-4 py-4 text-sm leading-7 text-text-primary shadow-sm">
            {body || job.descriptionText ? (
              <div className="whitespace-pre-wrap">
                <LinkedText text={body || job.descriptionText} />
              </div>
            ) : (
              <p className="text-text-secondary">No description available for this listing.</p>
            )}
          </div>
        </section>

        {!analyzing && job.status !== 'failed' ? (
          <section className="space-y-3">
            <h3 className="text-sm font-semibold text-text-primary">Fit analysis</h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:max-w-md">
              <ScoreMeter label="Current CV" score={job.currentCvScore} />
              <ScoreMeter label="Suggested" score={job.suggestedCvScore} emphasize />
            </div>
            {fitMessage ? (
              <p className="rounded-lg bg-background px-3 py-2 text-sm text-text-secondary">
                {fitMessage}
              </p>
            ) : null}
            {job.summary ? (
              <p className="text-sm leading-relaxed text-text-primary">{job.summary}</p>
            ) : null}
          </section>
        ) : null}

        {job.status === 'failed' && job.error ? (
          <div className="rounded-xl border border-error/30 bg-error/5 px-4 py-3 text-sm text-error">
            {job.error}
          </div>
        ) : null}

        {!analyzing && decisions.length > 0 ? (
          <section className="space-y-3">
            <h3 className="text-sm font-semibold text-text-primary">Project recommendations</h3>
            <ul className="space-y-3">
              {decisions.map((item) => (
                <li
                  key={`${item.slotIndex}-${item.currentProjectName}`}
                  className="rounded-xl border border-border bg-surface px-4 py-3 shadow-sm"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase ${
                        item.action === 'swap'
                          ? 'bg-warning/15 text-warning'
                          : 'bg-border text-text-secondary'
                      }`}
                    >
                      {item.action}
                    </span>
                    {item.impact ? (
                      <span className="text-[11px] text-text-secondary">Impact: {item.impact}</span>
                    ) : null}
                  </div>
                  <p className="mt-2 text-sm font-medium text-text-primary">
                    {item.currentProjectName}
                    {item.action === 'swap' && item.swapInProjectName
                      ? ` → ${item.swapInProjectName}`
                      : ''}
                  </p>
                  {item.rationale ? (
                    <p className="mt-1 text-sm text-text-secondary">{item.rationale}</p>
                  ) : null}
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </div>

      {job.status === 'ready' ? (
        <footer className="flex flex-col gap-2 border-t border-border bg-surface/90 px-4 py-4 backdrop-blur sm:flex-row sm:px-6">
          <Button
            type="button"
            className="w-full sm:flex-1"
            disabled={busy || job.id == null}
            onClick={() => onDecision('applied')}
          >
            I applied
          </Button>
          <Button
            type="button"
            variant="secondary"
            className="w-full sm:flex-1"
            disabled={busy || job.id == null}
            onClick={() => onDecision('skipped')}
          >
            Not applying
          </Button>
        </footer>
      ) : null}
    </div>
  )
}

export function ApplicationsPage() {
  const { gate, loading: profileLoading } = useProfile()
  const [jobs, setJobs] = useState<JobPackage[]>([])
  const [runStatus, setRunStatus] = useState<SearchRunStatusResponse | null>(null)
  const [filter, setFilter] = useState<FilterKey>('all')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [decisionBusy, setDecisionBusy] = useState(false)
  const [mobileShowDetail, setMobileShowDetail] = useState(false)

  const refresh = useCallback(async () => {
    const [latest, nextJobs] = await Promise.all([getLatestRun(), listJobs()])
    setRunStatus(latest)
    setJobs(nextJobs)
    setError(null)
  }, [])

  useEffect(() => {
    let cancelled = false
    void (async () => {
      try {
        await refresh()
      } catch (err: unknown) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load applications')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [refresh])

  useEffect(() => {
    const active =
      runStatus?.status === 'pending' ||
      runStatus?.status === 'running' ||
      jobs.some((job) => job.status === 'analyzing')
    if (!active) return

    const timer = window.setInterval(() => {
      void refresh().catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to refresh applications')
      })
    }, 2500)
    return () => window.clearInterval(timer)
  }, [jobs, refresh, runStatus?.status])

  const filtered = useMemo(() => {
    if (filter === 'all') return jobs
    return jobs.filter((job) => job.status === filter)
  }, [filter, jobs])

  useEffect(() => {
    if (filtered.length === 0) {
      setSelectedId(null)
      return
    }
    if (selectedId != null && filtered.some((job) => job.id === selectedId)) return
    setSelectedId(filtered[0]?.id ?? null)
  }, [filtered, selectedId])

  const selected = filtered.find((job) => job.id === selectedId) ?? null

  async function handleDecision(decision: 'applied' | 'skipped') {
    if (selected?.id == null) return
    setDecisionBusy(true)
    try {
      const updated = await setJobDecision(selected.id, decision)
      setJobs((prev) => prev.map((job) => (job.id === updated.id ? updated : job)))
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update job decision')
    } finally {
      setDecisionBusy(false)
    }
  }

  if (profileLoading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-sm text-text-secondary">
        Loading…
      </div>
    )
  }

  if (!gate.isComplete) {
    return (
      <div className="mx-auto max-w-lg space-y-4 rounded-xl border border-border bg-surface px-6 py-8 text-center shadow-sm">
        <h1 className="text-xl font-bold text-text-primary">Finish your profile first</h1>
        <p className="text-sm text-text-secondary">
          Applications needs a complete profile (CV, skills, and at least one project). You can stay
          on this URL — open Profile to finish setup, then come back.
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

  return (
    <div className="-mx-4 -my-6 flex min-h-[calc(100vh-3.5rem)] flex-col sm:-mx-6 lg:mx-0 lg:my-0 lg:min-h-[calc(100vh-3rem)] lg:rounded-xl lg:border lg:border-border lg:bg-surface lg:shadow-sm">
      <header className="border-b border-border bg-surface px-4 py-4 sm:px-6">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-primary">Applications</p>
            <h1 className="mt-1 text-2xl font-bold text-text-primary">Job inbox</h1>
            <p className="mt-1 text-sm text-text-secondary">
              {runStatus?.status === 'pending' || runStatus?.status === 'running'
                ? 'Search running — jobs appear here as analysis starts.'
                : jobs.length > 0
                  ? `${jobs.length} job${jobs.length === 1 ? '' : 's'} in your inbox`
                  : 'Start a search to fill this inbox.'}
            </p>
          </div>
          {runStatus ? (
            <p className="text-xs text-text-secondary">
              Run #{runStatus.runNumber} · {runStatus.status}
            </p>
          ) : null}
        </div>

        <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
          {FILTERS.map((item) => {
            const count =
              item.key === 'all' ? jobs.length : jobs.filter((job) => job.status === item.key).length
            return (
              <button
                key={item.key}
                type="button"
                onClick={() => setFilter(item.key)}
                className={`min-h-9 shrink-0 cursor-pointer rounded-full px-3 text-xs font-semibold transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                  filter === item.key
                    ? 'bg-primary text-white'
                    : 'bg-background text-text-secondary hover:bg-border/60'
                }`}
              >
                {item.label}
                {count > 0 ? ` (${count})` : ''}
              </button>
            )
          })}
        </div>
      </header>

      {error ? (
        <div className="border-b border-error/30 bg-error/5 px-4 py-3 text-sm text-error">{error}</div>
      ) : null}

      {loading ? (
        <div className="flex flex-1 items-center justify-center p-8 text-sm text-text-secondary">
          Loading applications…
        </div>
      ) : (
        <div className="flex min-h-0 flex-1">
          <aside
            className={`w-full border-r border-border bg-surface lg:block lg:w-80 xl:w-96 ${
              mobileShowDetail ? 'hidden' : 'block'
            }`}
          >
            {filtered.length === 0 ? (
              <div className="px-4 py-10 text-center text-sm text-text-secondary">
                No jobs in this filter yet.
              </div>
            ) : (
              <div className="h-full overflow-y-auto">
                {filtered.map((job) => (
                  <JobListItem
                    key={job.id ?? `${job.title}-${job.company}`}
                    job={job}
                    selected={job.id === selectedId}
                    onSelect={() => {
                      setSelectedId(job.id)
                      setMobileShowDetail(true)
                    }}
                  />
                ))}
              </div>
            )}
          </aside>

          <section
            className={`min-w-0 flex-1 bg-background ${
              mobileShowDetail ? 'block' : 'hidden lg:block'
            }`}
          >
            {selected ? (
              <>
                <div className="border-b border-border px-4 py-2 lg:hidden">
                  <Button type="button" variant="ghost" onClick={() => setMobileShowDetail(false)}>
                    ← Back to list
                  </Button>
                </div>
                <JobDetailPanel job={selected} onDecision={handleDecision} busy={decisionBusy} />
              </>
            ) : (
              <div className="flex h-full items-center justify-center p-8 text-sm text-text-secondary">
                Select a job to review details.
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  )
}

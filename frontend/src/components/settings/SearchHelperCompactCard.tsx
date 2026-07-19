import {
  ArrowDownTrayIcon,
  ArrowPathIcon,
  ArrowTopRightOnSquareIcon,
  CheckCircleIcon,
  ClipboardDocumentIcon,
  ComputerDesktopIcon,
  ExclamationTriangleIcon,
  LinkIcon,
  PuzzlePieceIcon,
} from '@heroicons/react/24/outline'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  getWorkerStatus,
  pairWorker,
  unpairWorker,
  type BrowserHealth,
} from '../../api/worker'
import { DOWNLOADS } from '../../constants/downloads'
import { Button } from '../ui/Button'

const WEBBRIDGE_INSTALL_URL = 'https://www.kimi.com/features/webbridge'
const WEBBRIDGE_LOCKED_DAEMON = 'v1.10.0'
const WEBBRIDGE_LOCKED_EXTENSION = '1.11.3'

const HEALTH_LABELS: Record<BrowserHealth, string> = {
  ready: 'Browser ready',
  busy: 'Search running',
  not_installed: 'WebBridge not connected',
  daemon_down: 'WebBridge is starting',
  profile_setup: 'Browser setup needed',
  error: 'Needs attention',
}

export function SearchHelperCompactCard() {
  const [connected, setConnected] = useState(false)
  const [browserHealth, setBrowserHealth] = useState<BrowserHealth | null>(null)
  const [workerToken, setWorkerToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [pairing, setPairing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const status = await getWorkerStatus()
      setConnected(status.connected)
      setBrowserHealth(status.browserHealth ?? null)
      setError(null)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Could not load Search Helper status')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
    const timer = window.setInterval(() => void refresh(), 3000)
    return () => window.clearInterval(timer)
  }, [refresh])

  const handlePair = async () => {
    setPairing(true)
    setError(null)
    try {
      const response = await pairWorker()
      setWorkerToken(response.workerToken)
      await refresh()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Could not create pairing code')
    } finally {
      setPairing(false)
    }
  }

  const handleUnpair = async () => {
    setPairing(true)
    setError(null)
    try {
      await unpairWorker()
      setWorkerToken(null)
      await refresh()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Could not disconnect Search Helper')
    } finally {
      setPairing(false)
    }
  }

  const handleCopyToken = async () => {
    if (!workerToken) return

    let copiedSuccessfully = false
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(workerToken)
        copiedSuccessfully = true
      }
    } catch {
      // Clipboard access may be unavailable on a non-secure local URL.
    }

    if (!copiedSuccessfully) {
      const textarea = document.createElement('textarea')
      textarea.value = workerToken
      textarea.setAttribute('readonly', '')
      textarea.style.position = 'fixed'
      textarea.style.left = '-9999px'
      document.body.appendChild(textarea)
      textarea.select()
      copiedSuccessfully = document.execCommand('copy')
      document.body.removeChild(textarea)
    }

    if (!copiedSuccessfully) {
      setError('Could not copy the code. Select it and press Ctrl+C.')
      return
    }

    setCopied(true)
    window.setTimeout(() => setCopied(false), 2000)
  }

  const browserLabel = browserHealth ? HEALTH_LABELS[browserHealth] : 'Set up browser'
  const isSearchReady = connected && browserHealth === 'ready'
  const statusLabel = loading
    ? 'Checking connection'
    : isSearchReady
      ? 'Ready to search'
      : connected
        ? browserLabel
        : 'Helper not connected'

  return (
    <section className="jp-surface rounded-[1.5rem] p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-primary-soft text-primary">
            <ComputerDesktopIcon className="h-5 w-5" aria-hidden="true" />
          </span>
          <div>
            <p className="jp-eyebrow">Desktop connection</p>
            <h2 className="jp-display mt-1 text-xl font-extrabold tracking-tight text-text-primary">Search Helper</h2>
            <p className="mt-2 max-w-xl text-sm leading-6 text-text-secondary">
              Connect this PC and your LinkedIn Chrome profile when you are ready to search.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 self-start">
          <span className={`inline-flex min-h-9 items-center gap-2 rounded-full px-3 text-xs font-bold ${isSearchReady ? 'bg-success-soft text-success' : connected ? 'bg-warning-soft text-warning' : 'bg-surface-muted text-text-secondary'}`}>
            <span className={`h-1.5 w-1.5 rounded-full ${isSearchReady ? 'bg-success' : connected ? 'bg-warning' : 'bg-text-tertiary'}`} />
            {statusLabel}
          </span>
          <Button
            type="button"
            variant="ghost"
            className="min-h-9 min-w-9 rounded-lg p-2"
            onClick={() => void refresh()}
            aria-label="Refresh Search Helper status"
            title="Refresh status"
          >
            <ArrowPathIcon className="h-4 w-4" aria-hidden="true" />
          </Button>
        </div>
      </div>

      {error ? (
        <div className="mt-4 flex items-start gap-3 rounded-xl border border-error/20 bg-error-soft px-4 py-3 text-sm text-error">
          <ExclamationTriangleIcon className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
          <p>{error}</p>
        </div>
      ) : null}

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <div className="rounded-2xl border border-border bg-surface-muted/45 p-4">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-secondary-soft text-secondary">
            <PuzzlePieceIcon className="h-4 w-4" aria-hidden="true" />
          </span>
          <p className="mt-3 text-sm font-extrabold text-text-primary">1. Browser</p>
          <p className="mt-1 text-xs leading-5 text-text-secondary">{browserLabel}. Use the Chrome profile where you use LinkedIn.</p>
          <p className="mt-2 text-[11px] leading-5 text-text-secondary">Required: daemon <strong className="text-text-primary">{WEBBRIDGE_LOCKED_DAEMON}</strong> + Chrome extension <strong className="text-text-primary">{WEBBRIDGE_LOCKED_EXTENSION}</strong>. Do not auto-update.</p>
          <a href={WEBBRIDGE_INSTALL_URL} target="_blank" rel="noreferrer" className="mt-3 inline-flex items-center gap-1 text-xs font-bold text-primary hover:text-primary-hover hover:underline">
            Get Kimi WebBridge <ArrowTopRightOnSquareIcon className="h-3.5 w-3.5" aria-hidden="true" />
          </a>
        </div>

        <div className="rounded-2xl border border-border bg-surface-muted/45 p-4">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary-soft text-primary">
            <ArrowDownTrayIcon className="h-4 w-4" aria-hidden="true" />
          </span>
          <p className="mt-3 text-sm font-extrabold text-text-primary">2. Helper app</p>
          <p className="mt-1 text-xs leading-5 text-text-secondary">Download the Windows Helper and open its Settings screen.</p>
          <a href={DOWNLOADS.searchHelperExe} className="mt-3 inline-flex items-center gap-1 text-xs font-bold text-primary hover:text-primary-hover hover:underline">
            Download Helper <ArrowDownTrayIcon className="h-3.5 w-3.5" aria-hidden="true" />
          </a>
        </div>

        <div className="rounded-2xl border border-primary/15 bg-primary-soft/35 p-4">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-white shadow-sm shadow-primary/25">
            <LinkIcon className="h-4 w-4" aria-hidden="true" />
          </span>
          <p className="mt-3 text-sm font-extrabold text-text-primary">3. Pair this PC</p>
          <p className="mt-1 text-xs leading-5 text-text-secondary">
            {workerToken ? 'Your pairing code is ready in the panel below.' : 'Generate a code only after the Search Helper app is open.'}
          </p>
          <Button type="button" className="mt-3 min-h-9 px-3 text-xs" onClick={() => void handlePair()} disabled={pairing}>
            {pairing ? 'Creating code...' : workerToken ? 'Generate a new code' : 'Create pairing code'}
          </Button>
        </div>
      </div>

      {workerToken ? (
        <section className="mt-4 rounded-2xl border border-primary/25 bg-primary-soft/45 p-4 sm:p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary text-white shadow-sm shadow-primary/20">
                <CheckCircleIcon className="h-5 w-5" aria-hidden="true" />
              </span>
              <div>
                <p className="jp-eyebrow">Pairing code ready</p>
                <h3 className="mt-1 text-base font-extrabold text-text-primary">Copy this code into Search Helper</h3>
                <p className="mt-1 text-sm leading-6 text-text-secondary">Paste it in Search Helper settings, save, then select Start.</p>
                <p className="mt-2 text-xs font-medium leading-5 text-warning">This pairing code is shown only in this session. Copy it now; if you refresh or leave this page before pairing, create a new code.</p>
              </div>
            </div>
            <Button type="button" variant="secondary" className="shrink-0" onClick={() => void handleCopyToken()}>
              <ClipboardDocumentIcon className="mr-2 h-4 w-4" aria-hidden="true" />
              {copied ? 'Copied' : 'Copy pairing code'}
            </Button>
          </div>
          <code className="mt-4 block break-all rounded-xl border border-primary/15 bg-surface px-4 py-4 font-mono text-sm font-bold tracking-wide text-text-primary sm:text-base">
            {workerToken}
          </code>
          <div className="mt-4 grid gap-2 text-xs leading-5 text-text-secondary sm:grid-cols-3">
            <p className="rounded-lg bg-surface/75 px-3 py-2"><strong className="text-text-primary">1.</strong> Copy the code.</p>
            <p className="rounded-lg bg-surface/75 px-3 py-2"><strong className="text-text-primary">2.</strong> Paste it in Helper settings.</p>
            <p className="rounded-lg bg-surface/75 px-3 py-2"><strong className="text-text-primary">3.</strong> Save, then select Start.</p>
          </div>
        </section>
      ) : null}

      <div className="mt-5 flex flex-col gap-3 border-t border-border pt-4 sm:flex-row sm:items-center sm:justify-between">
        <Link to="/settings/search-helper-guide" className="inline-flex items-center gap-2 text-sm font-bold text-primary hover:text-primary-hover hover:underline">
          View step-by-step setup guide and rules
          <ArrowTopRightOnSquareIcon className="h-4 w-4" aria-hidden="true" />
        </Link>
        <div className="flex flex-wrap items-center gap-3">
          {isSearchReady ? (
            <Link to="/search" className="inline-flex min-h-10 items-center justify-center rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2">
              Start job search
            </Link>
          ) : null}
          {connected ? (
            <Button type="button" variant="ghost" className="min-h-9 px-3 text-xs" onClick={() => void handleUnpair()} disabled={pairing}>
              Disconnect
            </Button>
          ) : null}
        </div>
      </div>
    </section>
  )
}

import {
  ArrowPathIcon,
  ArrowTopRightOnSquareIcon,
  ClipboardDocumentIcon,
  ComputerDesktopIcon,
  PuzzlePieceIcon,
} from '@heroicons/react/24/outline'
import { useCallback, useEffect, useState } from 'react'
import {
  getWorkerStatus,
  pairWorker,
  unpairWorker,
  type BrowserHealth,
} from '../../api/worker'
import { Button } from '../ui/Button'

const WEBBRIDGE_INSTALL_URL = 'https://www.kimi.com/features/webbridge'
/** Locked pair for JobPilot LinkedIn Posts — do not casually upgrade. */
const WEBBRIDGE_LOCKED_DAEMON = 'v1.10.0'
const WEBBRIDGE_LOCKED_EXTENSION = '1.11.3'
const WEBBRIDGE_VERSION_NOTE = `Use daemon ${WEBBRIDGE_LOCKED_DAEMON} + extension ${WEBBRIDGE_LOCKED_EXTENSION}. Do not auto-upgrade — newer builds can break LinkedIn Posts search.`

const HEALTH_LABELS: Record<BrowserHealth, string> = {
  ready: 'Ready to search',
  busy: 'Running a search',
  not_installed: 'Open Chrome — extension not connected',
  daemon_down: 'Starting WebBridge daemon…',
  profile_setup: 'WebBridge setup needed',
  error: 'Error',
}

const HEALTH_HINTS: Partial<Record<BrowserHealth, string>> = {
  not_installed:
    'Open Chrome with the Kimi WebBridge extension installed. It reconnects automatically.',
  daemon_down:
    'The Search Helper will try to start the daemon. If this persists, run: kimi-webbridge.exe start',
  profile_setup: 'Install Kimi WebBridge and the Chrome extension (see link below).',
}

function WebBridgeInstallCard() {
  return (
    <div className="rounded-lg border border-primary/20 bg-chip-bg/25 px-4 py-4">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
          <PuzzlePieceIcon className="h-5 w-5 text-primary" aria-hidden="true" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-text-primary">Install Kimi WebBridge</p>
          <p className="mt-1 text-xs text-text-secondary">
            Download the desktop helper and add the Chrome extension — both are required for
            browser search.
          </p>
          <p className="mt-2 text-xs font-medium text-text-primary">{WEBBRIDGE_VERSION_NOTE}</p>
          <a
            href={WEBBRIDGE_INSTALL_URL}
            target="_blank"
            rel="noreferrer"
            className="mt-3 inline-flex min-h-10 cursor-pointer items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white transition-colors duration-200 hover:bg-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          >
            Get Kimi WebBridge
            <ArrowTopRightOnSquareIcon className="h-4 w-4" aria-hidden="true" />
          </a>
        </div>
      </div>
    </div>
  )
}

export function SearchHelperSettings() {
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
      const message = err instanceof Error ? err.message : 'Failed to load Search Helper status'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
    const timer = window.setInterval(() => {
      void refresh()
    }, 3000)
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
      const message = err instanceof Error ? err.message : 'Failed to pair Search Helper'
      setError(message)
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
      const message = err instanceof Error ? err.message : 'Failed to disconnect Search Helper'
      setError(message)
    } finally {
      setPairing(false)
    }
  }

  const handleCopyToken = async () => {
    if (!workerToken) {
      return
    }
    await navigator.clipboard.writeText(workerToken)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 2000)
  }

  const healthLabel = browserHealth ? HEALTH_LABELS[browserHealth] ?? browserHealth : null
  const healthHint = browserHealth ? HEALTH_HINTS[browserHealth] : null
  const isSearchReady = connected && browserHealth === 'ready'

  return (
    <section className="rounded-xl border border-border bg-surface p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-chip-bg">
          <ComputerDesktopIcon className="h-6 w-6 text-primary" aria-hidden="true" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-text-primary">Search Helper</h2>
              <p className="mt-1 text-sm text-text-secondary">
                Runs on this PC — Kimi WebBridge + Qwen search your real Chrome session.
              </p>
            </div>
            <Button type="button" variant="ghost" onClick={() => void refresh()} aria-label="Refresh status">
              <ArrowPathIcon className="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>

          <div
            className={`mt-4 rounded-lg px-3 py-2 text-sm ${
              isSearchReady
                ? 'bg-success/10 text-success'
                : connected
                  ? 'bg-warning/10 text-warning'
                  : 'bg-background text-text-secondary'
            }`}
          >
            {loading ? (
              <span>Checking connection…</span>
            ) : connected ? (
              <span>
                Worker connected
                {healthLabel ? ` · ${healthLabel}` : ''}
              </span>
            ) : (
              <span>Worker not connected — pair below and run main.py</span>
            )}
          </div>

          {healthHint ? <p className="mt-2 text-xs text-text-secondary">{healthHint}</p> : null}
          {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}

          {!isSearchReady ? (
            <div className="mt-4">
              <WebBridgeInstallCard />
            </div>
          ) : null}

          <details className="mt-4 rounded-lg border border-border bg-background/50 px-4 py-3 text-sm">
            <summary className="cursor-pointer font-medium text-text-primary">
              Full setup checklist
            </summary>
            <ol className="mt-3 list-decimal space-y-2 pl-5 text-text-secondary">
              <li>
                Install Kimi WebBridge —{' '}
                <a
                  href={WEBBRIDGE_INSTALL_URL}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 font-medium text-primary hover:underline"
                >
                  kimi.com/features/webbridge
                  <ArrowTopRightOnSquareIcon className="h-3.5 w-3.5" aria-hidden="true" />
                </a>{' '}
                (binary {WEBBRIDGE_LOCKED_DAEMON} + Chrome extension {WEBBRIDGE_LOCKED_EXTENSION}).
                Do not auto-upgrade until Posts search is re-tested.
              </li>
              <li>Log into LinkedIn in your normal Chrome</li>
              <li>Pair this computer below and paste the token into worker/.env</li>
              <li>
                Run:{' '}
                <code className="rounded bg-surface px-1.5 py-0.5 text-xs">
                  .\.venv\Scripts\python.exe main.py
                </code>
              </li>
            </ol>
          </details>

          <div className="mt-4 flex flex-wrap gap-3">
            <Button type="button" onClick={() => void handlePair()} disabled={pairing}>
              {pairing ? 'Generating token…' : connected ? 'Generate new token' : 'Connect this computer'}
            </Button>
            {connected ? (
              <Button type="button" variant="ghost" onClick={() => void handleUnpair()} disabled={pairing}>
                Disconnect
              </Button>
            ) : null}
          </div>

          {workerToken ? (
            <div className="mt-4 rounded-lg border border-primary/20 bg-chip-bg/30 p-4">
              <p className="text-sm font-semibold text-text-primary">Worker token</p>
              <p className="mt-1 text-xs text-text-secondary">
                Paste into <code>worker/.env</code> as <code>WORKER_TOKEN</code>, then restart the helper.
              </p>
              <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center">
                <code className="block flex-1 break-all rounded-lg bg-surface px-3 py-2 text-xs text-text-primary">
                  {workerToken}
                </code>
                <Button type="button" variant="secondary" onClick={() => void handleCopyToken()}>
                  <ClipboardDocumentIcon className="mr-2 h-4 w-4" aria-hidden="true" />
                  {copied ? 'Copied' : 'Copy'}
                </Button>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  )
}

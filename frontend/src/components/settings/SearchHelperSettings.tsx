import {
  ArrowPathIcon,
  ClipboardDocumentIcon,
  ComputerDesktopIcon,
} from '@heroicons/react/24/outline'
import { useCallback, useEffect, useState } from 'react'
import {
  getWorkerStatus,
  pairWorker,
  unpairWorker,
  type BrowserHealth,
} from '../../api/worker'
import { Button } from '../ui/Button'

const HEALTH_LABELS: Record<BrowserHealth, string> = {
  ready: 'Ready',
  busy: 'Running a search',
  not_installed: 'Not installed',
  daemon_down: 'Daemon down',
  profile_setup: 'WebBridge setup needed',
  error: 'Error',
}

export function SearchHelperSettings() {
  const [connected, setConnected] = useState(false)
  const [healthLabel, setHealthLabel] = useState<string | null>(null)
  const [workerToken, setWorkerToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [pairing, setPairing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const status = await getWorkerStatus()
      setConnected(status.connected)
      setHealthLabel(
        status.browserHealth ? HEALTH_LABELS[status.browserHealth] ?? status.browserHealth : null,
      )
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

  return (
    <section className="rounded-lg border border-border bg-surface p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <ComputerDesktopIcon className="mt-0.5 h-6 w-6 shrink-0 text-primary" aria-hidden="true" />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-text-primary">Search Helper</h2>
              <p className="mt-1 text-sm text-text-secondary">
                Connect this computer to run LinkedIn/Indeed search locally via Kimi WebBridge.
              </p>
            </div>
            <Button type="button" variant="ghost" onClick={() => void refresh()}>
              <ArrowPathIcon className="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>

          <div className="mt-4 text-sm text-text-secondary">
            {loading ? (
              <span>Checking connection…</span>
            ) : connected ? (
              <span>
                Connected{healthLabel ? ` · ${healthLabel}` : ''}
              </span>
            ) : (
              <span>Not connected</span>
            )}
          </div>

          {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}

          <div className="mt-4 space-y-3">
            <p className="text-sm text-text-secondary">
              Pair this computer, copy the token into <code>worker/.env</code> as{' '}
              <code>WORKER_TOKEN</code>, then run:
            </p>
            <p className="rounded-lg bg-chip-bg px-3 py-2 font-mono text-xs text-text-primary">
              .\.venv\Scripts\python.exe main.py
            </p>
            <div className="flex flex-wrap gap-3">
              <Button type="button" onClick={() => void handlePair()} disabled={pairing}>
                {pairing ? 'Generating token…' : connected ? 'Generate new token' : 'Connect this computer'}
              </Button>
              {connected ? (
                <Button type="button" variant="ghost" onClick={() => void handleUnpair()} disabled={pairing}>
                  Disconnect
                </Button>
              ) : null}
            </div>
          </div>

          {workerToken ? (
            <div className="mt-4 rounded-lg border border-border bg-chip-bg/40 p-4">
              <p className="text-sm font-semibold text-text-primary">One-time worker token</p>
              <p className="mt-1 text-xs text-text-secondary">
                Paste into <code>worker/.env</code> and restart the Search Helper.
              </p>
              <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center">
                <code className="block flex-1 break-all rounded-lg bg-surface px-3 py-2 text-xs text-text-primary">
                  {workerToken}
                </code>
                <Button type="button" variant="secondary" onClick={() => void handleCopyToken()}>
                  <ClipboardDocumentIcon className="mr-2 h-4 w-4" aria-hidden="true" />
                  {copied ? 'Copied' : 'Copy token'}
                </Button>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  )
}

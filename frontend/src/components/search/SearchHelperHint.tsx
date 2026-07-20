import {
  ArrowTopRightOnSquareIcon,
  CheckCircleIcon,
  ComputerDesktopIcon,
  WrenchScrewdriverIcon,
} from '@heroicons/react/24/outline'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getWorkerStatus, type BrowserHealth } from '../../api/worker'

const WEBBRIDGE_INSTALL_URL = 'https://www.kimi.com/features/webbridge'

export type SearchHelperAvailability = {
  /** Paired + recent heartbeat (includes mid-search `busy`). */
  connected: boolean
  /** Safe to start a new search (`ready` only — not `busy`). */
  canStart: boolean
  browserHealth: BrowserHealth | null
}

interface SearchHelperHintProps {
  onReadyChange?: (ready: boolean) => void
  onAvailabilityChange?: (availability: SearchHelperAvailability) => void
}

export function SearchHelperHint({
  onReadyChange,
  onAvailabilityChange,
}: SearchHelperHintProps) {
  const [connected, setConnected] = useState<boolean | null>(null)
  const [browserHealth, setBrowserHealth] = useState<BrowserHealth | null>(null)

  useEffect(() => {
    let active = true

    const refresh = async () => {
      try {
        const status = await getWorkerStatus()
        if (!active) return
        const health = status.browserHealth ?? null
        // Heartbeat stays alive during search with health=busy. That is still connected.
        const isConnected = Boolean(status.connected)
        const canStart = Boolean(status.connected && health === 'ready')
        setConnected(isConnected)
        setBrowserHealth(health)
        onAvailabilityChange?.({
          connected: isConnected,
          canStart,
          browserHealth: health,
        })
        // Legacy: keep Start enabled only when truly ready (not busy).
        onReadyChange?.(canStart)
      } catch {
        if (!active) return
        setConnected(false)
        setBrowserHealth(null)
        onAvailabilityChange?.({
          connected: false,
          canStart: false,
          browserHealth: null,
        })
        onReadyChange?.(false)
      }
    }

    void refresh()
    const timer = window.setInterval(() => {
      void refresh()
    }, 5000)

    return () => {
      active = false
      window.clearInterval(timer)
    }
  }, [onReadyChange, onAvailabilityChange])

  if (connected === null) {
    return (
      <div className="flex items-center gap-3 rounded-2xl border border-border bg-surface/80 px-4 py-3 text-sm text-text-secondary">
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-secondary border-t-transparent" />
        Checking your Search Helper connection...
      </div>
    )
  }

  if (!connected) {
    return (
      <section className="flex flex-col gap-4 rounded-2xl border border-warning/20 bg-warning-soft px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-warning/10 text-warning">
            <ComputerDesktopIcon className="h-5 w-5" aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm font-semibold text-hitl-text">Your Search Helper needs pairing.</p>
            <p className="mt-1 text-xs leading-5 text-hitl-text/80">
              Pair this computer, then connect Chrome with WebBridge before launching a search.
            </p>
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-3 text-sm font-semibold">
          <Link to="/settings" className="text-primary hover:text-primary-hover hover:underline">
            Set up helper
          </Link>
          <a
            href={WEBBRIDGE_INSTALL_URL}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-primary hover:text-primary-hover hover:underline"
          >
            WebBridge
            <ArrowTopRightOnSquareIcon className="h-3.5 w-3.5" aria-hidden="true" />
          </a>
        </div>
      </section>
    )
  }

  // Mid-search: worker is connected and actively heartbeating as "busy".
  if (browserHealth === 'busy') {
    return (
      <section className="flex items-center gap-3 rounded-2xl border border-success/20 bg-success-soft px-4 py-3.5 text-sm text-success">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-success/10">
          <CheckCircleIcon className="h-5 w-5" aria-hidden="true" />
        </span>
        <div>
          <p className="font-semibold">Search Helper is connected and searching.</p>
          <p className="mt-0.5 text-xs text-success/80">
            A browser search is running on this PC. Follow progress in Applications.
          </p>
        </div>
      </section>
    )
  }

  if (browserHealth !== 'ready') {
    const detail: Record<Exclude<BrowserHealth, 'ready' | 'busy'>, string> = {
      not_installed: 'Open Chrome with the Kimi WebBridge extension installed.',
      daemon_down: 'The local WebBridge daemon is not ready yet.',
      profile_setup: 'WebBridge needs its first-time setup in Chrome.',
      error: 'JobPilot could not verify browser readiness.',
    }
    return (
      <section className="flex flex-col gap-4 rounded-2xl border border-warning/20 bg-warning-soft px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-warning/10 text-warning">
            <WrenchScrewdriverIcon className="h-5 w-5" aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm font-semibold text-hitl-text">Helper paired, browser not ready.</p>
            <p className="mt-1 text-xs leading-5 text-hitl-text/80">{detail[browserHealth ?? 'error']}</p>
          </div>
        </div>
        <Link
          to="/settings"
          className="shrink-0 text-sm font-semibold text-primary hover:text-primary-hover hover:underline"
        >
          Check setup
        </Link>
      </section>
    )
  }

  return (
    <section className="flex items-center gap-3 rounded-2xl border border-success/20 bg-success-soft px-4 py-3.5 text-sm text-success">
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-success/10">
        <CheckCircleIcon className="h-5 w-5" aria-hidden="true" />
      </span>
      <div>
        <p className="font-semibold">Search Helper is ready.</p>
        <p className="mt-0.5 text-xs text-success/80">Chrome and WebBridge are connected for this computer.</p>
      </div>
    </section>
  )
}

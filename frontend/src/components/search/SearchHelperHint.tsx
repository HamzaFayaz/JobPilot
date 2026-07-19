import { ArrowTopRightOnSquareIcon, PuzzlePieceIcon } from '@heroicons/react/24/outline'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getWorkerStatus, type BrowserHealth } from '../../api/worker'

const WEBBRIDGE_INSTALL_URL = 'https://www.kimi.com/features/webbridge'
const WEBBRIDGE_VERSION_NOTE =
  'Locked: daemon v1.10.0 + extension 1.11.3. Do not auto-upgrade.'

interface SearchHelperHintProps {
  onReadyChange?: (ready: boolean) => void
}

export function SearchHelperHint({ onReadyChange }: SearchHelperHintProps) {
  const [connected, setConnected] = useState<boolean | null>(null)
  const [browserHealth, setBrowserHealth] = useState<BrowserHealth | null>(null)

  useEffect(() => {
    let active = true

    const refresh = async () => {
      try {
        const status = await getWorkerStatus()
        if (!active) return
        setConnected(status.connected)
        setBrowserHealth(status.browserHealth ?? null)
        const ready = Boolean(status.connected && status.browserHealth === 'ready')
        onReadyChange?.(ready)
      } catch {
        if (!active) return
        setConnected(false)
        setBrowserHealth(null)
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
  }, [onReadyChange])

  if (connected === null) {
    return null
  }

  if (!connected) {
    return (
      <div className="rounded-lg border border-border bg-surface px-4 py-3 text-sm text-text-secondary">
        <p>
          Connect Search Helper in{' '}
          <Link to="/settings" className="font-medium text-primary hover:underline">
            Settings
          </Link>{' '}
          to run browser search on this PC.
        </p>
        <a
          href={WEBBRIDGE_INSTALL_URL}
          target="_blank"
          rel="noreferrer"
          className="mt-2 inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
        >
          <PuzzlePieceIcon className="h-4 w-4" aria-hidden="true" />
          Install Kimi WebBridge first
          <ArrowTopRightOnSquareIcon className="h-3.5 w-3.5" aria-hidden="true" />
        </a>
        <p className="mt-1 text-xs text-text-secondary">{WEBBRIDGE_VERSION_NOTE}</p>
      </div>
    )
  }

  if (browserHealth !== 'ready') {
    const needsInstall =
      browserHealth === 'not_installed' ||
      browserHealth === 'profile_setup' ||
      browserHealth === 'daemon_down'

    return (
      <div className="rounded-lg border border-warning/30 bg-hitl-bg/60 px-4 py-3 text-sm text-hitl-text">
        <p>
          Search Helper is connected but WebBridge is not ready
          {browserHealth === 'not_installed' ? '. Open Chrome with the extension' : ''}.{' '}
          <Link to="/settings" className="font-medium text-primary hover:underline">
            Check Settings
          </Link>
        </p>
        {needsInstall ? (
          <>
            <a
              href={WEBBRIDGE_INSTALL_URL}
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-flex items-center gap-1.5 font-medium text-primary hover:underline"
            >
              <PuzzlePieceIcon className="h-4 w-4" aria-hidden="true" />
              Install or update Kimi WebBridge
              <ArrowTopRightOnSquareIcon className="h-3.5 w-3.5" aria-hidden="true" />
            </a>
            <p className="mt-1 text-xs text-text-secondary">{WEBBRIDGE_VERSION_NOTE}</p>
          </>
        ) : null}
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-success/30 bg-success/5 px-4 py-3 text-sm text-success">
      Search Helper ready. WebBridge connected.
    </div>
  )
}

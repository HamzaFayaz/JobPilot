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
  UserCircleIcon,
} from '@heroicons/react/24/outline'
import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import {
  getWorkerStatus,
  pairWorker,
  unpairWorker,
  type BrowserHealth,
} from '../../api/worker'
import { DOWNLOADS, SUPPORT_EMAIL } from '../../constants/downloads'
import { useProfile } from '../../context/ProfileContext'
import { Button } from '../ui/Button'

const WEBBRIDGE_INSTALL_URL = 'https://www.kimi.com/features/webbridge'
const WEBBRIDGE_LOCKED_DAEMON = 'v1.10.0'
const WEBBRIDGE_LOCKED_EXTENSION = '1.11.3'

const HEALTH_LABELS: Record<BrowserHealth, string> = {
  ready: 'Ready to search',
  busy: 'A search is running',
  not_installed: 'Chrome extension is not connected',
  daemon_down: 'WebBridge is starting',
  profile_setup: 'WebBridge setup is needed',
  error: 'Connection needs attention',
}

const HEALTH_HINTS: Partial<Record<BrowserHealth, string>> = {
  not_installed: 'Open Chrome with the Kimi WebBridge extension installed. It reconnects automatically.',
  daemon_down: 'The Search Helper is starting WebBridge. If this persists, open the Helper again.',
  profile_setup: 'Install Kimi WebBridge and its Chrome extension, then return here to verify the connection.',
}

type SetupTone = 'neutral' | 'active' | 'complete'

interface SetupStepProps {
  number: string
  icon: ReactNode
  title: string
  description: string
  tone?: SetupTone
  children: ReactNode
}

function SetupStep({ number, icon, title, description, tone = 'neutral', children }: SetupStepProps) {
  const toneClasses: Record<SetupTone, string> = {
    neutral: 'border-border bg-surface',
    active: 'border-primary/25 bg-primary-soft/45',
    complete: 'border-success/25 bg-success-soft/60',
  }
  const iconClasses: Record<SetupTone, string> = {
    neutral: 'bg-surface-muted text-text-secondary',
    active: 'bg-primary text-white shadow-sm shadow-primary/25',
    complete: 'bg-success text-white shadow-sm shadow-success/25',
  }

  return (
    <li className={`rounded-2xl border p-4 sm:p-5 ${toneClasses[tone]}`}>
      <div className="flex gap-3 sm:gap-4">
        <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${iconClasses[tone]}`}>
          {icon}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className="text-[11px] font-extrabold uppercase tracking-[0.14em] text-text-tertiary">
              Step {number}
            </span>
            <h3 className="text-sm font-extrabold text-text-primary sm:text-base">{title}</h3>
          </div>
          <p className="mt-1.5 max-w-2xl text-sm leading-6 text-text-secondary">{description}</p>
          <div className="mt-4">{children}</div>
        </div>
      </div>
    </li>
  )
}

export function SearchHelperSetupCard() {
  const { gate } = useProfile()
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
      setError(err instanceof Error ? err.message : 'Failed to load Search Helper status')
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
      setError(err instanceof Error ? err.message : 'Failed to pair Search Helper')
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
      setError(err instanceof Error ? err.message : 'Failed to disconnect Search Helper')
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
      // Clipboard access may be blocked on non-secure local URLs.
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

  const healthLabel = browserHealth ? HEALTH_LABELS[browserHealth] ?? browserHealth : null
  const healthHint = browserHealth ? HEALTH_HINTS[browserHealth] : null
  const isSearchReady = connected && browserHealth === 'ready'
  const connectionLabel = loading
    ? 'Checking this computer'
    : isSearchReady
      ? 'Ready to search'
      : connected
        ? healthLabel ?? 'Connected'
        : 'Not connected'

  return (
    <section className="jp-surface overflow-hidden rounded-[1.5rem]">
      <div className="border-b border-border px-5 py-5 sm:px-6 sm:py-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex min-w-0 gap-3">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-primary-soft text-primary">
              <ComputerDesktopIcon className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <p className="jp-eyebrow">Your first search checklist</p>
              <h2 className="jp-display mt-1 text-xl font-extrabold tracking-tight text-text-primary sm:text-2xl">
                Set up this computer once.
              </h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-text-secondary">
                Follow the steps in order. JobPilot uses your normal Chrome session to help you review LinkedIn posts; it never applies on your behalf.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 self-start">
            <span
              className={`inline-flex min-h-9 items-center gap-2 rounded-full px-3 text-xs font-bold ${
                isSearchReady
                  ? 'bg-success-soft text-success'
                  : connected
                    ? 'bg-warning-soft text-warning'
                    : 'bg-surface-muted text-text-secondary'
              }`}
            >
              <span className={`h-1.5 w-1.5 rounded-full ${isSearchReady ? 'bg-success' : connected ? 'bg-warning' : 'bg-text-tertiary'}`} />
              {connectionLabel}
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
      </div>

      <div className="px-5 py-5 sm:px-6 sm:py-6">
        {error ? (
          <div className="mb-5 flex items-start gap-3 rounded-xl border border-error/20 bg-error-soft px-4 py-3 text-sm text-error">
            <ExclamationTriangleIcon className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
            <p>{error}</p>
          </div>
        ) : null}

        <ol className="space-y-3">
          <SetupStep
            number="01"
            icon={gate.isComplete ? <CheckCircleIcon className="h-5 w-5" aria-hidden="true" /> : <UserCircleIcon className="h-5 w-5" aria-hidden="true" />}
            title="Complete your career profile"
            description={gate.isComplete ? 'Your CV, skills, and project evidence are ready for matching.' : `Finish your CV, skills, and at least one project first (${gate.requiredComplete}/${gate.requiredTotal} complete).`}
            tone={gate.isComplete ? 'complete' : 'active'}
          >
            <Link
              to="/profile"
              className="inline-flex min-h-11 items-center justify-center rounded-xl border border-border-strong bg-surface px-4 py-2 text-sm font-semibold text-text-primary shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary/45 hover:bg-primary-soft/55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            >
              {gate.isComplete ? 'Review career profile' : 'Complete profile'}
            </Link>
          </SetupStep>

          <SetupStep
            number="02"
            icon={isSearchReady || browserHealth === 'ready' ? <CheckCircleIcon className="h-5 w-5" aria-hidden="true" /> : <PuzzlePieceIcon className="h-5 w-5" aria-hidden="true" />}
            title="Prepare your LinkedIn browser"
            description="Install Kimi WebBridge and its Chrome extension in the exact Chrome profile you use for LinkedIn. Then sign in to LinkedIn there."
            tone={isSearchReady ? 'complete' : browserHealth === 'profile_setup' || browserHealth === 'not_installed' ? 'active' : 'neutral'}
          >
            <p className="rounded-xl border border-warning/20 bg-warning-soft px-3 py-2 text-xs leading-5 text-hitl-text">Required: Kimi WebBridge daemon <strong>{WEBBRIDGE_LOCKED_DAEMON}</strong> + Chrome extension <strong>{WEBBRIDGE_LOCKED_EXTENSION}</strong>. Do not auto-update.</p>
            <a
              href={WEBBRIDGE_INSTALL_URL}
              target="_blank"
              rel="noreferrer"
              className="inline-flex min-h-11 items-center justify-center rounded-xl border border-border-strong bg-surface px-4 py-2 text-sm font-semibold text-text-primary shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary/45 hover:bg-primary-soft/55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            >
              Install Kimi WebBridge
              <ArrowTopRightOnSquareIcon className="ml-2 h-4 w-4" aria-hidden="true" />
            </a>
          </SetupStep>

          <SetupStep
            number="03"
            icon={<ArrowDownTrayIcon className="h-5 w-5" aria-hidden="true" />}
            title="Download and open Search Helper"
            description="Download the small Windows app and open it. Keep it open on its Settings screen so it is ready for your pairing code."
            tone={connected ? 'complete' : 'neutral'}
          >
            <a
              href={DOWNLOADS.searchHelperExe}
              className="inline-flex min-h-11 items-center justify-center rounded-xl border border-primary bg-primary px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-primary/20 transition-all hover:-translate-y-0.5 hover:bg-primary-hover hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            >
              <ArrowDownTrayIcon className="mr-2 h-4 w-4" aria-hidden="true" />
              Download Search Helper for Windows
            </a>
          </SetupStep>

          <SetupStep
            number="04"
            icon={workerToken || connected ? <CheckCircleIcon className="h-5 w-5" aria-hidden="true" /> : <LinkIcon className="h-5 w-5" aria-hidden="true" />}
            title="Create and paste the pairing code"
            description={workerToken ? 'Copy this one-time code, paste it into the open Search Helper app, and save its settings.' : 'Only create the code once the Helper app is open. Paste it there, then save the Helper settings.'}
            tone={workerToken || connected ? 'complete' : 'active'}
          >
            {workerToken ? (
              <div className="rounded-xl border border-primary/20 bg-surface/80 p-3">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                  <code className="block min-w-0 flex-1 break-all rounded-lg bg-background px-3 py-2.5 text-xs font-semibold text-text-primary">
                    {workerToken}
                  </code>
                  <Button type="button" variant="secondary" className="shrink-0" onClick={() => void handleCopyToken()}>
                    <ClipboardDocumentIcon className="mr-2 h-4 w-4" aria-hidden="true" />
                    {copied ? 'Copied' : 'Copy code'}
                  </Button>
                </div>
                <p className="mt-2 text-xs leading-5 text-text-secondary">
                  In Search Helper: Settings ? pairing code ? paste ? Save settings ? Start.
                </p>
                <p className="mt-2 text-xs font-medium leading-5 text-warning">
                  This pairing code is shown only in this session. Copy it now; if you refresh or leave this page before pairing, create a new code.
                </p>
              </div>
            ) : (
              <Button type="button" onClick={() => void handlePair()} disabled={pairing}>
                <LinkIcon className="mr-2 h-4 w-4" aria-hidden="true" />
                {pairing ? 'Creating code?' : 'Create pairing code'}
              </Button>
            )}
          </SetupStep>

          <SetupStep
            number="05"
            icon={isSearchReady ? <CheckCircleIcon className="h-5 w-5" aria-hidden="true" /> : <ArrowPathIcon className="h-5 w-5" aria-hidden="true" />}
            title={isSearchReady ? 'Connection complete ? start your search' : 'Start the Helper and verify'}
            description={
              isSearchReady
                ? 'This PC, the Search Helper, and your LinkedIn Chrome profile are connected. You are ready to search.'
                : healthHint ?? 'Back in Search Helper, select Start. JobPilot checks this connection automatically every few seconds.'
            }
            tone={isSearchReady ? 'complete' : connected ? 'active' : 'neutral'}
          >
            <div className="flex flex-wrap items-center gap-3">
              <span className={`inline-flex items-center gap-2 rounded-full px-3 py-2 text-xs font-bold ${isSearchReady ? 'bg-success-soft text-success' : 'bg-surface-muted text-text-secondary'}`}>
                <span className={`h-1.5 w-1.5 rounded-full ${isSearchReady ? 'bg-success' : 'bg-text-tertiary'}`} />
                {loading ? 'Checking status?' : healthLabel ?? 'Waiting for the Helper'}
              </span>
              {isSearchReady ? (
                <Link to="/search" className="inline-flex min-h-10 items-center justify-center rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2">
                  Start job search
                </Link>
              ) : null}
              {connected ? (
                <Button type="button" variant="ghost" className="min-h-9 px-3 text-xs" onClick={() => void handleUnpair()} disabled={pairing}>
                  Disconnect this computer
                </Button>
              ) : null}
            </div>
          </SetupStep>
        </ol>

        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <details className="rounded-xl border border-border bg-surface-muted/50 px-4 py-3 text-sm">
            <summary className="cursor-pointer font-bold text-text-primary">Windows download help</summary>
            <div className="mt-3 space-y-2 text-xs leading-5 text-text-secondary">
              <p>
                The Helper is an unsigned portable app, so Windows may show an unknown-publisher warning. Choose <strong className="text-text-primary">More info</strong>, then <strong className="text-text-primary">Run anyway</strong>.
              </p>
              <p>
                If Windows fully blocks it, contact <a href={`mailto:${SUPPORT_EMAIL}`} className="font-semibold text-primary hover:underline">{SUPPORT_EMAIL}</a>.
              </p>
            </div>
          </details>
          <details className="rounded-xl border border-border bg-surface-muted/50 px-4 py-3 text-sm">
            <summary className="cursor-pointer font-bold text-text-primary">Compatibility details</summary>
            <div className="mt-3 space-y-2 text-xs leading-5 text-text-secondary">
              <p>
                Use WebBridge daemon <strong className="text-text-primary">{WEBBRIDGE_LOCKED_DAEMON}</strong> and Chrome extension <strong className="text-text-primary">{WEBBRIDGE_LOCKED_EXTENSION}</strong>. Do not auto-upgrade until LinkedIn Posts search is re-tested.
              </p>
              <p>The Qwen model and Dashscope key stay on the JobPilot server. You never enter an API key in this browser or the Helper.</p>
            </div>
          </details>
        </div>
      </div>
    </section>
  )
}

import { Link, useSearchParams } from 'react-router-dom'
import { useEffect } from 'react'
import { CvUpload } from '../components/profile/CvUpload'
import { GitHubImport } from '../components/profile/GitHubImport'
import { GmailStrip } from '../components/profile/GmailStrip'
import { ProfileDerivedStatus } from '../components/profile/ProfileDerivedStatus'
import { RolesInput } from '../components/profile/RolesInput'
import { Button } from '../components/ui/Button'
import { ProgressBar } from '../components/ui/ProgressBar'
import { useProfile } from '../context/ProfileContext'

export function ProfilePage() {
  const { gate, refreshProfile } = useProfile()
  const [searchParams] = useSearchParams()
  const completeness = Math.round((gate.requiredComplete / gate.requiredTotal) * 100)
  const gmailError = searchParams.get('gmail') === 'error'
  const gmailMissingSend = searchParams.get('gmail') === 'missing_send_scope'

  useEffect(() => {
    if (
      searchParams.get('gmail') === 'connected' ||
      searchParams.get('github') === 'connected' ||
      searchParams.get('gmail') === 'error' ||
      searchParams.get('gmail') === 'missing_send_scope'
    ) {
      void refreshProfile()
      window.history.replaceState({}, '', '/profile')
    }
  }, [searchParams, refreshProfile])

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-text-primary sm:text-3xl">Profile Setup</h1>
        <p className="mt-2 text-sm text-text-secondary">
          Upload your CV, set target roles, and connect integrations. Skills and projects are
          managed in Settings once processing finishes.
        </p>
      </header>

      {gmailMissingSend ? (
        <div className="rounded-lg border border-warning/40 bg-hitl-bg p-4 text-sm text-hitl-text">
          <p className="font-semibold">Gmail connected partially — send permission missing</p>
          <p className="mt-2">
            Google only granted your <strong>email address</strong>, not{' '}
            <strong>Send email on your behalf</strong>. JobPilot needs both.
          </p>
          <ol className="mt-3 list-inside list-decimal space-y-1">
            <li>
              Enable <strong>Gmail API</strong> in Google Cloud → APIs &amp; Services →
              Library
            </li>
            <li>
              Revoke JobPilot at{' '}
              <a
                href="https://myaccount.google.com/permissions"
                className="font-semibold text-primary underline"
                target="_blank"
                rel="noreferrer"
              >
                Google Account permissions
              </a>
            </li>
            <li>
              Connect Gmail again and on the Google screen{' '}
              <strong>check the box</strong> for &quot;Send email on your behalf&quot;, then
              click Continue
            </li>
          </ol>
        </div>
      ) : null}

      {gmailError ? (
        <div className="rounded-lg border border-error/30 bg-error/5 p-4 text-sm text-error">
          Gmail connection failed. Try these steps:
          <ol className="mt-2 list-inside list-decimal space-y-1">
            <li>
              Revoke JobPilot at{' '}
              <a
                href="https://myaccount.google.com/permissions"
                className="font-semibold underline"
                target="_blank"
                rel="noreferrer"
              >
                Google Account permissions
              </a>
            </li>
            <li>Confirm Gmail API is enabled in Google Cloud Console</li>
            <li>Restart with <code className="text-xs">dev.cmd</code> and connect again</li>
          </ol>
        </div>
      ) : null}

      <div className="rounded-lg border border-warning/30 bg-hitl-bg p-4 text-sm text-hitl-text">
        You approve before anything is sent. JobPilot acts as your assistant, not your
        replacement.
      </div>

      <section>
        <div className="mb-2 flex items-end justify-between">
          <h2 className="text-base font-semibold text-text-primary">Profile completeness</h2>
          <span className="text-sm font-bold text-primary">{completeness}%</span>
        </div>
        <ProgressBar value={gate.requiredComplete} max={gate.requiredTotal} />
      </section>

      <CvUpload />
      <RolesInput />
      <GitHubImport />
      <GmailStrip />
      <ProfileDerivedStatus />

      <div className="flex flex-col gap-3 border-t border-border pt-6 sm:flex-row sm:justify-end">
        <Link to="/" className="w-full sm:w-auto">
          <Button variant="ghost" className="w-full">
            Back to welcome
          </Button>
        </Link>
        {gate.isComplete ? (
          <Link to="/search" className="w-full sm:w-auto">
            <Button className="w-full">Continue to Search</Button>
          </Link>
        ) : (
          <Button disabled className="w-full sm:w-auto">
            Complete required fields to continue
          </Button>
        )}
      </div>
    </div>
  )
}

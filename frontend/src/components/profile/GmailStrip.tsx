import { EnvelopeIcon } from '@heroicons/react/24/outline'
import { useProfile } from '../../context/ProfileContext'
import { Button } from '../ui/Button'

export function GmailStrip() {
  const { profile, toggleGmail } = useProfile()

  return (
    <section className="rounded-lg border border-border bg-surface p-6 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <EnvelopeIcon className="mt-0.5 h-6 w-6 text-primary" aria-hidden="true" />
          <div>
            <h3 className="text-base font-semibold text-text-primary">Gmail</h3>
            <p className="text-sm text-text-secondary">
              Connect Gmail to send approved applications. Optional for search.
            </p>
            {profile.gmailConnected && profile.gmailEmail ? (
              <p className="mt-1 text-sm font-medium text-success">
                Connected as {profile.gmailEmail}
              </p>
            ) : (
              <p className="mt-1 text-sm text-text-secondary">Not connected</p>
            )}
          </div>
        </div>
        {/* Wire to GET /auth/google when backend is available */}
        <Button variant="secondary" onClick={toggleGmail} className="w-full sm:w-auto">
          {profile.gmailConnected ? 'Disconnect' : 'Connect Gmail'}
        </Button>
      </div>
    </section>
  )
}

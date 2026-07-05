import { Link, useSearchParams } from 'react-router-dom'
import { useEffect } from 'react'
import { CvUpload } from '../components/profile/CvUpload'
import { GitHubImport } from '../components/profile/GitHubImport'
import { ProfileDerivedStatus } from '../components/profile/ProfileDerivedStatus'
import { RolesInput } from '../components/profile/RolesInput'
import { SearchPreferencesFields } from '../components/search/SearchPreferencesFields'
import { Button } from '../components/ui/Button'
import { ProgressBar } from '../components/ui/ProgressBar'
import { useProfile } from '../context/ProfileContext'

export function ProfilePage() {
  const { gate, refreshProfile, profile, updateProfile } = useProfile()
  const [searchParams] = useSearchParams()
  const completeness = Math.round((gate.requiredComplete / gate.requiredTotal) * 100)

  useEffect(() => {
    if (searchParams.get('github') === 'connected') {
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

      <section className="rounded-lg border border-border bg-surface p-6 shadow-sm">
        <h2 className="text-base font-semibold text-text-primary">Search preferences</h2>
        <p className="mt-1 text-sm text-text-secondary">
          Saved for your next search. One country per run keeps the agent fast.
        </p>
        <div className="mt-4">
          <SearchPreferencesFields
            profile={profile}
            onChange={(patch) => {
              void updateProfile(patch)
            }}
          />
        </div>
      </section>

      <GitHubImport />
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

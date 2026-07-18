import { CheckCircleIcon } from '@heroicons/react/24/outline'
import { useEffect } from 'react'
import { useSearchParams, Link as RouterLink } from 'react-router-dom'
import { CvUpload } from '../components/profile/CvUpload'
import { GitHubImport } from '../components/profile/GitHubImport'
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
    <div className="mx-auto max-w-2xl space-y-6">
      <header>
        <p className="text-sm font-medium text-primary">Profile</p>
        <h1 className="mt-1 text-2xl font-bold text-text-primary sm:text-3xl">
          {gate.isComplete ? 'Your profile' : 'Complete your profile'}
        </h1>
        <p className="mt-2 text-sm text-text-secondary">
          {gate.isComplete
            ? 'Update your CV, roles, or search defaults anytime. Skills and projects live in Settings.'
            : 'Upload your CV, add target roles, and connect GitHub to unlock search.'}
        </p>
      </header>

      <section className="rounded-xl border border-border bg-surface p-5 shadow-sm">
        <div className="mb-2 flex items-end justify-between gap-3">
          <span className="text-sm font-medium text-text-primary">Setup progress</span>
          <span className="text-sm font-bold text-primary">{completeness}%</span>
        </div>
        <ProgressBar value={gate.requiredComplete} max={gate.requiredTotal} />
        {gate.isComplete ? (
          <p className="mt-3 flex items-center gap-2 text-sm text-success">
            <CheckCircleIcon className="h-5 w-5 shrink-0" aria-hidden="true" />
            Profile complete — you can start searching.
          </p>
        ) : (
          <ul className="mt-3 space-y-1 text-xs text-text-secondary">
            <li className={gate.hasCv ? 'text-success' : ''}>{gate.hasCv ? '✓' : '○'} CV uploaded</li>
            <li className={gate.hasMinSkills ? 'text-success' : ''}>
              {gate.hasMinSkills ? '✓' : '○'} Skills extracted (min. 3)
            </li>
            <li className={gate.hasProject ? 'text-success' : ''}>
              {gate.hasProject ? '✓' : '○'} At least one project
            </li>
          </ul>
        )}
      </section>

      <CvUpload />
      <RolesInput />

      <section className="rounded-xl border border-border bg-surface p-6 shadow-sm">
        <h2 className="text-base font-semibold text-text-primary">Default search preferences</h2>
        <p className="mt-1 text-sm text-text-secondary">
          Saved for your next search. You can change these on the Search page too.
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

      {!gate.hasProject ? (
        <p className="rounded-lg border border-dashed border-border bg-background px-4 py-3 text-sm text-text-secondary">
          Need projects? Import repos above or{' '}
          <RouterLink to="/settings" className="font-semibold text-primary hover:underline">
            add them in Settings
          </RouterLink>
          .
        </p>
      ) : null}

      <div className="flex flex-col gap-3 border-t border-border pt-6 sm:flex-row sm:justify-end">
        {gate.isComplete ? (
          <RouterLink to="/applications" className="w-full sm:w-auto">
            <Button className="w-full">Open Applications</Button>
          </RouterLink>
        ) : (
          <Button disabled className="w-full sm:w-auto">
            Complete all steps above to unlock search
          </Button>
        )}
      </div>
    </div>
  )
}

import { Link } from 'react-router-dom'
import { SearchHelperSettings } from '../components/settings/SearchHelperSettings'
import { SkillsFromCv } from '../components/profile/SkillsFromCv'
import { ProjectsList } from '../components/profile/ProjectsList'
import { useProfile } from '../context/ProfileContext'

export function SettingsPage() {
  const { profile } = useProfile()
  const hasCv = Boolean(profile.cvFilename)
  const skillsReady = profile.skillsExtractionStatus === 'ready' && profile.skills.length > 0
  const hasProjects = profile.projects.length > 0

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-text-primary sm:text-3xl">Settings</h1>
        <p className="mt-2 text-sm text-text-secondary">
          View extracted skills and manage project cards after setup actions complete.
        </p>
      </header>

      <SearchHelperSettings />

      {!hasCv && !hasProjects && profile.skillsExtractionStatus === 'idle' ? (
        <div className="rounded-lg border border-border bg-background p-6 text-sm text-text-secondary">
          Complete{' '}
          <Link to="/profile" className="font-semibold text-primary hover:underline">
            profile setup
          </Link>{' '}
          first: upload your CV and optionally import GitHub repos. Skills and projects will
          appear here when ready.
        </div>
      ) : null}

      {(hasCv || profile.skillsExtractionStatus !== 'idle') && <SkillsFromCv />}

      {(hasProjects || hasCv) && <ProjectsList />}

      {hasCv && !skillsReady && profile.skillsExtractionStatus !== 'pending' ? (
        <p className="text-sm text-text-secondary">
          Skills are still processing or need a re-upload. Check back shortly.
        </p>
      ) : null}
    </div>
  )
}

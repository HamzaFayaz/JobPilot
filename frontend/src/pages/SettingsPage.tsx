import { Link } from 'react-router-dom'
import { SearchHelperSettings } from '../components/settings/SearchHelperSettings'
import { SkillsFromCv } from '../components/profile/SkillsFromCv'
import { ProjectsList } from '../components/profile/ProjectsList'
import { CollapsibleSection } from '../components/ui/CollapsibleSection'
import { useProfile } from '../context/ProfileContext'

export function SettingsPage() {
  const { profile } = useProfile()
  const hasCv = Boolean(profile.cvFilename)
  const skillsReady = profile.skillsExtractionStatus === 'ready' && profile.skills.length > 0
  const projectCount = profile.projects.length
  const hasProjects = projectCount > 0
  const setupEmpty =
    !hasCv && !hasProjects && profile.skillsExtractionStatus === 'idle'

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header>
        <p className="text-sm font-medium text-primary">Settings</p>
        <h1 className="mt-1 text-2xl font-bold text-text-primary sm:text-3xl">Account &amp; tools</h1>
        <p className="mt-2 text-sm text-text-secondary">
          Connect your Search Helper, review extracted skills, and manage project cards.
        </p>
      </header>

      <SearchHelperSettings />

      {setupEmpty ? (
        <div className="rounded-xl border border-border bg-surface p-6 text-sm text-text-secondary shadow-sm">
          Complete{' '}
          <Link to="/profile" className="font-semibold text-primary hover:underline">
            profile setup
          </Link>{' '}
          first. Upload your CV and optionally import GitHub repos. Skills and projects will appear
          here when ready.
        </div>
      ) : (
        <>
          {(hasCv || profile.skillsExtractionStatus !== 'idle') && (
            <CollapsibleSection
              title="Skills from CV"
              description={
                skillsReady
                  ? `${profile.skills.length} skills extracted`
                  : 'Processing or awaiting CV upload'
              }
              badge={skillsReady ? String(profile.skills.length) : undefined}
              defaultOpen={skillsReady && profile.skills.length <= 12}
            >
              <SkillsFromCv embedded />
            </CollapsibleSection>
          )}

          {(hasProjects || hasCv) && (
            <CollapsibleSection
              title="Projects"
              description={
                hasProjects
                  ? `${projectCount} project${projectCount !== 1 ? 's' : ''} in your profile`
                  : 'Add or import project cards for job matching'
              }
              badge={hasProjects ? String(projectCount) : undefined}
              defaultOpen={false}
            >
              <ProjectsList embedded />
            </CollapsibleSection>
          )}

          {hasCv && !skillsReady && profile.skillsExtractionStatus !== 'pending' ? (
            <p className="text-sm text-text-secondary">
              Skills are still processing or need a re-upload. Check back shortly.
            </p>
          ) : null}
        </>
      )}
    </div>
  )
}

import { Link } from 'react-router-dom'
import { useProfile } from '../../context/ProfileContext'

function skillsStatusLabel(
  status: string,
  count: number,
): { text: string; tone: 'muted' | 'pending' | 'ready' | 'error' } {
  if (status === 'pending') {
    return { text: 'Extracting skills from your CV…', tone: 'pending' }
  }
  if (status === 'failed') {
    return { text: 'Skill extraction failed — re-upload your CV', tone: 'error' }
  }
  if (status === 'ready' && count > 0) {
    return { text: `${count} skill${count !== 1 ? 's' : ''} ready`, tone: 'ready' }
  }
  if (status === 'idle' || count === 0) {
    return { text: 'Upload a CV to extract skills', tone: 'muted' }
  }
  return { text: 'Processing…', tone: 'pending' }
}

const toneClass = {
  muted: 'text-text-secondary',
  pending: 'text-warning',
  ready: 'text-success',
  error: 'text-error',
} as const

export function ProfileDerivedStatus() {
  const { profile } = useProfile()
  const skills = skillsStatusLabel(profile.skillsExtractionStatus, profile.skills.length)
  const projectCount = profile.projects.length
  const projectsText =
    projectCount > 0
      ? `${projectCount} project${projectCount !== 1 ? 's' : ''} saved`
      : 'Import from GitHub or add manually in Settings'

  return (
    <section className="rounded-lg border border-border bg-surface p-6 shadow-sm">
      <h3 className="text-base font-semibold text-text-primary">Skills &amp; projects</h3>
      <p className="mt-1 text-sm text-text-secondary">
        Auto-extracted skills and project cards appear in Settings when ready — not on this
        setup screen.
      </p>
      <ul className="mt-4 space-y-2 text-sm">
        <li className="flex flex-wrap items-center justify-between gap-2">
          <span className="text-text-secondary">Skills</span>
          <span className={toneClass[skills.tone]}>{skills.text}</span>
        </li>
        <li className="flex flex-wrap items-center justify-between gap-2">
          <span className="text-text-secondary">Projects</span>
          <span className={projectCount > 0 ? 'text-success' : 'text-text-secondary'}>
            {projectsText}
          </span>
        </li>
      </ul>
      <Link
        to="/settings"
        className="mt-4 inline-block text-sm font-semibold text-primary hover:underline"
      >
        Open Settings →
      </Link>
    </section>
  )
}

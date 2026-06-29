import { CodeBracketIcon } from '@heroicons/react/24/outline'
import { useProfile } from '../../context/ProfileContext'

export function SkillsFromCv() {
  const { profile } = useProfile()
  const { skills, skillsExtractionStatus, cvFilename } = profile

  return (
    <section className="rounded-lg border border-border bg-surface p-6 shadow-sm">
      <div className="mb-4 flex items-center gap-2">
        <CodeBracketIcon className="h-5 w-5 text-primary" aria-hidden="true" />
        <h3 className="text-base font-semibold text-text-primary">Skills from CV</h3>
      </div>

      {!cvFilename ? (
        <p className="text-sm text-text-secondary">
          Upload your CV to auto-extract skills. Skills cannot be edited manually.
        </p>
      ) : skillsExtractionStatus === 'pending' ? (
        <div className="flex items-center gap-2 text-sm text-text-secondary">
          <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          Extracting skills from your CV…
        </div>
      ) : skillsExtractionStatus === 'failed' ? (
        <p className="text-sm text-error">
          Skill extraction failed. Try re-uploading your CV.
        </p>
      ) : skills.length === 0 ? (
        <p className="text-sm text-text-secondary">No skills extracted yet.</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {skills.map((skill) => (
            <span
              key={skill}
              className="rounded-full bg-chip-bg px-3 py-1 text-sm font-medium text-text-primary"
            >
              {skill}
            </span>
          ))}
        </div>
      )}

      {skillsExtractionStatus === 'ready' && skills.length > 0 ? (
        <p className="mt-2 text-xs text-text-secondary">
          {skills.length} skill{skills.length !== 1 ? 's' : ''} extracted (read-only).
        </p>
      ) : null}
    </section>
  )
}

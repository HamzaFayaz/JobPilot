import { ArrowLeftIcon, FolderIcon, SparklesIcon } from '@heroicons/react/24/outline'
import { Link } from 'react-router-dom'
import { ProjectsList } from '../components/profile/ProjectsList'
import { useProfile } from '../context/ProfileContext'

export function ProjectEvidencePage() {
  const { profile } = useProfile()
  const projectCount = profile.projects.length

  return (
    <div className="space-y-6 pb-6 sm:space-y-8">
      <header className="relative overflow-hidden rounded-[1.75rem] border border-border bg-surface px-6 py-7 shadow-surface sm:px-8 sm:py-9">
        <div className="pointer-events-none absolute -right-16 -top-16 h-52 w-52 rounded-full bg-secondary/10 blur-3xl" />
        <div className="relative">
          <Link to="/settings" className="inline-flex items-center gap-2 text-sm font-bold text-primary hover:text-primary-hover hover:underline">
            <ArrowLeftIcon className="h-4 w-4" aria-hidden="true" />
            Back to Settings
          </Link>
          <p className="jp-eyebrow mt-6">Profile evidence</p>
          <h1 className="jp-display mt-2 text-3xl font-extrabold tracking-tight text-text-primary sm:text-4xl">
            Projects that prove your skills.
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
            Keep concise project cards here so JobPilot can understand the work behind your CV and make stronger fit assessments.
          </p>
        </div>
      </header>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(280px,0.8fr)]">
        <section className="jp-surface rounded-[1.5rem] p-5 sm:p-6">
          <div className="mb-5 flex items-start justify-between gap-4">
            <div>
              <p className="jp-eyebrow">Saved project cards</p>
              <h2 className="jp-display mt-1 text-xl font-extrabold tracking-tight text-text-primary">Manage project evidence</h2>
            </div>
            <span className="inline-flex min-h-9 items-center rounded-full bg-secondary-soft px-3 text-xs font-bold text-secondary">
              {projectCount} project{projectCount === 1 ? '' : 's'}
            </span>
          </div>
          <ProjectsList embedded />
        </section>

        <aside className="space-y-5">
          <section className="jp-surface rounded-[1.5rem] p-5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary-soft text-primary">
              <SparklesIcon className="h-5 w-5" aria-hidden="true" />
            </span>
            <h2 className="jp-display mt-4 text-lg font-extrabold tracking-tight text-text-primary">Make each card useful</h2>
            <ul className="mt-3 space-y-3 text-sm leading-6 text-text-secondary">
              <li>Use a clear project name.</li>
              <li>Explain what you built and your contribution.</li>
              <li>Keep the description short and specific.</li>
            </ul>
          </section>

          <section className="rounded-[1.5rem] border border-secondary/15 bg-secondary-soft/45 p-5">
            <FolderIcon className="h-5 w-5 text-secondary" aria-hidden="true" />
            <h2 className="jp-display mt-3 text-lg font-extrabold tracking-tight text-text-primary">Have GitHub projects?</h2>
            <p className="mt-2 text-sm leading-6 text-text-secondary">Import repositories from your career profile, then refine the cards here if needed.</p>
            <Link to="/profile" className="mt-4 inline-flex text-sm font-bold text-secondary hover:underline">Open career profile</Link>
          </section>
        </aside>
      </div>
    </div>
  )
}

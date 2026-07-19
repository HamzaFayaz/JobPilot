import {
  ArrowRightIcon,
  BookOpenIcon,
  CodeBracketIcon,
  FolderIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline'
import { Link } from 'react-router-dom'
import { SearchHelperCompactCard } from '../components/settings/SearchHelperCompactCard'
import { useProfile } from '../context/ProfileContext'

export function SettingsPage() {
  const { profile } = useProfile()
  const skillsReady = profile.skillsExtractionStatus === 'ready' && profile.skills.length > 0
  const projectCount = profile.projects.length
  const hasProjects = projectCount > 0

  return (
    <div className="space-y-6 pb-6 sm:space-y-8">
      <header className="flex flex-col gap-4 border-b border-border pb-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="jp-eyebrow">Settings</p>
          <h1 className="jp-display mt-2 text-3xl font-extrabold tracking-tight text-text-primary sm:text-4xl">
            Connections &amp; profile evidence
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
            Keep your search connection ready and review the evidence JobPilot uses to understand your fit.
          </p>
        </div>
        <span className="inline-flex items-center gap-2 self-start rounded-full border border-primary/15 bg-primary-soft px-3 py-2 text-xs font-bold text-primary sm:self-auto">
          <ShieldCheckIcon className="h-4 w-4" aria-hidden="true" />
          Your workspace
        </span>
      </header>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(270px,0.8fr)]">
        <SearchHelperCompactCard />

        <aside className="space-y-4">
          <Link to="/settings/search-helper-guide" className="group block rounded-[1.5rem] border border-primary/20 bg-primary-soft/55 p-5 transition-colors hover:bg-primary-soft focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-white shadow-sm shadow-primary/20">
              <BookOpenIcon className="h-5 w-5" aria-hidden="true" />
            </span>
            <p className="jp-eyebrow mt-5">Need help?</p>
            <h2 className="jp-display mt-1 text-xl font-extrabold tracking-tight text-text-primary">Open the setup guide</h2>
            <p className="mt-2 text-sm leading-6 text-text-secondary">A separate step-by-step guide for profile, WebBridge, Helper, pairing, and first search.</p>
            <span className="mt-4 inline-flex items-center gap-2 text-sm font-bold text-primary group-hover:text-primary-hover">
              View guide and rules
              <ArrowRightIcon className="h-4 w-4" aria-hidden="true" />
            </span>
          </Link>

          <section className="rounded-[1.5rem] border border-sidebar/10 bg-sidebar p-5 text-white shadow-lg shadow-slate-950/10">
            <p className="jp-eyebrow !text-teal-200">Your control</p>
            <p className="jp-display mt-2 text-lg font-extrabold tracking-tight">JobPilot recommends. You decide.</p>
            <p className="mt-2 text-sm leading-6 text-slate-300">Your browser session stays yours, and JobPilot never sends applications automatically.</p>
          </section>
        </aside>
      </div>

      <section aria-labelledby="evidence-heading" className="space-y-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="jp-eyebrow">Matching evidence</p>
            <h2 id="evidence-heading" className="jp-display mt-1 text-2xl font-extrabold tracking-tight text-text-primary">Skills and projects</h2>
            <p className="mt-2 text-sm text-text-secondary">Open each library when you want to review or manage its details.</p>
          </div>
          <Link to="/profile" className="text-sm font-bold text-primary hover:text-primary-hover hover:underline">Edit career profile</Link>
        </div>

        <div className="grid gap-5 lg:grid-cols-2">
          <Link to="/settings/skills" className="group jp-surface rounded-[1.5rem] p-5 transition-all hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 sm:p-6">
            <div className="flex items-start justify-between gap-4">
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-primary-soft text-primary">
                <CodeBracketIcon className="h-5 w-5" aria-hidden="true" />
              </span>
              <span className={`inline-flex min-h-9 items-center rounded-full px-3 text-xs font-bold ${skillsReady ? 'bg-success-soft text-success' : 'bg-surface-muted text-text-secondary'}`}>
                {skillsReady ? `${profile.skills.length} skills` : 'Pending'}
              </span>
            </div>
            <h3 className="jp-display mt-5 text-xl font-extrabold tracking-tight text-text-primary">Skill library</h3>
            <p className="mt-2 max-w-md text-sm leading-6 text-text-secondary">
              {skillsReady ? 'Browse your extracted skills in clear categories and search the full library.' : 'Your CV skills will appear here as soon as extraction is complete.'}
            </p>
            <span className="mt-5 inline-flex items-center gap-2 text-sm font-bold text-primary group-hover:text-primary-hover">
              View skills
              <ArrowRightIcon className="h-4 w-4" aria-hidden="true" />
            </span>
          </Link>

          <Link to="/settings/projects" className="group jp-surface rounded-[1.5rem] p-5 transition-all hover:-translate-y-0.5 hover:border-secondary/35 hover:shadow-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary focus-visible:ring-offset-2 sm:p-6">
            <div className="flex items-start justify-between gap-4">
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-secondary-soft text-secondary">
                <FolderIcon className="h-5 w-5" aria-hidden="true" />
              </span>
              <span className={`inline-flex min-h-9 items-center rounded-full px-3 text-xs font-bold ${hasProjects ? 'bg-secondary-soft text-secondary' : 'bg-surface-muted text-text-secondary'}`}>
                {projectCount || 'No projects'}
              </span>
            </div>
            <h3 className="jp-display mt-5 text-xl font-extrabold tracking-tight text-text-primary">Project library</h3>
            <p className="mt-2 max-w-md text-sm leading-6 text-text-secondary">
              {hasProjects ? 'Review and manage the work samples JobPilot uses to strengthen your job matches.' : 'Add focused project evidence so JobPilot can understand the work behind your skills.'}
            </p>
            <span className="mt-5 inline-flex items-center gap-2 text-sm font-bold text-secondary group-hover:text-secondary-hover">
              Manage projects
              <ArrowRightIcon className="h-4 w-4" aria-hidden="true" />
            </span>
          </Link>
        </div>
      </section>
    </div>
  )
}

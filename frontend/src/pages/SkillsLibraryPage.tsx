import {
  ArrowLeftIcon,
  CodeBracketIcon,
  DocumentTextIcon,
  MagnifyingGlassIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useProfile } from '../context/ProfileContext'

function getInitial(skill: string) {
  const initial = skill.trim().charAt(0).toUpperCase()
  return /^[A-Z0-9]$/.test(initial) ? initial : '#'
}

export function SkillsLibraryPage() {
  const { profile } = useProfile()
  const [query, setQuery] = useState('')
  const [activeLetter, setActiveLetter] = useState('All')
  const skillCount = profile.skills.length
  const isReady = profile.skillsExtractionStatus === 'ready' && skillCount > 0

  const availableLetters = useMemo(
    () => Array.from(new Set(profile.skills.map(getInitial))).sort((a, b) => a.localeCompare(b)),
    [profile.skills],
  )

  useEffect(() => {
    if (activeLetter !== 'All' && !availableLetters.includes(activeLetter)) {
      setActiveLetter('All')
    }
  }, [activeLetter, availableLetters])

  const visibleSkills = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()
    return profile.skills
      .filter((skill) => activeLetter === 'All' || getInitial(skill) === activeLetter)
      .filter((skill) => !normalizedQuery || skill.toLowerCase().includes(normalizedQuery))
  }, [activeLetter, profile.skills, query])

  return (
    <div className="space-y-6 pb-6 sm:space-y-8">
      <header className="relative overflow-hidden rounded-[1.75rem] border border-border bg-surface px-6 py-7 shadow-surface sm:px-8 sm:py-9">
        <div className="pointer-events-none absolute -right-16 -top-16 h-52 w-52 rounded-full bg-primary/10 blur-3xl" />
        <div className="relative">
          <Link to="/settings" className="inline-flex items-center gap-2 text-sm font-bold text-primary hover:text-primary-hover hover:underline">
            <ArrowLeftIcon className="h-4 w-4" aria-hidden="true" />
            Back to Settings
          </Link>
          <p className="jp-eyebrow mt-6">CV intelligence</p>
          <h1 className="jp-display mt-2 text-3xl font-extrabold tracking-tight text-text-primary sm:text-4xl">
            Your skill library
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
            A clean, searchable view of every skill extracted from your master CV.
          </p>
        </div>
      </header>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(280px,0.8fr)]">
        <section className="jp-surface rounded-[1.5rem] p-5 sm:p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="jp-eyebrow">Extracted skills</p>
              <h2 className="jp-display mt-1 text-xl font-extrabold tracking-tight text-text-primary">
                {isReady ? `${skillCount} skills ready for matching` : 'Skills are being prepared'}
              </h2>
            </div>
            <div className="relative w-full sm:max-w-xs">
              <MagnifyingGlassIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-tertiary" aria-hidden="true" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search skills"
                className="jp-input w-full pl-9 text-sm"
                aria-label="Search skills"
              />
            </div>
          </div>

          {!isReady ? (
            <div className="mt-6 rounded-2xl border border-dashed border-border-strong bg-surface-muted/45 px-5 py-8 text-center text-sm text-text-secondary">
              {profile.cvFilename ? 'JobPilot is still extracting your skills. This page updates when it is ready.' : 'Upload your master CV to create your skill library.'}
            </div>
          ) : (
            <>
              <div className="mt-5 flex flex-wrap gap-2 border-y border-border py-4">
                {['All', ...availableLetters].map((letter) => {
                  const count = letter === 'All'
                    ? skillCount
                    : profile.skills.filter((skill) => getInitial(skill) === letter).length
                  return (
                    <button
                      key={letter}
                      type="button"
                      onClick={() => setActiveLetter(letter)}
                      className={`inline-flex min-h-9 items-center gap-2 rounded-full border px-3 text-xs font-bold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 ${activeLetter === letter ? 'border-primary bg-primary text-white' : 'border-border bg-surface text-text-secondary hover:border-primary/35 hover:text-text-primary'}`}
                    >
                      {letter}
                      <span className={`rounded-full px-1.5 py-0.5 text-[10px] ${activeLetter === letter ? 'bg-white/20 text-white' : 'bg-surface-muted text-text-tertiary'}`}>{count}</span>
                    </button>
                  )
                })}
              </div>

              <div className="mt-5">
                {visibleSkills.length > 0 ? (
                  <section className="rounded-2xl border border-border bg-surface-muted/35 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <h3 className="text-sm font-extrabold text-text-primary">
                        {activeLetter === 'All' ? 'All skills' : `Skills starting with ${activeLetter}`}
                      </h3>
                      <span className="rounded-full bg-surface px-2.5 py-1 text-[11px] font-bold text-text-secondary">{visibleSkills.length}</span>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {visibleSkills.map((skill) => (
                        <span key={skill} className="rounded-full border border-border bg-surface px-3 py-1.5 text-sm font-medium text-text-primary">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </section>
                ) : (
                  <div className="rounded-2xl border border-dashed border-border-strong px-5 py-8 text-center text-sm text-text-secondary">
                    No skills match your current search or filter.
                  </div>
                )}
              </div>
            </>
          )}
        </section>

        <aside className="space-y-5">
          <section className="jp-surface rounded-[1.5rem] p-5">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-soft text-primary">
              <CodeBracketIcon className="h-5 w-5" aria-hidden="true" />
            </span>
            <h2 className="jp-display mt-4 text-lg font-extrabold tracking-tight text-text-primary">How skills are used</h2>
            <p className="mt-2 text-sm leading-6 text-text-secondary">JobPilot compares these skills with the requirements it finds in LinkedIn posts and shows you the evidence behind each fit score.</p>
          </section>

          <section className="rounded-[1.5rem] border border-secondary/15 bg-secondary-soft/45 p-5">
            <DocumentTextIcon className="h-5 w-5 text-secondary" aria-hidden="true" />
            <h2 className="jp-display mt-3 text-lg font-extrabold tracking-tight text-text-primary">Need to change them?</h2>
            <p className="mt-2 text-sm leading-6 text-text-secondary">Skills are read-only because they come from your CV. Update your master CV, then upload it again.</p>
            <Link to="/profile" className="mt-4 inline-flex items-center gap-2 text-sm font-bold text-secondary hover:underline">
              Update career profile
              <SparklesIcon className="h-4 w-4" aria-hidden="true" />
            </Link>
          </section>
        </aside>
      </div>
    </div>
  )
}

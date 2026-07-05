import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline'
import { useState } from 'react'
import { useProfile } from '../../context/ProfileContext'
import { Button } from '../ui/Button'

interface ProjectsListProps {
  /** When true, omit outer section chrome (used inside CollapsibleSection). */
  embedded?: boolean
}

export function ProjectsList({ embedded = false }: ProjectsListProps) {
  const { profile, addProject, updateProject, removeProject } = useProfile()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')

  const handleAdd = () => {
    const trimmedName = name.trim()
    const trimmedDescription = description.trim()
    if (!trimmedName) return
    addProject({ name: trimmedName, description: trimmedDescription })
    setName('')
    setDescription('')
  }

  const inner = (
    <>
      <div className="space-y-4">
        {profile.projects.map((project) => (
          <article
            key={project.id}
            className="rounded-lg border border-border bg-background p-4"
          >
            <div className="mb-3 flex items-start justify-between gap-3">
              <input
                aria-label="Project name"
                value={project.name}
                onChange={(e) => updateProject(project.id, { name: e.target.value })}
                className="w-full rounded-md border border-border px-3 py-2 text-sm font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              />
              <button
                type="button"
                aria-label={`Remove project ${project.name}`}
                className="inline-flex min-h-11 min-w-11 shrink-0 cursor-pointer items-center justify-center rounded-lg text-error transition-colors duration-200 hover:bg-error/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                onClick={() => removeProject(project.id)}
              >
                <TrashIcon className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
            <textarea
              aria-label="Project description"
              value={project.description}
              onChange={(e) => updateProject(project.id, { description: e.target.value })}
              rows={3}
              className="w-full rounded-md border border-border px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              placeholder="What did you build?"
            />
          </article>
        ))}
      </div>

      <div className="mt-4 space-y-3 rounded-lg border border-dashed border-border p-4">
        <input
          aria-label="New project name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Project name"
          className="w-full rounded-md border border-border px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        />
        <textarea
          aria-label="New project description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Short description"
          rows={2}
          className="w-full rounded-md border border-border px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        />
        <Button variant="secondary" onClick={handleAdd} className="w-full sm:w-auto">
          <PlusIcon className="mr-2 h-4 w-4" aria-hidden="true" />
          Add project
        </Button>
      </div>
    </>
  )

  if (embedded) {
    return inner
  }

  return (
    <section className="rounded-xl border border-border bg-surface p-6 shadow-sm">
      <h3 className="mb-4 text-base font-semibold text-text-primary">Projects</h3>
      {inner}
    </section>
  )
}

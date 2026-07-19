import { SparklesIcon } from '@heroicons/react/24/outline'
import { useProfile } from '../../context/ProfileContext'
import { ChipInput } from '../ui/ChipInput'

export function RolesInput() {
  const { profile, addRole, removeRole } = useProfile()

  return (
    <section className="jp-surface rounded-[1.5rem] p-5 sm:p-6">
      <div className="mb-5 flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-secondary-soft text-secondary">
          <SparklesIcon className="h-5 w-5" aria-hidden="true" />
        </span>
        <div>
          <p className="jp-eyebrow !text-secondary">Search signal</p>
          <h3 className="jp-display mt-1 text-lg font-extrabold tracking-tight text-text-primary">
            Roles worth scouting
          </h3>
        </div>
      </div>
      <ChipInput
        id="roles-input"
        label="Target roles"
        placeholder="e.g. Senior Backend Engineer"
        values={profile.targetRoles}
        onAdd={addRole}
        onRemove={removeRole}
      />
      <p className="mt-3 text-xs leading-5 text-text-secondary">
        JobPilot lets you select one target role per search run.
      </p>
    </section>
  )
}

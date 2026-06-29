import { useProfile } from '../../context/ProfileContext'
import { ChipInput } from '../ui/ChipInput'

export function RolesInput() {
  const { profile, addRole, removeRole } = useProfile()

  return (
    <section className="rounded-lg border border-border bg-surface p-6 shadow-sm">
      <ChipInput
        id="roles-input"
        label="Target roles"
        placeholder="Add a role and press Enter"
        values={profile.targetRoles}
        onAdd={addRole}
        onRemove={removeRole}
      />
      <p className="mt-2 text-xs text-text-secondary">
        Add one or more roles. Search will let you pick one per run.
      </p>
    </section>
  )
}

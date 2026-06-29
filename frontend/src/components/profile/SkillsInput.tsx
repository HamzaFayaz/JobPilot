import { useProfile } from '../../context/ProfileContext'
import { ChipInput } from '../ui/ChipInput'

export function SkillsInput() {
  const { profile, addSkill, removeSkill } = useProfile()

  return (
    <section className="rounded-lg border border-border bg-surface p-6 shadow-sm">
      <ChipInput
        id="skills-input"
        label="Skills"
        placeholder="Add a skill and press Enter"
        values={profile.skills}
        onAdd={addSkill}
        onRemove={removeSkill}
      />
      <p className="mt-2 text-xs text-text-secondary">Add at least 3 skills for search.</p>
    </section>
  )
}

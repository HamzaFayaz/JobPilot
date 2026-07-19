import { PlusIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { useState, type KeyboardEvent } from 'react'

interface ChipInputProps {
  label: string
  placeholder: string
  values: string[]
  onAdd: (value: string) => void
  onRemove: (value: string) => void
  id?: string
}

export function ChipInput({
  label,
  placeholder,
  values,
  onAdd,
  onRemove,
  id = 'chip-input',
}: ChipInputProps) {
  const [draft, setDraft] = useState('')

  const commit = () => {
    const trimmed = draft.trim()
    if (!trimmed) return
    onAdd(trimmed)
    setDraft('')
  }

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      event.preventDefault()
      commit()
    }
  }

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
        <label htmlFor={id} className="text-sm font-semibold text-text-primary">
          {label}
        </label>
        <span className="text-xs text-text-tertiary">Press Enter to add</span>
      </div>
      <div className="rounded-2xl border border-border bg-surface-muted/50 p-3">
        {values.length > 0 ? (
          <div className="mb-3 flex flex-wrap gap-2">
            {values.map((value) => (
              <span
                key={value}
                className="inline-flex min-h-10 items-center gap-1 rounded-xl border border-primary/10 bg-primary-soft px-2.5 text-sm font-semibold text-primary"
              >
                <span className="max-w-48 truncate">{value}</span>
                <button
                  type="button"
                  aria-label={`Remove ${value}`}
                  className="inline-flex min-h-9 min-w-9 cursor-pointer items-center justify-center rounded-lg text-primary transition-colors duration-200 hover:bg-primary/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  onClick={() => onRemove(value)}
                >
                  <XMarkIcon className="h-4 w-4" aria-hidden="true" />
                </button>
              </span>
            ))}
          </div>
        ) : (
          <p className="mb-3 text-xs leading-5 text-text-secondary">
            Add the roles you want JobPilot to prioritize.
          </p>
        )}
        <div className="flex gap-2">
          <input
            id={id}
            type="text"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={onKeyDown}
            onBlur={commit}
            placeholder={placeholder}
            className="jp-input min-w-0 flex-1 px-3 py-2 text-base sm:text-sm"
          />
          <button
            type="button"
            aria-label={`Add ${label.toLowerCase()}`}
            onClick={commit}
            className="inline-flex min-h-11 min-w-11 shrink-0 cursor-pointer items-center justify-center rounded-xl border border-primary/25 bg-surface text-primary transition-colors hover:bg-primary-soft focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            <PlusIcon className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  )
}

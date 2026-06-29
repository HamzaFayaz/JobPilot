import { XMarkIcon } from '@heroicons/react/24/outline'
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
      <label htmlFor={id} className="mb-2 block text-sm font-semibold text-text-primary">
        {label}
      </label>
      <div className="rounded-lg border border-border bg-surface p-3">
        <div className="mb-2 flex flex-wrap gap-2">
          {values.map((value) => (
            <span
              key={value}
              className="inline-flex min-h-11 items-center gap-1 rounded-full bg-chip-bg px-3 py-1 text-sm text-primary"
            >
              {value}
              <button
                type="button"
                aria-label={`Remove ${value}`}
                className="inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center rounded-full transition-colors duration-200 hover:bg-primary/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                onClick={() => onRemove(value)}
              >
                <XMarkIcon className="h-4 w-4" aria-hidden="true" />
              </button>
            </span>
          ))}
        </div>
        <input
          id={id}
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKeyDown}
          onBlur={commit}
          placeholder={placeholder}
          className="w-full rounded-md border border-border px-3 py-2 text-base text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary sm:text-sm"
        />
      </div>
    </div>
  )
}

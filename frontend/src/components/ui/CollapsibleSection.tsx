import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline'
import { useState, type ReactNode } from 'react'

interface CollapsibleSectionProps {
  title: string
  description?: string
  badge?: string
  defaultOpen?: boolean
  children: ReactNode
}

export function CollapsibleSection({
  title,
  description,
  badge,
  defaultOpen = false,
  children,
}: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <section className="overflow-hidden rounded-xl border border-border bg-surface shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex w-full cursor-pointer items-center gap-3 px-5 py-4 text-left transition-colors duration-200 hover:bg-chip-bg/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-primary"
        aria-expanded={open}
      >
        {open ? (
          <ChevronDownIcon className="h-5 w-5 shrink-0 text-text-secondary" aria-hidden="true" />
        ) : (
          <ChevronRightIcon className="h-5 w-5 shrink-0 text-text-secondary" aria-hidden="true" />
        )}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-base font-semibold text-text-primary">{title}</h2>
            {badge ? (
              <span className="rounded-full bg-chip-bg px-2.5 py-0.5 text-xs font-medium text-primary">
                {badge}
              </span>
            ) : null}
          </div>
          {description && !open ? (
            <p className="mt-0.5 truncate text-sm text-text-secondary">{description}</p>
          ) : null}
        </div>
      </button>
      {open ? <div className="border-t border-border px-5 py-5">{children}</div> : null}
    </section>
  )
}

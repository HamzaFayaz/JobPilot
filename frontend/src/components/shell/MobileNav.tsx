import { Bars3Icon, PaperAirplaneIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { useEffect, useState } from 'react'
import { Sidebar } from './Sidebar'

export function MobileNav() {
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (!open) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('keydown', onKeyDown)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = ''
    }
  }, [open])

  return (
    <>
      <header className="flex items-center justify-between border-b border-border/80 bg-surface/90 px-4 py-3 backdrop-blur lg:hidden">
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-white shadow-sm shadow-primary/25">
            <PaperAirplaneIcon className="h-4.5 w-4.5 -rotate-45" aria-hidden="true" />
          </span>
          <div>
            <p className="jp-display text-base font-extrabold tracking-tight text-text-primary">JobPilot</p>
            <p className="text-[10px] font-medium uppercase tracking-[0.1em] text-text-tertiary">
              Pilot desk
            </p>
          </div>
        </div>
        <button
          type="button"
          aria-expanded={open}
          aria-controls="mobile-drawer"
          aria-label={open ? 'Close navigation menu' : 'Open navigation menu'}
          className="inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center rounded-xl border border-border bg-surface transition-colors duration-200 hover:bg-surface-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          onClick={() => setOpen((prev) => !prev)}
        >
          {open ? (
            <XMarkIcon className="h-6 w-6" aria-hidden="true" />
          ) : (
            <Bars3Icon className="h-6 w-6" aria-hidden="true" />
          )}
        </button>
      </header>

      {open ? (
        <button
          type="button"
          aria-label="Close navigation overlay"
          className="fixed inset-0 z-40 bg-black/40 lg:hidden"
          onClick={() => setOpen(false)}
        />
      ) : null}

      <div
        id="mobile-drawer"
        className={`fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-200 lg:hidden ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-hidden={!open}
      >
        <Sidebar onNavigate={() => setOpen(false)} className="shadow-xl" />
      </div>
    </>
  )
}

import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline'
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
      <header className="flex items-center justify-between border-b border-border bg-surface px-4 py-3 lg:hidden">
        <div>
          <p className="text-base font-bold text-text-primary">JobPilot</p>
          <p className="text-xs text-text-secondary">Your AI job application copilot</p>
        </div>
        <button
          type="button"
          aria-expanded={open}
          aria-controls="mobile-drawer"
          aria-label={open ? 'Close navigation menu' : 'Open navigation menu'}
          className="inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center rounded-lg border border-border transition-colors duration-200 hover:bg-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
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
        className={`fixed inset-y-0 left-0 z-50 w-60 transform transition-transform duration-200 lg:hidden ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-hidden={!open}
      >
        <Sidebar onNavigate={() => setOpen(false)} className="shadow-xl" />
      </div>
    </>
  )
}

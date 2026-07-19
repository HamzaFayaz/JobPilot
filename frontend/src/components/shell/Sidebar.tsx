import {
  ArrowRightOnRectangleIcon,
  Cog6ToothIcon,
  DocumentTextIcon,
  MagnifyingGlassIcon,
  PaperAirplaneIcon,
  SparklesIcon,
  UserCircleIcon,
} from '@heroicons/react/24/outline'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useProfile } from '../../context/ProfileContext'

interface SidebarProps {
  onNavigate?: () => void
  className?: string
}

type NavItem = {
  key: string
  label: string
  to?: string
  icon: typeof UserCircleIcon
  disabled?: boolean
  requiresGate?: boolean
}

const navItems: NavItem[] = [
  { key: 'profile', label: 'Profile', to: '/profile', icon: UserCircleIcon },
  {
    key: 'search',
    label: 'Search',
    to: '/search',
    icon: MagnifyingGlassIcon,
    requiresGate: true,
  },
  {
    key: 'applications',
    label: 'Applications',
    to: '/applications',
    icon: DocumentTextIcon,
    requiresGate: true,
  },
  { key: 'settings', label: 'Settings', to: '/settings', icon: Cog6ToothIcon },
]

export function Sidebar({ onNavigate, className = '' }: SidebarProps) {
  const { gate } = useProfile()
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
    onNavigate?.()
  }

  return (
    <aside
      className={`jp-grid-pattern relative flex h-full w-64 flex-col overflow-hidden bg-sidebar text-white ${className}`}
      aria-label="Main navigation"
    >
      <div className="pointer-events-none absolute -right-20 -top-20 h-48 w-48 rounded-full bg-primary/20 blur-3xl" />
      <div className="relative border-b border-white/10 px-5 py-6">
        <NavLink
          to={gate.isComplete ? '/applications' : '/'}
          onClick={onNavigate}
          className="group block cursor-pointer rounded-xl transition-colors duration-200 hover:text-teal-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          <span className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-white shadow-lg shadow-black/20 transition-transform duration-200 group-hover:-rotate-6 group-hover:scale-105">
              <PaperAirplaneIcon className="h-5 w-5 -rotate-45" aria-hidden="true" />
            </span>
            <span>
              <span className="jp-display block text-lg font-extrabold tracking-tight">JobPilot</span>
              <span className="mt-0.5 block text-[11px] font-medium tracking-wide text-slate-400">
                Career intelligence
              </span>
            </span>
          </span>
        </NavLink>
      </div>

      <nav className="relative flex-1 px-3 py-5">
        <p className="px-3 pb-2 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">
          Workspace
        </p>
        <ul className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const blockedByGate = item.requiresGate && !gate.isComplete
            const isDisabled = item.disabled || blockedByGate

            if (isDisabled || !item.to) {
              return (
                <li key={item.key}>
                  <span
                    className="flex min-h-11 cursor-not-allowed items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-400 opacity-60"
                    aria-disabled="true"
                  >
                    <Icon className="h-6 w-6 shrink-0" aria-hidden="true" />
                    {item.label}
                  </span>
                </li>
              )
            }

            return (
              <li key={item.key}>
                <NavLink
                  to={item.to}
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    `flex min-h-11 cursor-pointer items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                      isActive
                        ? 'bg-primary/16 text-white ring-1 ring-inset ring-primary/60 shadow-inner shadow-black/10'
                        : 'text-slate-300 hover:bg-white/7 hover:text-white'
                    }`
                  }
                >
                  <Icon className="h-6 w-6 shrink-0" aria-hidden="true" />
                  {item.label}
                </NavLink>
              </li>
            )
          })}
        </ul>
      </nav>

      <div className="relative border-t border-white/10 px-4 py-4">
        <div className="mb-3 flex items-center gap-2 rounded-xl border border-white/8 bg-white/5 px-3 py-2 text-[11px] text-slate-300">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-50" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
          </span>
          <SparklesIcon className="h-3.5 w-3.5 text-teal-200" aria-hidden="true" />
          Your pilot desk
        </div>
        {user && (
          <p className="truncate px-1 text-xs text-slate-400" title={user.email}>
            {user.email}
          </p>
        )}
        <button
          type="button"
          onClick={() => void handleLogout()}
          className="mt-2 flex min-h-11 w-full cursor-pointer items-center gap-3 rounded-xl px-3 py-2 text-sm text-slate-300 transition-colors duration-200 hover:bg-white/7 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          <ArrowRightOnRectangleIcon className="h-6 w-6 shrink-0" aria-hidden="true" />
          Log out
        </button>
      </div>
    </aside>
  )
}

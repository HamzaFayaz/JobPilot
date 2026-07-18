import {
  ArrowRightOnRectangleIcon,
  Cog6ToothIcon,
  DocumentTextIcon,
  MagnifyingGlassIcon,
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
      className={`flex h-full w-60 flex-col bg-sidebar text-white ${className}`}
      aria-label="Main navigation"
    >
      <div className="border-b border-white/10 px-5 py-6">
        <NavLink
          to={gate.isComplete ? '/applications' : '/'}
          onClick={onNavigate}
          className="block cursor-pointer rounded-md transition-colors duration-200 hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          <p className="text-lg font-bold tracking-tight">JobPilot</p>
          <p className="mt-1 text-xs text-slate-300">Your AI job application copilot</p>
        </NavLink>
      </div>

      <nav className="flex-1 px-3 py-4">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const blockedByGate = item.requiresGate && !gate.isComplete
            const isDisabled = item.disabled || blockedByGate

            if (isDisabled || !item.to) {
              return (
                <li key={item.key}>
                  <span
                    className="flex min-h-11 cursor-not-allowed items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-400 opacity-60"
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
                    `flex min-h-11 cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                      isActive
                        ? 'bg-white/10 text-white ring-1 ring-inset ring-primary'
                        : 'text-slate-200 hover:bg-white/5'
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

      <div className="border-t border-white/10 px-4 py-4">
        {user && (
          <p className="truncate text-xs text-slate-400" title={user.email}>
            {user.email}
          </p>
        )}
        <button
          type="button"
          onClick={() => void handleLogout()}
          className="mt-2 flex min-h-11 w-full cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-200 transition-colors duration-200 hover:bg-white/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          <ArrowRightOnRectangleIcon className="h-6 w-6 shrink-0" aria-hidden="true" />
          Log out
        </button>
      </div>
    </aside>
  )
}

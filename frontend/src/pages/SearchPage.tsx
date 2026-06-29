import {
  LightBulbIcon,
  MagnifyingGlassIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline'
import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { useProfile } from '../context/ProfileContext'

type Platform = 'linkedin' | 'indeed'

export function SearchPage() {
  const { profile, gate } = useProfile()
  const [role, setRole] = useState(profile.targetRoles[0] ?? '')
  const [platform, setPlatform] = useState<Platform>('linkedin')
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    if (profile.targetRoles.length && !profile.targetRoles.includes(role)) {
      setRole(profile.targetRoles[0])
    }
  }, [profile.targetRoles, role])

  if (!gate.isComplete) {
    return <Navigate to="/profile" replace />
  }

  const showToast = () => {
    setToast('Search coming soon — backend integration is not wired yet.')
    window.setTimeout(() => setToast(null), 3000)
  }

  const summaryParts = [
    profile.cvFilename ?? 'No CV',
    `${profile.skills.length} skills`,
    `${profile.projects.length} projects`,
  ]

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-bold text-text-primary sm:text-3xl">New Search</h1>
        <p className="mt-2 text-sm text-text-secondary">
          Configure your AI agent to find and score relevant job opportunities.
        </p>
      </header>

      <div className="mx-auto max-w-xl">
        <div className="rounded-lg border border-border bg-surface p-6 shadow-sm">
          <div className="mb-6 flex items-start gap-3 rounded-lg bg-hitl-bg p-4 text-hitl-text">
            <ShieldCheckIcon className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
            <p className="text-sm">
              <span className="font-semibold">Human-in-the-loop:</span> You approve before
              anything is sent.
            </p>
          </div>

          <form
            className="space-y-6"
            onSubmit={(e) => {
              e.preventDefault()
              showToast()
            }}
          >
            <div>
              <label htmlFor="target-role" className="mb-2 block text-sm font-semibold">
                Target role
              </label>
              {profile.targetRoles.length === 0 ? (
                <p className="text-sm text-text-secondary">
                  Add target roles on your profile first.
                </p>
              ) : (
                <select
                  id="target-role"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full cursor-pointer rounded-lg border border-border bg-surface px-3 py-3 text-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary sm:text-sm"
                >
                  {profile.targetRoles.map((targetRole) => (
                    <option key={targetRole} value={targetRole}>
                      {targetRole}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <fieldset>
              <legend className="mb-2 text-sm font-semibold text-text-primary">Platform</legend>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {([
                  { id: 'linkedin' as const, label: 'LinkedIn', badge: 'in', color: 'bg-[#0A66C2]' },
                  { id: 'indeed' as const, label: 'Indeed', badge: 'i', color: 'bg-[#2164f3]' },
                ]).map((item) => (
                  <label
                    key={item.id}
                    className={`flex cursor-pointer items-center justify-between rounded-lg border p-4 transition-colors duration-200 ${
                      platform === item.id
                        ? 'border-primary bg-chip-bg/40'
                        : 'border-border hover:border-primary/40'
                    }`}
                  >
                    <span className="flex items-center gap-3">
                      <span
                        className={`flex h-8 w-8 items-center justify-center rounded text-sm font-bold text-white ${item.color}`}
                      >
                        {item.badge}
                      </span>
                      <span className="text-sm font-medium">{item.label}</span>
                    </span>
                    <input
                      type="radio"
                      name="platform"
                      value={item.id}
                      checked={platform === item.id}
                      onChange={() => setPlatform(item.id)}
                      className="h-4 w-4 cursor-pointer accent-primary"
                    />
                  </label>
                ))}
              </div>
            </fieldset>

            <p className="flex items-center gap-2 text-sm text-text-secondary">
              <MagnifyingGlassIcon className="h-4 w-4" aria-hidden="true" />
              {summaryParts.join(' · ')}
            </p>

            <Button
              type="submit"
              className="w-full"
              disabled={!profile.targetRoles.length}
            >
              Start search
            </Button>
          </form>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <article className="rounded-lg border border-border bg-surface p-5">
          <LightBulbIcon className="mb-2 h-6 w-6 text-primary" aria-hidden="true" />
          <h2 className="text-sm font-semibold">Tip: Be specific with roles</h2>
          <p className="mt-1 text-xs text-text-secondary">
            Narrow titles like &quot;Senior Backend Engineer&quot; produce better matches than
            generic labels.
          </p>
        </article>
        <article className="rounded-lg border border-border bg-surface p-5">
          <ShieldCheckIcon className="mb-2 h-6 w-6 text-primary" aria-hidden="true" />
          <h2 className="text-sm font-semibold">You stay in control</h2>
          <p className="mt-1 text-xs text-text-secondary">
            Search results will feed into a human-approved application flow — nothing sends
            automatically.
          </p>
        </article>
      </div>

      {toast ? (
        <div
          role="status"
          className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-lg bg-sidebar px-4 py-3 text-sm text-white shadow-lg"
        >
          {toast}
        </div>
      ) : null}
    </div>
  )
}

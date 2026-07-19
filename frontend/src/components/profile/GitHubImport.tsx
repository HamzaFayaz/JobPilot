import { CodeBracketIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { useState } from 'react'
import {
  disconnectGitHub,
  importGitHubRepos,
  listGitHubRepos,
  OAUTH_BASE,
} from '../../api/profile'
import { useProfile } from '../../context/ProfileContext'
import type { GitHubRepo } from '../../types/profile'
import { Button } from '../ui/Button'

export function GitHubImport() {
  const { profile, refreshProfile } = useProfile()
  const [repos, setRepos] = useState<GitHubRepo[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [modalOpen, setModalOpen] = useState(false)
  const [loadingRepos, setLoadingRepos] = useState(false)
  const [importing, setImporting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const openModal = async () => {
    setError(null)
    setLoadingRepos(true)
    setModalOpen(true)
    try {
      const list = await listGitHubRepos()
      setRepos(list)
    } catch {
      setError('Failed to load repositories.')
    } finally {
      setLoadingRepos(false)
    }
  }

  const handleConnect = () => {
    window.location.href = `${OAUTH_BASE}/auth/github`
  }

  const handleDisconnect = async () => {
    await disconnectGitHub()
    await refreshProfile()
  }

  const toggleRepo = (fullName: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(fullName)) next.delete(fullName)
      else next.add(fullName)
      return next
    })
  }

  const handleImport = async () => {
    if (selected.size === 0) return
    setImporting(true)
    setError(null)
    try {
      await importGitHubRepos([...selected])
      await refreshProfile()
      setModalOpen(false)
      setSelected(new Set())
    } catch (err: unknown) {
      const message =
        err instanceof Error && err.message
          ? err.message
          : 'Import failed. Please try again.'
      setError(message)
    } finally {
      setImporting(false)
    }
  }

  const indexingPending = profile.projectsIndexingStatus === 'pending'
  const indexingFailed = profile.projectsIndexingStatus === 'failed'

  return (
    <>
      <section className="rounded-lg border border-border bg-surface p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <CodeBracketIcon className="mt-0.5 h-6 w-6 text-primary" aria-hidden="true" />
            <div>
              <h3 className="text-base font-semibold text-text-primary">Import from GitHub</h3>
              <p className="text-sm text-text-secondary">
                Connect GitHub and import READMEs as project cards.
              </p>
              {profile.githubConnected && profile.githubUsername ? (
                <p className="mt-1 text-sm font-medium text-success">
                  Connected as {profile.githubUsername}
                </p>
              ) : null}
              {indexingPending ? (
                <p className="mt-1 text-sm font-medium text-warning">
                  Preparing projects in the background. This can take a few minutes.
                </p>
              ) : null}
              {indexingFailed ? (
                <p className="mt-1 text-sm font-medium text-error">
                  Last import failed. Try importing again.
                </p>
              ) : null}
            </div>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            {profile.githubConnected ? (
              <>
                <Button
                  variant="secondary"
                  className="w-full sm:w-auto"
                  onClick={() => void openModal()}
                  disabled={indexingPending}
                >
                  Import repos
                </Button>
                <Button variant="ghost" className="w-full sm:w-auto" onClick={() => void handleDisconnect()}>
                  Disconnect
                </Button>
              </>
            ) : (
              <Button variant="secondary" className="w-full sm:w-auto" onClick={handleConnect}>
                Connect GitHub
              </Button>
            )}
          </div>
        </div>
        {error && !modalOpen ? <p className="mt-2 text-sm text-error">{error}</p> : null}
      </section>

      {modalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[80vh] w-full max-w-lg overflow-hidden rounded-lg border border-border bg-surface shadow-lg">
            <div className="flex items-center justify-between border-b border-border p-4">
              <h3 className="text-base font-semibold text-text-primary">Select repositories</h3>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="rounded p-1 text-text-secondary hover:bg-chip-bg"
                aria-label="Close"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
            <div className="max-h-96 overflow-y-auto p-4">
              {loadingRepos ? (
                <p className="text-sm text-text-secondary">Loading repositories…</p>
              ) : repos.length === 0 ? (
                <p className="text-sm text-text-secondary">No repositories found.</p>
              ) : (
                <ul className="space-y-2">
                  {repos.map((repo) => (
                    <li key={repo.full_name}>
                      <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border p-3 hover:bg-chip-bg/30">
                        <input
                          type="checkbox"
                          checked={selected.has(repo.full_name)}
                          onChange={() => toggleRepo(repo.full_name)}
                          className="mt-1"
                        />
                        <div>
                          <span className="text-sm font-medium text-text-primary">
                            {repo.full_name}
                          </span>
                          {repo.description ? (
                            <p className="text-xs text-text-secondary">{repo.description}</p>
                          ) : null}
                          <p className="text-xs text-text-secondary">
                            {repo.private ? 'Private' : 'Public'}
                            {repo.fork ? ' · Fork' : ''}
                          </p>
                        </div>
                      </label>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="flex justify-end gap-2 border-t border-border p-4">
              <Button variant="ghost" onClick={() => setModalOpen(false)}>
                Cancel
              </Button>
              <Button
                disabled={selected.size === 0 || importing}
                onClick={() => void handleImport()}
              >
                {importing ? 'Starting…' : `Import (${selected.size})`}
              </Button>
            </div>
            {error ? <p className="px-4 pb-4 text-sm text-error">{error}</p> : null}
          </div>
        </div>
      ) : null}
    </>
  )
}

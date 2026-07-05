import {
  EMPTY_PROFILE,
  type GitHubRepo,
  type Profile,
} from '../types/profile'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

function normalize(profile: Partial<Profile>): Profile {
  return {
    ...EMPTY_PROFILE,
    ...profile,
    skills: profile.skills ?? [],
    targetRoles: profile.targetRoles ?? [],
    searchRole: profile.searchRole ?? null,
    searchPlatform: profile.searchPlatform ?? 'linkedin',
    searchCountry: profile.searchCountry ?? null,
    searchWorkMode: profile.searchWorkMode ?? 'both',
    searchMaxListings: profile.searchMaxListings ?? 8,
    searchJobAge: profile.searchJobAge ?? 'week',
    projects: profile.projects ?? [],
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { credentials: 'include', ...init })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || `Request failed: ${res.status}`)
  }
  return res.json() as Promise<T>
}

export async function getProfile(): Promise<Profile> {
  return normalize(await apiFetch<Profile>('/api/profile'))
}

export async function updateProfile(patch: Partial<Profile>): Promise<Profile> {
  const body: Record<string, unknown> = {}
  if (patch.targetRoles !== undefined) body.targetRoles = patch.targetRoles
  if (patch.searchRole !== undefined) body.searchRole = patch.searchRole
  if (patch.searchPlatform !== undefined) body.searchPlatform = patch.searchPlatform
  if (patch.searchCountry !== undefined) body.searchCountry = patch.searchCountry
  if (patch.searchWorkMode !== undefined) body.searchWorkMode = patch.searchWorkMode
  if (patch.searchMaxListings !== undefined) body.searchMaxListings = patch.searchMaxListings
  if (patch.searchJobAge !== undefined) body.searchJobAge = patch.searchJobAge
  if (patch.projects !== undefined) body.projects = patch.projects
  return normalize(
    await apiFetch<Profile>('/api/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  )
}

export async function uploadCv(file: File): Promise<Profile> {
  const form = new FormData()
  form.append('cv', file)
  return normalize(await apiFetch<Profile>('/api/profile/cv', { method: 'POST', body: form }))
}

export async function disconnectGmail(): Promise<void> {
  await apiFetch('/api/auth/google', { method: 'DELETE' })
}

export async function disconnectGitHub(): Promise<void> {
  await apiFetch('/api/auth/github', { method: 'DELETE' })
}

export async function listGitHubRepos(): Promise<GitHubRepo[]> {
  return apiFetch<GitHubRepo[]>('/api/github/repos')
}

export async function importGitHubRepos(repos: string[]): Promise<Profile> {
  return normalize(
    await apiFetch<Profile>('/api/github/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repos }),
    }),
  )
}

// Same origin in production (nginx proxies /auth); direct to API in local dev.
export const OAUTH_BASE =
  (import.meta.env.VITE_OAUTH_BASE as string | undefined) ??
  (API_BASE || (import.meta.env.DEV ? 'http://localhost:8000' : ''))

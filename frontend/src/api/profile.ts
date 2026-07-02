import {
  EMPTY_PROFILE,
  PROFILE_STORAGE_KEY,
  type GitHubRepo,
  type Profile,
} from '../types/profile'

const USE_MOCK = import.meta.env.VITE_USE_MOCK_API === 'true'
const API_BASE = import.meta.env.VITE_API_BASE ?? ''

function mockReadRaw(): Profile | null {
  try {
    const raw = localStorage.getItem(PROFILE_STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw) as Profile
  } catch {
    return null
  }
}

function normalize(profile: Partial<Profile>): Profile {
  return {
    ...EMPTY_PROFILE,
    ...profile,
    skills: profile.skills ?? [],
    targetRoles: profile.targetRoles ?? [],
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
  if (USE_MOCK) {
    return normalize(mockReadRaw() ?? EMPTY_PROFILE)
  }
  return apiFetch<Profile>('/api/profile')
}

export async function updateProfile(patch: Partial<Profile>): Promise<Profile> {
  if (USE_MOCK) {
    const current = normalize(mockReadRaw() ?? EMPTY_PROFILE)
    const next = normalize({ ...current, ...patch })
    localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(next))
    return next
  }
  const body: Record<string, unknown> = {}
  if (patch.targetRoles !== undefined) body.targetRoles = patch.targetRoles
  if (patch.projects !== undefined) body.projects = patch.projects
  return apiFetch<Profile>('/api/profile', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export async function uploadCv(file: File): Promise<Profile> {
  if (USE_MOCK) {
    const current = normalize(mockReadRaw() ?? EMPTY_PROFILE)
    const next = normalize({
      ...current,
      cvFilename: file.name,
      cvFileMeta: { size: file.size },
      skillsExtractionStatus: 'ready',
      skills: ['TypeScript', 'React', 'Python'],
    })
    localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(next))
    return next
  }
  const form = new FormData()
  form.append('cv', file)
  return apiFetch<Profile>('/api/profile/cv', { method: 'POST', body: form })
}

export async function disconnectGmail(): Promise<void> {
  if (USE_MOCK) {
    const current = normalize(mockReadRaw() ?? EMPTY_PROFILE)
    localStorage.setItem(
      PROFILE_STORAGE_KEY,
      JSON.stringify({ ...current, gmailConnected: false, gmailEmail: null }),
    )
    return
  }
  await apiFetch('/api/auth/google', { method: 'DELETE' })
}

export async function disconnectGitHub(): Promise<void> {
  if (USE_MOCK) {
    const current = normalize(mockReadRaw() ?? EMPTY_PROFILE)
    localStorage.setItem(
      PROFILE_STORAGE_KEY,
      JSON.stringify({
        ...current,
        githubConnected: false,
        githubUsername: null,
      }),
    )
    return
  }
  await apiFetch('/api/auth/github', { method: 'DELETE' })
}

export async function listGitHubRepos(): Promise<GitHubRepo[]> {
  return apiFetch<GitHubRepo[]>('/api/github/repos')
}

export async function importGitHubRepos(repos: string[]): Promise<Profile> {
  return apiFetch<Profile>('/api/github/import', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repos }),
  })
}

// Same origin in production (nginx proxies /auth); direct to API in local dev.
export const OAUTH_BASE =
  (import.meta.env.VITE_OAUTH_BASE as string | undefined) ??
  (API_BASE || (import.meta.env.DEV ? 'http://localhost:8000' : ''))

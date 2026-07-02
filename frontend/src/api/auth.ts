const API_BASE = import.meta.env.VITE_API_BASE ?? ''

export interface AuthUser {
  id: number
  email: string
}

async function authFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...init,
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || `Request failed: ${res.status}`)
  }
  if (res.status === 204) {
    return undefined as T
  }
  return res.json() as Promise<T>
}

export async function signup(email: string, password: string): Promise<AuthUser> {
  return authFetch<AuthUser>('/api/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
}

export async function login(email: string, password: string): Promise<AuthUser> {
  return authFetch<AuthUser>('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
}

export async function logout(): Promise<void> {
  await authFetch<void>('/api/auth/logout', { method: 'POST' })
}

export async function getMe(): Promise<AuthUser | null> {
  const res = await fetch(`${API_BASE}/api/auth/me`, { credentials: 'include' })
  if (res.status === 401) return null
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || `Request failed: ${res.status}`)
  }
  return res.json() as Promise<AuthUser>
}

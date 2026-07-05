export type BrowserHealth =
  | 'ready'
  | 'not_installed'
  | 'daemon_down'
  | 'profile_setup'
  | 'busy'
  | 'error'

export interface WorkerStatusResponse {
  connected: boolean
  browserHealth?: BrowserHealth | null
  lastSeenAt?: string | null
  label?: string | null
}

export interface WorkerPairResponse {
  workerToken: string
}

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
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

export async function getWorkerStatus(): Promise<WorkerStatusResponse> {
  return apiFetch<WorkerStatusResponse>('/api/worker/status')
}

export async function pairWorker(): Promise<WorkerPairResponse> {
  return apiFetch<WorkerPairResponse>('/api/worker/pair', {
    method: 'POST',
  })
}

export async function unpairWorker(): Promise<void> {
  await apiFetch<void>('/api/worker/pair', {
    method: 'DELETE',
  })
}

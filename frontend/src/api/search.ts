import type { SearchPlatform } from '../types/profile'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

export type RunStatus = 'pending' | 'running' | 'completed' | 'failed'
export type JobPackageStatus = 'ready' | 'applied' | 'failed'
export type CvDecision = 'keep' | 'swap'

export interface SearchStartResponse {
  runId: number
  status: RunStatus
}

export interface SearchRunStatusResponse {
  runId: number
  status: RunStatus
  jobsReadyCount: number
  progress?: number | null
  error?: string | null
}

export interface JobPackage {
  id: number | null
  runId: number | null
  title: string
  company: string
  url: string
  platform: SearchPlatform
  descriptionText: string
  summary: string
  matchScore: number | null
  currentCvScore: number | null
  suggestedCvScore: number | null
  cvDecision: CvDecision | null
  swapOutProject: string | null
  swapInText: string | null
  draftEmail: string
  status: JobPackageStatus
  error: string | null
  createdAt: string | null
  updatedAt: string | null
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...init,
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || `Request failed: ${res.status}`)
  }
  return res.json() as Promise<T>
}

export async function startSearch(): Promise<SearchStartResponse> {
  return apiFetch<SearchStartResponse>('/api/search', {
    method: 'POST',
  })
}

export async function getLatestRun(): Promise<SearchRunStatusResponse | null> {
  return apiFetch<SearchRunStatusResponse | null>('/api/runs/latest')
}

export async function getRunStatus(runId: number): Promise<SearchRunStatusResponse> {
  return apiFetch<SearchRunStatusResponse>(`/api/runs/${runId}/status`)
}

export async function listRunJobs(runId: number): Promise<JobPackage[]> {
  return apiFetch<JobPackage[]>(`/api/jobs?runId=${runId}`)
}

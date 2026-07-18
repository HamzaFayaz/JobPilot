import type { SearchPlatform } from '../types/profile'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

export type RunStatus = 'pending' | 'running' | 'completed' | 'failed'
export type JobPackageStatus = 'analyzing' | 'ready' | 'applied' | 'skipped' | 'failed'
export type CvDecision = 'keep' | 'swap'
export type JobDecision = 'applied' | 'skipped'

export interface SearchStartResponse {
  runId: number
  runNumber: number
  status: RunStatus
}

export interface SearchRunStatusResponse {
  runId: number
  runNumber: number
  status: RunStatus
  jobsReadyCount: number
  progress?: number | null
  error?: string | null
}

export interface ProjectDecisionView {
  slotIndex: number
  action: 'keep' | 'swap'
  currentProjectName: string
  swapInProjectName: string | null
  rationale: string
  impact: string | null
  targetRequirementIds: string[]
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
  analysis: Record<string, unknown>
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

export async function listJobs(): Promise<JobPackage[]> {
  return apiFetch<JobPackage[]>('/api/jobs')
}

export async function setJobDecision(
  jobId: number,
  decision: JobDecision,
): Promise<JobPackage> {
  return apiFetch<JobPackage>(`/api/jobs/${jobId}/decision`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision }),
  })
}

export function extractProjectDecisions(job: JobPackage): ProjectDecisionView[] {
  const analysis = job.analysis ?? {}
  const classified =
    (analysis.accepted_user_facing_result as Record<string, unknown> | undefined) ??
    (analysis.classified_result as Record<string, unknown> | undefined) ??
    (analysis.accepted_model_result as Record<string, unknown> | undefined) ??
    null
  const raw = (classified?.project_decisions as unknown[]) ?? []
  return raw
    .map((item) => {
      if (!item || typeof item !== 'object') return null
      const row = item as Record<string, unknown>
      const action = row.action === 'swap' ? 'swap' : 'keep'
      return {
        slotIndex: Number(row.slot_index ?? 0),
        action,
        currentProjectName: String(row.current_project_name ?? 'Project'),
        swapInProjectName:
          row.swap_in_project_name == null ? null : String(row.swap_in_project_name),
        rationale: String(row.rationale ?? ''),
        impact: row.impact == null ? null : String(row.impact),
        targetRequirementIds: Array.isArray(row.target_requirement_ids)
          ? row.target_requirement_ids.map(String)
          : [],
      } satisfies ProjectDecisionView
    })
    .filter((item): item is ProjectDecisionView => item !== null)
}

export function extractFitMessage(job: JobPackage): string | null {
  const analysis = job.analysis ?? {}
  const classified =
    (analysis.accepted_user_facing_result as Record<string, unknown> | undefined) ??
    (analysis.classified_result as Record<string, unknown> | undefined)
  const message = classified?.fit_message
  return typeof message === 'string' && message.trim() ? message : null
}

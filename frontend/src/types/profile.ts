export interface Project {
  id: string
  name: string
  description: string
  source?: 'manual' | 'github'
}

export type SkillsExtractionStatus = 'idle' | 'pending' | 'ready' | 'failed'

export interface Profile {
  cvFilename: string | null
  cvFileMeta: { size: number } | null
  skills: string[]
  skillsExtractionStatus: SkillsExtractionStatus
  targetRoles: string[]
  projects: Project[]
  gmailConnected: boolean
  gmailEmail: string | null
  githubConnected: boolean
  githubUsername: string | null
}

export const EMPTY_PROFILE: Profile = {
  cvFilename: null,
  cvFileMeta: null,
  skills: [],
  skillsExtractionStatus: 'idle',
  targetRoles: [],
  projects: [],
  gmailConnected: false,
  gmailEmail: null,
  githubConnected: false,
  githubUsername: null,
}

export const PROFILE_STORAGE_KEY = 'jobpilot-profile'

export interface GitHubRepo {
  name: string
  full_name: string
  private: boolean
  fork: boolean
  description: string | null
  default_branch: string
}

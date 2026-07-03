export interface Project {
  id: string
  name: string
  description: string
  source?: 'manual' | 'github'
}

export type SkillsExtractionStatus = 'idle' | 'pending' | 'ready' | 'failed'
export type SearchPlatform = 'linkedin' | 'indeed'

export interface Profile {
  cvFilename: string | null
  cvFileMeta: { size: number } | null
  skills: string[]
  skillsExtractionStatus: SkillsExtractionStatus
  targetRoles: string[]
  searchRole: string | null
  searchPlatform: SearchPlatform
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
  searchRole: null,
  searchPlatform: 'linkedin',
  projects: [],
  gmailConnected: false,
  gmailEmail: null,
  githubConnected: false,
  githubUsername: null,
}

export interface GitHubRepo {
  name: string
  full_name: string
  private: boolean
  fork: boolean
  description: string | null
  default_branch: string
}

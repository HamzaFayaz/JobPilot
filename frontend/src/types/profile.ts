export interface Project {
  id: string
  name: string
  description: string
  source?: 'manual' | 'github'
}

export type SkillsExtractionStatus = 'idle' | 'pending' | 'ready' | 'failed'
export type ProjectsIndexingStatus = 'idle' | 'pending' | 'ready' | 'failed'
export type SearchPlatform = 'linkedin' | 'indeed'
export type SearchWorkMode = 'remote' | 'onsite' | 'both'
export type SearchJobAge = '24h' | 'week' | 'month'

export interface Profile {
  cvFilename: string | null
  cvFileMeta: { size: number } | null
  skills: string[]
  skillsExtractionStatus: SkillsExtractionStatus
  projectsIndexingStatus: ProjectsIndexingStatus
  targetRoles: string[]
  searchRole: string | null
  searchPlatform: SearchPlatform
  searchCountry: string | null
  searchWorkMode: SearchWorkMode
  searchMaxListings: number
  searchJobAge: SearchJobAge
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
  projectsIndexingStatus: 'idle',
  targetRoles: [],
  searchRole: null,
  searchPlatform: 'linkedin',
  searchCountry: null,
  searchWorkMode: 'both',
  searchMaxListings: 8,
  searchJobAge: 'week',
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

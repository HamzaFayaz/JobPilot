export interface Project {
  id: string
  name: string
  description: string
}

export interface Profile {
  cvFilename: string | null
  cvFileMeta: { size: number } | null
  skills: string[]
  targetRoles: string[]
  projects: Project[]
  gmailConnected: boolean
  gmailEmail: string | null
}

export const EMPTY_PROFILE: Profile = {
  cvFilename: null,
  cvFileMeta: null,
  skills: [],
  targetRoles: [],
  projects: [],
  gmailConnected: false,
  gmailEmail: null,
}

export const PROFILE_STORAGE_KEY = 'jobpilot-profile'

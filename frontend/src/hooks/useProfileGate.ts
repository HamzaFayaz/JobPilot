import { useMemo } from 'react'
import type { Profile } from '../types/profile'

export interface ProfileGate {
  hasCv: boolean
  hasMinSkills: boolean
  hasProject: boolean
  requiredComplete: number
  requiredTotal: number
  isComplete: boolean
}

export function evaluateProfileGate(profile: Profile): ProfileGate {
  const hasCv = Boolean(profile.cvFilename)
  const hasMinSkills = profile.skills.length >= 3
  const hasProject = profile.projects.length >= 1
  const requiredComplete = [hasCv, hasMinSkills, hasProject].filter(Boolean).length

  return {
    hasCv,
    hasMinSkills,
    hasProject,
    requiredComplete,
    requiredTotal: 3,
    isComplete: hasCv && hasMinSkills && hasProject,
  }
}

export function useProfileGate(profile: Profile): ProfileGate {
  return useMemo(() => evaluateProfileGate(profile), [profile])
}

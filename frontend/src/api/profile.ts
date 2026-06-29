import {
  EMPTY_PROFILE,
  PROFILE_STORAGE_KEY,
  type Profile,
} from '../types/profile'

function readRaw(): Profile | null {
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

export function loadProfile(): Profile {
  return normalize(readRaw() ?? EMPTY_PROFILE)
}

export function saveProfile(profile: Profile): Profile {
  const next = normalize(profile)
  localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(next))
  return next
}

export function updateProfile(patch: Partial<Profile>): Profile {
  const current = loadProfile()
  return saveProfile({ ...current, ...patch })
}

export function clearProfile(): void {
  localStorage.removeItem(PROFILE_STORAGE_KEY)
}

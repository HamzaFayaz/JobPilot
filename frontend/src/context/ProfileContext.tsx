import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { loadProfile, saveProfile } from '../api/profile'
import { useProfileGate } from '../hooks/useProfileGate'
import type { Profile, Project } from '../types/profile'

interface ProfileContextValue {
  profile: Profile
  gate: ReturnType<typeof useProfileGate>
  setProfile: (profile: Profile) => void
  updateProfile: (patch: Partial<Profile>) => void
  setCv: (filename: string, size: number) => void
  addSkill: (skill: string) => void
  removeSkill: (skill: string) => void
  addRole: (role: string) => void
  removeRole: (role: string) => void
  addProject: (project: Omit<Project, 'id'>) => void
  updateProject: (id: string, patch: Partial<Omit<Project, 'id'>>) => void
  removeProject: (id: string) => void
  toggleGmail: () => void
}

const ProfileContext = createContext<ProfileContextValue | null>(null)

export function ProfileProvider({ children }: { children: ReactNode }) {
  const [profile, setProfileState] = useState<Profile>(() => loadProfile())
  const gate = useProfileGate(profile)

  const persist = useCallback((next: Profile) => {
    setProfileState(saveProfile(next))
  }, [])

  const setProfile = useCallback(
    (next: Profile) => {
      persist(next)
    },
    [persist],
  )

  const updateProfile = useCallback(
    (patch: Partial<Profile>) => {
      persist({ ...profile, ...patch })
    },
    [persist, profile],
  )

  const setCv = useCallback(
    (filename: string, size: number) => {
      updateProfile({ cvFilename: filename, cvFileMeta: { size } })
    },
    [updateProfile],
  )

  const addSkill = useCallback(
    (skill: string) => {
      const trimmed = skill.trim()
      if (!trimmed || profile.skills.includes(trimmed)) return
      updateProfile({ skills: [...profile.skills, trimmed] })
    },
    [profile.skills, updateProfile],
  )

  const removeSkill = useCallback(
    (skill: string) => {
      updateProfile({ skills: profile.skills.filter((s) => s !== skill) })
    },
    [profile.skills, updateProfile],
  )

  const addRole = useCallback(
    (role: string) => {
      const trimmed = role.trim()
      if (!trimmed || profile.targetRoles.includes(trimmed)) return
      updateProfile({ targetRoles: [...profile.targetRoles, trimmed] })
    },
    [profile.targetRoles, updateProfile],
  )

  const removeRole = useCallback(
    (role: string) => {
      updateProfile({ targetRoles: profile.targetRoles.filter((r) => r !== role) })
    },
    [profile.targetRoles, updateProfile],
  )

  const addProject = useCallback(
    (project: Omit<Project, 'id'>) => {
      const entry: Project = { ...project, id: crypto.randomUUID() }
      updateProfile({ projects: [...profile.projects, entry] })
    },
    [profile.projects, updateProfile],
  )

  const updateProject = useCallback(
    (id: string, patch: Partial<Omit<Project, 'id'>>) => {
      updateProfile({
        projects: profile.projects.map((p) => (p.id === id ? { ...p, ...patch } : p)),
      })
    },
    [profile.projects, updateProfile],
  )

  const removeProject = useCallback(
    (id: string) => {
      updateProfile({ projects: profile.projects.filter((p) => p.id !== id) })
    },
    [profile.projects, updateProfile],
  )

  const toggleGmail = useCallback(() => {
    if (profile.gmailConnected) {
      updateProfile({ gmailConnected: false, gmailEmail: null })
    } else {
      updateProfile({ gmailConnected: true, gmailEmail: 'you@gmail.com' })
    }
  }, [profile.gmailConnected, updateProfile])

  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key === 'jobpilot-profile') {
        setProfileState(loadProfile())
      }
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  const value = useMemo(
    () => ({
      profile,
      gate,
      setProfile,
      updateProfile,
      setCv,
      addSkill,
      removeSkill,
      addRole,
      removeRole,
      addProject,
      updateProject,
      removeProject,
      toggleGmail,
    }),
    [
      profile,
      gate,
      setProfile,
      updateProfile,
      setCv,
      addSkill,
      removeSkill,
      addRole,
      removeRole,
      addProject,
      updateProject,
      removeProject,
      toggleGmail,
    ],
  )

  return <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>
}

export function useProfile() {
  const ctx = useContext(ProfileContext)
  if (!ctx) throw new Error('useProfile must be used within ProfileProvider')
  return ctx
}

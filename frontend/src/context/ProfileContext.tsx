import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import {
  getProfile,
  updateProfile as apiUpdateProfile,
  uploadCv as apiUploadCv,
} from '../api/profile'
import { useAuth } from './AuthContext'
import { useProfileGate } from '../hooks/useProfileGate'
import { EMPTY_PROFILE, type Profile, type Project } from '../types/profile'

interface ProfileContextValue {
  profile: Profile
  loading: boolean
  error: string | null
  gate: ReturnType<typeof useProfileGate>
  refreshProfile: () => Promise<void>
  updateProfile: (patch: Partial<Profile>) => Promise<void>
  uploadCv: (file: File) => Promise<void>
  addRole: (role: string) => void
  removeRole: (role: string) => void
  addProject: (project: Omit<Project, 'id'>) => void
  updateProject: (id: string, patch: Partial<Omit<Project, 'id'>>) => void
  removeProject: (id: string) => void
}

const ProfileContext = createContext<ProfileContextValue | null>(null)

export function ProfileProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [profile, setProfile] = useState<Profile>(EMPTY_PROFILE)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const gate = useProfileGate(profile)

  const refreshProfile = useCallback(async () => {
    if (!user) {
      setProfile(EMPTY_PROFILE)
      setLoading(false)
      return
    }
    try {
      setError(null)
      const data = await getProfile()
      setProfile(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load profile')
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    void refreshProfile()
  }, [refreshProfile])

  // Poll while GitHub import / CV skills are preparing so UI unlocks when ready.
  useEffect(() => {
    const pending =
      profile.projectsIndexingStatus === 'pending' ||
      profile.skillsExtractionStatus === 'pending'
    if (!user || !pending) return
    const timer = window.setInterval(() => {
      void refreshProfile()
    }, 3000)
    return () => window.clearInterval(timer)
  }, [
    user,
    profile.projectsIndexingStatus,
    profile.skillsExtractionStatus,
    refreshProfile,
  ])

  const persistPatch = useCallback(async (patch: Partial<Profile>) => {
    const next = await apiUpdateProfile(patch)
    setProfile(next)
  }, [])

  const updateProfile = useCallback(
    async (patch: Partial<Profile>) => {
      await persistPatch(patch)
    },
    [persistPatch],
  )

  const uploadCv = useCallback(async (file: File) => {
    setProfile((p) => ({ ...p, skillsExtractionStatus: 'pending' }))
    const next = await apiUploadCv(file)
    setProfile(next)
  }, [])

  const addRole = useCallback(
    (role: string) => {
      const trimmed = role.trim()
      if (!trimmed || profile.targetRoles.includes(trimmed)) return
      void persistPatch({ targetRoles: [...profile.targetRoles, trimmed] })
    },
    [profile.targetRoles, persistPatch],
  )

  const removeRole = useCallback(
    (role: string) => {
      void persistPatch({
        targetRoles: profile.targetRoles.filter((r) => r !== role),
      })
    },
    [profile.targetRoles, persistPatch],
  )

  const addProject = useCallback(
    (project: Omit<Project, 'id'>) => {
      const entry: Project = { ...project, id: crypto.randomUUID(), source: 'manual' }
      void persistPatch({ projects: [...profile.projects, entry] })
    },
    [profile.projects, persistPatch],
  )

  const updateProject = useCallback(
    (id: string, patch: Partial<Omit<Project, 'id'>>) => {
      void persistPatch({
        projects: profile.projects.map((p) => (p.id === id ? { ...p, ...patch } : p)),
      })
    },
    [profile.projects, persistPatch],
  )

  const removeProject = useCallback(
    (id: string) => {
      void persistPatch({
        projects: profile.projects.filter((p) => p.id !== id),
      })
    },
    [profile.projects, persistPatch],
  )

  const value = useMemo(
    () => ({
      profile,
      loading,
      error,
      gate,
      refreshProfile,
      updateProfile,
      uploadCv,
      addRole,
      removeRole,
      addProject,
      updateProject,
      removeProject,
    }),
    [
      profile,
      loading,
      error,
      gate,
      refreshProfile,
      updateProfile,
      uploadCv,
      addRole,
      removeRole,
      addProject,
      updateProject,
      removeProject,
    ],
  )

  return <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>
}

export function useProfile() {
  const ctx = useContext(ProfileContext)
  if (!ctx) throw new Error('useProfile must be used within ProfileProvider')
  return ctx
}

import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from './components/auth/ProtectedRoute'
import { AppShell } from './components/shell/AppShell'
import { AuthProvider } from './context/AuthContext'
import { ProfileProvider } from './context/ProfileContext'
import { LoginPage } from './pages/LoginPage'
import { ProfilePage } from './pages/ProfilePage'
import { ApplicationsPage } from './pages/ApplicationsPage'
import { ProjectEvidencePage } from './pages/ProjectEvidencePage'
import { SearchPage } from './pages/SearchPage'
import { SearchHelperGuidePage } from './pages/SearchHelperGuidePage'
import { SettingsPage } from './pages/SettingsPage'
import { SkillsLibraryPage } from './pages/SkillsLibraryPage'
import { SignupPage } from './pages/SignupPage'
import { WelcomePage } from './pages/WelcomePage'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route element={<ProtectedRoute />}>
            <Route
              element={
                <ProfileProvider>
                  <AppShell />
                </ProfileProvider>
              }
            >
              <Route index element={<WelcomePage />} />
              <Route path="profile" element={<ProfilePage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="settings/search-helper-guide" element={<SearchHelperGuidePage />} />
              <Route path="settings/projects" element={<ProjectEvidencePage />} />
              <Route path="settings/skills" element={<SkillsLibraryPage />} />
              <Route path="search" element={<SearchPage />} />
              <Route path="applications" element={<ApplicationsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

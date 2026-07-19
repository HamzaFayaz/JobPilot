import { Outlet, useLocation } from 'react-router-dom'
import { AppTopbar } from './AppTopbar'
import { MobileNav } from './MobileNav'
import { Sidebar } from './Sidebar'

export function AppShell() {
  const { pathname } = useLocation()
  const wide = pathname.startsWith('/applications')

  return (
    <div className="min-h-screen overflow-x-hidden bg-background text-text-primary">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-sidebar focus:px-4 focus:py-2 focus:text-white focus:outline-none focus:ring-2 focus:ring-primary"
      >
        Skip to main content
      </a>
      <MobileNav />
      <div className="lg:flex">
        <div className="hidden lg:fixed lg:inset-y-0 lg:block lg:w-64">
          <Sidebar />
        </div>
        <main
          id="main-content"
          className="w-full px-4 py-6 sm:px-6 lg:ml-64 lg:px-8 lg:py-7 xl:px-10"
        >
          <div className={`mx-auto w-full ${wide ? 'max-w-[1440px]' : 'max-w-[1180px]'}`}>
            <AppTopbar />
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}

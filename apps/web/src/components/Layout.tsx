import { Outlet, Link, NavLink } from 'react-router-dom'
import { useAuth } from '../store/AuthContext'

const NAV_LINKS = [
  { to: '/dashboard', label: 'Overview' },
  { to: '/search', label: 'Search' },
  { to: '/hardware-products', label: 'Hardware Products' },
  { to: '/companies', label: 'Companies' },
  { to: '/datacenters', label: 'Datacenters' },
  { to: '/notes', label: 'Research Notes' },
  { to: '/sources', label: 'Sources' },
]

const ADMIN_LINKS = [
  { to: '/admin/users', label: 'User Management' },
]

export default function Layout() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  return (
    <div className="min-h-screen flex flex-col">
      {/* Skip-to-content for keyboard users */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:m-2 focus:rounded focus:bg-blue-600 focus:px-4 focus:py-2 focus:text-white"
      >
        Skip to content
      </a>

      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <Link to="/dashboard" className="text-lg font-semibold text-gray-900">
          AI Infra Research
        </Link>
        <nav aria-label="Header navigation" className="flex gap-4 text-sm text-gray-600">
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              isActive ? 'text-blue-600 font-medium' : 'hover:text-gray-900'
            }
          >
            Dashboard
          </NavLink>
        </nav>
      </header>

      <div className="flex flex-1">
        <aside className="w-56 border-r border-gray-200 bg-gray-50 p-4 shrink-0">
          <nav aria-label="Sidebar navigation" className="flex flex-col gap-1 text-sm">
            {NAV_LINKS.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `px-3 py-2 rounded-md ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`
                }
                aria-current={undefined}
              >
                {({ isActive }) => (
                  <span aria-current={isActive ? 'page' : undefined}>{label}</span>
                )}
              </NavLink>
            ))}

            {isAdmin && (
              <>
                <div
                  className="mt-4 mb-1 px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider"
                  aria-hidden="true"
                >
                  Admin
                </div>
                {ADMIN_LINKS.map(({ to, label }) => (
                  <NavLink
                    key={to}
                    to={to}
                    className={({ isActive }) =>
                      `px-3 py-2 rounded-md ${
                        isActive
                          ? 'bg-blue-50 text-blue-700 font-medium'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`
                    }
                  >
                    {({ isActive }) => (
                      <span aria-current={isActive ? 'page' : undefined}>{label}</span>
                    )}
                  </NavLink>
                ))}
              </>
            )}
          </nav>
        </aside>

        <main id="main-content" className="flex-1 p-6 bg-white" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}

import { Outlet, Link, NavLink } from 'react-router-dom'

const navLinks = [
  { to: '/dashboard', label: 'Overview' },
  { to: '/hardware-products', label: 'Hardware Products' },
  { to: '/companies', label: 'Companies' },
  { to: '/datacenters', label: 'Datacenters' },
  { to: '/notes', label: 'Research Notes' },
]

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <Link to="/dashboard" className="text-lg font-semibold text-gray-900">
          AI Infra Research
        </Link>
        <nav className="flex gap-4 text-sm text-gray-600">
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
          <nav className="flex flex-col gap-1 text-sm">
            {navLinks.map(({ to, label }) => (
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
                {label}
              </NavLink>
            ))}
          </nav>
        </aside>

        <main className="flex-1 p-6 bg-white">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

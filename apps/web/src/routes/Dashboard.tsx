import { useAuth } from '../store/AuthContext'

const ROLE_BADGE: Record<string, string> = {
  admin: 'bg-red-100 text-red-700',
  analyst: 'bg-blue-100 text-blue-700',
  viewer: 'bg-gray-100 text-gray-600',
}

export default function Dashboard() {
  const { user, logout } = useAuth()

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <button
          onClick={logout}
          className="text-sm text-gray-500 hover:text-gray-900 border border-gray-300 rounded-md px-3 py-1.5 hover:bg-gray-50 transition-colors"
        >
          Sign out
        </button>
      </div>

      {user && (
        <div className="inline-flex items-center gap-2 rounded-lg bg-gray-50 border border-gray-200 px-4 py-3 text-sm text-gray-700">
          <span>Logged in as</span>
          <span className="font-medium">{user.email}</span>
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-semibold ${ROLE_BADGE[user.role] ?? 'bg-gray-100 text-gray-600'}`}
          >
            {user.role}
          </span>
        </div>
      )}

      <p className="mt-6 text-gray-400 text-sm">
        Research dashboard content goes here. (Slice 2)
      </p>
    </div>
  )
}

import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../store/AuthContext'

export default function ProtectedRoute() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500 text-sm">
        Loading...
      </div>
    )
  }

  return user ? <Outlet /> : <Navigate to="/login" replace />
}

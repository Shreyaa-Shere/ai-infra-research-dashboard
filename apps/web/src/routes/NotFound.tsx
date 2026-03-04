import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
      <h1 className="text-6xl font-bold text-gray-300 mb-4">404</h1>
      <p className="text-gray-600 mb-6">Page not found.</p>
      <Link to="/dashboard" className="text-blue-600 hover:underline text-sm">
        Go to Dashboard
      </Link>
    </div>
  )
}

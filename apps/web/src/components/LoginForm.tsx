import { useState } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { loginSchema, type LoginInput } from '../lib/schemas'
import { useAuth } from '../store/AuthContext'

type FieldErrors = Partial<Record<keyof LoginInput, string>>

export default function LoginForm() {
  const { login, isLoading, error } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const successMessage = (location.state as { message?: string } | null)?.message ?? null
  const [data, setData] = useState<Partial<LoginInput>>({ email: '', password: '' })
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    const result = loginSchema.safeParse(data)
    if (!result.success) {
      const errs: FieldErrors = {}
      for (const issue of result.error.issues) {
        errs[issue.path[0] as keyof LoginInput] = issue.message
      }
      setFieldErrors(errs)
      return
    }

    setFieldErrors({})
    await login(result.data.email, result.data.password)
    // AuthContext sets user on success; navigate after re-render
    navigate('/dashboard', { replace: true })
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white shadow rounded-lg p-8 flex flex-col gap-5"
    >
      {successMessage && (
        <div className="rounded-md bg-green-50 border border-green-200 px-4 py-3 text-sm text-green-700">
          {successMessage}
        </div>
      )}

      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
          Email
        </label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          value={data.email ?? ''}
          onChange={(e) => setData((d) => ({ ...d, email: e.target.value }))}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {fieldErrors.email && (
          <p className="mt-1 text-xs text-red-600">{fieldErrors.email}</p>
        )}
      </div>

      <div>
        <div className="flex items-center justify-between mb-1">
          <label htmlFor="password" className="block text-sm font-medium text-gray-700">
            Password
          </label>
          <Link to="/forgot-password" className="text-xs text-blue-600 hover:underline">
            Forgot password?
          </Link>
        </div>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          value={data.password ?? ''}
          onChange={(e) => setData((d) => ({ ...d, password: e.target.value }))}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {fieldErrors.password && (
          <p className="mt-1 text-xs text-red-600">{fieldErrors.password}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full bg-blue-600 text-white py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-60"
      >
        {isLoading ? 'Signing in…' : 'Sign In'}
      </button>
    </form>
  )
}

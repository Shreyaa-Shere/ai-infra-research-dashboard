import { useState } from 'react'
import { loginSchema, type LoginInput } from '../lib/schemas'

type FieldErrors = Partial<Record<keyof LoginInput, string>>

export default function LoginForm() {
  const [data, setData] = useState<Partial<LoginInput>>({ email: '', password: '' })
  const [errors, setErrors] = useState<FieldErrors>({})

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const result = loginSchema.safeParse(data)

    if (!result.success) {
      const fieldErrors: FieldErrors = {}
      for (const issue of result.error.issues) {
        const field = issue.path[0] as keyof LoginInput
        fieldErrors[field] = issue.message
      }
      setErrors(fieldErrors)
      return
    }

    setErrors({})
    // Auth integration goes here (Slice 1).
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white shadow rounded-lg p-8 flex flex-col gap-5"
    >
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
        <input
          type="email"
          value={data.email ?? ''}
          onChange={(e) => setData((d) => ({ ...d, email: e.target.value }))}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
        <input
          type="password"
          value={data.password ?? ''}
          onChange={(e) => setData((d) => ({ ...d, password: e.target.value }))}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {errors.password && (
          <p className="mt-1 text-xs text-red-600">{errors.password}</p>
        )}
      </div>

      <button
        type="submit"
        className="w-full bg-blue-600 text-white py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
      >
        Sign In
      </button>
    </form>
  )
}

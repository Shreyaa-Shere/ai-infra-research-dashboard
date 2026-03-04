const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(
  path: string,
  init: RequestInit & { token?: string } = {}
): Promise<T> {
  const { token, headers: extraHeaders, ...rest } = init
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(extraHeaders as Record<string, string>),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE}${path}`, { ...rest, headers })

  if (res.status === 204) return undefined as T

  const data = await res.json()
  if (!res.ok) {
    const err = data?.error ?? {}
    throw new ApiError(res.status, err.code ?? 'UNKNOWN', err.message ?? 'Request failed')
  }
  return data as T
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface User {
  id: string
  email: string
  role: 'admin' | 'analyst' | 'viewer'
  is_active: boolean
  created_at: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface RefreshResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

// ── Auth calls ────────────────────────────────────────────────────────────────

export const authApi = {
  login: (email: string, password: string) =>
    request<LoginResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  refresh: (refreshToken: string) =>
    request<RefreshResponse>('/api/v1/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),

  logout: (accessToken: string, refreshToken: string) =>
    request<void>('/api/v1/auth/logout', {
      method: 'POST',
      token: accessToken,
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),

  me: (accessToken: string) =>
    request<User>('/api/v1/me', { token: accessToken }),
}

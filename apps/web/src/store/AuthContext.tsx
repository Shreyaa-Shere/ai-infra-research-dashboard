/**
 * Auth store using React Context + useReducer.
 *
 * Token storage strategy (local dev):
 *   - access_token  → in-memory (React state) — lost on page refresh, re-fetched via refresh flow
 *   - refresh_token → localStorage under key "rft"
 *
 * Production note: move refresh_token to an httpOnly cookie set by the API
 * (/api/v1/auth/refresh reads it server-side) to eliminate XSS exposure.
 */

import {
  createContext,
  useContext,
  useReducer,
  useCallback,
  useEffect,
  type ReactNode,
} from 'react'
import { authApi, type User } from '../lib/api'

const REFRESH_KEY = 'rft'

interface AuthState {
  user: User | null
  accessToken: string | null
  isLoading: boolean
  error: string | null
}

type AuthAction =
  | { type: 'SET_LOADING' }
  | { type: 'SET_ERROR'; payload: string }
  | {
      type: 'LOGIN_SUCCESS'
      payload: { user: User; accessToken: string; refreshToken: string }
    }
  | { type: 'REFRESH_SUCCESS'; payload: { accessToken: string; refreshToken: string } }
  | { type: 'LOGOUT' }

// Start loading if there's a stored refresh token — prevents ProtectedRoute from
// redirecting to /login on first render before the silent-refresh effect runs.
const _hasStoredToken =
  typeof localStorage !== 'undefined' && !!localStorage.getItem('rft')

const initialState: AuthState = {
  user: null,
  accessToken: null,
  isLoading: _hasStoredToken,
  error: null,
}

function reducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: true, error: null }
    case 'SET_ERROR':
      return { ...state, isLoading: false, error: action.payload }
    case 'LOGIN_SUCCESS':
      localStorage.setItem(REFRESH_KEY, action.payload.refreshToken)
      return {
        user: action.payload.user,
        accessToken: action.payload.accessToken,
        isLoading: false,
        error: null,
      }
    case 'REFRESH_SUCCESS':
      localStorage.setItem(REFRESH_KEY, action.payload.refreshToken)
      return { ...state, accessToken: action.payload.accessToken, isLoading: false }
    case 'LOGOUT':
      localStorage.removeItem(REFRESH_KEY)
      return { ...initialState }
    default:
      return state
  }
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refresh: () => Promise<boolean>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState)

  // On mount: attempt silent refresh if a stored token exists
  useEffect(() => {
    const stored = localStorage.getItem(REFRESH_KEY)
    if (stored) {
      dispatch({ type: 'SET_LOADING' })
      authApi
        .refresh(stored)
        .then(async (data) => {
          const user = await authApi.me(data.access_token)
          dispatch({
            type: 'LOGIN_SUCCESS',
            payload: { user, accessToken: data.access_token, refreshToken: data.refresh_token },
          })
        })
        .catch(() => {
          localStorage.removeItem(REFRESH_KEY)
          dispatch({ type: 'LOGOUT' })
        })
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    dispatch({ type: 'SET_LOADING' })
    try {
      const data = await authApi.login(email, password)
      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: {
          user: data.user,
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
        },
      })
    } catch (err) {
      dispatch({ type: 'SET_ERROR', payload: (err as Error).message })
    }
  }, [])

  const logout = useCallback(async () => {
    const storedRefresh = localStorage.getItem(REFRESH_KEY)
    if (state.accessToken && storedRefresh) {
      await authApi.logout(state.accessToken, storedRefresh).catch(() => null)
    }
    dispatch({ type: 'LOGOUT' })
  }, [state.accessToken])

  const refresh = useCallback(async (): Promise<boolean> => {
    const stored = localStorage.getItem(REFRESH_KEY)
    if (!stored) return false
    try {
      const data = await authApi.refresh(stored)
      dispatch({
        type: 'REFRESH_SUCCESS',
        payload: { accessToken: data.access_token, refreshToken: data.refresh_token },
      })
      return true
    } catch {
      dispatch({ type: 'LOGOUT' })
      return false
    }
  }, [])

  return (
    <AuthContext.Provider value={{ ...state, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}

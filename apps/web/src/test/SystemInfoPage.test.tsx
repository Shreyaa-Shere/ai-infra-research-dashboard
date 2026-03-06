import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import * as AuthModule from '../store/AuthContext'
import * as ApiModule from '../lib/api'

vi.mock('../lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/api')>()
  return { ...actual, systemApi: { info: vi.fn() } }
})

import SystemInfoPage from '../routes/admin/SystemInfoPage'
import { systemApi } from '../lib/api'

const MOCK_HEALTHY: import('../lib/entities').SystemInfo = {
  version: '1.0.0',
  git_sha: 'abc1234def5678',
  environment: 'development',
  uptime_seconds: 3661,
  db_connected: true,
  redis_connected: true,
}

const MOCK_DEGRADED: import('../lib/entities').SystemInfo = {
  ...MOCK_HEALTHY,
  redis_connected: false,
}

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) => (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  )
}

describe('SystemInfoPage', () => {
  beforeEach(() => {
    vi.spyOn(AuthModule, 'useAuth').mockReturnValue({
      user: { id: 'u1', email: 'admin@example.com', role: 'admin', is_active: true, created_at: '' },
      accessToken: 'admin-token',
      isLoading: false,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
    })
    vi.clearAllMocks()
  })

  it('renders heading and auto-refresh description', () => {
    vi.mocked(systemApi.info).mockResolvedValue(MOCK_HEALTHY)
    render(<SystemInfoPage />, { wrapper: makeWrapper() })
    expect(screen.getByText('System Info')).toBeInTheDocument()
    expect(screen.getByText(/auto-refreshes every 30/i)).toBeInTheDocument()
  })

  it('shows version, environment and uptime when data loads', async () => {
    vi.mocked(systemApi.info).mockResolvedValue(MOCK_HEALTHY)
    render(<SystemInfoPage />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByText('1.0.0')).toBeInTheDocument()
    })
    expect(screen.getByText('development')).toBeInTheDocument()
    // Uptime: 3661s = 1h 1m 1s
    expect(screen.getByText(/1h 1m 1s/)).toBeInTheDocument()
  })

  it('shows git SHA in monospace code element', async () => {
    vi.mocked(systemApi.info).mockResolvedValue(MOCK_HEALTHY)
    render(<SystemInfoPage />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByText('abc1234def5678')).toBeInTheDocument()
    })
  })

  it('shows "Connected" for both services when healthy', async () => {
    vi.mocked(systemApi.info).mockResolvedValue(MOCK_HEALTHY)
    render(<SystemInfoPage />, { wrapper: makeWrapper() })

    await waitFor(() => {
      const connected = screen.getAllByText('Connected')
      expect(connected.length).toBe(2)
    })
    expect(screen.getByText('All systems operational')).toBeInTheDocument()
  })

  it('shows "Unreachable" and "Degraded" when Redis is down', async () => {
    vi.mocked(systemApi.info).mockResolvedValue(MOCK_DEGRADED)
    render(<SystemInfoPage />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByText('Unreachable')).toBeInTheDocument()
    })
    expect(screen.getByText('Degraded')).toBeInTheDocument()
  })

  it('shows error state when fetch fails', async () => {
    vi.mocked(systemApi.info).mockRejectedValue(new Error('Network error'))
    render(<SystemInfoPage />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText('Failed to load system info.')).toBeInTheDocument()
    })
  })
})

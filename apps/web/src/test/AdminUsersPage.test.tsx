import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import * as AuthModule from '../store/AuthContext'

// Mock the api module at module level so all imports share the mock
vi.mock('../lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/api')>()
  return {
    ...actual,
    usersApi: {
      list: vi.fn(),
      invite: vi.fn(),
      acceptInvite: vi.fn(),
      update: vi.fn(),
    },
  }
})

import UsersPage from '../routes/admin/UsersPage'
import { usersApi } from '../lib/api'

const MOCK_USERS = [
  {
    id: 'user-1',
    email: 'admin@example.com',
    role: 'admin',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'user-2',
    email: 'analyst@example.com',
    role: 'analyst',
    is_active: true,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
]

const MOCK_PAGINATED = {
  items: MOCK_USERS,
  total: 2,
  limit: 20,
  offset: 0,
}

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) => (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  )
}

function mockAdmin() {
  vi.spyOn(AuthModule, 'useAuth').mockReturnValue({
    user: { id: 'user-1', email: 'admin@example.com', role: 'admin', is_active: true, created_at: '' },
    accessToken: 'admin-token',
    isLoading: false,
    error: null,
    login: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
  })
}

describe('UsersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders users table after loading', async () => {
    mockAdmin()
    vi.mocked(usersApi.list).mockResolvedValue(MOCK_PAGINATED)

    render(<UsersPage />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByTestId('users-table')).toBeInTheDocument()
    })
    expect(screen.getByText('admin@example.com')).toBeInTheDocument()
    expect(screen.getByText('analyst@example.com')).toBeInTheDocument()
  })

  it('shows invite modal when invite button clicked', async () => {
    mockAdmin()
    vi.mocked(usersApi.list).mockResolvedValue(MOCK_PAGINATED)

    render(<UsersPage />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByTestId('invite-user-button'))
    fireEvent.click(screen.getByTestId('invite-user-button'))

    expect(screen.getByTestId('invite-modal')).toBeInTheDocument()
    expect(screen.getByTestId('invite-email-input')).toBeInTheDocument()
  })

  it('shows error state when users fetch fails', async () => {
    mockAdmin()
    vi.mocked(usersApi.list).mockRejectedValue(new Error('Network error'))

    render(<UsersPage />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText('Failed to load users.')).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
  })

  it('shows invite URL after successful invite', async () => {
    mockAdmin()
    vi.mocked(usersApi.list).mockResolvedValue(MOCK_PAGINATED)
    vi.mocked(usersApi.invite).mockResolvedValue({
      id: 'invite-1',
      email: 'new@example.com',
      role: 'analyst',
      invite_url: 'http://localhost:5173/accept-invite?token=abc123',
      expires_at: '2024-02-01T00:00:00Z',
      created_at: '2024-01-01T00:00:00Z',
    })

    render(<UsersPage />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByTestId('invite-user-button'))
    fireEvent.click(screen.getByTestId('invite-user-button'))

    fireEvent.change(screen.getByTestId('invite-email-input'), {
      target: { value: 'new@example.com' },
    })
    fireEvent.submit(screen.getByTestId('invite-email-input').closest('form')!)

    await waitFor(() => {
      expect(screen.getByText(/accept-invite\?token=/)).toBeInTheDocument()
    })
  })
})

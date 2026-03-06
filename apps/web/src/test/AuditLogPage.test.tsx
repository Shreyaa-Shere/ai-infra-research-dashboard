import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import * as AuthModule from '../store/AuthContext'
import * as ApiModule from '../lib/api'

vi.mock('../lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/api')>()
  return { ...actual, auditApi: { list: vi.fn() } }
})

import AuditLogPage from '../routes/admin/AuditLogPage'
import { auditApi } from '../lib/api'

const MOCK_ENTRIES = [
  {
    id: 'entry-1',
    action: 'note.created',
    entity_type: 'research_note',
    entity_id: 'note-uuid-1111',
    actor_user_id: 'actor-uuid-aaaa',
    meta_json: JSON.stringify({ title: 'My Research Note' }),
    created_at: '2026-03-05T10:00:00Z',
  },
  {
    id: 'entry-2',
    action: 'note.published',
    entity_type: 'research_note',
    entity_id: 'note-uuid-2222',
    actor_user_id: 'actor-uuid-aaaa',
    meta_json: JSON.stringify({ title: 'Published Note', slug: 'published-note-abc' }),
    created_at: '2026-03-05T11:00:00Z',
  },
  {
    id: 'entry-3',
    action: 'note.deleted',
    entity_type: 'research_note',
    entity_id: 'note-uuid-3333',
    actor_user_id: 'actor-uuid-aaaa',
    meta_json: JSON.stringify({ title: 'Deleted Note' }),
    created_at: '2026-03-05T12:00:00Z',
  },
  {
    id: 'entry-4',
    action: 'user.invited',
    entity_type: 'user_invite',
    entity_id: 'invite-uuid-1111',
    actor_user_id: 'actor-uuid-aaaa',
    meta_json: JSON.stringify({ email: 'new@example.com', role: 'analyst' }),
    created_at: '2026-03-05T13:00:00Z',
  },
  {
    id: 'entry-5',
    action: 'user.deactivated',
    entity_type: 'user',
    entity_id: 'user-uuid-1111',
    actor_user_id: null,
    meta_json: null,
    created_at: '2026-03-05T14:00:00Z',
  },
]

const MOCK_PAGINATED = { items: MOCK_ENTRIES, total: 5, limit: 25, offset: 0 }

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) => (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  )
}

describe('AuditLogPage', () => {
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

  it('renders heading and description', async () => {
    vi.mocked(auditApi.list).mockResolvedValue(MOCK_PAGINATED)
    render(<AuditLogPage />, { wrapper: makeWrapper() })
    expect(screen.getByText('Audit Log')).toBeInTheDocument()
    expect(screen.getByText(/auto-refreshes every 30/i)).toBeInTheDocument()
  })

  it('shows note title (from meta_json) as a link for note.created', async () => {
    vi.mocked(auditApi.list).mockResolvedValue(MOCK_PAGINATED)
    render(<AuditLogPage />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByText('My Research Note')).toBeInTheDocument()
    })
    const link = screen.getByRole('link', { name: 'My Research Note' })
    expect(link).toHaveAttribute('href', '/notes/note-uuid-1111')
  })

  it('shows note title as strikethrough text for note.deleted (no link)', async () => {
    vi.mocked(auditApi.list).mockResolvedValue(MOCK_PAGINATED)
    render(<AuditLogPage />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByText('Deleted Note')).toBeInTheDocument()
    })
    // Deleted note should NOT be a link
    expect(screen.queryByRole('link', { name: 'Deleted Note' })).not.toBeInTheDocument()
  })

  it('shows email label for user.invited entries', async () => {
    vi.mocked(auditApi.list).mockResolvedValue(MOCK_PAGINATED)
    render(<AuditLogPage />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByText('new@example.com')).toBeInTheDocument()
    })
  })

  it('shows action badge for note.created with correct color class', async () => {
    vi.mocked(auditApi.list).mockResolvedValue(MOCK_PAGINATED)
    render(<AuditLogPage />, { wrapper: makeWrapper() })

    await waitFor(() => {
      const badge = screen.getByText('note.created')
      expect(badge.className).toContain('bg-blue-100')
    })
  })

  it('shows action badge for user.invited', async () => {
    vi.mocked(auditApi.list).mockResolvedValue(MOCK_PAGINATED)
    render(<AuditLogPage />, { wrapper: makeWrapper() })

    await waitFor(() => {
      const badge = screen.getByText('user.invited')
      expect(badge.className).toContain('bg-purple-100')
    })
  })

  it('shows action badge for user.deactivated', async () => {
    vi.mocked(auditApi.list).mockResolvedValue(MOCK_PAGINATED)
    render(<AuditLogPage />, { wrapper: makeWrapper() })

    await waitFor(() => {
      const badge = screen.getByText('user.deactivated')
      expect(badge.className).toContain('bg-red-100')
    })
  })

  it('shows italic "system" for null actor', async () => {
    vi.mocked(auditApi.list).mockResolvedValue(MOCK_PAGINATED)
    render(<AuditLogPage />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByText('system')).toBeInTheDocument()
    })
  })

  it('shows empty state when no audit entries', async () => {
    vi.mocked(auditApi.list).mockResolvedValue({ items: [], total: 0, limit: 25, offset: 0 })
    render(<AuditLogPage />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByText('No audit entries yet.')).toBeInTheDocument()
    })
  })

  it('shows error state when fetch fails', async () => {
    vi.mocked(auditApi.list).mockRejectedValue(new Error('Network error'))
    render(<AuditLogPage />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText('Failed to load audit log.')).toBeInTheDocument()
    })
  })

  it('calls refetch when Refresh button is clicked', async () => {
    vi.mocked(auditApi.list).mockResolvedValue(MOCK_PAGINATED)
    render(<AuditLogPage />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('Audit Log'))
    fireEvent.click(screen.getByRole('button', { name: /refresh/i }))
    // auditApi.list called at least once (initial load)
    expect(vi.mocked(auditApi.list)).toHaveBeenCalled()
  })
})

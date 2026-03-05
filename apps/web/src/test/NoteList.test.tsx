import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import * as AuthModule from '../store/AuthContext'
import NoteList from '../routes/notes/NoteList'

const MOCK_NOTE = {
  id: 'note-uuid-1',
  title: 'H100 Supply Chain Analysis',
  body_markdown: '# H100\n\nGreat GPU.',
  status: 'published',
  slug: 'h100-supply-chain-analysis-abc12345',
  tags: ['gpu', 'supply-chain'],
  author: { id: 'user-uuid-1', email: 'analyst@example.com' },
  linked_entities: [],
  created_at: '2026-03-01T00:00:00Z',
  updated_at: '2026-03-01T00:00:00Z',
  published_at: '2026-03-02T00:00:00Z',
}

const MOCK_RESPONSE = {
  items: [MOCK_NOTE],
  total: 1,
  limit: 20,
  offset: 0,
}

const EMPTY_RESPONSE = { items: [], total: 0, limit: 20, offset: 0 }

function makeWrapper(mockJson: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockJson),
      })
    )
  )

  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={qc}>
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    )
  }
}

describe('NoteList', () => {
  beforeEach(() => {
    vi.spyOn(AuthModule, 'useAuth').mockReturnValue({
      user: { id: 'u1', email: 'admin@example.com', role: 'admin', is_active: true, created_at: '' },
      accessToken: 'fake-token',
      isLoading: false,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
    })
  })

  it('renders table with note title and status', async () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<NoteList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('H100 Supply Chain Analysis')).toBeInTheDocument()
    })
    expect(screen.getByText('published')).toBeInTheDocument()
    expect(screen.getByText('Title')).toBeInTheDocument()
    // 'Status' appears as both the filter label and the column header
    expect(screen.getAllByText('Status').length).toBeGreaterThanOrEqual(1)
  })

  it('shows "New Note" button for admin', async () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<NoteList />, { wrapper: Wrapper })
    expect(screen.getByText('+ New Note')).toBeInTheDocument()
  })

  it('shows empty state when no notes', async () => {
    const Wrapper = makeWrapper(EMPTY_RESPONSE)
    render(<NoteList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('No research notes found.')).toBeInTheDocument()
    })
  })

  it('renders tag chips', async () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<NoteList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('gpu')).toBeInTheDocument()
      expect(screen.getByText('supply-chain')).toBeInTheDocument()
    })
  })

  it('shows error state when fetch fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 500,
          json: () => Promise.resolve({ error: { code: 'SERVER_ERROR', message: 'Server error' } }),
        })
      )
    )
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const Wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={qc}>
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    )
    render(<NoteList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText('Failed to load research notes.')).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
  })
})

import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import * as AuthModule from '../store/AuthContext'
import SearchPage from '../routes/search/SearchPage'

const MOCK_NOTE_RESULT = {
  id: 'note-uuid-1',
  type: 'note',
  title: 'H100 Training Cluster Analysis',
  snippet: 'Deep dive into <mark>H100</mark> GPU clusters.',
  score: 0.8,
  status: 'published',
  tags: ['gpu'],
  author_id: 'author-1',
  slug: 'h100-analysis',
  published_at: '2024-01-15T00:00:00Z',
  created_at: '2024-01-10T00:00:00Z',
  updated_at: '2024-01-15T00:00:00Z',
}

const MOCK_SOURCE_RESULT = {
  id: 'src-uuid-1',
  type: 'source',
  title: 'NVIDIA H100 Deployment Article',
  snippet: '<mark>H100</mark> GPU deployed in Azure.',
  score: 0.7,
  url: 'https://example.com/h100',
  source_name: 'AI Hardware Weekly',
  source_type: 'file',
  status: 'ingested',
  published_at: '2024-01-20T00:00:00Z',
  created_at: '2024-01-20T00:00:00Z',
}

const MOCK_RESPONSE = {
  items: [MOCK_NOTE_RESULT, MOCK_SOURCE_RESULT],
  total: 2,
  limit: 20,
  offset: 0,
  query: 'H100',
}

const EMPTY_RESPONSE = {
  items: [],
  total: 0,
  limit: 20,
  offset: 0,
  query: 'xyzzy',
}

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
        <MemoryRouter initialEntries={['/search?q=H100']}>{children}</MemoryRouter>
      </QueryClientProvider>
    )
  }
}

describe('SearchPage', () => {
  beforeEach(() => {
    vi.spyOn(AuthModule, 'useAuth').mockReturnValue({
      user: {
        id: 'u1',
        email: 'analyst@example.com',
        role: 'analyst',
        is_active: true,
        created_at: '',
      },
      accessToken: 'fake-token',
      isLoading: false,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
    })
  })

  it('renders search input', () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<SearchPage />, { wrapper: Wrapper })
    expect(screen.getByPlaceholderText('Search notes and sources…')).toBeInTheDocument()
  })

  it('renders note result', async () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<SearchPage />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('H100 Training Cluster Analysis')).toBeInTheDocument()
    })
    expect(screen.getByText('Note')).toBeInTheDocument()
  })

  it('renders source result', async () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<SearchPage />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('NVIDIA H100 Deployment Article')).toBeInTheDocument()
    })
    expect(screen.getByText('Source')).toBeInTheDocument()
  })

  it('shows empty state when no results', async () => {
    const Wrapper = makeWrapper(EMPTY_RESPONSE)
    render(<SearchPage />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText(/No results found/)).toBeInTheDocument()
    })
  })

  it('renders tabs for All, Notes, Sources', () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<SearchPage />, { wrapper: Wrapper })

    expect(screen.getByText('All')).toBeInTheDocument()
    expect(screen.getByText('Notes')).toBeInTheDocument()
    expect(screen.getByText('Sources')).toBeInTheDocument()
  })

  it('shows filter panel when toggle clicked', () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<SearchPage />, { wrapper: Wrapper })

    fireEvent.click(screen.getByText(/Filters/))
    expect(screen.getByText('Apply Filters')).toBeInTheDocument()
  })

  it('shows Note Status filter for analyst', () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<SearchPage />, { wrapper: Wrapper })

    fireEvent.click(screen.getByText(/Filters/))
    expect(screen.getByText('Note Status')).toBeInTheDocument()
  })

  it('does not show draft/review status options for viewer', () => {
    vi.spyOn(AuthModule, 'useAuth').mockReturnValue({
      user: {
        id: 'u2',
        email: 'viewer@example.com',
        role: 'viewer',
        is_active: true,
        created_at: '',
      },
      accessToken: 'fake-token',
      isLoading: false,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
    })

    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<SearchPage />, { wrapper: Wrapper })

    fireEvent.click(screen.getByText(/Filters/))
    // Viewer only gets the 'published' option in the status dropdown
    expect(screen.queryByRole('option', { name: 'draft' })).not.toBeInTheDocument()
    expect(screen.queryByRole('option', { name: 'review' })).not.toBeInTheDocument()
  })

  it('shows total count in active tab', async () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<SearchPage />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('(2)')).toBeInTheDocument()
    })
  })
})

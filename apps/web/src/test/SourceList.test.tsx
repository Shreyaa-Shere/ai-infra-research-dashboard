import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import * as AuthModule from '../store/AuthContext'
import SourceList from '../routes/sources/SourceList'

const MOCK_SOURCE = {
  id: 'src-uuid-1',
  title: 'NVIDIA H100 Shipments Surge in Q3 2024',
  url: 'https://example.com/nvidia-h100-q3-2024',
  source_name: 'AI Hardware Weekly',
  source_type: 'file',
  published_at: '2024-09-15T10:00:00Z',
  status: 'ingested',
  entity_count: 3,
  created_at: '2026-03-01T00:00:00Z',
}

const MOCK_RESPONSE = {
  items: [MOCK_SOURCE],
  total: 1,
  limit: 20,
  offset: 0,
}

const MOCK_RUNS_RESPONSE = {
  items: [],
  total: 0,
  limit: 5,
  offset: 0,
}

const EMPTY_RESPONSE = { items: [], total: 0, limit: 20, offset: 0 }

function makeWrapper(mockSourcesJson: unknown, mockRunsJson: unknown = MOCK_RUNS_RESPONSE) {
  let callCount = 0
  vi.stubGlobal(
    'fetch',
    vi.fn(() => {
      callCount++
      const json = callCount === 1 ? mockSourcesJson : mockRunsJson
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(json),
      })
    })
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

describe('SourceList', () => {
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

  it('renders table with source title', async () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<SourceList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('NVIDIA H100 Shipments Surge in Q3 2024')).toBeInTheDocument()
    })
    expect(screen.getByText('AI Hardware Weekly')).toBeInTheDocument()
  })

  it('renders status badge', async () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<SourceList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('ingested')).toBeInTheDocument()
    })
  })

  it('shows "Run Ingestion" button for analyst', () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<SourceList />, { wrapper: Wrapper })
    expect(screen.getByText('+ Run Ingestion')).toBeInTheDocument()
  })

  it('does not show "Run Ingestion" button for viewer', () => {
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
    render(<SourceList />, { wrapper: Wrapper })
    expect(screen.queryByText('+ Run Ingestion')).not.toBeInTheDocument()
  })

  it('shows empty state when no sources', async () => {
    const Wrapper = makeWrapper(EMPTY_RESPONSE)
    render(<SourceList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(
        screen.getByText('No source documents found. Run ingestion to populate sources.')
      ).toBeInTheDocument()
    })
  })

  it('renders entity count', async () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<SourceList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument()
    })
  })

  it('renders source type badge', async () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<SourceList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('file')).toBeInTheDocument()
    })
  })
})

import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import * as AuthModule from '../store/AuthContext'
import CompanyList from '../routes/companies/CompanyList'

const MOCK_RESPONSE = {
  items: [
    {
      id: 'co-1',
      name: 'NVIDIA',
      type: 'vendor',
      region: 'US',
      website: 'https://nvidia.com',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'co-2',
      name: 'TSMC',
      type: 'fab',
      region: 'TW',
      website: null,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
  ],
  total: 2,
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
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={qc}>
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    )
  }
}

describe('CompanyList', () => {
  beforeEach(() => {
    vi.spyOn(AuthModule, 'useAuth').mockReturnValue({
      user: null,
      accessToken: 'fake-token',
      isLoading: false,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
    })
  })

  it('renders table with company names', async () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<CompanyList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('NVIDIA')).toBeInTheDocument()
      expect(screen.getByText('TSMC')).toBeInTheDocument()
    })
    expect(screen.getByText('Name')).toBeInTheDocument()
  })

  it('shows type badge', async () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<CompanyList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('vendor')).toBeInTheDocument()
      expect(screen.getByText('fab')).toBeInTheDocument()
    })
  })

  it('shows empty state when no companies', async () => {
    const Wrapper = makeWrapper(EMPTY_RESPONSE)
    render(<CompanyList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('No companies found.')).toBeInTheDocument()
    })
  })

  it('shows error state when fetch fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 500,
          json: () => Promise.resolve({ error: { code: 'SERVER_ERROR', message: 'fail' } }),
        })
      )
    )
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const Wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={qc}>
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    )
    render(<CompanyList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText('Failed to load companies.')).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
  })
})

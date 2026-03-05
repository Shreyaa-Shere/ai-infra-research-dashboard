import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import * as AuthModule from '../store/AuthContext'
import DatacenterList from '../routes/datacenters/DatacenterList'

const MOCK_RESPONSE = {
  items: [
    {
      id: 'dc-1',
      name: 'US West GPU Cluster',
      region: 'us-west-2',
      status: 'active',
      power_mw: 320,
      owner_company: { id: 'co-1', name: 'Amazon' },
      notes: null,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'dc-2',
      name: 'EU AI Datacenter',
      region: 'eu-west-1',
      status: 'planned',
      power_mw: 150,
      owner_company: null,
      notes: null,
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

describe('DatacenterList', () => {
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

  it('renders table with datacenter names', async () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<DatacenterList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('US West GPU Cluster')).toBeInTheDocument()
      expect(screen.getByText('EU AI Datacenter')).toBeInTheDocument()
    })
    expect(screen.getByText('Name')).toBeInTheDocument()
  })

  it('shows status badge', async () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<DatacenterList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('active')).toBeInTheDocument()
      expect(screen.getByText('planned')).toBeInTheDocument()
    })
  })

  it('shows owner company name', async () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<DatacenterList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('Amazon')).toBeInTheDocument()
    })
  })

  it('shows empty state when no datacenters', async () => {
    const Wrapper = makeWrapper(EMPTY_RESPONSE)
    render(<DatacenterList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('No datacenter sites found.')).toBeInTheDocument()
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
    render(<DatacenterList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText('Failed to load datacenter sites.')).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
  })
})

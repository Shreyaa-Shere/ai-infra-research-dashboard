import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import * as AuthModule from '../store/AuthContext'
import DatacenterList from '../routes/datacenters/DatacenterList'

const MOCK_DATACENTERS = [
  {
    id: 'dc-1',
    name: 'US West Prime',
    region: 'us-west-2',
    status: 'active',
    power_mw: 150,
    owner_company: { id: 'co-1', name: 'Acme Cloud' },
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'dc-2',
    name: 'EU Frankfurt',
    region: 'eu-central-1',
    status: 'planned',
    power_mw: null,
    owner_company: null,
    created_at: '2026-01-02T00:00:00Z',
    updated_at: '2026-01-02T00:00:00Z',
  },
]

const MOCK_RESPONSE = { items: MOCK_DATACENTERS, total: 2, limit: 20, offset: 0 }
const EMPTY_RESPONSE = { items: [], total: 0, limit: 20, offset: 0 }

function mockFetch(json: unknown, ok = true) {
  vi.stubGlobal(
    'fetch',
    vi.fn(() =>
      Promise.resolve({
        ok,
        status: ok ? 200 : 500,
        json: () => Promise.resolve(ok ? json : { error: { code: 'SERVER_ERROR', message: 'fail' } }),
      })
    )
  )
}

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

function mockAuth(role: 'admin' | 'analyst' | 'viewer') {
  vi.spyOn(AuthModule, 'useAuth').mockReturnValue({
    user: { id: 'u1', email: `${role}@example.com`, role, is_active: true, created_at: '' },
    accessToken: 'token',
    isLoading: false,
    error: null,
    login: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
  })
}

describe('DatacenterList', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('renders datacenter names and regions', async () => {
    mockAuth('viewer')
    mockFetch(MOCK_RESPONSE)
    render(<DatacenterList />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByText('US West Prime')).toBeInTheDocument()
      expect(screen.getByText('EU Frankfurt')).toBeInTheDocument()
    })
    expect(screen.getByText('us-west-2')).toBeInTheDocument()
    expect(screen.getByText('eu-central-1')).toBeInTheDocument()
  })

  it('renders owner company name', async () => {
    mockAuth('viewer')
    mockFetch(MOCK_RESPONSE)
    render(<DatacenterList />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('US West Prime'))
    expect(screen.getByText('Acme Cloud')).toBeInTheDocument()
  })

  it('renders power capacity with MW suffix', async () => {
    mockAuth('viewer')
    mockFetch(MOCK_RESPONSE)
    render(<DatacenterList />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('US West Prime'))
    expect(screen.getByText('150 MW')).toBeInTheDocument()
  })

  it('renders status badges', async () => {
    mockAuth('viewer')
    mockFetch(MOCK_RESPONSE)
    render(<DatacenterList />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('US West Prime'))
    expect(screen.getByText('active')).toBeInTheDocument()
    expect(screen.getByText('planned')).toBeInTheDocument()
  })

  it('shows "+ Add Datacenter" for analyst', async () => {
    mockAuth('analyst')
    mockFetch(MOCK_RESPONSE)
    render(<DatacenterList />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('US West Prime'))
    expect(screen.getByText('+ Add Datacenter')).toBeInTheDocument()
  })

  it('hides "+ Add Datacenter" for viewer', async () => {
    mockAuth('viewer')
    mockFetch(MOCK_RESPONSE)
    render(<DatacenterList />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('US West Prime'))
    expect(screen.queryByText('+ Add Datacenter')).not.toBeInTheDocument()
  })

  it('shows Edit button for analyst', async () => {
    mockAuth('analyst')
    mockFetch(MOCK_RESPONSE)
    render(<DatacenterList />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('US West Prime'))
    expect(screen.getAllByRole('button', { name: /edit us west prime/i }).length).toBeGreaterThan(0)
  })

  it('shows Delete button only for admin', async () => {
    mockAuth('admin')
    mockFetch(MOCK_RESPONSE)
    render(<DatacenterList />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('US West Prime'))
    expect(screen.getAllByRole('button', { name: /delete us west prime/i }).length).toBeGreaterThan(0)
  })

  it('hides Delete for analyst', async () => {
    mockAuth('analyst')
    mockFetch(MOCK_RESPONSE)
    render(<DatacenterList />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('US West Prime'))
    expect(screen.queryByRole('button', { name: /delete us west prime/i })).not.toBeInTheDocument()
  })

  it('shows empty state when no datacenters', async () => {
    mockAuth('viewer')
    mockFetch(EMPTY_RESPONSE)
    render(<DatacenterList />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByText('No datacenter sites found.')).toBeInTheDocument()
    })
  })

  it('shows error state when fetch fails', async () => {
    mockAuth('viewer')
    mockFetch(null, false)
    render(<DatacenterList />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText('Failed to load datacenter sites.')).toBeInTheDocument()
    })
  })

  it('shows delete confirmation dialog when Delete is clicked', async () => {
    mockAuth('admin')
    mockFetch(MOCK_RESPONSE)
    render(<DatacenterList />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('US West Prime'))
    fireEvent.click(screen.getByRole('button', { name: /delete us west prime/i }))

    await waitFor(() => {
      expect(screen.getByText('Delete Datacenter Site')).toBeInTheDocument()
      expect(screen.getByText(/This cannot be undone/i)).toBeInTheDocument()
    })
  })
})

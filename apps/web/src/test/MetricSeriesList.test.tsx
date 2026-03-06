import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import * as AuthModule from '../store/AuthContext'
import MetricSeriesList from '../routes/metric-series/MetricSeriesList'

const MOCK_SERIES = [
  {
    id: 'series-1',
    name: 'H100 Shipment Volume',
    entity_type: 'hardware_product',
    entity_id: 'hw-1',
    unit: 'units (thousands)',
    frequency: 'monthly',
    source: 'IDC Report',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'series-2',
    name: 'NVIDIA Revenue',
    entity_type: 'company',
    entity_id: 'co-1',
    unit: 'USD millions',
    frequency: 'quarterly',
    source: null,
    created_at: '2026-01-02T00:00:00Z',
    updated_at: '2026-01-02T00:00:00Z',
  },
]

const MOCK_RESPONSE = { items: MOCK_SERIES, total: 2, limit: 20, offset: 0 }
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

describe('MetricSeriesList', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('renders series names, units and frequency badges', async () => {
    mockAuth('viewer')
    mockFetch(MOCK_RESPONSE)
    render(<MetricSeriesList />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByText('H100 Shipment Volume')).toBeInTheDocument()
      expect(screen.getByText('NVIDIA Revenue')).toBeInTheDocument()
    })
    expect(screen.getByText('units (thousands)')).toBeInTheDocument()
    expect(screen.getByText('USD millions')).toBeInTheDocument()
    expect(screen.getByText('monthly')).toBeInTheDocument()
  })

  it('renders entity type labels', async () => {
    mockAuth('viewer')
    mockFetch(MOCK_RESPONSE)
    render(<MetricSeriesList />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByText('Hardware')).toBeInTheDocument()
      expect(screen.getByText('Company')).toBeInTheDocument()
    })
  })

  it('renders source column (shows — for null)', async () => {
    mockAuth('viewer')
    mockFetch(MOCK_RESPONSE)
    render(<MetricSeriesList />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByText('IDC Report')).toBeInTheDocument()
    })
  })

  it('shows "+ Add Series" for analyst', async () => {
    mockAuth('analyst')
    mockFetch(MOCK_RESPONSE)
    render(<MetricSeriesList />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('H100 Shipment Volume'))
    expect(screen.getByText('+ Add Series')).toBeInTheDocument()
  })

  it('hides "+ Add Series" for viewer', async () => {
    mockAuth('viewer')
    mockFetch(MOCK_RESPONSE)
    render(<MetricSeriesList />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('H100 Shipment Volume'))
    expect(screen.queryByText('+ Add Series')).not.toBeInTheDocument()
  })

  it('shows Edit actions for analyst', async () => {
    mockAuth('analyst')
    mockFetch(MOCK_RESPONSE)
    render(<MetricSeriesList />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('H100 Shipment Volume'))
    expect(screen.getAllByRole('button', { name: /edit h100 shipment volume/i }).length).toBeGreaterThan(0)
  })

  it('shows Delete actions only for admin', async () => {
    mockAuth('admin')
    mockFetch(MOCK_RESPONSE)
    render(<MetricSeriesList />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('H100 Shipment Volume'))
    expect(screen.getAllByRole('button', { name: /delete h100 shipment volume/i }).length).toBeGreaterThan(0)
  })

  it('hides Delete for analyst (not admin)', async () => {
    mockAuth('analyst')
    mockFetch(MOCK_RESPONSE)
    render(<MetricSeriesList />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('H100 Shipment Volume'))
    expect(screen.queryByRole('button', { name: /delete h100/i })).not.toBeInTheDocument()
  })

  it('shows empty state when no series', async () => {
    mockAuth('viewer')
    mockFetch(EMPTY_RESPONSE)
    render(<MetricSeriesList />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByText('No metric series found.')).toBeInTheDocument()
    })
  })

  it('shows error state when fetch fails', async () => {
    mockAuth('viewer')
    mockFetch(null, false)
    render(<MetricSeriesList />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText('Failed to load metric series.')).toBeInTheDocument()
    })
  })

  it('shows delete confirmation dialog when Delete is clicked', async () => {
    mockAuth('admin')
    mockFetch(MOCK_RESPONSE)
    render(<MetricSeriesList />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('H100 Shipment Volume'))
    fireEvent.click(screen.getByRole('button', { name: /delete h100 shipment volume/i }))

    await waitFor(() => {
      expect(screen.getByText('Delete Metric Series')).toBeInTheDocument()
      expect(screen.getByText(/all data points will also be deleted/i)).toBeInTheDocument()
    })
  })
})

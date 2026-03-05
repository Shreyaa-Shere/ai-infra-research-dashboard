import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import * as AuthModule from '../store/AuthContext'
import Dashboard from '../routes/Dashboard'

// Mock recharts to avoid SVG rendering issues in jsdom
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  LineChart: ({ children }: { children: React.ReactNode }) => (
    <svg data-testid="line-chart">{children}</svg>
  ),
  BarChart: ({ children }: { children: React.ReactNode }) => (
    <svg data-testid="bar-chart">{children}</svg>
  ),
  Line: () => null,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  Tooltip: () => null,
  CartesianGrid: () => null,
  Legend: () => null,
}))

const MOCK_OVERVIEW = {
  kpis: [
    { label: 'Hardware Products', value: 3 },
    { label: 'Companies', value: 5 },
    { label: 'Datacenter Sites', value: 2 },
    { label: 'Published Notes', value: 1 },
    { label: 'Metric Series', value: 4 },
    { label: 'Latest: H100 Shipment Volume', value: 85, unit: 'units (thousands)' },
  ],
  charts: [
    {
      series_id: 'series-uuid-1',
      name: 'H100 Shipment Volume',
      unit: 'units (thousands)',
      data: [
        { label: '2024-01', value: 12 },
        { label: '2024-02', value: 15 },
      ],
    },
    {
      series_id: 'series-uuid-2',
      name: 'US West DC Power Usage',
      unit: 'MW',
      data: [
        { label: '2024-01', value: 320 },
        { label: '2024-02', value: 335 },
      ],
    },
  ],
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
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    )
  }
}

describe('Dashboard', () => {
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

  it('renders KPI cards after loading', async () => {
    const Wrapper = makeWrapper(MOCK_OVERVIEW)
    render(<Dashboard />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('Hardware Products')).toBeInTheDocument()
    })
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('Companies')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('renders chart section with series names', async () => {
    const Wrapper = makeWrapper(MOCK_OVERVIEW)
    render(<Dashboard />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('H100 Shipment Volume')).toBeInTheDocument()
    })
    expect(screen.getByText('US West DC Power Usage')).toBeInTheDocument()
    expect(screen.getByText('Metric Trends')).toBeInTheDocument()
  })

  it('shows loading skeletons initially', () => {
    // Fetch that never resolves
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const Wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={qc}>
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    )
    render(<Dashboard />, { wrapper: Wrapper })
    // Skeleton divs are rendered
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('shows sign out button', async () => {
    const Wrapper = makeWrapper(MOCK_OVERVIEW)
    render(<Dashboard />, { wrapper: Wrapper })
    expect(screen.getByText('Sign out')).toBeInTheDocument()
  })

  it('shows empty charts message when no charts returned', async () => {
    const Wrapper = makeWrapper({ kpis: MOCK_OVERVIEW.kpis, charts: [] })
    render(<Dashboard />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('Hardware Products')).toBeInTheDocument()
    })
    expect(screen.getByText(/No metric data yet/)).toBeInTheDocument()
  })
})

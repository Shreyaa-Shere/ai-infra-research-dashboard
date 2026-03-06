import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import * as AuthModule from '../store/AuthContext'

// Mock recharts before component import (vi.mock is hoisted automatically)
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="chart-container">{children}</div>
  ),
  LineChart: ({ children }: { children: React.ReactNode }) => (
    <svg data-testid="line-chart">{children}</svg>
  ),
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  Tooltip: () => null,
  CartesianGrid: () => null,
}))

import MetricSeriesDetail from '../routes/metric-series/MetricSeriesDetail'

const MOCK_SERIES = {
  id: 'series-1',
  name: 'H100 Shipment Volume',
  entity_type: 'hardware_product',
  entity_id: 'hw-uuid-1111',
  unit: 'units (thousands)',
  frequency: 'monthly',
  source: 'IDC Report',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

const MOCK_POINTS = [
  { id: 'pt-1', metric_series_id: 'series-1', timestamp: '2026-01-01T00:00:00Z', value: 50 },
  { id: 'pt-2', metric_series_id: 'series-1', timestamp: '2026-02-01T00:00:00Z', value: 75 },
  { id: 'pt-3', metric_series_id: 'series-1', timestamp: '2026-03-01T00:00:00Z', value: 100 },
]

function makeFetchMock(seriesJson: unknown, pointsJson: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn((url: string) => {
      // Route by URL: /points suffix → points list, otherwise → series detail
      const body = url.includes('/points') ? pointsJson : seriesJson
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(body),
      })
    })
  )
}

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/metric-series/series-1']}>
        <Routes>
          <Route path="/metric-series/:id" element={children} />
        </Routes>
      </MemoryRouter>
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

describe('MetricSeriesDetail', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('renders series name, unit, frequency and source', async () => {
    mockAuth('viewer')
    makeFetchMock(MOCK_SERIES, MOCK_POINTS)

    render(<MetricSeriesDetail />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByText('H100 Shipment Volume')).toBeInTheDocument()
    })
    // unit appears in detail row and possibly summary; getAllByText handles both
    expect(screen.getAllByText('units (thousands)').length).toBeGreaterThan(0)
    expect(screen.getByText('monthly')).toBeInTheDocument()
    expect(screen.getByText('IDC Report')).toBeInTheDocument()
  })

  it('renders back link to metric series list', async () => {
    mockAuth('viewer')
    makeFetchMock(MOCK_SERIES, MOCK_POINTS)

    render(<MetricSeriesDetail />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('H100 Shipment Volume'))
    expect(screen.getByText('← Back to Metric Series')).toBeInTheDocument()
  })

  it('renders Export CSV button', async () => {
    mockAuth('viewer')
    makeFetchMock(MOCK_SERIES, MOCK_POINTS)

    render(<MetricSeriesDetail />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('H100 Shipment Volume'))
    expect(screen.getByRole('button', { name: /export csv/i })).toBeInTheDocument()
  })

  it('renders trend chart container', async () => {
    mockAuth('viewer')
    makeFetchMock(MOCK_SERIES, MOCK_POINTS)

    render(<MetricSeriesDetail />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('H100 Shipment Volume'))
    expect(screen.getByTestId('chart-container')).toBeInTheDocument()
  })

  it('shows latest value in summary card', async () => {
    mockAuth('viewer')
    makeFetchMock(MOCK_SERIES, MOCK_POINTS)

    render(<MetricSeriesDetail />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('H100 Shipment Volume'))
    // Latest point value is 100 — appears in summary card and data table
    await waitFor(() => {
      expect(screen.getAllByText('100').length).toBeGreaterThan(0)
    })
  })

  it('shows Edit and Delete buttons for admin', async () => {
    mockAuth('admin')
    makeFetchMock(MOCK_SERIES, MOCK_POINTS)

    render(<MetricSeriesDetail />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('H100 Shipment Volume'))
    expect(screen.getByRole('button', { name: /^edit$/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^delete$/i })).toBeInTheDocument()
  })

  it('hides Edit/Delete for viewer', async () => {
    mockAuth('viewer')
    makeFetchMock(MOCK_SERIES, MOCK_POINTS)

    render(<MetricSeriesDetail />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('H100 Shipment Volume'))
    expect(screen.queryByRole('button', { name: /^edit$/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^delete$/i })).not.toBeInTheDocument()
  })

  it('shows "Add Points" button for analyst', async () => {
    mockAuth('analyst')
    makeFetchMock(MOCK_SERIES, MOCK_POINTS)

    render(<MetricSeriesDetail />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('H100 Shipment Volume'))
    expect(screen.getByRole('button', { name: /add points/i })).toBeInTheDocument()
  })

  it('renders entity link to hardware product detail', async () => {
    mockAuth('viewer')
    makeFetchMock(MOCK_SERIES, MOCK_POINTS)

    render(<MetricSeriesDetail />, { wrapper: makeWrapper() })

    await waitFor(() => screen.getByText('H100 Shipment Volume'))
    const entityLink = screen.getByRole('link', { name: /hardware product/i })
    expect(entityLink).toHaveAttribute('href', '/hardware-products/hw-uuid-1111')
  })

  it('shows error state when series fetch fails', async () => {
    mockAuth('viewer')
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 404,
          json: () => Promise.resolve({ error: { code: 'NOT_FOUND', message: 'Not found' } }),
        })
      )
    )

    render(<MetricSeriesDetail />, { wrapper: makeWrapper() })

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText('Metric series not found.')).toBeInTheDocument()
    })
  })
})

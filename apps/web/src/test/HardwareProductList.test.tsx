import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import { AuthProvider } from '../store/AuthContext'
import HardwareProductList from '../routes/hardware-products/HardwareProductList'

const MOCK_RESPONSE = {
  items: [
    {
      id: 'uuid-1',
      name: 'H100',
      vendor: 'NVIDIA',
      category: 'GPU',
      release_date: '2023-03-22',
      memory_gb: 80,
      tdp_watts: 700,
      process_node: '4nm',
      notes: null,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'uuid-2',
      name: 'A100',
      vendor: 'NVIDIA',
      category: 'GPU',
      release_date: '2020-05-14',
      memory_gb: 80,
      tdp_watts: 400,
      process_node: '7nm',
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

  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  // Stub AuthContext to provide a token without going through login
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <AuthProvider>{children}</AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>
    )
  }
}

describe('HardwareProductList', () => {
  it('renders table with column headers and rows', async () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<HardwareProductList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('H100')).toBeInTheDocument()
      expect(screen.getByText('A100')).toBeInTheDocument()
    })

    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Vendor')).toBeInTheDocument()
    expect(screen.getByText('Category')).toBeInTheDocument()
  })

  it('renders pagination controls with correct text', async () => {
    const Wrapper = makeWrapper(MOCK_RESPONSE)
    render(<HardwareProductList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText(/Showing 1–2 of 2/)).toBeInTheDocument()
    })
  })

  it('shows empty state when no items', async () => {
    const Wrapper = makeWrapper(EMPTY_RESPONSE)
    render(<HardwareProductList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('No hardware products found.')).toBeInTheDocument()
    })
  })

  it('shows "No results" in pagination when empty', async () => {
    const Wrapper = makeWrapper(EMPTY_RESPONSE)
    render(<HardwareProductList />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('No results')).toBeInTheDocument()
    })
  })
})

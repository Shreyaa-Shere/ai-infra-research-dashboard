import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi } from 'vitest'

import PublishedNote from '../routes/published/PublishedNote'

const MOCK_NOTE = {
  id: 'note-uuid-1',
  title: 'H100 Supply Chain Analysis',
  body_markdown: '## Analysis\n\nGreat GPU with CoWoS packaging.',
  status: 'published',
  slug: 'h100-supply-chain-analysis-abc12345',
  tags: ['gpu', 'supply-chain'],
  author: { id: 'user-uuid-1', email: 'analyst@example.com' },
  linked_entities: [
    {
      entity_type: 'hardware_product',
      entity_id: 'hw-uuid-1',
      display: { name: 'H100', kind: 'GPU' },
    },
  ],
  created_at: '2026-03-01T00:00:00Z',
  updated_at: '2026-03-01T00:00:00Z',
  published_at: '2026-03-02T00:00:00Z',
}

function makeWrapper(mockJson: unknown, ok = true, status = 200) {
  vi.stubGlobal(
    'fetch',
    vi.fn(() =>
      Promise.resolve({
        ok,
        status,
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
        <MemoryRouter initialEntries={['/published/h100-supply-chain-analysis-abc12345']}>
          <Routes>
            <Route path="/published/:slug" element={children} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    )
  }
}

describe('PublishedNote', () => {
  it('renders note title, author, and tags', async () => {
    const Wrapper = makeWrapper(MOCK_NOTE)
    render(<PublishedNote />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('H100 Supply Chain Analysis')).toBeInTheDocument()
    })
    expect(screen.getByText('analyst@example.com')).toBeInTheDocument()
    expect(screen.getByText('gpu')).toBeInTheDocument()
    expect(screen.getByText('supply-chain')).toBeInTheDocument()
  })

  it('renders markdown body content', async () => {
    const Wrapper = makeWrapper(MOCK_NOTE)
    render(<PublishedNote />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText(/Great GPU with CoWoS packaging/)).toBeInTheDocument()
    })
  })

  it('renders linked entity', async () => {
    const Wrapper = makeWrapper(MOCK_NOTE)
    render(<PublishedNote />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('H100')).toBeInTheDocument()
      expect(screen.getByText(/hardware_product/)).toBeInTheDocument()
    })
  })

  it('shows 404 message when note not found', async () => {
    const errorPayload = { error: { code: 'NOT_FOUND', message: 'Not found', details: {} } }
    const Wrapper = makeWrapper(errorPayload, false, 404)
    render(<PublishedNote />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('Note not found')).toBeInTheDocument()
    })
  })
})

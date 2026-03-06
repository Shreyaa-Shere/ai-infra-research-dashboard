import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import * as AuthModule from '../store/AuthContext'

vi.mock('../lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/api')>()
  return {
    ...actual,
    notesApi: {
      ...actual.notesApi,
      get: vi.fn(),
      update: vi.fn(),
      create: vi.fn(),
      delete: vi.fn(),
      publish: vi.fn(),
    },
    hardwareProductsApi: { list: vi.fn().mockResolvedValue({ items: [], total: 0, limit: 5, offset: 0 }) },
    companiesApi: { list: vi.fn().mockResolvedValue({ items: [], total: 0, limit: 5, offset: 0 }) },
    datacentersApi: { list: vi.fn().mockResolvedValue({ items: [], total: 0, limit: 5, offset: 0 }) },
  }
})

import NoteEditor from '../routes/notes/NoteEditor'
import { notesApi } from '../lib/api'

const DRAFT_NOTE = {
  id: 'note-1',
  title: 'Draft Note',
  body_markdown: 'Some content',
  status: 'draft' as const,
  slug: null,
  tags: [],
  author: { id: 'analyst-1', email: 'analyst@example.com' },
  linked_entities: [],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  published_at: null,
}

const REVIEW_NOTE = { ...DRAFT_NOTE, status: 'review' as const }

function makeWrapper(role: 'admin' | 'analyst', userId = 'analyst-1') {
  vi.spyOn(AuthModule, 'useAuth').mockReturnValue({
    user: { id: userId, email: `${role}@example.com`, role, is_active: true, created_at: '' },
    accessToken: 'token',
    isLoading: false,
    error: null,
    login: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
  })

  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/notes/note-1']}>
        <Routes>
          <Route path="/notes/:id" element={children} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('NoteEditor', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('shows "Submit for Review" button for analyst on a draft note', async () => {
    vi.mocked(notesApi.get).mockResolvedValue(DRAFT_NOTE)
    render(<NoteEditor />, { wrapper: makeWrapper('analyst') })

    await waitFor(() => {
      expect(screen.getByText('Submit for Review')).toBeInTheDocument()
    })
    expect(screen.queryByText('Reject to Draft')).not.toBeInTheDocument()
  })

  it('does NOT show "Reject to Draft" for analyst on a review note', async () => {
    vi.mocked(notesApi.get).mockResolvedValue(REVIEW_NOTE)
    render(<NoteEditor />, { wrapper: makeWrapper('analyst') })

    await waitFor(() => {
      expect(screen.getByText('Save Draft')).toBeInTheDocument()
    })
    expect(screen.queryByText('Reject to Draft')).not.toBeInTheDocument()
    expect(screen.queryByText('Submit for Review')).not.toBeInTheDocument()
  })

  it('shows "Reject to Draft" button for admin on a review note', async () => {
    vi.mocked(notesApi.get).mockResolvedValue(REVIEW_NOTE)
    render(<NoteEditor />, { wrapper: makeWrapper('admin', 'admin-1') })

    await waitFor(() => {
      expect(screen.getByText('Reject to Draft')).toBeInTheDocument()
    })
  })

  it('does NOT show "Reject to Draft" for admin on a draft note', async () => {
    vi.mocked(notesApi.get).mockResolvedValue(DRAFT_NOTE)
    render(<NoteEditor />, { wrapper: makeWrapper('admin', 'admin-1') })

    await waitFor(() => {
      expect(screen.getByText('Submit for Review')).toBeInTheDocument()
    })
    expect(screen.queryByText('Reject to Draft')).not.toBeInTheDocument()
  })

  it('shows "Back to Research Notes" link', async () => {
    vi.mocked(notesApi.get).mockResolvedValue(DRAFT_NOTE)
    render(<NoteEditor />, { wrapper: makeWrapper('analyst') })

    await waitFor(() => {
      expect(screen.getByText('← Back to Research Notes')).toBeInTheDocument()
    })
  })
})

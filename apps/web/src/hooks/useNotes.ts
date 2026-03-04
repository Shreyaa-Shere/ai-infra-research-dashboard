import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { notesApi } from '../lib/api'
import type { NoteStatus, ResearchNoteCreate, ResearchNoteUpdate } from '../lib/entities'
import { useAuth } from '../store/AuthContext'

// ── list ──────────────────────────────────────────────────────────────────────

export function useNotes(params: {
  limit?: number
  offset?: number
  status?: NoteStatus
  tag?: string
  q?: string
} = {}) {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: ['notes', params],
    queryFn: () => notesApi.list(accessToken!, params),
    enabled: !!accessToken,
  })
}

// ── single note ───────────────────────────────────────────────────────────────

export function useNote(id: string) {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: ['notes', id],
    queryFn: () => notesApi.get(accessToken!, id),
    enabled: !!accessToken && !!id,
  })
}

// ── published (no auth) ───────────────────────────────────────────────────────

export function usePublishedNote(slug: string) {
  return useQuery({
    queryKey: ['published', slug],
    queryFn: () => notesApi.getPublished(slug),
    enabled: !!slug,
    retry: false,
  })
}

// ── create ────────────────────────────────────────────────────────────────────

export function useCreateNote() {
  const { accessToken } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ResearchNoteCreate) => notesApi.create(accessToken!, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notes'] }),
  })
}

// ── update ────────────────────────────────────────────────────────────────────

export function useUpdateNote() {
  const { accessToken } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ResearchNoteUpdate }) =>
      notesApi.update(accessToken!, id, data),
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: ['notes'] })
      qc.invalidateQueries({ queryKey: ['notes', id] })
    },
  })
}

// ── publish ───────────────────────────────────────────────────────────────────

export function usePublishNote() {
  const { accessToken } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => notesApi.publish(accessToken!, id),
    onSuccess: (_data, id) => {
      qc.invalidateQueries({ queryKey: ['notes'] })
      qc.invalidateQueries({ queryKey: ['notes', id] })
    },
  })
}

// ── delete ────────────────────────────────────────────────────────────────────

export function useDeleteNote() {
  const { accessToken } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => notesApi.delete(accessToken!, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notes'] }),
  })
}

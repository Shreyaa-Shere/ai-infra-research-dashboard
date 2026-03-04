import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { companiesApi } from '../lib/api'
import type { CompanyCreate, CompanyUpdate } from '../lib/entities'
import { useAuth } from '../store/AuthContext'

export function useCompanies(params: { limit?: number; offset?: number; type?: string } = {}) {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: ['companies', params],
    queryFn: () => companiesApi.list(accessToken!, params),
    enabled: !!accessToken,
  })
}

export function useCompany(id: string) {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: ['companies', id],
    queryFn: () => companiesApi.get(accessToken!, id),
    enabled: !!accessToken && !!id,
  })
}

export function useCreateCompany() {
  const { accessToken } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CompanyCreate) => companiesApi.create(accessToken!, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['companies'] }),
  })
}

export function useUpdateCompany() {
  const { accessToken } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CompanyUpdate }) =>
      companiesApi.update(accessToken!, id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['companies'] }),
  })
}

export function useDeleteCompany() {
  const { accessToken } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => companiesApi.delete(accessToken!, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['companies'] }),
  })
}

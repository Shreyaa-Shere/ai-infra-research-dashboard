import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { datacentersApi } from '../lib/api'
import type { DatacenterCreate, DatacenterUpdate } from '../lib/entities'
import { useAuth } from '../store/AuthContext'

export function useDatacenters(params: {
  limit?: number
  offset?: number
  owner_company_id?: string
  status?: string
} = {}) {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: ['datacenters', params],
    queryFn: () => datacentersApi.list(accessToken!, params),
    enabled: !!accessToken,
  })
}

export function useDatacenter(id: string) {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: ['datacenters', id],
    queryFn: () => datacentersApi.get(accessToken!, id),
    enabled: !!accessToken && !!id,
  })
}

export function useCreateDatacenter() {
  const { accessToken } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: DatacenterCreate) => datacentersApi.create(accessToken!, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['datacenters'] }),
  })
}

export function useUpdateDatacenter() {
  const { accessToken } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: DatacenterUpdate }) =>
      datacentersApi.update(accessToken!, id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['datacenters'] }),
  })
}

export function useDeleteDatacenter() {
  const { accessToken } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => datacentersApi.delete(accessToken!, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['datacenters'] }),
  })
}

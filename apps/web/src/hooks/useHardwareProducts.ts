import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { hardwareProductsApi } from '../lib/api'
import type { HardwareProductCreate, HardwareProductUpdate } from '../lib/entities'
import { useAuth } from '../store/AuthContext'

export function useHardwareProducts(params: {
  limit?: number
  offset?: number
  vendor?: string
  category?: string
} = {}) {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: ['hardware-products', params],
    queryFn: () => hardwareProductsApi.list(accessToken!, params),
    enabled: !!accessToken,
  })
}

export function useHardwareProduct(id: string) {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: ['hardware-products', id],
    queryFn: () => hardwareProductsApi.get(accessToken!, id),
    enabled: !!accessToken && !!id,
  })
}

export function useCreateHardwareProduct() {
  const { accessToken } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: HardwareProductCreate) =>
      hardwareProductsApi.create(accessToken!, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['hardware-products'] }),
  })
}

export function useUpdateHardwareProduct() {
  const { accessToken } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: HardwareProductUpdate }) =>
      hardwareProductsApi.update(accessToken!, id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['hardware-products'] }),
  })
}

export function useDeleteHardwareProduct() {
  const { accessToken } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => hardwareProductsApi.delete(accessToken!, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['hardware-products'] }),
  })
}

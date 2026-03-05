import { useQuery } from '@tanstack/react-query'
import { searchApi } from '../lib/api'
import type { SearchParams } from '../lib/entities'
import { useAuth } from '../store/AuthContext'

export function useSearchResults(params: SearchParams | null) {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: ['search', params],
    queryFn: () => searchApi.search(accessToken!, params!),
    enabled: !!accessToken && !!params && params.q.trim().length > 0,
    staleTime: 30_000,
  })
}

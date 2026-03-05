const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(
  path: string,
  init: RequestInit & { token?: string } = {}
): Promise<T> {
  const { token, headers: extraHeaders, ...rest } = init
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(extraHeaders as Record<string, string>),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE}${path}`, { ...rest, headers })

  if (res.status === 204) return undefined as T

  const data = await res.json()
  if (!res.ok) {
    const err = data?.error ?? {}
    throw new ApiError(res.status, err.code ?? 'UNKNOWN', err.message ?? 'Request failed')
  }
  return data as T
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface User {
  id: string
  email: string
  role: 'admin' | 'analyst' | 'viewer'
  is_active: boolean
  created_at: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface RefreshResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

import type {
  Company,
  CompanyCreate,
  CompanyUpdate,
  DatacenterCreate,
  DatacenterSite,
  DatacenterUpdate,
  HardwareProduct,
  HardwareProductCreate,
  HardwareProductUpdate,
  IngestionTriggerRequest,
  IngestionTriggerResponse,
  IngestionRunResponse,
  LinkedEntityDisplay,
  LinkedEntityInput,
  MetricEntityType,
  MetricPoint,
  MetricPointsUpsertRequest,
  MetricSeries,
  MetricSeriesCreate,
  MetricSeriesUpdate,
  MetricsOverview,
  NoteStatus,
  PaginatedResponse,
  ResearchNote,
  ResearchNoteCreate,
  ResearchNoteUpdate,
  SearchParams,
  SearchResponse,
  SourceDocumentDetail,
  SourceDocumentSummary,
  SourceType,
} from './entities'

// ── Auth calls ────────────────────────────────────────────────────────────────

export const authApi = {
  login: (email: string, password: string) =>
    request<LoginResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  refresh: (refreshToken: string) =>
    request<RefreshResponse>('/api/v1/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),

  logout: (accessToken: string, refreshToken: string) =>
    request<void>('/api/v1/auth/logout', {
      method: 'POST',
      token: accessToken,
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),

  me: (accessToken: string) =>
    request<User>('/api/v1/me', { token: accessToken }),
}

// ── Entity helpers ────────────────────────────────────────────────────────────

function qs(params: Record<string, string | number | undefined | null>): string {
  const p = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v != null) p.set(k, String(v))
  }
  const s = p.toString()
  return s ? `?${s}` : ''
}

// ── Hardware Products ─────────────────────────────────────────────────────────

export const hardwareProductsApi = {
  list: (
    token: string,
    params: { limit?: number; offset?: number; vendor?: string; category?: string } = {}
  ) =>
    request<PaginatedResponse<HardwareProduct>>(
      `/api/v1/hardware-products${qs(params)}`,
      { token }
    ),

  get: (token: string, id: string) =>
    request<HardwareProduct>(`/api/v1/hardware-products/${id}`, { token }),

  create: (token: string, data: HardwareProductCreate) =>
    request<HardwareProduct>('/api/v1/hardware-products', {
      method: 'POST',
      token,
      body: JSON.stringify(data),
    }),

  update: (token: string, id: string, data: HardwareProductUpdate) =>
    request<HardwareProduct>(`/api/v1/hardware-products/${id}`, {
      method: 'PATCH',
      token,
      body: JSON.stringify(data),
    }),

  delete: (token: string, id: string) =>
    request<void>(`/api/v1/hardware-products/${id}`, { method: 'DELETE', token }),
}

// ── Companies ─────────────────────────────────────────────────────────────────

export const companiesApi = {
  list: (
    token: string,
    params: { limit?: number; offset?: number; type?: string } = {}
  ) =>
    request<PaginatedResponse<Company>>(
      `/api/v1/companies${qs(params)}`,
      { token }
    ),

  get: (token: string, id: string) =>
    request<Company>(`/api/v1/companies/${id}`, { token }),

  create: (token: string, data: CompanyCreate) =>
    request<Company>('/api/v1/companies', {
      method: 'POST',
      token,
      body: JSON.stringify(data),
    }),

  update: (token: string, id: string, data: CompanyUpdate) =>
    request<Company>(`/api/v1/companies/${id}`, {
      method: 'PATCH',
      token,
      body: JSON.stringify(data),
    }),

  delete: (token: string, id: string) =>
    request<void>(`/api/v1/companies/${id}`, { method: 'DELETE', token }),
}

// ── Datacenters ───────────────────────────────────────────────────────────────

export const datacentersApi = {
  list: (
    token: string,
    params: { limit?: number; offset?: number; owner_company_id?: string; status?: string } = {}
  ) =>
    request<PaginatedResponse<DatacenterSite>>(
      `/api/v1/datacenters${qs(params)}`,
      { token }
    ),

  get: (token: string, id: string) =>
    request<DatacenterSite>(`/api/v1/datacenters/${id}`, { token }),

  create: (token: string, data: DatacenterCreate) =>
    request<DatacenterSite>('/api/v1/datacenters', {
      method: 'POST',
      token,
      body: JSON.stringify(data),
    }),

  update: (token: string, id: string, data: DatacenterUpdate) =>
    request<DatacenterSite>(`/api/v1/datacenters/${id}`, {
      method: 'PATCH',
      token,
      body: JSON.stringify(data),
    }),

  delete: (token: string, id: string) =>
    request<void>(`/api/v1/datacenters/${id}`, { method: 'DELETE', token }),
}

// ── Notes ─────────────────────────────────────────────────────────────────────

export const notesApi = {
  list: (
    token: string,
    params: {
      limit?: number
      offset?: number
      status?: NoteStatus
      tag?: string
      q?: string
    } = {}
  ) =>
    request<PaginatedResponse<ResearchNote>>(
      `/api/v1/notes${qs(params)}`,
      { token }
    ),

  get: (token: string, id: string) =>
    request<ResearchNote>(`/api/v1/notes/${id}`, { token }),

  create: (token: string, data: ResearchNoteCreate) =>
    request<ResearchNote>('/api/v1/notes', {
      method: 'POST',
      token,
      body: JSON.stringify(data),
    }),

  update: (token: string, id: string, data: ResearchNoteUpdate) =>
    request<ResearchNote>(`/api/v1/notes/${id}`, {
      method: 'PATCH',
      token,
      body: JSON.stringify(data),
    }),

  delete: (token: string, id: string) =>
    request<void>(`/api/v1/notes/${id}`, { method: 'DELETE', token }),

  publish: (token: string, id: string) =>
    request<ResearchNote>(`/api/v1/notes/${id}/publish`, {
      method: 'POST',
      token,
    }),

  getLinks: (token: string, id: string) =>
    request<LinkedEntityDisplay[]>(`/api/v1/notes/${id}/links`, { token }),

  replaceLinks: (token: string, id: string, links: LinkedEntityInput[]) =>
    request<LinkedEntityDisplay[]>(`/api/v1/notes/${id}/links`, {
      method: 'PUT',
      token,
      body: JSON.stringify(links),
    }),

  getPublished: (slug: string) =>
    request<ResearchNote>(`/api/v1/published/${slug}`),
}

// ── Metrics ───────────────────────────────────────────────────────────────────

export const metricsApi = {
  overview: (token: string) =>
    request<MetricsOverview>('/api/v1/metrics/overview', { token }),

  listSeries: (
    token: string,
    params: { limit?: number; offset?: number; entity_type?: MetricEntityType; entity_id?: string } = {}
  ) =>
    request<PaginatedResponse<MetricSeries>>(
      `/api/v1/metric-series${qs(params)}`,
      { token }
    ),

  getSeries: (token: string, id: string) =>
    request<MetricSeries>(`/api/v1/metric-series/${id}`, { token }),

  createSeries: (token: string, data: MetricSeriesCreate) =>
    request<MetricSeries>('/api/v1/metric-series', {
      method: 'POST',
      token,
      body: JSON.stringify(data),
    }),

  updateSeries: (token: string, id: string, data: MetricSeriesUpdate) =>
    request<MetricSeries>(`/api/v1/metric-series/${id}`, {
      method: 'PATCH',
      token,
      body: JSON.stringify(data),
    }),

  deleteSeries: (token: string, id: string) =>
    request<void>(`/api/v1/metric-series/${id}`, { method: 'DELETE', token }),

  upsertPoints: (token: string, id: string, data: MetricPointsUpsertRequest) =>
    request<{ upserted: number }>(`/api/v1/metric-series/${id}/points`, {
      method: 'POST',
      token,
      body: JSON.stringify(data),
    }),

  listPoints: (
    token: string,
    id: string,
    params: { from_ts?: string; to_ts?: string; limit?: number } = {}
  ) =>
    request<MetricPoint[]>(
      `/api/v1/metric-series/${id}/points${qs(params)}`,
      { token }
    ),

  exportCsvUrl: (id: string) => `${BASE}/api/v1/metric-series/${id}/export.csv`,
}

// ── Sources ───────────────────────────────────────────────────────────────────

export const sourcesApi = {
  list: (
    token: string,
    params: { limit?: number; offset?: number; source_type?: SourceType; q?: string } = {}
  ) =>
    request<PaginatedResponse<SourceDocumentSummary>>(
      `/api/v1/sources${qs(params)}`,
      { token }
    ),

  get: (token: string, id: string) =>
    request<SourceDocumentDetail>(`/api/v1/sources/${id}`, { token }),
}

// ── Ingestion ─────────────────────────────────────────────────────────────────

export const ingestionApi = {
  trigger: (token: string, data: IngestionTriggerRequest) =>
    request<IngestionTriggerResponse>('/api/v1/ingestion/run', {
      method: 'POST',
      token,
      body: JSON.stringify(data),
    }),

  listRuns: (token: string, params: { limit?: number; offset?: number } = {}) =>
    request<PaginatedResponse<IngestionRunResponse>>(
      `/api/v1/ingestion/runs${qs(params)}`,
      { token }
    ),

  getRun: (token: string, id: string) =>
    request<IngestionRunResponse>(`/api/v1/ingestion/runs/${id}`, { token }),
}

// ── Search ────────────────────────────────────────────────────────────────────

export const searchApi = {
  search: (token: string, params: SearchParams) => {
    const p = new URLSearchParams()
    p.set('q', params.q)
    if (params.type) p.set('type', params.type)
    if (params.limit != null) p.set('limit', String(params.limit))
    if (params.offset != null) p.set('offset', String(params.offset))
    if (params.tags?.length) params.tags.forEach((t) => p.append('tags', t))
    if (params.status) p.set('status', params.status)
    if (params.entity_type) p.set('entity_type', params.entity_type)
    if (params.entity_id) p.set('entity_id', params.entity_id)
    if (params.start) p.set('start', params.start)
    if (params.end) p.set('end', params.end)
    if (params.source_type) p.set('source_type', params.source_type)
    return request<SearchResponse>(`/api/v1/search?${p.toString()}`, { token })
  },
}

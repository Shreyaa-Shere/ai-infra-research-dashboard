export type HardwareCategory = 'GPU' | 'CPU' | 'Networking' | 'Accelerator'
export type CompanyType = 'fab' | 'idm' | 'cloud' | 'vendor' | 'research'
export type DatacenterStatus = 'planned' | 'active' | 'retired'

export interface HardwareProduct {
  id: string
  name: string
  vendor: string
  category: HardwareCategory
  release_date: string | null
  memory_gb: number | null
  tdp_watts: number | null
  process_node: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface HardwareProductCreate {
  name: string
  vendor: string
  category: HardwareCategory
  release_date?: string | null
  memory_gb?: number | null
  tdp_watts?: number | null
  process_node?: string | null
  notes?: string | null
}

export interface HardwareProductUpdate {
  name?: string
  vendor?: string
  category?: HardwareCategory
  release_date?: string | null
  memory_gb?: number | null
  tdp_watts?: number | null
  process_node?: string | null
  notes?: string | null
}

export interface Company {
  id: string
  name: string
  type: CompanyType
  region: string
  website: string | null
  created_at: string
  updated_at: string
}

export interface CompanyCreate {
  name: string
  type: CompanyType
  region: string
  website?: string | null
}

export interface CompanyUpdate {
  name?: string
  type?: CompanyType
  region?: string
  website?: string | null
}

export interface DatacenterSite {
  id: string
  name: string
  region: string
  owner_company_id: string | null
  owner_company: Company | null
  power_mw: number | null
  status: DatacenterStatus
  notes: string | null
  created_at: string
  updated_at: string
}

export interface DatacenterCreate {
  name: string
  region: string
  owner_company_id?: string | null
  power_mw?: number | null
  status?: DatacenterStatus
  notes?: string | null
}

export interface DatacenterUpdate {
  name?: string
  region?: string
  owner_company_id?: string | null
  power_mw?: number | null
  status?: DatacenterStatus
  notes?: string | null
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

// ── Notes ─────────────────────────────────────────────────────────────────────

export type NoteStatus = 'draft' | 'review' | 'published'
export type EntityType = 'hardware_product' | 'company' | 'datacenter'

export interface AuthorInfo {
  id: string
  email: string
}

export interface LinkedEntityDisplay {
  entity_type: EntityType
  entity_id: string
  display: { name: string; kind: string }
}

export interface LinkedEntityInput {
  entity_type: EntityType
  entity_id: string
}

export interface ResearchNote {
  id: string
  title: string
  body_markdown: string
  status: NoteStatus
  slug: string | null
  tags: string[]
  author: AuthorInfo
  linked_entities: LinkedEntityDisplay[]
  created_at: string
  updated_at: string
  published_at: string | null
}

export interface ResearchNoteCreate {
  title: string
  body_markdown: string
  tags?: string[]
  linked_entities?: LinkedEntityInput[]
}

export interface ResearchNoteUpdate {
  title?: string
  body_markdown?: string
  tags?: string[]
  status?: 'draft' | 'review'
  linked_entities?: LinkedEntityInput[]
}

// ── Metrics ───────────────────────────────────────────────────────────────────

export type MetricEntityType = 'hardware_product' | 'company' | 'datacenter'
export type MetricFrequency = 'daily' | 'weekly' | 'monthly'

export interface MetricSeries {
  id: string
  name: string
  entity_type: MetricEntityType
  entity_id: string
  unit: string
  frequency: MetricFrequency
  source: string | null
  created_at: string
  updated_at: string
}

export interface MetricSeriesCreate {
  name: string
  entity_type: MetricEntityType
  entity_id: string
  unit: string
  frequency?: MetricFrequency
  source?: string | null
}

export interface MetricSeriesUpdate {
  name?: string
  unit?: string
  frequency?: MetricFrequency
  source?: string | null
}

export interface MetricPointIn {
  timestamp: string
  value: number
}

export interface MetricPointsUpsertRequest {
  points: MetricPointIn[]
}

export interface MetricPoint {
  id: string
  metric_series_id: string
  timestamp: string
  value: number
}

export interface KPIBlock {
  label: string
  value: number | string
  unit?: string | null
  change_pct?: number | null
}

export interface ChartPoint {
  label: string
  value: number
}

export interface ChartSeries {
  series_id: string
  name: string
  unit: string
  data: ChartPoint[]
}

export interface MetricsOverview {
  kpis: KPIBlock[]
  charts: ChartSeries[]
}

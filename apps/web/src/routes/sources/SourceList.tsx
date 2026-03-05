import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DataTable, { type Column } from '../../components/DataTable'
import EmptyState from '../../components/EmptyState'
import LoadingSkeleton from '../../components/LoadingSkeleton'
import PaginationControls from '../../components/PaginationControls'
import { useSources, useTriggerIngestion, useIngestionRuns } from '../../hooks/useSources'
import { useAuth } from '../../store/AuthContext'
import type { IngestionRunResponse, SourceDocumentSummary, SourceType } from '../../lib/entities'

const LIMIT = 20

const STATUS_COLORS: Record<string, string> = {
  ingested: 'bg-green-100 text-green-700',
  skipped: 'bg-yellow-100 text-yellow-700',
  error: 'bg-red-100 text-red-700',
}

const RUN_STATUS_COLORS: Record<string, string> = {
  running: 'bg-blue-100 text-blue-700',
  success: 'bg-green-100 text-green-700',
  partial: 'bg-yellow-100 text-yellow-700',
  error: 'bg-red-100 text-red-700',
}

const SOURCE_TYPE_OPTIONS: Array<{ label: string; value: SourceType | '' }> = [
  { label: 'All types', value: '' },
  { label: 'File', value: 'file' },
  { label: 'RSS', value: 'rss' },
  { label: 'JSON', value: 'json' },
]

export default function SourceList() {
  const [offset, setOffset] = useState(0)
  const [sourceType, setSourceType] = useState<SourceType | ''>('')
  const [q, setQ] = useState('')
  const [qInput, setQInput] = useState('')
  const [showRuns, setShowRuns] = useState(false)
  const navigate = useNavigate()
  const { user } = useAuth()

  const canTrigger = user?.role === 'admin' || user?.role === 'analyst'

  const { data, isLoading, isError } = useSources({
    limit: LIMIT,
    offset,
    source_type: sourceType || undefined,
    q: q || undefined,
  })

  const { data: runsData } = useIngestionRuns({ limit: 5 })
  const triggerMutation = useTriggerIngestion()

  const columns: Column<SourceDocumentSummary>[] = [
    {
      key: 'title',
      header: 'Title',
      render: (row) => (
        <span className="font-medium text-gray-900 line-clamp-1">{row.title}</span>
      ),
    },
    {
      key: 'source_name',
      header: 'Source',
      render: (row) => (
        <span className="text-sm text-gray-600">{row.source_name}</span>
      ),
    },
    {
      key: 'source_type',
      header: 'Type',
      render: (row) => (
        <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
          {row.source_type}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => (
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[row.status] ?? ''}`}
        >
          {row.status}
        </span>
      ),
    },
    {
      key: 'entity_count',
      header: 'Entities',
      render: (row) => (
        <span className="text-sm tabular-nums">{row.entity_count}</span>
      ),
    },
    {
      key: 'published_at',
      header: 'Published',
      render: (row) =>
        row.published_at ? (
          <span className="text-sm text-gray-500">
            {new Date(row.published_at).toLocaleDateString()}
          </span>
        ) : (
          '—'
        ),
    },
  ]

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    setQ(qInput)
    setOffset(0)
  }

  function handleReset() {
    setSourceType('')
    setQ('')
    setQInput('')
    setOffset(0)
  }

  function handleTrigger() {
    triggerMutation.mutate({
      source_type: 'file',
      source_name: 'local-ingest',
      dry_run: false,
    })
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Sources</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowRuns((v) => !v)}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
          >
            {showRuns ? 'Hide Runs' : 'Show Runs'}
          </button>
          {canTrigger && (
            <button
              onClick={handleTrigger}
              disabled={triggerMutation.isPending}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {triggerMutation.isPending ? 'Starting…' : '+ Run Ingestion'}
            </button>
          )}
        </div>
      </div>

      {triggerMutation.isSuccess && (
        <div className="mb-4 rounded-md bg-green-50 px-4 py-3 text-sm text-green-700">
          Ingestion run started — run ID: {triggerMutation.data.run_id}
        </div>
      )}

      {triggerMutation.isError && (
        <div className="mb-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          Failed to start ingestion run.
        </div>
      )}

      {/* Recent Runs Panel */}
      {showRuns && runsData && runsData.items.length > 0 && (
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4">
          <h2 className="mb-3 text-sm font-semibold text-gray-700">Recent Ingestion Runs</h2>
          <div className="space-y-2">
            {runsData.items.map((run: IngestionRunResponse) => (
              <div
                key={run.id}
                className="flex items-center justify-between rounded-md bg-gray-50 px-3 py-2 text-sm"
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${RUN_STATUS_COLORS[run.status] ?? ''}`}
                  >
                    {run.status}
                  </span>
                  <span className="text-gray-600">{run.source_name}</span>
                  {run.dry_run && (
                    <span className="rounded-full bg-purple-100 px-2 py-0.5 text-xs text-purple-700">
                      dry-run
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-4 text-gray-500">
                  {run.stats && (
                    <span>
                      {run.stats.ingested} in · {run.stats.skipped} skip · {run.stats.errors} err
                    </span>
                  )}
                  <span>{new Date(run.started_at).toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <form onSubmit={handleSearch} className="mb-4 flex flex-wrap items-end gap-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">Source type</label>
          <select
            value={sourceType}
            onChange={(e) => {
              setSourceType(e.target.value as SourceType | '')
              setOffset(0)
            }}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {SOURCE_TYPE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">Search</label>
          <input
            value={qInput}
            onChange={(e) => setQInput(e.target.value)}
            placeholder="title or text…"
            className="w-56 rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          type="submit"
          className="rounded-md bg-gray-800 px-3 py-1.5 text-sm text-white hover:bg-gray-900"
        >
          Search
        </button>
        <button
          type="button"
          onClick={handleReset}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
        >
          Reset
        </button>
      </form>

      {isLoading && <LoadingSkeleton rows={5} cols={6} />}

      {isError && (
        <p className="text-sm text-red-600">Failed to load sources.</p>
      )}

      {!isLoading && !isError && data && (
        <>
          {data.items.length === 0 ? (
            <EmptyState message="No source documents found. Run ingestion to populate sources." />
          ) : (
            <DataTable
              columns={columns}
              data={data.items}
              onRowClick={(row) => navigate(`/sources/${row.id}`)}
            />
          )}
          <PaginationControls
            total={data.total}
            limit={data.limit}
            offset={data.offset}
            onOffsetChange={setOffset}
          />
        </>
      )}
    </div>
  )
}

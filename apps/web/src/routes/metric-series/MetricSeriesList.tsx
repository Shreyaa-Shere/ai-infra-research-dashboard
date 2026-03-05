import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ConfirmDialog from '../../components/ConfirmDialog'
import DataTable, { type Column } from '../../components/DataTable'
import EmptyState from '../../components/EmptyState'
import ErrorState from '../../components/ErrorState'
import LoadingSkeleton from '../../components/LoadingSkeleton'
import PaginationControls from '../../components/PaginationControls'
import { useMetricSeries, useDeleteMetricSeries } from '../../hooks/useMetrics'
import { useAuth } from '../../store/AuthContext'
import type { MetricSeries } from '../../lib/entities'
import MetricSeriesForm from './MetricSeriesForm'

const LIMIT = 20

const FREQ_COLORS: Record<string, string> = {
  daily: 'bg-blue-100 text-blue-700',
  weekly: 'bg-indigo-100 text-indigo-700',
  monthly: 'bg-purple-100 text-purple-700',
}

const ENTITY_TYPE_LABELS: Record<string, string> = {
  hardware_product: 'Hardware',
  company: 'Company',
  datacenter: 'Datacenter',
}

export default function MetricSeriesList() {
  const [offset, setOffset] = useState(0)
  const [showForm, setShowForm] = useState(false)
  const [editTarget, setEditTarget] = useState<MetricSeries | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<MetricSeries | null>(null)
  const navigate = useNavigate()
  const { user } = useAuth()

  const canWrite = user?.role === 'admin' || user?.role === 'analyst'
  const canDelete = user?.role === 'admin'

  const { data, isLoading, isError, refetch } = useMetricSeries({ limit: LIMIT, offset })
  const deleteMutation = useDeleteMetricSeries()

  const columns: Column<MetricSeries>[] = [
    { key: 'name', header: 'Name' },
    {
      key: 'entity_type',
      header: 'Entity Type',
      render: (row) => ENTITY_TYPE_LABELS[row.entity_type] ?? row.entity_type,
    },
    { key: 'unit', header: 'Unit' },
    {
      key: 'frequency',
      header: 'Frequency',
      render: (row) => (
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${FREQ_COLORS[row.frequency] ?? 'bg-gray-100 text-gray-700'}`}>
          {row.frequency}
        </span>
      ),
    },
    {
      key: 'source',
      header: 'Source',
      render: (row) => row.source ?? '—',
    },
    ...(canWrite
      ? [
          {
            key: 'actions' as keyof MetricSeries,
            header: '',
            render: (row: MetricSeries) => (
              <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                <button
                  onClick={() => setEditTarget(row)}
                  className="rounded px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  aria-label={`Edit ${row.name}`}
                >
                  Edit
                </button>
                {canDelete && (
                  <button
                    onClick={() => setDeleteTarget(row)}
                    className="rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500"
                    aria-label={`Delete ${row.name}`}
                  >
                    Delete
                  </button>
                )}
              </div>
            ),
          },
        ]
      : []),
  ]

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Metric Series</h1>
        {canWrite && (
          <button
            onClick={() => setShowForm(true)}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            + Add Series
          </button>
        )}
      </div>

      {isLoading && <LoadingSkeleton rows={5} cols={5} />}
      {isError && <ErrorState message="Failed to load metric series." onRetry={() => void refetch()} />}

      {!isLoading && !isError && data && (
        <>
          {data.items.length === 0 ? (
            <EmptyState message="No metric series found." />
          ) : (
            <DataTable
              columns={columns}
              data={data.items}
              onRowClick={(row) => navigate(`/metric-series/${row.id}`)}
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

      {(showForm || editTarget) && (
        <MetricSeriesForm
          initial={editTarget ?? undefined}
          onClose={() => { setShowForm(false); setEditTarget(null) }}
        />
      )}

      {deleteTarget && (
        <ConfirmDialog
          title="Delete Metric Series"
          message={`Delete "${deleteTarget.name}"? All data points will also be deleted. This cannot be undone.`}
          isPending={deleteMutation.isPending}
          onConfirm={() =>
            deleteMutation.mutate(deleteTarget.id, {
              onSuccess: () => setDeleteTarget(null),
            })
          }
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  )
}

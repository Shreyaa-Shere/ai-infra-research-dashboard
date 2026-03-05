import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import ConfirmDialog from '../../components/ConfirmDialog'
import ErrorState from '../../components/ErrorState'
import LoadingSkeleton from '../../components/LoadingSkeleton'
import {
  useDeleteMetricSeries,
  useMetricPoints,
  useMetricSeriesDetail,
  useUpsertMetricPoints,
} from '../../hooks/useMetrics'
import { metricsApi } from '../../lib/api'
import { useAuth } from '../../store/AuthContext'
import MetricSeriesForm from './MetricSeriesForm'

const ENTITY_TYPE_LABELS: Record<string, string> = {
  hardware_product: 'Hardware Product',
  company: 'Company',
  datacenter: 'Datacenter',
}

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between border-b border-gray-100 py-2 text-sm">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-gray-800">{value ?? '—'}</span>
    </div>
  )
}

export default function MetricSeriesDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()

  const { data, isLoading, isError, refetch } = useMetricSeriesDetail(id)
  const { data: points, isLoading: pointsLoading } = useMetricPoints(id, { limit: 100 })
  const deleteMutation = useDeleteMetricSeries()
  const upsertMutation = useUpsertMetricPoints(id ?? '')

  const [showEdit, setShowEdit] = useState(false)
  const [showDelete, setShowDelete] = useState(false)
  const [showAddPoint, setShowAddPoint] = useState(false)
  const [addMode, setAddMode] = useState<'single' | 'bulk'>('single')

  // Single point form
  const [pointDate, setPointDate] = useState('')
  const [pointValue, setPointValue] = useState('')
  const [pointError, setPointError] = useState<string | null>(null)

  // Bulk CSV form
  const [bulkCsv, setBulkCsv] = useState('')
  const [bulkError, setBulkError] = useState<string | null>(null)
  const [bulkSuccess, setBulkSuccess] = useState<string | null>(null)

  const canWrite = user?.role === 'admin' || user?.role === 'analyst'
  const canDelete = user?.role === 'admin'

  if (isLoading) return <LoadingSkeleton rows={6} cols={2} />
  if (isError || !data) return <ErrorState message="Metric series not found." onRetry={() => void refetch()} />

  function handleAddSinglePoint(e: React.FormEvent) {
    e.preventDefault()
    setPointError(null)
    if (!pointDate) { setPointError('Date is required'); return }
    const val = Number(pointValue)
    if (pointValue === '' || isNaN(val)) { setPointError('Valid number required'); return }

    upsertMutation.mutate(
      { points: [{ timestamp: new Date(pointDate).toISOString(), value: val }] },
      {
        onSuccess: () => {
          setPointDate('')
          setPointValue('')
          setShowAddPoint(false)
        },
        onError: (err) => setPointError(err.message),
      }
    )
  }

  function handleBulkImport(e: React.FormEvent) {
    e.preventDefault()
    setBulkError(null)
    setBulkSuccess(null)

    const lines = bulkCsv.trim().split('\n').filter(Boolean)
    if (lines.length === 0) { setBulkError('No data to import'); return }

    const parsed: Array<{ timestamp: string; value: number }> = []
    for (const line of lines) {
      const parts = line.split(',')
      if (parts.length !== 2) { setBulkError(`Invalid line: "${line.trim()}" — expected "YYYY-MM-DD,value"`); return }
      const [datePart, valuePart] = parts
      const ts = new Date(datePart.trim())
      const val = Number(valuePart.trim())
      if (isNaN(ts.getTime())) { setBulkError(`Invalid date: "${datePart.trim()}"`); return }
      if (isNaN(val)) { setBulkError(`Invalid value: "${valuePart.trim()}"`); return }
      parsed.push({ timestamp: ts.toISOString(), value: val })
    }

    upsertMutation.mutate(
      { points: parsed },
      {
        onSuccess: (res) => {
          setBulkSuccess(`Imported ${res.upserted} data point${res.upserted !== 1 ? 's' : ''}.`)
          setBulkCsv('')
        },
        onError: (err) => setBulkError(err.message),
      }
    )
  }

  return (
    <div className="max-w-3xl">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <Link
          to="/metric-series"
          className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
        >
          ← Back to Metric Series
        </Link>
        <div className="flex items-center gap-2">
          <a
            href={metricsApi.exportCsvUrl(data.id)}
            download
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
          >
            Export CSV
          </a>
          {canWrite && (
            <>
              <button
                onClick={() => setShowEdit(true)}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
              >
                Edit
              </button>
              {canDelete && (
                <button
                  onClick={() => setShowDelete(true)}
                  className="rounded-md border border-red-300 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50"
                >
                  Delete
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Metadata */}
      <h1 className="text-2xl font-bold text-gray-900">{data.name}</h1>
      <p className="mt-1 text-sm text-gray-500">
        {ENTITY_TYPE_LABELS[data.entity_type] ?? data.entity_type}
      </p>

      <div className="mt-6 rounded-lg border border-gray-200 p-4">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
          Series Info
        </h2>
        <DetailRow label="Unit" value={data.unit} />
        <DetailRow label="Frequency" value={data.frequency} />
        <DetailRow label="Source" value={data.source} />
        <DetailRow label="Entity ID" value={<span className="font-mono text-xs">{data.entity_id}</span>} />
      </div>

      {/* Data Points */}
      <div className="mt-6">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-400">
            Data Points
          </h2>
          {canWrite && (
            <button
              onClick={() => setShowAddPoint((v) => !v)}
              className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
            >
              {showAddPoint ? 'Cancel' : '+ Add Points'}
            </button>
          )}
        </div>

        {/* Add Points Panel */}
        {showAddPoint && (
          <div className="mb-4 rounded-lg border border-gray-200 p-4">
            {/* Tab switcher */}
            <div className="mb-4 flex gap-2 border-b border-gray-200">
              <button
                type="button"
                onClick={() => setAddMode('single')}
                className={`px-3 py-1.5 text-sm font-medium ${addMode === 'single' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
              >
                Single Point
              </button>
              <button
                type="button"
                onClick={() => setAddMode('bulk')}
                className={`px-3 py-1.5 text-sm font-medium ${addMode === 'bulk' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
              >
                Bulk CSV
              </button>
            </div>

            {addMode === 'single' ? (
              <form onSubmit={handleAddSinglePoint} className="flex items-end gap-3">
                <div>
                  <label htmlFor="pt-date" className="mb-1 block text-sm font-medium text-gray-700">
                    Date
                  </label>
                  <input
                    id="pt-date"
                    type="date"
                    value={pointDate}
                    onChange={(e) => setPointDate(e.target.value)}
                    className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="pt-value" className="mb-1 block text-sm font-medium text-gray-700">
                    Value ({data.unit})
                  </label>
                  <input
                    id="pt-value"
                    type="number"
                    step="any"
                    value={pointValue}
                    onChange={(e) => setPointValue(e.target.value)}
                    className="w-36 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0.0"
                  />
                </div>
                <button
                  type="submit"
                  disabled={upsertMutation.isPending}
                  className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {upsertMutation.isPending ? 'Saving…' : 'Add'}
                </button>
                {pointError && (
                  <p role="alert" className="text-xs text-red-600">{pointError}</p>
                )}
              </form>
            ) : (
              <form onSubmit={handleBulkImport} className="space-y-3">
                <p className="text-xs text-gray-500">
                  One line per data point in format: <code className="font-mono">YYYY-MM-DD,value</code>
                </p>
                <textarea
                  rows={6}
                  value={bulkCsv}
                  onChange={(e) => setBulkCsv(e.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={'2024-01-01,100\n2024-02-01,120\n2024-03-01,115'}
                />
                {bulkError && (
                  <p role="alert" className="text-xs text-red-600">{bulkError}</p>
                )}
                {bulkSuccess && (
                  <p role="status" className="text-xs text-green-600">{bulkSuccess}</p>
                )}
                <button
                  type="submit"
                  disabled={upsertMutation.isPending}
                  className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {upsertMutation.isPending ? 'Importing…' : 'Import'}
                </button>
              </form>
            )}
          </div>
        )}

        {/* Points Table */}
        {pointsLoading ? (
          <LoadingSkeleton rows={4} cols={2} />
        ) : !points || points.length === 0 ? (
          <p className="rounded-lg border border-dashed border-gray-200 py-8 text-center text-sm text-gray-400">
            No data points yet.
          </p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-gray-200">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                <tr>
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4 py-3 text-right">Value ({data.unit})</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {[...points]
                  .sort((a, b) => b.timestamp.localeCompare(a.timestamp))
                  .map((pt) => (
                    <tr key={pt.id} className="hover:bg-gray-50">
                      <td className="px-4 py-2 text-gray-700">
                        {new Date(pt.timestamp).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-2 text-right font-medium text-gray-900">
                        {pt.value.toLocaleString()}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <p className="mt-6 text-xs text-gray-400">
        Created {new Date(data.created_at).toLocaleDateString()}
      </p>

      {showEdit && (
        <MetricSeriesForm initial={data} onClose={() => setShowEdit(false)} />
      )}

      {showDelete && (
        <ConfirmDialog
          title="Delete Metric Series"
          message={`Delete "${data.name}"? All data points will also be deleted. This cannot be undone.`}
          isPending={deleteMutation.isPending}
          onConfirm={() =>
            deleteMutation.mutate(data.id, {
              onSuccess: () => navigate('/metric-series'),
            })
          }
          onCancel={() => setShowDelete(false)}
        />
      )}
    </div>
  )
}

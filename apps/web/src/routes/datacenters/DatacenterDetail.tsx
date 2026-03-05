import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import ConfirmDialog from '../../components/ConfirmDialog'
import ErrorState from '../../components/ErrorState'
import LoadingSkeleton from '../../components/LoadingSkeleton'
import { useDatacenter, useDeleteDatacenter } from '../../hooks/useDatacenters'
import { useMetricSeries } from '../../hooks/useMetrics'
import { useAuth } from '../../store/AuthContext'
import DatacenterForm from './DatacenterForm'

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-green-100 text-green-700',
  planned: 'bg-yellow-100 text-yellow-700',
  retired: 'bg-gray-100 text-gray-500',
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between border-b border-gray-100 py-2 text-sm">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-gray-800">{value ?? '—'}</span>
    </div>
  )
}

export default function DatacenterDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { data, isLoading, isError, refetch } = useDatacenter(id!)
  const { data: seriesData } = useMetricSeries({ entity_type: 'datacenter', entity_id: id, limit: 5 })
  const deleteMutation = useDeleteDatacenter()
  const [showEdit, setShowEdit] = useState(false)
  const [showDelete, setShowDelete] = useState(false)

  const canWrite = user?.role === 'admin' || user?.role === 'analyst'
  const canDelete = user?.role === 'admin'

  if (isLoading) return <LoadingSkeleton rows={5} cols={2} />
  if (isError || !data) return <ErrorState message="Datacenter site not found." onRetry={() => void refetch()} />

  return (
    <div>
      {/* Top bar */}
      <div className="mb-6 flex items-center justify-between">
        <Link
          to="/datacenters"
          className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
        >
          ← Back to Datacenter Sites
        </Link>
        {canWrite && (
          <div className="flex items-center gap-2">
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
          </div>
        )}
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left: main content */}
        <div className="lg:col-span-2">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{data.name}</h1>
            <span
              className={`rounded-full px-3 py-1 text-sm font-medium ${STATUS_COLORS[data.status] ?? 'bg-gray-100 text-gray-700'}`}
            >
              {data.status}
            </span>
          </div>

          <div className="mt-6 rounded-lg border border-gray-200 p-4">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
              Details
            </h2>
            <Row label="Region" value={data.region} />
            <Row
              label="Owner"
              value={
                data.owner_company ? (
                  <Link
                    to={`/companies/${data.owner_company.id}`}
                    className="text-blue-600 hover:underline"
                  >
                    {data.owner_company.name}
                  </Link>
                ) : (
                  '—'
                )
              }
            />
            <Row
              label="Power Capacity"
              value={data.power_mw != null ? `${data.power_mw} MW` : null}
            />
          </div>

          {data.notes && (
            <div className="mt-4 rounded-lg border border-gray-200 p-4">
              <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-gray-400">
                Notes
              </h2>
              <p className="text-sm text-gray-700">{data.notes}</p>
            </div>
          )}

          <p className="mt-6 text-xs text-gray-400">
            Added {new Date(data.created_at).toLocaleDateString()}
          </p>
        </div>

        {/* Right: related metric series */}
        <div className="space-y-4">
          <div className="rounded-lg border border-gray-200 p-4">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
              Metric Series
            </h2>
            {!seriesData || seriesData.items.length === 0 ? (
              <p className="text-sm text-gray-400">No metric series linked.</p>
            ) : (
              <ul className="space-y-2">
                {seriesData.items.map((s) => (
                  <li key={s.id}>
                    <Link
                      to={`/metric-series/${s.id}`}
                      className="block rounded-md p-2 hover:bg-gray-50"
                    >
                      <p className="text-sm font-medium text-gray-800">{s.name}</p>
                      <p className="text-xs text-gray-400">{s.unit} · {s.frequency}</p>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Quick stats */}
          {data.power_mw != null && (
            <div className="rounded-lg border border-gray-200 p-4">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
                Quick Stats
              </h2>
              <div className="text-center">
                <p className="text-3xl font-bold text-gray-900">{data.power_mw}</p>
                <p className="text-xs text-gray-400">MW capacity</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {showEdit && (
        <DatacenterForm initial={data} onClose={() => setShowEdit(false)} />
      )}

      {showDelete && (
        <ConfirmDialog
          title="Delete Datacenter Site"
          message={`Delete "${data.name}"? This cannot be undone.`}
          isPending={deleteMutation.isPending}
          onConfirm={() =>
            deleteMutation.mutate(data.id, {
              onSuccess: () => navigate('/datacenters'),
            })
          }
          onCancel={() => setShowDelete(false)}
        />
      )}
    </div>
  )
}

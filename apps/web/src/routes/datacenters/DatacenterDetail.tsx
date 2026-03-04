import { Link, useParams } from 'react-router-dom'
import LoadingSkeleton from '../../components/LoadingSkeleton'
import { useDatacenter } from '../../hooks/useDatacenters'

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
  const { data, isLoading, isError } = useDatacenter(id!)

  if (isLoading) return <LoadingSkeleton rows={5} cols={2} />
  if (isError || !data) return <p className="text-sm text-red-600">Datacenter site not found.</p>

  return (
    <div className="max-w-2xl">
      <Link
        to="/datacenters"
        className="mb-4 inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
      >
        ← Back to Datacenter Sites
      </Link>

      <div className="mt-4 flex items-center gap-3">
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
  )
}

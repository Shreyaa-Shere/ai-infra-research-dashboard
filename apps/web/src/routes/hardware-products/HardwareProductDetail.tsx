import { useParams, Link } from 'react-router-dom'
import { useHardwareProduct } from '../../hooks/useHardwareProducts'
import LoadingSkeleton from '../../components/LoadingSkeleton'

function SpecRow({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="flex justify-between border-b border-gray-100 py-2 text-sm">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-gray-800">{value ?? '—'}</span>
    </div>
  )
}

export default function HardwareProductDetail() {
  const { id } = useParams<{ id: string }>()
  const { data, isLoading, isError } = useHardwareProduct(id!)

  if (isLoading) return <LoadingSkeleton rows={6} cols={2} />
  if (isError || !data)
    return <p className="text-sm text-red-600">Hardware product not found.</p>

  return (
    <div className="max-w-2xl">
      <Link
        to="/hardware-products"
        className="mb-4 inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
      >
        ← Back to Hardware Products
      </Link>

      <div className="mt-4 flex items-center gap-3">
        <h1 className="text-2xl font-bold text-gray-900">{data.name}</h1>
        <span className="rounded-full bg-purple-100 px-3 py-1 text-sm font-medium text-purple-700">
          {data.category}
        </span>
      </div>
      <p className="mt-1 text-sm text-gray-500">{data.vendor}</p>

      <div className="mt-6 rounded-lg border border-gray-200 p-4">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
          Specifications
        </h2>
        <SpecRow label="Memory" value={data.memory_gb != null ? `${data.memory_gb} GB` : null} />
        <SpecRow label="TDP" value={data.tdp_watts != null ? `${data.tdp_watts} W` : null} />
        <SpecRow label="Process Node" value={data.process_node} />
        <SpecRow label="Release Date" value={data.release_date} />
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

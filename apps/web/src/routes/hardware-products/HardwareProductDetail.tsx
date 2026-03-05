import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import LoadingSkeleton from '../../components/LoadingSkeleton'
import ErrorState from '../../components/ErrorState'
import ConfirmDialog from '../../components/ConfirmDialog'
import HardwareProductForm from './HardwareProductForm'
import { useHardwareProduct, useDeleteHardwareProduct } from '../../hooks/useHardwareProducts'
import { useAuth } from '../../store/AuthContext'

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
  const navigate = useNavigate()
  const { user } = useAuth()
  const { data, isLoading, isError, refetch } = useHardwareProduct(id!)
  const deleteMutation = useDeleteHardwareProduct()
  const [showEdit, setShowEdit] = useState(false)
  const [showDelete, setShowDelete] = useState(false)

  const canWrite = user?.role === 'admin' || user?.role === 'analyst'
  const canDelete = user?.role === 'admin'

  if (isLoading) return <LoadingSkeleton rows={6} cols={2} />
  if (isError || !data) return <ErrorState message="Hardware product not found." onRetry={() => void refetch()} />

  return (
    <div className="max-w-2xl">
      <div className="mb-4 flex items-center justify-between">
        <Link
          to="/hardware-products"
          className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
        >
          ← Back to Hardware Products
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
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-gray-400">Notes</h2>
          <p className="text-sm text-gray-700">{data.notes}</p>
        </div>
      )}

      <p className="mt-6 text-xs text-gray-400">
        Added {new Date(data.created_at).toLocaleDateString()}
      </p>

      {showEdit && (
        <HardwareProductForm initial={data} onClose={() => setShowEdit(false)} />
      )}

      {showDelete && (
        <ConfirmDialog
          title="Delete Hardware Product"
          message={`Delete "${data.name}"? This cannot be undone.`}
          isPending={deleteMutation.isPending}
          onConfirm={() =>
            deleteMutation.mutate(data.id, {
              onSuccess: () => navigate('/hardware-products'),
            })
          }
          onCancel={() => setShowDelete(false)}
        />
      )}
    </div>
  )
}

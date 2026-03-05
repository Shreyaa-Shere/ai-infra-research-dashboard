import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DataTable, { type Column } from '../../components/DataTable'
import EmptyState from '../../components/EmptyState'
import ErrorState from '../../components/ErrorState'
import LoadingSkeleton from '../../components/LoadingSkeleton'
import PaginationControls from '../../components/PaginationControls'
import ConfirmDialog from '../../components/ConfirmDialog'
import HardwareProductForm from './HardwareProductForm'
import { useHardwareProducts, useDeleteHardwareProduct } from '../../hooks/useHardwareProducts'
import { useAuth } from '../../store/AuthContext'
import type { HardwareProduct } from '../../lib/entities'

const LIMIT = 20

export default function HardwareProductList() {
  const [offset, setOffset] = useState(0)
  const [showForm, setShowForm] = useState(false)
  const [editTarget, setEditTarget] = useState<HardwareProduct | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<HardwareProduct | null>(null)
  const navigate = useNavigate()
  const { user } = useAuth()

  const canWrite = user?.role === 'admin' || user?.role === 'analyst'
  const canDelete = user?.role === 'admin'

  const { data, isLoading, isError, refetch } = useHardwareProducts({ limit: LIMIT, offset })
  const deleteMutation = useDeleteHardwareProduct()

  const columns: Column<HardwareProduct>[] = [
    { key: 'name', header: 'Name' },
    { key: 'vendor', header: 'Vendor' },
    {
      key: 'category',
      header: 'Category',
      render: (row) => (
        <span className="rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-700">
          {row.category}
        </span>
      ),
    },
    {
      key: 'release_date',
      header: 'Release Date',
      render: (row) => row.release_date ?? '—',
    },
    {
      key: 'memory_gb',
      header: 'Memory (GB)',
      render: (row) => (row.memory_gb != null ? `${row.memory_gb} GB` : '—'),
    },
    ...(canWrite
      ? [
          {
            key: 'actions' as keyof HardwareProduct,
            header: '',
            render: (row: HardwareProduct) => (
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
        <h1 className="text-xl font-semibold text-gray-900">Hardware Products</h1>
        {canWrite && (
          <button
            onClick={() => setShowForm(true)}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            + Add Product
          </button>
        )}
      </div>

      {isLoading && <LoadingSkeleton rows={5} cols={5} />}
      {isError && <ErrorState message="Failed to load hardware products." onRetry={() => void refetch()} />}

      {!isLoading && !isError && data && (
        <>
          {data.items.length === 0 ? (
            <EmptyState message="No hardware products found." />
          ) : (
            <DataTable
              columns={columns}
              data={data.items}
              onRowClick={(row) => navigate(`/hardware-products/${row.id}`)}
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
        <HardwareProductForm
          initial={editTarget ?? undefined}
          onClose={() => { setShowForm(false); setEditTarget(null) }}
        />
      )}

      {deleteTarget && (
        <ConfirmDialog
          title="Delete Hardware Product"
          message={`Delete "${deleteTarget.name}"? This cannot be undone.`}
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

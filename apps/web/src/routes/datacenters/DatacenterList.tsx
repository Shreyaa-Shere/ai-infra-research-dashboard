import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ConfirmDialog from '../../components/ConfirmDialog'
import DataTable, { type Column } from '../../components/DataTable'
import EmptyState from '../../components/EmptyState'
import ErrorState from '../../components/ErrorState'
import LoadingSkeleton from '../../components/LoadingSkeleton'
import PaginationControls from '../../components/PaginationControls'
import { useDatacenters, useDeleteDatacenter } from '../../hooks/useDatacenters'
import { useAuth } from '../../store/AuthContext'
import type { DatacenterSite } from '../../lib/entities'
import DatacenterForm from './DatacenterForm'

const LIMIT = 20

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-green-100 text-green-700',
  planned: 'bg-yellow-100 text-yellow-700',
  retired: 'bg-gray-100 text-gray-500',
}

export default function DatacenterList() {
  const [offset, setOffset] = useState(0)
  const [showForm, setShowForm] = useState(false)
  const [editTarget, setEditTarget] = useState<DatacenterSite | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<DatacenterSite | null>(null)
  const navigate = useNavigate()
  const { user } = useAuth()

  const canWrite = user?.role === 'admin' || user?.role === 'analyst'
  const canDelete = user?.role === 'admin'

  const { data, isLoading, isError, refetch } = useDatacenters({ limit: LIMIT, offset })
  const deleteMutation = useDeleteDatacenter()

  const columns: Column<DatacenterSite>[] = [
    { key: 'name', header: 'Name' },
    { key: 'region', header: 'Region' },
    {
      key: 'owner_company',
      header: 'Owner',
      render: (row) => row.owner_company?.name ?? '—',
    },
    {
      key: 'power_mw',
      header: 'Power (MW)',
      render: (row) => (row.power_mw != null ? `${row.power_mw} MW` : '—'),
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => (
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[row.status] ?? 'bg-gray-100 text-gray-700'}`}
        >
          {row.status}
        </span>
      ),
    },
    ...(canWrite
      ? [
          {
            key: 'actions' as keyof DatacenterSite,
            header: '',
            render: (row: DatacenterSite) => (
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
        <h1 className="text-xl font-semibold text-gray-900">Datacenter Sites</h1>
        {canWrite && (
          <button
            onClick={() => setShowForm(true)}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            + Add Datacenter
          </button>
        )}
      </div>

      {isLoading && <LoadingSkeleton rows={5} cols={5} />}
      {isError && <ErrorState message="Failed to load datacenter sites." onRetry={() => void refetch()} />}

      {!isLoading && !isError && data && (
        <>
          {data.items.length === 0 ? (
            <EmptyState message="No datacenter sites found." />
          ) : (
            <DataTable
              columns={columns}
              data={data.items}
              onRowClick={(row) => navigate(`/datacenters/${row.id}`)}
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
        <DatacenterForm
          initial={editTarget ?? undefined}
          onClose={() => { setShowForm(false); setEditTarget(null) }}
        />
      )}

      {deleteTarget && (
        <ConfirmDialog
          title="Delete Datacenter Site"
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

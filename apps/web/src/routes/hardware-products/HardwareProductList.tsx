import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DataTable, { type Column } from '../../components/DataTable'
import EmptyState from '../../components/EmptyState'
import LoadingSkeleton from '../../components/LoadingSkeleton'
import PaginationControls from '../../components/PaginationControls'
import { useHardwareProducts } from '../../hooks/useHardwareProducts'
import type { HardwareProduct } from '../../lib/entities'

const LIMIT = 20

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
]

export default function HardwareProductList() {
  const [offset, setOffset] = useState(0)
  const navigate = useNavigate()
  const { data, isLoading, isError } = useHardwareProducts({ limit: LIMIT, offset })

  return (
    <div>
      <h1 className="mb-6 text-xl font-semibold text-gray-900">Hardware Products</h1>

      {isLoading && <LoadingSkeleton rows={5} cols={5} />}

      {isError && (
        <p className="text-sm text-red-600">Failed to load hardware products.</p>
      )}

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
    </div>
  )
}

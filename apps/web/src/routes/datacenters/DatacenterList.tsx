import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DataTable, { type Column } from '../../components/DataTable'
import EmptyState from '../../components/EmptyState'
import LoadingSkeleton from '../../components/LoadingSkeleton'
import PaginationControls from '../../components/PaginationControls'
import { useDatacenters } from '../../hooks/useDatacenters'
import type { DatacenterSite } from '../../lib/entities'

const LIMIT = 20

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-green-100 text-green-700',
  planned: 'bg-yellow-100 text-yellow-700',
  retired: 'bg-gray-100 text-gray-500',
}

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
]

export default function DatacenterList() {
  const [offset, setOffset] = useState(0)
  const navigate = useNavigate()
  const { data, isLoading, isError } = useDatacenters({ limit: LIMIT, offset })

  return (
    <div>
      <h1 className="mb-6 text-xl font-semibold text-gray-900">Datacenter Sites</h1>

      {isLoading && <LoadingSkeleton rows={5} cols={5} />}

      {isError && <p className="text-sm text-red-600">Failed to load datacenter sites.</p>}

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
    </div>
  )
}

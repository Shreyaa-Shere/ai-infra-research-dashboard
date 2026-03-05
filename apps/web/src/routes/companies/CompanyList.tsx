import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DataTable, { type Column } from '../../components/DataTable'
import EmptyState from '../../components/EmptyState'
import ErrorState from '../../components/ErrorState'
import LoadingSkeleton from '../../components/LoadingSkeleton'
import PaginationControls from '../../components/PaginationControls'
import { useCompanies } from '../../hooks/useCompanies'
import type { Company } from '../../lib/entities'

const LIMIT = 20

const TYPE_COLORS: Record<string, string> = {
  fab: 'bg-blue-100 text-blue-700',
  idm: 'bg-indigo-100 text-indigo-700',
  cloud: 'bg-sky-100 text-sky-700',
  vendor: 'bg-green-100 text-green-700',
  research: 'bg-orange-100 text-orange-700',
}

const columns: Column<Company>[] = [
  { key: 'name', header: 'Name' },
  {
    key: 'type',
    header: 'Type',
    render: (row) => (
      <span
        className={`rounded-full px-2 py-0.5 text-xs font-medium ${TYPE_COLORS[row.type] ?? 'bg-gray-100 text-gray-700'}`}
      >
        {row.type}
      </span>
    ),
  },
  { key: 'region', header: 'Region' },
  {
    key: 'website',
    header: 'Website',
    render: (row) =>
      row.website ? (
        <a
          href={row.website}
          target="_blank"
          rel="noreferrer"
          className="text-blue-600 hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          {row.website.replace(/^https?:\/\//, '')}
        </a>
      ) : (
        '—'
      ),
  },
]

export default function CompanyList() {
  const [offset, setOffset] = useState(0)
  const navigate = useNavigate()
  const { data, isLoading, isError, refetch } = useCompanies({ limit: LIMIT, offset })

  return (
    <div>
      <h1 className="mb-6 text-xl font-semibold text-gray-900">Companies</h1>

      {isLoading && <LoadingSkeleton rows={5} cols={4} />}

      {isError && <ErrorState message="Failed to load companies." onRetry={() => void refetch()} />}

      {!isLoading && !isError && data && (
        <>
          {data.items.length === 0 ? (
            <EmptyState message="No companies found." />
          ) : (
            <DataTable
              columns={columns}
              data={data.items}
              onRowClick={(row) => navigate(`/companies/${row.id}`)}
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

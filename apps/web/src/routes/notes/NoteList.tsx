import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DataTable, { type Column } from '../../components/DataTable'
import EmptyState from '../../components/EmptyState'
import LoadingSkeleton from '../../components/LoadingSkeleton'
import PaginationControls from '../../components/PaginationControls'
import { useNotes } from '../../hooks/useNotes'
import { useAuth } from '../../store/AuthContext'
import type { NoteStatus, ResearchNote } from '../../lib/entities'

const LIMIT = 20

const STATUS_COLORS: Record<NoteStatus, string> = {
  draft: 'bg-gray-100 text-gray-700',
  review: 'bg-yellow-100 text-yellow-700',
  published: 'bg-green-100 text-green-700',
}

const STATUS_OPTIONS: Array<{ label: string; value: NoteStatus | '' }> = [
  { label: 'All statuses', value: '' },
  { label: 'Draft', value: 'draft' },
  { label: 'Review', value: 'review' },
  { label: 'Published', value: 'published' },
]

export default function NoteList() {
  const [offset, setOffset] = useState(0)
  const [status, setStatus] = useState<NoteStatus | ''>('')
  const [tag, setTag] = useState('')
  const [q, setQ] = useState('')
  const [tagInput, setTagInput] = useState('')
  const [qInput, setQInput] = useState('')
  const navigate = useNavigate()
  const { user } = useAuth()

  const { data, isLoading, isError } = useNotes({
    limit: LIMIT,
    offset,
    status: status || undefined,
    tag: tag || undefined,
    q: q || undefined,
  })

  const canCreate = user?.role === 'admin' || user?.role === 'analyst'

  const columns: Column<ResearchNote>[] = [
    { key: 'title', header: 'Title' },
    {
      key: 'status',
      header: 'Status',
      render: (row) => (
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[row.status]}`}
        >
          {row.status}
        </span>
      ),
    },
    {
      key: 'tags',
      header: 'Tags',
      render: (row) =>
        row.tags.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {row.tags.map((t) => (
              <span
                key={t}
                className="rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-700"
              >
                {t}
              </span>
            ))}
          </div>
        ) : (
          '—'
        ),
    },
    {
      key: 'author',
      header: 'Author',
      render: (row) => (
        <span className="text-sm text-gray-600">{row.author.email}</span>
      ),
    },
    {
      key: 'updated_at',
      header: 'Updated',
      render: (row) => (
        <span className="text-sm text-gray-500">
          {new Date(row.updated_at).toLocaleDateString()}
        </span>
      ),
    },
  ]

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    setQ(qInput)
    setTag(tagInput)
    setOffset(0)
  }

  function handleReset() {
    setStatus('')
    setTag('')
    setQ('')
    setTagInput('')
    setQInput('')
    setOffset(0)
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Research Notes</h1>
        {canCreate && (
          <button
            onClick={() => navigate('/notes/new')}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            + New Note
          </button>
        )}
      </div>

      {/* Filters */}
      <form onSubmit={handleSearch} className="mb-4 flex flex-wrap items-end gap-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">Status</label>
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value as NoteStatus | '')
              setOffset(0)
            }}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {STATUS_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">Tag</label>
          <input
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            placeholder="e.g. gpu"
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">Search</label>
          <input
            value={qInput}
            onChange={(e) => setQInput(e.target.value)}
            placeholder="title or body..."
            className="w-52 rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          type="submit"
          className="rounded-md bg-gray-800 px-3 py-1.5 text-sm text-white hover:bg-gray-900"
        >
          Search
        </button>
        <button
          type="button"
          onClick={handleReset}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
        >
          Reset
        </button>
      </form>

      {isLoading && <LoadingSkeleton rows={5} cols={5} />}

      {isError && (
        <p className="text-sm text-red-600">Failed to load research notes.</p>
      )}

      {!isLoading && !isError && data && (
        <>
          {data.items.length === 0 ? (
            <EmptyState message="No research notes found." />
          ) : (
            <DataTable
              columns={columns}
              data={data.items}
              onRowClick={(row) => navigate(`/notes/${row.id}`)}
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

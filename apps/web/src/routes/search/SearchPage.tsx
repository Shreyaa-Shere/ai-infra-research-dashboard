import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import LoadingSkeleton from '../../components/LoadingSkeleton'
import { useSearchResults } from '../../hooks/useSearch'
import { useAuth } from '../../store/AuthContext'
import type { NoteSearchResult, NoteStatus, SearchResult, SourceSearchResult } from '../../lib/entities'

type TabType = 'all' | 'note' | 'source'

const TABS: { value: TabType; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'note', label: 'Notes' },
  { value: 'source', label: 'Sources' },
]

const STATUS_OPTIONS = ['draft', 'review', 'published']
const SOURCE_TYPE_OPTIONS = ['rss', 'json', 'file']

function NoteResultCard({ item }: { item: NoteSearchResult }) {
  return (
    <Link
      to={`/notes/${item.id}`}
      className="block rounded-lg border border-gray-200 p-4 hover:border-blue-300 hover:shadow-sm transition-all"
    >
      <div className="flex items-start gap-2">
        <span className="mt-0.5 shrink-0 rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
          Note
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="font-medium text-gray-900 truncate">{item.title}</h3>
          {item.snippet && (
            <p
              className="mt-1 text-sm text-gray-600 line-clamp-2"
              dangerouslySetInnerHTML={{ __html: item.snippet }}
            />
          )}
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-gray-500">
            <span
              className={`rounded-full px-2 py-0.5 font-medium ${
                item.status === 'published'
                  ? 'bg-green-100 text-green-700'
                  : item.status === 'review'
                  ? 'bg-yellow-100 text-yellow-700'
                  : 'bg-gray-100 text-gray-600'
              }`}
            >
              {item.status}
            </span>
            {item.tags.map((t) => (
              <span key={t} className="rounded-full bg-gray-100 px-2 py-0.5">
                #{t}
              </span>
            ))}
            {item.published_at && (
              <span>{new Date(item.published_at).toLocaleDateString()}</span>
            )}
          </div>
        </div>
      </div>
    </Link>
  )
}

function SourceResultCard({ item }: { item: SourceSearchResult }) {
  return (
    <Link
      to={`/sources/${item.id}`}
      className="block rounded-lg border border-gray-200 p-4 hover:border-blue-300 hover:shadow-sm transition-all"
    >
      <div className="flex items-start gap-2">
        <span className="mt-0.5 shrink-0 rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-700">
          Source
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="font-medium text-gray-900 truncate">{item.title}</h3>
          {item.snippet && (
            <p
              className="mt-1 text-sm text-gray-600 line-clamp-2"
              dangerouslySetInnerHTML={{ __html: item.snippet }}
            />
          )}
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-gray-500">
            <span className="rounded-full bg-gray-100 px-2 py-0.5">{item.source_type}</span>
            <span>{item.source_name}</span>
            {item.published_at && (
              <span>{new Date(item.published_at).toLocaleDateString()}</span>
            )}
          </div>
        </div>
      </div>
    </Link>
  )
}

function ResultCard({ item }: { item: SearchResult }) {
  if (item.type === 'note') return <NoteResultCard item={item} />
  return <SourceResultCard item={item} />
}

export default function SearchPage() {
  const { user } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()

  const [inputValue, setInputValue] = useState(searchParams.get('q') ?? '')
  const [activeTab, setActiveTab] = useState<TabType>(
    (searchParams.get('type') as TabType) ?? 'all'
  )
  const [status, setStatus] = useState<NoteStatus | ''>((searchParams.get('status') ?? '') as NoteStatus | '')
  const [sourceType, setSourceType] = useState(searchParams.get('source_type') ?? '')
  const [showFilters, setShowFilters] = useState(false)
  const [page, setPage] = useState(0)

  const limit = 20
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Sync input from URL on mount
  const committedQ = searchParams.get('q') ?? ''

  const searchQueryParams = committedQ.trim()
    ? {
        q: committedQ,
        type: activeTab,
        limit,
        offset: page * limit,
        status: status || undefined,
        source_type: (sourceType || undefined) as 'rss' | 'json' | 'file' | undefined,
      }
    : null

  const { data, isLoading, isError } = useSearchResults(searchQueryParams)

  function commitSearch(q: string) {
    const p = new URLSearchParams()
    if (q.trim()) p.set('q', q.trim())
    if (activeTab !== 'all') p.set('type', activeTab)
    if (status) p.set('status', status)
    if (sourceType) p.set('source_type', sourceType)
    setSearchParams(p)
    setPage(0)
  }

  function handleInput(value: string) {
    setInputValue(value)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => commitSearch(value), 400)
  }

  function handleTabChange(tab: TabType) {
    setActiveTab(tab)
    setPage(0)
    const p = new URLSearchParams(searchParams)
    p.set('type', tab)
    p.delete('offset')
    setSearchParams(p)
  }

  function handleFilterApply() {
    commitSearch(inputValue)
  }

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [])

  const totalPages = data ? Math.ceil(data.total / limit) : 0

  return (
    <div className="max-w-3xl">
      <h1 className="text-xl font-bold text-gray-900 mb-4">Search</h1>

      {/* Search input */}
      <div className="relative mb-4">
        <input
          type="search"
          value={inputValue}
          onChange={(e) => handleInput(e.target.value)}
          placeholder="Search notes and sources…"
          className="w-full rounded-lg border border-gray-300 px-4 py-2.5 pr-10 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          autoFocus
        />
        {isLoading && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
            …
          </span>
        )}
      </div>

      {/* Tabs + filter toggle */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex gap-1">
          {TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => handleTabChange(tab.value)}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                activeTab === tab.value
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {tab.label}
              {data && tab.value === activeTab && (
                <span className="ml-1.5 text-xs opacity-75">({data.total})</span>
              )}
            </button>
          ))}
        </div>
        <button
          onClick={() => setShowFilters((v) => !v)}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          {showFilters ? '▲ Filters' : '▼ Filters'}
        </button>
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="mb-4 rounded-lg border border-gray-200 p-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {(activeTab === 'all' || activeTab === 'note') && (
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">
                  Note Status
                </label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="w-full rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
                >
                  <option value="">Any</option>
                  {/* Viewers can only see published, but the filter is still useful for analyst+ */}
                  {user?.role !== 'viewer'
                    ? STATUS_OPTIONS.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))
                    : <option value="published">published</option>}
                </select>
              </div>
            )}
            {(activeTab === 'all' || activeTab === 'source') && (
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">
                  Source Type
                </label>
                <select
                  value={sourceType}
                  onChange={(e) => setSourceType(e.target.value)}
                  className="w-full rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
                >
                  <option value="">Any</option>
                  {SOURCE_TYPE_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
          <button
            onClick={handleFilterApply}
            className="mt-3 rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
          >
            Apply Filters
          </button>
        </div>
      )}

      {/* Results */}
      {!committedQ.trim() && (
        <p className="text-sm text-gray-500 text-center py-12">
          Enter a search query to find research notes and source documents.
        </p>
      )}

      {committedQ.trim() && isLoading && <LoadingSkeleton rows={5} cols={1} />}

      {committedQ.trim() && isError && (
        <p className="text-sm text-red-600 py-4">Search failed. Please try again.</p>
      )}

      {committedQ.trim() && !isLoading && !isError && data && data.items.length === 0 && (
        <div className="py-12 text-center">
          <p className="text-sm text-gray-500">
            No results found for <strong>"{data.query}"</strong>.
          </p>
        </div>
      )}

      {data && data.items.length > 0 && (
        <>
          <div className="space-y-3">
            {data.items.map((item) => (
              <ResultCard key={`${item.type}-${item.id}`} item={item} />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-between text-sm text-gray-600">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="rounded-md border border-gray-300 px-3 py-1.5 hover:bg-gray-50 disabled:opacity-40"
              >
                ← Previous
              </button>
              <span>
                Page {page + 1} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="rounded-md border border-gray-300 px-3 py-1.5 hover:bg-gray-50 disabled:opacity-40"
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../../store/AuthContext'
import { auditApi } from '../../lib/api'
import ErrorState from '../../components/ErrorState'
import PaginationControls from '../../components/PaginationControls'
import type { AuditLogEntry } from '../../lib/entities'

const LIMIT = 25

const ACTION_COLORS: Record<string, string> = {
  // Note actions
  'note.created': 'bg-blue-100 text-blue-700',
  'note.updated': 'bg-yellow-100 text-yellow-700',
  'note.published': 'bg-green-100 text-green-700',
  'note.deleted': 'bg-red-100 text-red-700',
  // User actions
  'user.invited': 'bg-purple-100 text-purple-700',
  'user.invite_accepted': 'bg-teal-100 text-teal-700',
  'user.role_changed': 'bg-orange-100 text-orange-700',
  'user.deactivated': 'bg-red-100 text-red-600',
  'user.activated': 'bg-green-100 text-green-700',
}

const ENTITY_ROUTES: Record<string, string> = {
  research_note: '/notes',
  hardware_product: '/hardware-products',
  company: '/companies',
  datacenter: '/datacenters',
}

function parseMetaLabel(entry: AuditLogEntry): string | null {
  if (!entry.meta_json) return null
  try {
    const meta = JSON.parse(entry.meta_json) as Record<string, unknown>
    // Note entries store title
    if (typeof meta.title === 'string') return meta.title
    // User entries store email
    if (typeof meta.email === 'string') return meta.email
    if (typeof meta.name === 'string') return meta.name
  } catch {
    // ignore parse errors
  }
  return null
}

function EntityLink({ entry }: { entry: AuditLogEntry }) {
  const route = ENTITY_ROUTES[entry.entity_type]
  const label = parseMetaLabel(entry) ?? entry.entity_id?.slice(0, 8) ?? '—'
  // Deleted entities can't be linked (they no longer exist)
  if (route && entry.entity_id && !entry.action.endsWith('.deleted')) {
    return (
      <Link
        to={`${route}/${entry.entity_id}`}
        className="text-blue-600 hover:underline text-sm font-medium"
      >
        {label}
      </Link>
    )
  }
  return (
    <span className={`text-sm font-medium ${entry.action.endsWith('.deleted') ? 'text-gray-400 line-through' : 'text-gray-700'}`}>
      {label}
    </span>
  )
}

export default function AuditLogPage() {
  const { accessToken } = useAuth()
  const [offset, setOffset] = useState(0)

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['audit-log', offset],
    queryFn: () => auditApi.list(accessToken!, { limit: LIMIT, offset }),
    enabled: !!accessToken,
    refetchInterval: 30_000,
  })

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Audit Log</h1>
          <p className="mt-1 text-sm text-gray-500">
            All create, update, publish, and delete events — auto-refreshes every 30 s
          </p>
        </div>
        <button
          onClick={() => void refetch()}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
        >
          Refresh
        </button>
      </div>

      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-12 animate-pulse rounded-md bg-gray-100" />
          ))}
        </div>
      )}

      {error && (
        <ErrorState message="Failed to load audit log." onRetry={() => void refetch()} />
      )}

      {!isLoading && !error && data && (
        <>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                <tr>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Entity</th>
                  <th className="px-4 py-3">Actor</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.items.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                      No audit entries yet.
                    </td>
                  </tr>
                ) : (
                  data.items.map((entry: AuditLogEntry) => (
                    <tr key={entry.id} className="hover:bg-gray-50">
                      <td className="whitespace-nowrap px-4 py-3 text-gray-500">
                        {new Date(entry.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                            ACTION_COLORS[entry.action] ?? 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {entry.action}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-col">
                          <EntityLink entry={entry} />
                          <span className="mt-0.5 text-xs text-gray-400">
                            {entry.entity_type.replace(/_/g, ' ')}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {entry.actor_user_id ? (
                          <span
                            className="inline-block rounded bg-gray-100 px-1.5 py-0.5 font-mono text-xs text-gray-600"
                            title={entry.actor_user_id}
                          >
                            {entry.actor_user_id.slice(0, 8)}…
                          </span>
                        ) : (
                          <span className="text-xs italic text-gray-400">system</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

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

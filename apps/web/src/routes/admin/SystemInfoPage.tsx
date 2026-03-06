import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../../store/AuthContext'
import { systemApi } from '../../lib/api'
import ErrorState from '../../components/ErrorState'

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span
      className={`inline-block h-2.5 w-2.5 rounded-full ${ok ? 'bg-green-500' : 'bg-red-500'}`}
      aria-label={ok ? 'connected' : 'disconnected'}
    />
  )
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-gray-100 py-3 text-sm">
      <span className="font-medium text-gray-500">{label}</span>
      <span className="text-gray-900">{value}</span>
    </div>
  )
}

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  const parts: string[] = []
  if (d > 0) parts.push(`${d}d`)
  if (h > 0) parts.push(`${h}h`)
  if (m > 0) parts.push(`${m}m`)
  parts.push(`${s}s`)
  return parts.join(' ')
}

export default function SystemInfoPage() {
  const { accessToken } = useAuth()

  const { data, isLoading, error, refetch, dataUpdatedAt } = useQuery({
    queryKey: ['system-info'],
    queryFn: () => systemApi.info(accessToken!),
    enabled: !!accessToken,
    refetchInterval: 30_000,
  })

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">System Info</h1>
          <p className="mt-1 text-sm text-gray-500">
            Live service health and build metadata — auto-refreshes every 30 s
          </p>
        </div>
        <button
          onClick={() => void refetch()}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
        >
          Refresh now
        </button>
      </div>

      {isLoading && (
        <div className="space-y-3 rounded-lg border border-gray-200 p-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-8 animate-pulse rounded bg-gray-100" />
          ))}
        </div>
      )}

      {error && (
        <ErrorState message="Failed to load system info." onRetry={() => void refetch()} />
      )}

      {!isLoading && !error && data && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Build info */}
          <div className="rounded-lg border border-gray-200 p-4">
            <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-400">
              Build
            </h2>
            <InfoRow label="Version" value={data.version} />
            <InfoRow
              label="Git SHA"
              value={
                <code className="rounded bg-gray-100 px-1.5 py-0.5 text-xs font-mono text-gray-700">
                  {data.git_sha}
                </code>
              }
            />
            <InfoRow
              label="Environment"
              value={
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    data.environment === 'production'
                      ? 'bg-red-100 text-red-700'
                      : data.environment === 'staging'
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-blue-100 text-blue-700'
                  }`}
                >
                  {data.environment}
                </span>
              }
            />
            <InfoRow label="Uptime" value={formatUptime(data.uptime_seconds)} />
          </div>

          {/* Service health */}
          <div className="rounded-lg border border-gray-200 p-4">
            <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-400">
              Services
            </h2>
            <InfoRow
              label="PostgreSQL"
              value={
                <div className="flex items-center gap-2">
                  <StatusDot ok={data.db_connected} />
                  <span className={data.db_connected ? 'text-green-700' : 'text-red-700'}>
                    {data.db_connected ? 'Connected' : 'Unreachable'}
                  </span>
                </div>
              }
            />
            <InfoRow
              label="Redis"
              value={
                <div className="flex items-center gap-2">
                  <StatusDot ok={data.redis_connected} />
                  <span className={data.redis_connected ? 'text-green-700' : 'text-red-700'}>
                    {data.redis_connected ? 'Connected' : 'Unreachable'}
                  </span>
                </div>
              }
            />
            <div className="mt-4 border-t border-gray-100 pt-3">
              <InfoRow
                label="Overall status"
                value={
                  data.db_connected && data.redis_connected ? (
                    <span className="flex items-center gap-1.5 text-green-700 font-medium">
                      <StatusDot ok={true} />
                      All systems operational
                    </span>
                  ) : (
                    <span className="flex items-center gap-1.5 text-red-700 font-medium">
                      <StatusDot ok={false} />
                      Degraded
                    </span>
                  )
                }
              />
            </div>
          </div>

          {/* Last checked */}
          {dataUpdatedAt > 0 && (
            <p className="col-span-full text-xs text-gray-400">
              Last checked: {new Date(dataUpdatedAt).toLocaleTimeString()}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

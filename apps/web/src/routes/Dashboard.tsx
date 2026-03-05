import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { useMetricsOverview } from '../hooks/useMetrics'
import { useAuth } from '../store/AuthContext'
import ErrorState from '../components/ErrorState'
import type { ChartSeries, KPIBlock } from '../lib/entities'

const ROLE_BADGE: Record<string, string> = {
  admin: 'bg-red-100 text-red-700',
  analyst: 'bg-blue-100 text-blue-700',
  viewer: 'bg-gray-100 text-gray-600',
}

// Palette for chart lines / bars
const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6']

function KPICard({ kpi }: { kpi: KPIBlock }) {
  return (
    <div data-testid="kpi-card" className="rounded-xl border border-gray-200 bg-white px-5 py-4 shadow-sm">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide truncate">
        {kpi.label}
      </p>
      <p className="mt-1 text-2xl font-bold text-gray-900">
        {typeof kpi.value === 'number' ? kpi.value.toLocaleString() : kpi.value}
        {kpi.unit && (
          <span className="ml-1 text-sm font-normal text-gray-400">{kpi.unit}</span>
        )}
      </p>
      {kpi.change_pct != null && (
        <p
          className={`mt-1 text-xs font-medium ${
            kpi.change_pct >= 0 ? 'text-green-600' : 'text-red-500'
          }`}
        >
          {kpi.change_pct >= 0 ? '+' : ''}
          {kpi.change_pct.toFixed(1)}% vs prev period
        </p>
      )}
    </div>
  )
}

function MetricChart({ series, index }: { series: ChartSeries; index: number }) {
  const color = COLORS[index % COLORS.length]
  // DC capacity series use BarChart; others use LineChart
  const isBar = series.name.toLowerCase().includes('capacity') ||
                series.name.toLowerCase().includes('power') ||
                series.name.toLowerCase().includes('dc')

  return (
    <div className="rounded-xl border border-gray-200 bg-white px-5 pt-4 pb-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-800 truncate">{series.name}</h3>
        <span className="text-xs text-gray-400">{series.unit}</span>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        {isBar ? (
          <BarChart data={series.data} margin={{ top: 0, right: 8, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 10, fill: '#9ca3af' }}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
              formatter={(v: number) => [v.toLocaleString(), series.unit]}
            />
            <Bar dataKey="value" fill={color} radius={[3, 3, 0, 0]} />
          </BarChart>
        ) : (
          <LineChart data={series.data} margin={{ top: 0, right: 8, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 10, fill: '#9ca3af' }}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
              formatter={(v: number) => [v.toLocaleString(), series.unit]}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </LineChart>
        )}
      </ResponsiveContainer>
    </div>
  )
}

export default function Dashboard() {
  const { user, logout } = useAuth()
  const { data: overview, isLoading, error, refetch } = useMetricsOverview()

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          {user && (
            <div className="mt-1 inline-flex items-center gap-2 text-sm text-gray-500">
              <span>{user.email}</span>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                  ROLE_BADGE[user.role] ?? 'bg-gray-100 text-gray-600'
                }`}
              >
                {user.role}
              </span>
            </div>
          )}
        </div>
        <button
          onClick={logout}
          className="text-sm text-gray-500 hover:text-gray-900 border border-gray-300 rounded-md px-3 py-1.5 hover:bg-gray-50 transition-colors"
        >
          Sign out
        </button>
      </div>

      {/* KPI Cards */}
      {isLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="rounded-xl border border-gray-200 bg-white px-5 py-4 shadow-sm animate-pulse"
            >
              <div className="h-3 bg-gray-200 rounded w-1/2 mb-3" />
              <div className="h-7 bg-gray-200 rounded w-2/3" />
            </div>
          ))}
        </div>
      ) : error ? (
        <ErrorState message="Failed to load metrics." onRetry={() => void refetch()} />
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
          {overview?.kpis.map((kpi) => (
            <KPICard key={kpi.label} kpi={kpi} />
          ))}
        </div>
      )}

      {/* Charts */}
      {!isLoading && !error && overview && overview.charts.length > 0 && (
        <>
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Metric Trends</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {overview.charts.map((chart, i) => (
              <MetricChart key={chart.series_id} series={chart} index={i} />
            ))}
          </div>
        </>
      )}

      {!isLoading && !error && overview && overview.charts.length === 0 && (
        <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 py-12 text-center">
          <p className="text-sm text-gray-500">
            No metric data yet.{' '}
            <a href="/metrics" className="text-indigo-600 hover:underline">
              Add metric series
            </a>{' '}
            to see charts here.
          </p>
        </div>
      )}
    </div>
  )
}

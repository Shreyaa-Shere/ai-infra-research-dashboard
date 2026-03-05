import { Link, useParams } from 'react-router-dom'
import LoadingSkeleton from '../../components/LoadingSkeleton'
import ErrorState from '../../components/ErrorState'
import { useSource } from '../../hooks/useSources'
import type { EntityType } from '../../lib/entities'

const ENTITY_TYPE_LABELS: Record<EntityType, string> = {
  hardware_product: 'Hardware',
  company: 'Company',
  datacenter: 'Datacenter',
}

const ENTITY_TYPE_COLORS: Record<EntityType, string> = {
  hardware_product: 'bg-purple-100 text-purple-700',
  company: 'bg-blue-100 text-blue-700',
  datacenter: 'bg-green-100 text-green-700',
}

const ENTITY_TYPE_ROUTES: Record<EntityType, string> = {
  hardware_product: '/hardware-products',
  company: '/companies',
  datacenter: '/datacenters',
}

const STATUS_COLORS: Record<string, string> = {
  ingested: 'bg-green-100 text-green-700',
  skipped: 'bg-yellow-100 text-yellow-700',
  error: 'bg-red-100 text-red-700',
}

export default function SourceDetail() {
  const { id } = useParams<{ id: string }>()
  const { data, isLoading, isError, refetch } = useSource(id!)

  if (isLoading) return <LoadingSkeleton rows={8} cols={2} />
  if (isError || !data)
    return <ErrorState message="Source document not found." onRetry={() => void refetch()} />

  return (
    <div>
      {/* Back link */}
      <div className="mb-6">
        <Link
          to="/sources"
          className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
        >
          ← Back to Sources
        </Link>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left: main content */}
        <div className="lg:col-span-2">
          <div className="flex flex-wrap items-start gap-3">
            <h1 className="text-xl font-bold leading-tight text-gray-900">{data.title}</h1>
            <span
              className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[data.status] ?? ''}`}
            >
              {data.status}
            </span>
          </div>

          <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-gray-500">
            <span>{data.source_name}</span>
            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs">{data.source_type}</span>
            {data.published_at && (
              <span>Published {new Date(data.published_at).toLocaleDateString()}</span>
            )}
            {data.url && (
              <a
                href={data.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                Source URL ↗
              </a>
            )}
          </div>

          {/* Raw Text */}
          {data.raw_text && (
            <div className="mt-6 rounded-lg border border-gray-200 p-4">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
                Content
              </h2>
              <p className="text-sm leading-relaxed text-gray-700 whitespace-pre-wrap">
                {data.raw_text}
              </p>
            </div>
          )}

          {/* Extracted entities detail */}
          {data.extracted_entities && Object.keys(data.extracted_entities).length > 0 && (
            <div className="mt-4 rounded-lg border border-gray-200 p-4">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
                Entity Extraction Details
              </h2>
              <div className="space-y-2">
                {Object.entries(data.extracted_entities).map(([type, entities]) => (
                  <div key={type} className="text-sm">
                    <span className="font-medium capitalize text-gray-700">
                      {type.replace(/_/g, ' ')}:
                    </span>{' '}
                    <span className="text-gray-600">
                      {(entities as Array<{ name: string }>).map((e) => e.name).join(', ') || '—'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <p className="mt-6 text-xs text-gray-400">
            Ingested {new Date(data.created_at).toLocaleDateString()}
          </p>
        </div>

        {/* Right: linked entities as clickable cards */}
        <div className="space-y-4">
          <div className="rounded-lg border border-gray-200 p-4">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
              Linked Entities ({data.entity_links.length})
            </h2>
            {data.entity_links.length === 0 ? (
              <p className="text-sm text-gray-400">No entities extracted.</p>
            ) : (
              <ul className="space-y-2">
                {data.entity_links.map((link) => (
                  <li key={`${link.entity_type}-${link.entity_id}`}>
                    <Link
                      to={`${ENTITY_TYPE_ROUTES[link.entity_type]}/${link.entity_id}`}
                      className="flex items-center justify-between rounded-md p-2 hover:bg-gray-50"
                    >
                      <span className="text-sm font-medium text-gray-800">
                        {link.entity_name ?? link.entity_id}
                      </span>
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${ENTITY_TYPE_COLORS[link.entity_type] ?? 'bg-gray-100 text-gray-700'}`}
                      >
                        {ENTITY_TYPE_LABELS[link.entity_type]}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Meta info panel */}
          <div className="rounded-lg border border-gray-200 p-4">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
              Document Info
            </h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Source</span>
                <span className="font-medium text-gray-800">{data.source_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Type</span>
                <span className="font-medium text-gray-800">{data.source_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Entities</span>
                <span className="font-medium text-gray-800">{data.entity_links.length}</span>
              </div>
              {data.publisher && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Publisher</span>
                  <span className="font-medium text-gray-800 truncate max-w-[120px]" title={data.publisher}>
                    {data.publisher}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

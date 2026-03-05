import { Link, useParams } from 'react-router-dom'
import LoadingSkeleton from '../../components/LoadingSkeleton'
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

const STATUS_COLORS: Record<string, string> = {
  ingested: 'bg-green-100 text-green-700',
  skipped: 'bg-yellow-100 text-yellow-700',
  error: 'bg-red-100 text-red-700',
}

export default function SourceDetail() {
  const { id } = useParams<{ id: string }>()
  const { data, isLoading, isError } = useSource(id!)

  if (isLoading) return <LoadingSkeleton rows={8} cols={2} />
  if (isError || !data)
    return <p className="text-sm text-red-600">Source document not found.</p>

  return (
    <div className="max-w-3xl">
      <Link
        to="/sources"
        className="mb-4 inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
      >
        ← Back to Sources
      </Link>

      <div className="mt-4">
        <div className="flex flex-wrap items-start gap-3">
          <h1 className="text-xl font-bold text-gray-900 leading-tight">{data.title}</h1>
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
      </div>

      {/* Entity Links */}
      {data.entity_links.length > 0 && (
        <div className="mt-6 rounded-lg border border-gray-200 p-4">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
            Extracted Entities ({data.entity_links.length})
          </h2>
          <div className="flex flex-wrap gap-2">
            {data.entity_links.map((link) => (
              <span
                key={`${link.entity_type}-${link.entity_id}`}
                className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium ${ENTITY_TYPE_COLORS[link.entity_type] ?? 'bg-gray-100 text-gray-700'}`}
              >
                <span className="text-xs opacity-70">
                  {ENTITY_TYPE_LABELS[link.entity_type]}
                </span>
                {link.entity_name}
              </span>
            ))}
          </div>
        </div>
      )}

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

      {/* Extracted entities JSON */}
      {data.extracted_entities && Object.keys(data.extracted_entities).length > 0 && (
        <div className="mt-6 rounded-lg border border-gray-200 p-4">
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
  )
}

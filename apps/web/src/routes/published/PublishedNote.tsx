import { useParams, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { usePublishedNote } from '../../hooks/useNotes'
import type { EntityType } from '../../lib/entities'

function entityPath(entity_type: EntityType, entity_id: string): string {
  switch (entity_type) {
    case 'hardware_product':
      return `/hardware-products/${entity_id}`
    case 'company':
      return `/companies/${entity_id}`
    case 'datacenter':
      return `/datacenters/${entity_id}`
  }
}

export default function PublishedNote() {
  const { slug } = useParams<{ slug: string }>()
  const { data: note, isLoading, isError, error } = usePublishedNote(slug ?? '')

  if (isLoading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-2/3 rounded bg-gray-200" />
          <div className="h-4 w-1/3 rounded bg-gray-200" />
          <div className="space-y-2 pt-8">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-4 rounded bg-gray-100" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (isError) {
    const status = (error as { status?: number })?.status
    return (
      <div className="mx-auto max-w-3xl px-4 py-24 text-center">
        <p className="text-5xl font-bold text-gray-200">{status === 404 ? '404' : 'Error'}</p>
        <p className="mt-4 text-xl font-semibold text-gray-700">
          {status === 404 ? 'Note not found' : 'Failed to load note'}
        </p>
        <p className="mt-2 text-sm text-gray-500">
          This note may not exist or may not be published yet.
        </p>
        <Link
          to="/dashboard"
          className="mt-6 inline-block rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
        >
          Back to Dashboard
        </Link>
      </div>
    )
  }

  if (!note) return null

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <header className="border-b border-gray-200 bg-white px-6 py-3">
        <Link to="/dashboard" className="text-sm font-medium text-blue-600 hover:underline">
          ← AI Infra Research
        </Link>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-12">
        {/* Meta */}
        <div className="mb-2 flex flex-wrap items-center gap-2">
          {note.tags.map((t) => (
            <span
              key={t}
              className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700"
            >
              {t}
            </span>
          ))}
        </div>

        <h1 className="mb-4 text-3xl font-bold text-gray-900">{note.title}</h1>

        <p className="mb-8 text-sm text-gray-500">
          By <span className="font-medium text-gray-700">{note.author.email}</span>
          {note.published_at && (
            <>
              {' · Published '}
              <time dateTime={note.published_at}>
                {new Date(note.published_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </time>
            </>
          )}
        </p>

        {/* Body */}
        <article className="prose prose-gray max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{note.body_markdown}</ReactMarkdown>
        </article>

        {/* Linked entities */}
        {note.linked_entities.length > 0 && (
          <div className="mt-12 border-t border-gray-200 pt-8">
            <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">
              Referenced Entities
            </h2>
            <div className="flex flex-wrap gap-3">
              {note.linked_entities.map((le) => (
                <Link
                  key={le.entity_id}
                  to={entityPath(le.entity_type, le.entity_id)}
                  className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm shadow-sm hover:border-blue-300 hover:shadow"
                >
                  <span className="font-medium text-gray-800">{le.display.name}</span>
                  <span className="text-xs text-gray-400">
                    {le.entity_type} · {le.display.kind}
                  </span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

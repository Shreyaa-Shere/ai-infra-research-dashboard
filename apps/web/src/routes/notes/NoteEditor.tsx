import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useNote, useCreateNote, useUpdateNote, usePublishNote, useDeleteNote } from '../../hooks/useNotes'
import { useAuth } from '../../store/AuthContext'
import LoadingSkeleton from '../../components/LoadingSkeleton'
import type { EntityType, LinkedEntityInput } from '../../lib/entities'
import { hardwareProductsApi, companiesApi, datacentersApi } from '../../lib/api'

type EditorTab = 'write' | 'preview'

interface EntityOption {
  id: string
  label: string
  kind: string
  entity_type: EntityType
}

async function searchEntities(token: string, query: string): Promise<EntityOption[]> {
  const [hwResp, coResp, dcResp] = await Promise.allSettled([
    hardwareProductsApi.list(token, { limit: 5 }),
    companiesApi.list(token, { limit: 5 }),
    datacentersApi.list(token, { limit: 5 }),
  ])

  const results: EntityOption[] = []

  if (hwResp.status === 'fulfilled') {
    for (const hw of hwResp.value.items) {
      if (!query || hw.name.toLowerCase().includes(query.toLowerCase())) {
        results.push({ id: hw.id, label: hw.name, kind: hw.category, entity_type: 'hardware_product' })
      }
    }
  }
  if (coResp.status === 'fulfilled') {
    for (const co of coResp.value.items) {
      if (!query || co.name.toLowerCase().includes(query.toLowerCase())) {
        results.push({ id: co.id, label: co.name, kind: co.type, entity_type: 'company' })
      }
    }
  }
  if (dcResp.status === 'fulfilled') {
    for (const dc of dcResp.value.items) {
      if (!query || dc.name.toLowerCase().includes(query.toLowerCase())) {
        results.push({ id: dc.id, label: dc.name, kind: dc.status, entity_type: 'datacenter' })
      }
    }
  }
  return results
}

export default function NoteEditor() {
  const { id } = useParams<{ id: string }>()
  const isNew = !id || id === 'new'
  const navigate = useNavigate()
  const { user, accessToken } = useAuth()

  const { data: existing, isLoading } = useNote(isNew ? '' : id!)
  const createNote = useCreateNote()
  const updateNote = useUpdateNote()
  const publishNote = usePublishNote()
  const deleteNote = useDeleteNote()

  const [tab, setTab] = useState<EditorTab>('write')
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState('')
  const [linkedEntities, setLinkedEntities] = useState<LinkedEntityInput[]>([])
  const [entitySearch, setEntitySearch] = useState('')
  const [entityOptions, setEntityOptions] = useState<EntityOption[]>([])
  const [showEntityDropdown, setShowEntityDropdown] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  // Populate form from existing note
  useEffect(() => {
    if (existing) {
      setTitle(existing.title)
      setBody(existing.body_markdown)
      setTags(existing.tags)
      setLinkedEntities(
        existing.linked_entities.map((le) => ({
          entity_type: le.entity_type,
          entity_id: le.entity_id,
        }))
      )
    }
  }, [existing])

  // Entity search
  useEffect(() => {
    if (!accessToken || entitySearch.length < 1) {
      setEntityOptions([])
      return
    }
    const timer = setTimeout(async () => {
      const opts = await searchEntities(accessToken, entitySearch)
      setEntityOptions(opts)
    }, 300)
    return () => clearTimeout(timer)
  }, [entitySearch, accessToken])

  const canEdit =
    user?.role === 'admin' ||
    (user?.role === 'analyst' && (isNew || existing?.author.id === user.id))
  const canPublish = user?.role === 'admin' || user?.role === 'analyst'
  const isPublished = existing?.status === 'published'

  function addTag(e: React.KeyboardEvent<HTMLInputElement>) {
    if ((e.key === 'Enter' || e.key === ',') && tagInput.trim()) {
      e.preventDefault()
      const newTag = tagInput.trim().toLowerCase().replace(/,/g, '')
      if (newTag && !tags.includes(newTag)) {
        setTags([...tags, newTag])
      }
      setTagInput('')
    }
  }

  function removeTag(t: string) {
    setTags(tags.filter((x) => x !== t))
  }

  function addEntityLink(opt: EntityOption) {
    const exists = linkedEntities.some(
      (le) => le.entity_id === opt.id && le.entity_type === opt.entity_type
    )
    if (!exists) {
      setLinkedEntities([...linkedEntities, { entity_type: opt.entity_type, entity_id: opt.id }])
    }
    setEntitySearch('')
    setShowEntityDropdown(false)
  }

  function removeEntityLink(entity_id: string) {
    setLinkedEntities(linkedEntities.filter((le) => le.entity_id !== entity_id))
  }

  function getEntityLabel(le: LinkedEntityInput): string {
    const opt = entityOptions.find((o) => o.id === le.entity_id)
    if (opt) return `${opt.label} (${opt.entity_type})`
    if (existing) {
      const linked = existing.linked_entities.find((x) => x.entity_id === le.entity_id)
      if (linked) return `${linked.display.name} (${linked.entity_type})`
    }
    return `${le.entity_type}:${le.entity_id.slice(0, 8)}`
  }

  async function handleSave(newStatus?: 'draft' | 'review') {
    if (!title.trim() || !body.trim()) {
      setError('Title and body are required.')
      return
    }
    setError(null)
    setSaving(true)
    try {
      if (isNew) {
        const created = await createNote.mutateAsync({
          title,
          body_markdown: body,
          tags,
          linked_entities: linkedEntities,
        })
        navigate(`/notes/${created.id}`)
      } else {
        await updateNote.mutateAsync({
          id: id!,
          data: {
            title,
            body_markdown: body,
            tags,
            linked_entities: linkedEntities,
            status: newStatus,
          },
        })
      }
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  async function handlePublish() {
    if (!id) return
    setSaving(true)
    try {
      const published = await publishNote.mutateAsync(id)
      navigate(`/published/${published.slug}`)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!id || !window.confirm('Delete this note? This cannot be undone.')) return
    setSaving(true)
    try {
      await deleteNote.mutateAsync(id)
      navigate('/notes')
    } catch (err) {
      setError((err as Error).message)
      setSaving(false)
    }
  }

  if (!isNew && isLoading) return <LoadingSkeleton rows={6} cols={1} />

  if (!isNew && !isLoading && !existing) {
    return <p className="text-sm text-red-600">Note not found.</p>
  }

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">
          {isNew ? 'New Research Note' : 'Edit Note'}
        </h1>
        {!isNew && existing?.status === 'published' && existing.slug && (
          <a
            href={`/published/${existing.slug}`}
            className="text-sm text-blue-600 hover:underline"
          >
            View published →
          </a>
        )}
      </div>

      {error && (
        <div className="mb-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Title */}
      <div className="mb-4">
        <label className="mb-1 block text-sm font-medium text-gray-700">Title</label>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          disabled={!canEdit || isPublished}
          placeholder="Research note title..."
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
        />
      </div>

      {/* Editor / Preview tabs */}
      <div className="mb-4">
        <div className="mb-0 flex border-b border-gray-200">
          {(['write', 'preview'] as EditorTab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium capitalize ${
                tab === t
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
        {tab === 'write' ? (
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            disabled={!canEdit || isPublished}
            rows={20}
            placeholder="Write your research note in Markdown..."
            className="w-full rounded-b-md rounded-tr-md border border-t-0 border-gray-300 p-3 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
          />
        ) : (
          <div className="min-h-[20rem] rounded-b-md rounded-tr-md border border-t-0 border-gray-300 bg-white p-4 prose prose-sm max-w-none overflow-auto">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{body || '_No content yet._'}</ReactMarkdown>
          </div>
        )}
      </div>

      {/* Tags */}
      <div className="mb-4">
        <label className="mb-1 block text-sm font-medium text-gray-700">Tags</label>
        <div className="flex flex-wrap items-center gap-1 rounded-md border border-gray-300 px-2 py-1.5 focus-within:ring-2 focus-within:ring-blue-500">
          {tags.map((t) => (
            <span
              key={t}
              className="flex items-center gap-1 rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700"
            >
              {t}
              {canEdit && !isPublished && (
                <button
                  type="button"
                  onClick={() => removeTag(t)}
                  className="text-blue-500 hover:text-blue-700"
                >
                  ×
                </button>
              )}
            </span>
          ))}
          {canEdit && !isPublished && (
            <input
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={addTag}
              placeholder="Add tag + Enter"
              className="min-w-[8rem] border-none bg-transparent text-sm outline-none"
            />
          )}
        </div>
      </div>

      {/* Linked entities */}
      <div className="mb-6">
        <label className="mb-1 block text-sm font-medium text-gray-700">
          Linked Entities
        </label>
        <div className="flex flex-wrap gap-1 mb-2">
          {linkedEntities.map((le) => (
            <span
              key={le.entity_id}
              className="flex items-center gap-1 rounded-full bg-purple-100 px-2 py-0.5 text-xs text-purple-700"
            >
              {getEntityLabel(le)}
              {canEdit && !isPublished && (
                <button
                  type="button"
                  onClick={() => removeEntityLink(le.entity_id)}
                  className="text-purple-500 hover:text-purple-700"
                >
                  ×
                </button>
              )}
            </span>
          ))}
        </div>
        {canEdit && !isPublished && (
          <div className="relative">
            <input
              value={entitySearch}
              onChange={(e) => {
                setEntitySearch(e.target.value)
                setShowEntityDropdown(true)
              }}
              onFocus={() => setShowEntityDropdown(true)}
              placeholder="Search hardware / company / datacenter..."
              className="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {showEntityDropdown && entityOptions.length > 0 && (
              <div className="absolute z-10 mt-1 w-full rounded-md border border-gray-200 bg-white shadow-lg">
                {entityOptions.map((opt) => (
                  <button
                    key={`${opt.entity_type}:${opt.id}`}
                    type="button"
                    onClick={() => addEntityLink(opt)}
                    className="flex w-full items-center justify-between px-3 py-2 text-sm hover:bg-gray-50"
                  >
                    <span>{opt.label}</span>
                    <span className="text-xs text-gray-400">{opt.entity_type} · {opt.kind}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Actions */}
      {(canEdit || canPublish) && (
        <div className="flex flex-wrap items-center gap-3 border-t border-gray-200 pt-4">
          {canEdit && !isPublished && (
            <>
              <button
                onClick={() => handleSave('draft')}
                disabled={saving}
                className="rounded-md bg-white border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                Save Draft
              </button>
              {existing?.status === 'draft' && (
                <button
                  onClick={() => handleSave('review')}
                  disabled={saving}
                  className="rounded-md border border-yellow-400 bg-yellow-50 px-4 py-2 text-sm font-medium text-yellow-800 hover:bg-yellow-100 disabled:opacity-50"
                >
                  Move to Review
                </button>
              )}
            </>
          )}
          {canPublish && !isNew && !isPublished && (
            <button
              onClick={handlePublish}
              disabled={saving}
              className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
            >
              Publish
            </button>
          )}
          {isNew && (
            <button
              onClick={() => handleSave()}
              disabled={saving}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              Create Note
            </button>
          )}
          {!isNew && canEdit && (
            <button
              onClick={handleDelete}
              disabled={saving}
              className="ml-auto rounded-md border border-red-300 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
            >
              Delete
            </button>
          )}
        </div>
      )}
    </div>
  )
}

import { useState } from 'react'
import FormModal from '../../components/FormModal'
import { useCreateHardwareProduct, useUpdateHardwareProduct } from '../../hooks/useHardwareProducts'
import type { HardwareCategory, HardwareProduct } from '../../lib/entities'

const CATEGORIES: HardwareCategory[] = ['GPU', 'CPU', 'Networking', 'Accelerator']

interface Props {
  initial?: HardwareProduct
  onClose: () => void
}

interface FormState {
  name: string
  vendor: string
  category: HardwareCategory
  release_date: string
  memory_gb: string
  tdp_watts: string
  process_node: string
  notes: string
}

function toForm(p?: HardwareProduct): FormState {
  return {
    name: p?.name ?? '',
    vendor: p?.vendor ?? '',
    category: p?.category ?? 'GPU',
    release_date: p?.release_date ?? '',
    memory_gb: p?.memory_gb != null ? String(p.memory_gb) : '',
    tdp_watts: p?.tdp_watts != null ? String(p.tdp_watts) : '',
    process_node: p?.process_node ?? '',
    notes: p?.notes ?? '',
  }
}

export default function HardwareProductForm({ initial, onClose }: Props) {
  const [form, setForm] = useState<FormState>(toForm(initial))
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({})
  const [apiError, setApiError] = useState<string | null>(null)

  const createMutation = useCreateHardwareProduct()
  const updateMutation = useUpdateHardwareProduct()
  const isEdit = !!initial
  const isPending = createMutation.isPending || updateMutation.isPending

  function set(field: keyof FormState, value: string) {
    setForm((f) => ({ ...f, [field]: value }))
    setErrors((e) => ({ ...e, [field]: undefined }))
  }

  function validate(): boolean {
    const e: Partial<Record<keyof FormState, string>> = {}
    if (!form.name.trim()) e.name = 'Name is required'
    if (!form.vendor.trim()) e.vendor = 'Vendor is required'
    if (!form.category) e.category = 'Category is required'
    if (form.memory_gb && isNaN(Number(form.memory_gb)))
      e.memory_gb = 'Must be a number'
    if (form.tdp_watts && isNaN(Number(form.tdp_watts)))
      e.tdp_watts = 'Must be a number'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validate()) return
    setApiError(null)

    const payload = {
      name: form.name.trim(),
      vendor: form.vendor.trim(),
      category: form.category,
      release_date: form.release_date || null,
      memory_gb: form.memory_gb ? Number(form.memory_gb) : null,
      tdp_watts: form.tdp_watts ? Number(form.tdp_watts) : null,
      process_node: form.process_node.trim() || null,
      notes: form.notes.trim() || null,
    }

    if (isEdit) {
      updateMutation.mutate(
        { id: initial!.id, data: payload },
        { onSuccess: onClose, onError: (err) => setApiError(err.message) }
      )
    } else {
      createMutation.mutate(payload, {
        onSuccess: onClose,
        onError: (err) => setApiError(err.message),
      })
    }
  }

  return (
    <FormModal title={isEdit ? 'Edit Hardware Product' : 'Add Hardware Product'} onClose={onClose}>
      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        {apiError && (
          <div role="alert" className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
            {apiError}
          </div>
        )}

        {/* Name */}
        <div>
          <label htmlFor="hp-name" className="mb-1 block text-sm font-medium text-gray-700">
            Name <span aria-hidden="true" className="text-red-500">*</span>
          </label>
          <input
            id="hp-name"
            value={form.name}
            onChange={(e) => set('name', e.target.value)}
            aria-invalid={!!errors.name}
            aria-describedby={errors.name ? 'hp-name-err' : undefined}
            className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.name ? 'border-red-400' : 'border-gray-300'}`}
            placeholder="e.g. H100 SXM5"
          />
          {errors.name && <p id="hp-name-err" className="mt-1 text-xs text-red-600">{errors.name}</p>}
        </div>

        {/* Vendor */}
        <div>
          <label htmlFor="hp-vendor" className="mb-1 block text-sm font-medium text-gray-700">
            Vendor <span aria-hidden="true" className="text-red-500">*</span>
          </label>
          <input
            id="hp-vendor"
            value={form.vendor}
            onChange={(e) => set('vendor', e.target.value)}
            aria-invalid={!!errors.vendor}
            aria-describedby={errors.vendor ? 'hp-vendor-err' : undefined}
            className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.vendor ? 'border-red-400' : 'border-gray-300'}`}
            placeholder="e.g. NVIDIA"
          />
          {errors.vendor && <p id="hp-vendor-err" className="mt-1 text-xs text-red-600">{errors.vendor}</p>}
        </div>

        {/* Category */}
        <div>
          <label htmlFor="hp-category" className="mb-1 block text-sm font-medium text-gray-700">
            Category <span aria-hidden="true" className="text-red-500">*</span>
          </label>
          <select
            id="hp-category"
            value={form.category}
            onChange={(e) => set('category', e.target.value as HardwareCategory)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Release Date */}
          <div>
            <label htmlFor="hp-release" className="mb-1 block text-sm font-medium text-gray-700">
              Release Date
            </label>
            <input
              id="hp-release"
              type="date"
              value={form.release_date}
              onChange={(e) => set('release_date', e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Process Node */}
          <div>
            <label htmlFor="hp-node" className="mb-1 block text-sm font-medium text-gray-700">
              Process Node
            </label>
            <input
              id="hp-node"
              value={form.process_node}
              onChange={(e) => set('process_node', e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g. 4nm"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Memory */}
          <div>
            <label htmlFor="hp-memory" className="mb-1 block text-sm font-medium text-gray-700">
              Memory (GB)
            </label>
            <input
              id="hp-memory"
              type="number"
              min="0"
              value={form.memory_gb}
              onChange={(e) => set('memory_gb', e.target.value)}
              aria-invalid={!!errors.memory_gb}
              className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.memory_gb ? 'border-red-400' : 'border-gray-300'}`}
              placeholder="e.g. 80"
            />
            {errors.memory_gb && <p className="mt-1 text-xs text-red-600">{errors.memory_gb}</p>}
          </div>

          {/* TDP */}
          <div>
            <label htmlFor="hp-tdp" className="mb-1 block text-sm font-medium text-gray-700">
              TDP (Watts)
            </label>
            <input
              id="hp-tdp"
              type="number"
              min="0"
              value={form.tdp_watts}
              onChange={(e) => set('tdp_watts', e.target.value)}
              aria-invalid={!!errors.tdp_watts}
              className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.tdp_watts ? 'border-red-400' : 'border-gray-300'}`}
              placeholder="e.g. 700"
            />
            {errors.tdp_watts && <p className="mt-1 text-xs text-red-600">{errors.tdp_watts}</p>}
          </div>
        </div>

        {/* Notes */}
        <div>
          <label htmlFor="hp-notes" className="mb-1 block text-sm font-medium text-gray-700">
            Notes
          </label>
          <textarea
            id="hp-notes"
            rows={3}
            value={form.notes}
            onChange={(e) => set('notes', e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Additional notes…"
          />
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isPending}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Create'}
          </button>
        </div>
      </form>
    </FormModal>
  )
}

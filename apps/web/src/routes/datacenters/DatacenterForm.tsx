import { useState } from 'react'
import FormModal from '../../components/FormModal'
import { useCreateDatacenter, useUpdateDatacenter } from '../../hooks/useDatacenters'
import { useCompanies } from '../../hooks/useCompanies'
import type { DatacenterCreate, DatacenterSite, DatacenterStatus } from '../../lib/entities'

const STATUSES: DatacenterStatus[] = ['planned', 'active', 'retired']

interface Props {
  initial?: DatacenterSite
  onClose: () => void
}

interface FormState {
  name: string
  region: string
  status: DatacenterStatus
  power_mw: string
  owner_company_id: string
  notes: string
}

function toForm(d?: DatacenterSite): FormState {
  return {
    name: d?.name ?? '',
    region: d?.region ?? '',
    status: d?.status ?? 'planned',
    power_mw: d?.power_mw != null ? String(d.power_mw) : '',
    owner_company_id: d?.owner_company_id ?? '',
    notes: d?.notes ?? '',
  }
}

export default function DatacenterForm({ initial, onClose }: Props) {
  const [form, setForm] = useState<FormState>(toForm(initial))
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({})
  const [apiError, setApiError] = useState<string | null>(null)

  const createMutation = useCreateDatacenter()
  const updateMutation = useUpdateDatacenter()
  const { data: companiesData } = useCompanies({ limit: 100 })
  const isEdit = !!initial
  const isPending = createMutation.isPending || updateMutation.isPending

  function set(field: keyof FormState, value: string) {
    setForm((f) => ({ ...f, [field]: value }))
    setErrors((e) => ({ ...e, [field]: undefined }))
  }

  function validate(): boolean {
    const e: Partial<Record<keyof FormState, string>> = {}
    if (!form.name.trim()) e.name = 'Name is required'
    if (!form.region.trim()) e.region = 'Region is required'
    if (form.power_mw && isNaN(Number(form.power_mw)))
      e.power_mw = 'Must be a number'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validate()) return
    setApiError(null)

    const payload: DatacenterCreate = {
      name: form.name.trim(),
      region: form.region.trim(),
      status: form.status,
      power_mw: form.power_mw ? Number(form.power_mw) : null,
      owner_company_id: form.owner_company_id || null,
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
    <FormModal title={isEdit ? 'Edit Datacenter Site' : 'Add Datacenter Site'} onClose={onClose}>
      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        {apiError && (
          <div role="alert" className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
            {apiError}
          </div>
        )}

        {/* Name */}
        <div>
          <label htmlFor="dc-name" className="mb-1 block text-sm font-medium text-gray-700">
            Name <span aria-hidden="true" className="text-red-500">*</span>
          </label>
          <input
            id="dc-name"
            value={form.name}
            onChange={(e) => set('name', e.target.value)}
            aria-invalid={!!errors.name}
            aria-describedby={errors.name ? 'dc-name-err' : undefined}
            className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.name ? 'border-red-400' : 'border-gray-300'}`}
            placeholder="e.g. US West GPU Cluster"
          />
          {errors.name && <p id="dc-name-err" className="mt-1 text-xs text-red-600">{errors.name}</p>}
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Region */}
          <div>
            <label htmlFor="dc-region" className="mb-1 block text-sm font-medium text-gray-700">
              Region <span aria-hidden="true" className="text-red-500">*</span>
            </label>
            <input
              id="dc-region"
              value={form.region}
              onChange={(e) => set('region', e.target.value)}
              aria-invalid={!!errors.region}
              aria-describedby={errors.region ? 'dc-region-err' : undefined}
              className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.region ? 'border-red-400' : 'border-gray-300'}`}
              placeholder="e.g. us-west-2"
            />
            {errors.region && <p id="dc-region-err" className="mt-1 text-xs text-red-600">{errors.region}</p>}
          </div>

          {/* Status */}
          <div>
            <label htmlFor="dc-status" className="mb-1 block text-sm font-medium text-gray-700">
              Status <span aria-hidden="true" className="text-red-500">*</span>
            </label>
            <select
              id="dc-status"
              value={form.status}
              onChange={(e) => set('status', e.target.value as DatacenterStatus)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Power */}
          <div>
            <label htmlFor="dc-power" className="mb-1 block text-sm font-medium text-gray-700">
              Power Capacity (MW)
            </label>
            <input
              id="dc-power"
              type="number"
              min="0"
              value={form.power_mw}
              onChange={(e) => set('power_mw', e.target.value)}
              aria-invalid={!!errors.power_mw}
              className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.power_mw ? 'border-red-400' : 'border-gray-300'}`}
              placeholder="e.g. 320"
            />
            {errors.power_mw && <p className="mt-1 text-xs text-red-600">{errors.power_mw}</p>}
          </div>

          {/* Owner Company */}
          <div>
            <label htmlFor="dc-owner" className="mb-1 block text-sm font-medium text-gray-700">
              Owner Company
            </label>
            <select
              id="dc-owner"
              value={form.owner_company_id}
              onChange={(e) => set('owner_company_id', e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">— None —</option>
              {companiesData?.items.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Notes */}
        <div>
          <label htmlFor="dc-notes" className="mb-1 block text-sm font-medium text-gray-700">
            Notes
          </label>
          <textarea
            id="dc-notes"
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

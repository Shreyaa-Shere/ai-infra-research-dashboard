import { useState } from 'react'
import FormModal from '../../components/FormModal'
import { useHardwareProducts } from '../../hooks/useHardwareProducts'
import { useCompanies } from '../../hooks/useCompanies'
import { useDatacenters } from '../../hooks/useDatacenters'
import {
  useCreateMetricSeries,
  useUpdateMetricSeries,
} from '../../hooks/useMetrics'
import type {
  MetricEntityType,
  MetricFrequency,
  MetricSeries,
  MetricSeriesCreate,
  MetricSeriesUpdate,
} from '../../lib/entities'

const ENTITY_TYPES: MetricEntityType[] = ['hardware_product', 'company', 'datacenter']
const ENTITY_TYPE_LABELS: Record<MetricEntityType, string> = {
  hardware_product: 'Hardware Product',
  company: 'Company',
  datacenter: 'Datacenter',
}
const FREQUENCIES: MetricFrequency[] = ['daily', 'weekly', 'monthly']

interface Props {
  initial?: MetricSeries
  onClose: () => void
}

interface FormState {
  name: string
  entity_type: MetricEntityType
  entity_id: string
  unit: string
  frequency: MetricFrequency
  source: string
}

function toForm(s?: MetricSeries): FormState {
  return {
    name: s?.name ?? '',
    entity_type: s?.entity_type ?? 'hardware_product',
    entity_id: s?.entity_id ?? '',
    unit: s?.unit ?? '',
    frequency: s?.frequency ?? 'monthly',
    source: s?.source ?? '',
  }
}

export default function MetricSeriesForm({ initial, onClose }: Props) {
  const [form, setForm] = useState<FormState>(toForm(initial))
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({})
  const [apiError, setApiError] = useState<string | null>(null)

  const isEdit = !!initial
  const createMutation = useCreateMetricSeries()
  const updateMutation = useUpdateMetricSeries(initial?.id ?? '')
  const isPending = createMutation.isPending || updateMutation.isPending

  // Load all entity lists unconditionally (React hooks rules)
  const { data: hwData } = useHardwareProducts({ limit: 200 })
  const { data: coData } = useCompanies({ limit: 200 })
  const { data: dcData } = useDatacenters({ limit: 200 })

  const entityOptions =
    form.entity_type === 'hardware_product'
      ? hwData?.items.map((e) => ({ id: e.id, name: e.name })) ?? []
      : form.entity_type === 'company'
        ? coData?.items.map((e) => ({ id: e.id, name: e.name })) ?? []
        : dcData?.items.map((e) => ({ id: e.id, name: e.name })) ?? []

  function set(field: keyof FormState, value: string) {
    setForm((f) => {
      const next = { ...f, [field]: value }
      // Reset entity_id when entity_type changes
      if (field === 'entity_type') next.entity_id = ''
      return next
    })
    setErrors((e) => ({ ...e, [field]: undefined }))
  }

  function validate(): boolean {
    const e: Partial<Record<keyof FormState, string>> = {}
    if (!form.name.trim()) e.name = 'Name is required'
    if (!isEdit && !form.entity_id) e.entity_id = 'Entity is required'
    if (!form.unit.trim()) e.unit = 'Unit is required'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  function handleSubmit(ev: React.FormEvent) {
    ev.preventDefault()
    if (!validate()) return
    setApiError(null)

    if (isEdit) {
      const payload: MetricSeriesUpdate = {
        name: form.name.trim(),
        unit: form.unit.trim(),
        frequency: form.frequency,
        source: form.source.trim() || null,
      }
      updateMutation.mutate(payload, {
        onSuccess: onClose,
        onError: (err) => setApiError(err.message),
      })
    } else {
      const payload: MetricSeriesCreate = {
        name: form.name.trim(),
        entity_type: form.entity_type,
        entity_id: form.entity_id,
        unit: form.unit.trim(),
        frequency: form.frequency,
        source: form.source.trim() || null,
      }
      createMutation.mutate(payload, {
        onSuccess: onClose,
        onError: (err) => setApiError(err.message),
      })
    }
  }

  return (
    <FormModal title={isEdit ? 'Edit Metric Series' : 'Add Metric Series'} onClose={onClose}>
      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        {apiError && (
          <div role="alert" className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
            {apiError}
          </div>
        )}

        {/* Name */}
        <div>
          <label htmlFor="ms-name" className="mb-1 block text-sm font-medium text-gray-700">
            Name <span aria-hidden="true" className="text-red-500">*</span>
          </label>
          <input
            id="ms-name"
            value={form.name}
            onChange={(e) => set('name', e.target.value)}
            aria-invalid={!!errors.name}
            aria-describedby={errors.name ? 'ms-name-err' : undefined}
            className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.name ? 'border-red-400' : 'border-gray-300'}`}
            placeholder="e.g. H100 Quarterly Shipments"
          />
          {errors.name && <p id="ms-name-err" className="mt-1 text-xs text-red-600">{errors.name}</p>}
        </div>

        {/* Entity Type + Entity */}
        {!isEdit && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="ms-entity-type" className="mb-1 block text-sm font-medium text-gray-700">
                Entity Type <span aria-hidden="true" className="text-red-500">*</span>
              </label>
              <select
                id="ms-entity-type"
                value={form.entity_type}
                onChange={(e) => set('entity_type', e.target.value as MetricEntityType)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {ENTITY_TYPES.map((t) => (
                  <option key={t} value={t}>{ENTITY_TYPE_LABELS[t]}</option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="ms-entity-id" className="mb-1 block text-sm font-medium text-gray-700">
                Entity <span aria-hidden="true" className="text-red-500">*</span>
              </label>
              <select
                id="ms-entity-id"
                value={form.entity_id}
                onChange={(e) => set('entity_id', e.target.value)}
                aria-invalid={!!errors.entity_id}
                className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.entity_id ? 'border-red-400' : 'border-gray-300'}`}
              >
                <option value="">— Select —</option>
                {entityOptions.map((opt) => (
                  <option key={opt.id} value={opt.id}>{opt.name}</option>
                ))}
              </select>
              {errors.entity_id && (
                <p className="mt-1 text-xs text-red-600">{errors.entity_id}</p>
              )}
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          {/* Unit */}
          <div>
            <label htmlFor="ms-unit" className="mb-1 block text-sm font-medium text-gray-700">
              Unit <span aria-hidden="true" className="text-red-500">*</span>
            </label>
            <input
              id="ms-unit"
              value={form.unit}
              onChange={(e) => set('unit', e.target.value)}
              aria-invalid={!!errors.unit}
              aria-describedby={errors.unit ? 'ms-unit-err' : undefined}
              className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.unit ? 'border-red-400' : 'border-gray-300'}`}
              placeholder="e.g. units, USD B, MW"
            />
            {errors.unit && <p id="ms-unit-err" className="mt-1 text-xs text-red-600">{errors.unit}</p>}
          </div>

          {/* Frequency */}
          <div>
            <label htmlFor="ms-freq" className="mb-1 block text-sm font-medium text-gray-700">
              Frequency
            </label>
            <select
              id="ms-freq"
              value={form.frequency}
              onChange={(e) => set('frequency', e.target.value as MetricFrequency)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {FREQUENCIES.map((f) => (
                <option key={f} value={f}>{f.charAt(0).toUpperCase() + f.slice(1)}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Source */}
        <div>
          <label htmlFor="ms-source" className="mb-1 block text-sm font-medium text-gray-700">
            Source
          </label>
          <input
            id="ms-source"
            value={form.source}
            onChange={(e) => set('source', e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g. NVIDIA earnings, IDC report"
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

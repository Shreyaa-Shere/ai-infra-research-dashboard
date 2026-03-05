import { useState } from 'react'
import FormModal from '../../components/FormModal'
import { useCreateCompany, useUpdateCompany } from '../../hooks/useCompanies'
import type { Company, CompanyCreate, CompanyType } from '../../lib/entities'

const COMPANY_TYPES: CompanyType[] = ['fab', 'idm', 'cloud', 'vendor', 'research']
const TYPE_LABELS: Record<CompanyType, string> = {
  fab: 'Fab',
  idm: 'IDM',
  cloud: 'Cloud',
  vendor: 'Vendor',
  research: 'Research',
}

interface Props {
  initial?: Company
  onClose: () => void
}

interface FormState {
  name: string
  type: CompanyType
  region: string
  website: string
}

function toForm(c?: Company): FormState {
  return {
    name: c?.name ?? '',
    type: c?.type ?? 'vendor',
    region: c?.region ?? '',
    website: c?.website ?? '',
  }
}

export default function CompanyForm({ initial, onClose }: Props) {
  const [form, setForm] = useState<FormState>(toForm(initial))
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({})
  const [apiError, setApiError] = useState<string | null>(null)

  const createMutation = useCreateCompany()
  const updateMutation = useUpdateCompany()
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
    if (form.website && !/^https?:\/\/.+/.test(form.website.trim()))
      e.website = 'Must start with http:// or https://'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validate()) return
    setApiError(null)

    const payload: CompanyCreate = {
      name: form.name.trim(),
      type: form.type,
      region: form.region.trim(),
      website: form.website.trim() || null,
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
    <FormModal title={isEdit ? 'Edit Company' : 'Add Company'} onClose={onClose}>
      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        {apiError && (
          <div role="alert" className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
            {apiError}
          </div>
        )}

        {/* Name */}
        <div>
          <label htmlFor="co-name" className="mb-1 block text-sm font-medium text-gray-700">
            Name <span aria-hidden="true" className="text-red-500">*</span>
          </label>
          <input
            id="co-name"
            value={form.name}
            onChange={(e) => set('name', e.target.value)}
            aria-invalid={!!errors.name}
            aria-describedby={errors.name ? 'co-name-err' : undefined}
            className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.name ? 'border-red-400' : 'border-gray-300'}`}
            placeholder="e.g. TSMC"
          />
          {errors.name && <p id="co-name-err" className="mt-1 text-xs text-red-600">{errors.name}</p>}
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Type */}
          <div>
            <label htmlFor="co-type" className="mb-1 block text-sm font-medium text-gray-700">
              Type <span aria-hidden="true" className="text-red-500">*</span>
            </label>
            <select
              id="co-type"
              value={form.type}
              onChange={(e) => set('type', e.target.value as CompanyType)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {COMPANY_TYPES.map((t) => (
                <option key={t} value={t}>{TYPE_LABELS[t]}</option>
              ))}
            </select>
          </div>

          {/* Region */}
          <div>
            <label htmlFor="co-region" className="mb-1 block text-sm font-medium text-gray-700">
              Region <span aria-hidden="true" className="text-red-500">*</span>
            </label>
            <input
              id="co-region"
              value={form.region}
              onChange={(e) => set('region', e.target.value)}
              aria-invalid={!!errors.region}
              aria-describedby={errors.region ? 'co-region-err' : undefined}
              className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.region ? 'border-red-400' : 'border-gray-300'}`}
              placeholder="e.g. TW"
            />
            {errors.region && <p id="co-region-err" className="mt-1 text-xs text-red-600">{errors.region}</p>}
          </div>
        </div>

        {/* Website */}
        <div>
          <label htmlFor="co-website" className="mb-1 block text-sm font-medium text-gray-700">
            Website
          </label>
          <input
            id="co-website"
            type="url"
            value={form.website}
            onChange={(e) => set('website', e.target.value)}
            aria-invalid={!!errors.website}
            aria-describedby={errors.website ? 'co-website-err' : undefined}
            className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.website ? 'border-red-400' : 'border-gray-300'}`}
            placeholder="https://example.com"
          />
          {errors.website && <p id="co-website-err" className="mt-1 text-xs text-red-600">{errors.website}</p>}
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

import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import ConfirmDialog from '../../components/ConfirmDialog'
import ErrorState from '../../components/ErrorState'
import LoadingSkeleton from '../../components/LoadingSkeleton'
import { useCompany, useDeleteCompany } from '../../hooks/useCompanies'
import { useDatacenters } from '../../hooks/useDatacenters'
import { useAuth } from '../../store/AuthContext'
import CompanyForm from './CompanyForm'

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-green-100 text-green-700',
  planned: 'bg-yellow-100 text-yellow-700',
  retired: 'bg-gray-100 text-gray-500',
}

export default function CompanyDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { data, isLoading, isError, refetch } = useCompany(id!)
  const { data: dcData } = useDatacenters({ owner_company_id: id, limit: 5 })
  const deleteMutation = useDeleteCompany()
  const [showEdit, setShowEdit] = useState(false)
  const [showDelete, setShowDelete] = useState(false)

  const canWrite = user?.role === 'admin' || user?.role === 'analyst'
  const canDelete = user?.role === 'admin'

  if (isLoading) return <LoadingSkeleton rows={4} cols={2} />
  if (isError || !data) return <ErrorState message="Company not found." onRetry={() => void refetch()} />

  return (
    <div>
      {/* Top bar */}
      <div className="mb-6 flex items-center justify-between">
        <Link
          to="/companies"
          className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
        >
          ← Back to Companies
        </Link>
        {canWrite && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowEdit(true)}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
            >
              Edit
            </button>
            {canDelete && (
              <button
                onClick={() => setShowDelete(true)}
                className="rounded-md border border-red-300 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50"
              >
                Delete
              </button>
            )}
          </div>
        )}
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left: main content */}
        <div className="lg:col-span-2">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{data.name}</h1>
            <span className="rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-700">
              {data.type}
            </span>
          </div>

          <div className="mt-6 rounded-lg border border-gray-200 p-4">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
              Details
            </h2>
            <div className="flex justify-between border-b border-gray-100 py-2 text-sm">
              <span className="text-gray-500">Region</span>
              <span className="font-medium text-gray-800">{data.region}</span>
            </div>
            <div className="flex justify-between py-2 text-sm">
              <span className="text-gray-500">Website</span>
              {data.website ? (
                <a
                  href={data.website}
                  target="_blank"
                  rel="noreferrer"
                  className="font-medium text-blue-600 hover:underline"
                >
                  {data.website.replace(/^https?:\/\//, '')}
                </a>
              ) : (
                <span className="text-gray-400">—</span>
              )}
            </div>
          </div>

          <p className="mt-6 text-xs text-gray-400">
            Added {new Date(data.created_at).toLocaleDateString()}
          </p>
        </div>

        {/* Right: owned datacenters */}
        <div className="space-y-4">
          <div className="rounded-lg border border-gray-200 p-4">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
              Owned Datacenters
            </h2>
            {!dcData || dcData.items.length === 0 ? (
              <p className="text-sm text-gray-400">No datacenters linked.</p>
            ) : (
              <ul className="space-y-2">
                {dcData.items.map((dc) => (
                  <li key={dc.id}>
                    <Link
                      to={`/datacenters/${dc.id}`}
                      className="block rounded-md p-2 hover:bg-gray-50"
                    >
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-gray-800">{dc.name}</p>
                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[dc.status] ?? 'bg-gray-100 text-gray-700'}`}>
                          {dc.status}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400">{dc.region}{dc.power_mw != null ? ` · ${dc.power_mw} MW` : ''}</p>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
            {dcData && dcData.total > 5 && (
              <Link
                to="/datacenters"
                className="mt-3 block text-center text-xs text-blue-600 hover:underline"
              >
                View all {dcData.total} datacenters →
              </Link>
            )}
          </div>
        </div>
      </div>

      {showEdit && (
        <CompanyForm initial={data} onClose={() => setShowEdit(false)} />
      )}

      {showDelete && (
        <ConfirmDialog
          title="Delete Company"
          message={`Delete "${data.name}"? This cannot be undone.`}
          isPending={deleteMutation.isPending}
          onConfirm={() =>
            deleteMutation.mutate(data.id, {
              onSuccess: () => navigate('/companies'),
            })
          }
          onCancel={() => setShowDelete(false)}
        />
      )}
    </div>
  )
}

import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import ConfirmDialog from '../../components/ConfirmDialog'
import ErrorState from '../../components/ErrorState'
import LoadingSkeleton from '../../components/LoadingSkeleton'
import { useCompany, useDeleteCompany } from '../../hooks/useCompanies'
import { useAuth } from '../../store/AuthContext'
import CompanyForm from './CompanyForm'

export default function CompanyDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { data, isLoading, isError, refetch } = useCompany(id!)
  const deleteMutation = useDeleteCompany()
  const [showEdit, setShowEdit] = useState(false)
  const [showDelete, setShowDelete] = useState(false)

  const canWrite = user?.role === 'admin' || user?.role === 'analyst'
  const canDelete = user?.role === 'admin'

  if (isLoading) return <LoadingSkeleton rows={4} cols={2} />
  if (isError || !data) return <ErrorState message="Company not found." onRetry={() => void refetch()} />

  return (
    <div className="max-w-2xl">
      <div className="mb-4 flex items-center justify-between">
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

      <div className="mt-4 flex items-center gap-3">
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
              {data.website}
            </a>
          ) : (
            <span className="text-gray-400">—</span>
          )}
        </div>
      </div>

      <p className="mt-6 text-xs text-gray-400">
        Added {new Date(data.created_at).toLocaleDateString()}
      </p>

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

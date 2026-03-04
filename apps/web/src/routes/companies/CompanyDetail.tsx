import { Link, useParams } from 'react-router-dom'
import LoadingSkeleton from '../../components/LoadingSkeleton'
import { useCompany } from '../../hooks/useCompanies'

export default function CompanyDetail() {
  const { id } = useParams<{ id: string }>()
  const { data, isLoading, isError } = useCompany(id!)

  if (isLoading) return <LoadingSkeleton rows={4} cols={2} />
  if (isError || !data) return <p className="text-sm text-red-600">Company not found.</p>

  return (
    <div className="max-w-2xl">
      <Link
        to="/companies"
        className="mb-4 inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
      >
        ← Back to Companies
      </Link>

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
    </div>
  )
}

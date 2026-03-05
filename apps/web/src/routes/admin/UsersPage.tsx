import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../../store/AuthContext'
import { usersApi, ApiError } from '../../lib/api'
import ErrorState from '../../components/ErrorState'
import type { UserAdminOut, Role } from '../../lib/entities'

const ROLES: Array<'analyst' | 'viewer'> = ['analyst', 'viewer']

export default function UsersPage() {
  const { accessToken } = useAuth()
  const qc = useQueryClient()

  const [limit] = useState(20)
  const [offset, setOffset] = useState(0)

  // ── invite modal state ────────────────────────────────────────────────────
  const [showInvite, setShowInvite] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState<'analyst' | 'viewer'>('analyst')
  const [inviteResult, setInviteResult] = useState<string | null>(null)
  const [inviteError, setInviteError] = useState<string | null>(null)

  // ── data ──────────────────────────────────────────────────────────────────
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['users', limit, offset],
    queryFn: () => usersApi.list(accessToken!, { limit, offset }),
    enabled: !!accessToken,
  })

  // ── invite mutation ───────────────────────────────────────────────────────
  const inviteMutation = useMutation({
    mutationFn: ({ email, role }: { email: string; role: 'analyst' | 'viewer' }) =>
      usersApi.invite(accessToken!, { email, role }),
    onSuccess: (result) => {
      setInviteResult(result.invite_url)
      setInviteEmail('')
      setInviteRole('analyst')
    },
    onError: (err) => {
      setInviteError(err instanceof ApiError ? err.message : 'Failed to send invite')
    },
  })

  // ── update mutation ───────────────────────────────────────────────────────
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { role?: Role; is_active?: boolean } }) =>
      usersApi.update(accessToken!, id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  })

  function handleInviteSubmit(e: React.FormEvent) {
    e.preventDefault()
    setInviteError(null)
    setInviteResult(null)
    inviteMutation.mutate({ email: inviteEmail, role: inviteRole })
  }

  function handleCloseInvite() {
    setShowInvite(false)
    setInviteEmail('')
    setInviteRole('analyst')
    setInviteResult(null)
    setInviteError(null)
  }

  const total = data?.total ?? 0

  return (
    <div data-testid="admin-users-page">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">User Management</h1>
        <button
          onClick={() => setShowInvite(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700"
          data-testid="invite-user-button"
        >
          Invite user
        </button>
      </div>

      {/* Users table */}
      {isLoading ? (
        <p className="text-sm text-gray-500">Loading…</p>
      ) : error ? (
        <ErrorState message="Failed to load users." onRetry={() => void refetch()} />
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="min-w-full text-sm" data-testid="users-table">
              <thead className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Joined</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data?.items.map((user: UserAdminOut) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{user.email}</td>
                    <td className="px-4 py-3">
                      <select
                        value={user.role}
                        onChange={(e) =>
                          updateMutation.mutate({
                            id: user.id,
                            data: { role: e.target.value as Role },
                          })
                        }
                        className="border border-gray-300 rounded px-2 py-1 text-xs"
                        data-testid={`role-select-${user.id}`}
                      >
                        {(['admin', 'analyst', 'viewer'] as Role[]).map((r) => (
                          <option key={r} value={r}>
                            {r}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          user.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() =>
                          updateMutation.mutate({
                            id: user.id,
                            data: { is_active: !user.is_active },
                          })
                        }
                        className={`text-xs px-2 py-1 rounded border ${
                          user.is_active
                            ? 'border-red-300 text-red-600 hover:bg-red-50'
                            : 'border-green-300 text-green-600 hover:bg-green-50'
                        }`}
                        data-testid={`toggle-active-${user.id}`}
                      >
                        {user.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between mt-4 text-sm text-gray-600">
            <span>
              {offset + 1}–{Math.min(offset + limit, total)} of {total}
            </span>
            <div className="flex gap-2">
              <button
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - limit))}
                className="px-3 py-1 border rounded disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={offset + limit >= total}
                onClick={() => setOffset(offset + limit)}
                className="px-3 py-1 border rounded disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}

      {/* Invite modal */}
      {showInvite && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" data-testid="invite-modal">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Invite new user</h2>

            {inviteResult ? (
              <div className="space-y-4">
                <p className="text-sm text-gray-700">Share this invite link with the user:</p>
                <div className="bg-gray-50 border border-gray-200 rounded p-3 text-xs break-all font-mono">
                  {inviteResult}
                </div>
                <div className="flex justify-end">
                  <button
                    onClick={handleCloseInvite}
                    className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                  >
                    Done
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleInviteSubmit} className="space-y-4">
                {inviteError && (
                  <p className="text-sm text-red-600">{inviteError}</p>
                )}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email address
                  </label>
                  <input
                    type="email"
                    required
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="colleague@example.com"
                    data-testid="invite-email-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value as 'analyst' | 'viewer')}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    data-testid="invite-role-select"
                  >
                    {ROLES.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={handleCloseInvite}
                    className="px-4 py-2 border border-gray-300 text-sm rounded hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={inviteMutation.isPending}
                    className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                    {inviteMutation.isPending ? 'Sending…' : 'Send invite'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

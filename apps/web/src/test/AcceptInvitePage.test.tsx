import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import AcceptInvitePage from '../routes/accept-invite/AcceptInvitePage'

function renderWithToken(token: string) {
  return render(
    <MemoryRouter initialEntries={[`/accept-invite?token=${token}`]}>
      <Routes>
        <Route path="/accept-invite" element={<AcceptInvitePage />} />
        <Route path="/login" element={<div data-testid="login-page">Login</div>} />
      </Routes>
    </MemoryRouter>
  )
}

describe('AcceptInvitePage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders the form when token is present', () => {
    renderWithToken('valid-token-123')
    expect(screen.getByTestId('accept-invite-form')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/at least 8 characters/i)).toBeInTheDocument()
  })

  it('shows error when password is too short', async () => {
    renderWithToken('valid-token-123')

    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: 'short' },
    })
    fireEvent.change(screen.getByLabelText(/confirm/i), {
      target: { value: 'short' },
    })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(screen.getByText(/at least 8 characters/i)).toBeInTheDocument()
    })
  })

  it('shows error when passwords do not match', async () => {
    renderWithToken('valid-token-123')

    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: 'Password123!' },
    })
    fireEvent.change(screen.getByLabelText(/confirm/i), {
      target: { value: 'Different123!' },
    })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(screen.getByText(/do not match/i)).toBeInTheDocument()
    })
  })

  it('navigates to login on successful accept', async () => {
    vi.spyOn(await import('../lib/api'), 'usersApi', 'get').mockReturnValue({
      list: vi.fn(),
      invite: vi.fn(),
      acceptInvite: vi.fn().mockResolvedValue({ id: 'new-user', email: 'x@x.com', role: 'analyst', is_active: true, created_at: '', updated_at: '' }),
      update: vi.fn(),
    })

    renderWithToken('good-token')

    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: 'Goodpass1!' },
    })
    fireEvent.change(screen.getByLabelText(/confirm/i), {
      target: { value: 'Goodpass1!' },
    })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(screen.getByTestId('login-page')).toBeInTheDocument()
    })
  })

  it('shows error message from API on failure', async () => {
    const { ApiError } = await import('../lib/api')
    vi.spyOn(await import('../lib/api'), 'usersApi', 'get').mockReturnValue({
      list: vi.fn(),
      invite: vi.fn(),
      acceptInvite: vi.fn().mockRejectedValue(new ApiError(400, 'INVITE_USED', 'This invite has already been used')),
      update: vi.fn(),
    })

    renderWithToken('used-token')

    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: 'Goodpass1!' },
    })
    fireEvent.change(screen.getByLabelText(/confirm/i), {
      target: { value: 'Goodpass1!' },
    })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(screen.getByText(/already been used/i)).toBeInTheDocument()
    })
  })
})

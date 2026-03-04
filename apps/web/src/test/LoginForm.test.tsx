import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import { describe, it, expect, vi } from 'vitest'

import { AuthProvider } from '../store/AuthContext'
import LoginForm from '../components/LoginForm'

// Prevent real fetch calls in unit tests
vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve({}) })))

function renderForm() {
  const qc = new QueryClient()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <AuthProvider>
          <LoginForm />
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('LoginForm validation', () => {
  it('shows email error when submitted empty', async () => {
    renderForm()
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => {
      expect(screen.getByText('Invalid email address')).toBeInTheDocument()
    })
  })

  it('shows password error when email is valid but password is short', async () => {
    renderForm()
    await userEvent.type(screen.getByLabelText(/email/i), 'user@example.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'short')
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => {
      expect(
        screen.getByText('Password must be at least 8 characters')
      ).toBeInTheDocument()
    })
  })

  it('clears field errors when input becomes valid', async () => {
    renderForm()
    // Submit empty to trigger errors
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => screen.getByText('Invalid email address'))

    // Fix email
    await userEvent.type(screen.getByLabelText(/email/i), 'user@example.com')
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => {
      expect(screen.queryByText('Invalid email address')).not.toBeInTheDocument()
    })
  })
})

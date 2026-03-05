import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import * as AuthModule from '../store/AuthContext'
import Layout from '../components/Layout'

function renderLayout(path = '/dashboard') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<div>Dashboard</div>} />
          <Route path="/search" element={<div>Search</div>} />
          <Route path="/companies" element={<div>Companies</div>} />
          <Route path="/admin/users" element={<div>Admin</div>} />
        </Route>
      </Routes>
    </MemoryRouter>
  )
}

describe('Layout accessibility', () => {
  beforeEach(() => {
    vi.spyOn(AuthModule, 'useAuth').mockReturnValue({
      user: { id: 'u1', email: 'admin@example.com', role: 'admin', is_active: true, created_at: '' },
      accessToken: 'fake-token',
      isLoading: false,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
    })
  })

  it('renders skip-to-content link pointing to #main-content', () => {
    renderLayout()
    const skip = screen.getByText('Skip to content')
    expect(skip).toBeInTheDocument()
    expect(skip).toHaveAttribute('href', '#main-content')
  })

  it('renders header nav with aria-label', () => {
    renderLayout()
    expect(screen.getByRole('navigation', { name: 'Header navigation' })).toBeInTheDocument()
  })

  it('renders sidebar nav with aria-label', () => {
    renderLayout()
    expect(screen.getByRole('navigation', { name: 'Sidebar navigation' })).toBeInTheDocument()
  })

  it('renders main landmark with id="main-content"', () => {
    renderLayout()
    const main = screen.getByRole('main')
    expect(main).toHaveAttribute('id', 'main-content')
  })

  it('sets aria-current="page" on the active nav link', () => {
    renderLayout('/dashboard')
    // The active sidebar link for /dashboard renders span with aria-current="page"
    const activeSpan = screen.getAllByText('Overview').find(
      (el) => el.getAttribute('aria-current') === 'page'
    )
    expect(activeSpan).toBeDefined()
  })

  it('does not set aria-current on inactive nav links', () => {
    renderLayout('/dashboard')
    const searchSpan = screen.getByText('Search')
    expect(searchSpan).not.toHaveAttribute('aria-current', 'page')
  })

  it('shows Admin section only for admin role', () => {
    renderLayout()
    expect(screen.getByText('User Management')).toBeInTheDocument()
  })

  it('hides Admin section for non-admin role', () => {
    vi.spyOn(AuthModule, 'useAuth').mockReturnValue({
      user: { id: 'u2', email: 'viewer@example.com', role: 'viewer', is_active: true, created_at: '' },
      accessToken: 'fake-token',
      isLoading: false,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
    })
    renderLayout()
    expect(screen.queryByText('User Management')).not.toBeInTheDocument()
  })
})

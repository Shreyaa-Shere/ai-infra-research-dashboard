import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect } from 'vitest'

import { queryClient } from '../lib/queryClient'
import App from '../App'

function wrapper(initialEntries: string[]) {
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('App routing', () => {
  it('renders login page at /login', () => {
    render(wrapper(['/login']))
    expect(screen.getByText('AI Infra Research Dashboard')).toBeInTheDocument()
  })

  it('renders 404 for unknown route', () => {
    render(wrapper(['/does-not-exist']))
    expect(screen.getByText('404')).toBeInTheDocument()
  })
})

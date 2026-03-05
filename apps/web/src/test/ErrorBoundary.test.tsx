import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import ErrorBoundary from '../components/ErrorBoundary'

// Component that throws on render
function Bomb({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) throw new Error('test explosion')
  return <div>All good</div>
}

describe('ErrorBoundary', () => {
  // Suppress console.error for expected React error boundary logs
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders children when no error', () => {
    render(
      <ErrorBoundary>
        <Bomb shouldThrow={false} />
      </ErrorBoundary>
    )
    expect(screen.getByText('All good')).toBeInTheDocument()
  })

  it('renders fallback UI when child throws', () => {
    render(
      <ErrorBoundary>
        <Bomb shouldThrow={true} />
      </ErrorBoundary>
    )
    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText('test explosion')).toBeInTheDocument()
  })

  it('renders custom fallback prop when provided', () => {
    render(
      <ErrorBoundary fallback={<div>Custom fallback</div>}>
        <Bomb shouldThrow={true} />
      </ErrorBoundary>
    )
    expect(screen.getByText('Custom fallback')).toBeInTheDocument()
  })

  it('shows reload button in default fallback', () => {
    render(
      <ErrorBoundary>
        <Bomb shouldThrow={true} />
      </ErrorBoundary>
    )
    expect(screen.getByRole('button', { name: /reload page/i })).toBeInTheDocument()
  })
})

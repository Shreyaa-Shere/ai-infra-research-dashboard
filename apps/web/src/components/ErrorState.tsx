interface ErrorStateProps {
  message?: string
  onRetry?: () => void
}

export default function ErrorState({
  message = 'Failed to load data.',
  onRetry,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center py-16 text-center"
    >
      <svg
        className="mb-4 h-10 w-10 text-red-400"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M12 9v3.75m9.303 3.376c.866 1.5-.217 3.374-1.948 3.374H4.645c-1.73 0-2.813-1.874-1.948-3.374L10.052 3.378c.866-1.5 3.032-1.5 3.898 0L21.303 16.126z"
        />
      </svg>
      <p className="text-sm font-medium text-gray-700">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          Try again
        </button>
      )}
    </div>
  )
}

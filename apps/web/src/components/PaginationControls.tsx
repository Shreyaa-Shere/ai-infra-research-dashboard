interface PaginationControlsProps {
  total: number
  limit: number
  offset: number
  onOffsetChange: (offset: number) => void
}

export default function PaginationControls({
  total,
  limit,
  offset,
  onOffsetChange,
}: PaginationControlsProps) {
  const start = total === 0 ? 0 : offset + 1
  const end = Math.min(offset + limit, total)
  const hasPrev = offset > 0
  const hasNext = offset + limit < total

  return (
    <div className="flex items-center justify-between py-3 text-sm text-gray-600">
      <span>
        {total === 0
          ? 'No results'
          : `Showing ${start}–${end} of ${total}`}
      </span>
      <div className="flex gap-2">
        <button
          onClick={() => onOffsetChange(Math.max(0, offset - limit))}
          disabled={!hasPrev}
          className="rounded border border-gray-300 px-3 py-1 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Previous
        </button>
        <button
          onClick={() => onOffsetChange(offset + limit)}
          disabled={!hasNext}
          className="rounded border border-gray-300 px-3 py-1 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Next
        </button>
      </div>
    </div>
  )
}

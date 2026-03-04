interface LoadingSkeletonProps {
  rows?: number
  cols?: number
}

export default function LoadingSkeleton({ rows = 5, cols = 4 }: LoadingSkeletonProps) {
  return (
    <div className="overflow-hidden rounded-lg border border-gray-200">
      <div className="bg-gray-50 px-4 py-3">
        <div className="flex gap-4">
          {Array.from({ length: cols }).map((_, i) => (
            <div key={i} className="h-3 flex-1 animate-pulse rounded bg-gray-200" />
          ))}
        </div>
      </div>
      <div className="divide-y divide-gray-100 bg-white">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex gap-4 px-4 py-3">
            {Array.from({ length: cols }).map((_, j) => (
              <div
                key={j}
                className="h-4 flex-1 animate-pulse rounded bg-gray-100"
                style={{ animationDelay: `${(i * cols + j) * 50}ms` }}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

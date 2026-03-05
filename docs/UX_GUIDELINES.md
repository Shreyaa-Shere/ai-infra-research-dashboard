# UX Guidelines

Conventions for UI components, states, and accessibility across the AI Infra Research Dashboard frontend.

## Loading States

Use `LoadingSkeleton` for any data that takes time to fetch. Never show a blank page.

```tsx
import LoadingSkeleton from '../../components/LoadingSkeleton'

{isLoading && <LoadingSkeleton rows={5} cols={4} />}
```

- `rows` — number of placeholder rows
- `cols` — number of placeholder columns
- Always place the skeleton where the real content will appear (same vertical space)

For page-level or detail-page loading, an inline skeleton block is preferred over a spinner to reduce layout shift.

## Error States

Use `ErrorState` for fetch errors. Always offer a retry when `refetch` is available.

```tsx
import ErrorState from '../../components/ErrorState'

{isError && (
  <ErrorState
    message="Failed to load companies."
    onRetry={() => void refetch()}
  />
)}
```

- `message` — short, specific description of what failed
- `onRetry` — optional; omit on detail pages where navigating back is the better action
- The component sets `role="alert"` so screen readers announce the error immediately

For page-level crashes (unexpected JS exceptions), `ErrorBoundary` in `main.tsx` catches them and shows a reload prompt.

## Empty States

Use `EmptyState` when a list loads successfully but returns zero items.

```tsx
import EmptyState from '../../components/EmptyState'

{data.items.length === 0 && (
  <EmptyState message="No hardware products found." />
)}
```

Keep the message actionable when possible (e.g. "Run ingestion to populate sources.").

## Consistent Page Structure

Every list page follows this pattern:

```tsx
{isLoading && <LoadingSkeleton rows={5} cols={N} />}
{isError && <ErrorState message="..." onRetry={...} />}
{!isLoading && !isError && data && (
  <>
    {data.items.length === 0
      ? <EmptyState message="..." />
      : <DataTable columns={columns} data={data.items} onRowClick={...} />
    }
    <PaginationControls ... />
  </>
)}
```

## Accessibility

### Skip-to-content

A "Skip to content" link is the first focusable element in `Layout.tsx`. It is visually hidden until focused (`.sr-only focus:not-sr-only`). Do not remove it.

### Navigation landmarks

- `<header>` contains the top nav with `aria-label="Header navigation"`
- `<aside>` contains the sidebar with `aria-label="Sidebar navigation"`
- `<main id="main-content" tabIndex={-1}>` is the skip-link target

### Active page indication

Use `aria-current="page"` on the active `NavLink`. The render-prop pattern is used in `Layout.tsx`:

```tsx
<NavLink to={to}>
  {({ isActive }) => (
    <span aria-current={isActive ? 'page' : undefined}>{label}</span>
  )}
</NavLink>
```

### Error announcements

Inline error states use `role="alert"` so assistive technologies announce them without requiring focus. Icons within error states use `aria-hidden="true"`.

### Form labels

Every `<input>` and `<select>` must have an associated `<label>`. Use `htmlFor` + `id`, or wrap the input inside the label.

### Focus management

- After a modal opens, move focus to the first interactive element inside it
- After a modal closes, return focus to the trigger element
- Use `tabIndex={-1}` on elements that need to be focus targets but not in the tab order (e.g., `<main>` for skip-link)

## Colour and badges

Status badges use Tailwind utility classes via a `Record<string, string>` constant at the top of each component:

```ts
const STATUS_COLORS: Record<string, string> = {
  active: 'bg-green-100 text-green-700',
  planned: 'bg-yellow-100 text-yellow-700',
  retired: 'bg-gray-100 text-gray-500',
}
```

Always provide a fallback (`?? 'bg-gray-100 text-gray-700'`) for unknown values.

## Toast / Feedback Messages

For mutation outcomes (create, publish, trigger), show an inline banner rather than a toast:

```tsx
{mutation.isSuccess && (
  <div className="mb-4 rounded-md bg-green-50 px-4 py-3 text-sm text-green-700">
    Operation successful.
  </div>
)}
{mutation.isError && (
  <div className="mb-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
    Operation failed. Please try again.
  </div>
)}
```

Position banners directly below the page header, above the main content.

## DataTable

`DataTable` is a generic table component that accepts typed `columns` and `data`:

```tsx
<DataTable<MyEntity>
  columns={columns}
  data={data.items}
  onRowClick={(row) => navigate(`/my-entity/${row.id}`)}
/>
```

Every row is keyboard accessible (Enter / Space triggers `onRowClick`).

## Pagination

Use `PaginationControls` for all paginated list pages:

```tsx
<PaginationControls
  total={data.total}
  limit={data.limit}
  offset={data.offset}
  onOffsetChange={setOffset}
/>
```

Reset `offset` to `0` whenever a filter changes.

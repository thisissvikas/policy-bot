# React Standards

## Components
- Use functional components with hooks. Do not write new class components.
- One component per file. File name should match the component name (PascalCase).
- Keep components focused: a component should render one logical unit of UI.
- Extract complex logic into custom hooks rather than putting it directly in components.

## Props
- All props must be typed (TypeScript interface or type alias). No untyped props.
- Destructure props in the function signature for clarity.
- Provide default values for optional props using default parameter syntax.

## State Management
- Use local state (`useState`) for UI-only state that is not shared.
- Use context for state shared across a subtree.
- Do not put derived state in `useState` — compute it from existing state during render.

## Effects
- Every `useEffect` must have a dependency array. An empty array `[]` means "run once on mount" — document this intent with a comment.
- Clean up side effects in the return function of `useEffect` (timers, subscriptions, listeners).
- Do not fetch data directly in `useEffect` in new code — use a data-fetching library (React Query, SWR, etc.).

## Performance
- Do not use `React.memo`, `useMemo`, or `useCallback` without profiling first. Premature optimization adds complexity.
- Avoid inline object and array literals in JSX props if they cause unnecessary re-renders in performance-sensitive components.

## Keys
- Always provide a stable, unique `key` prop when rendering lists. Never use array index as a key unless the list is static and will never reorder.

## Accessibility
- Interactive elements must be keyboard-accessible.
- Provide `alt` text for all images.
- Use semantic HTML elements — prefer `<button>` over `<div onClick>`.

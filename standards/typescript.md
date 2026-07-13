# TypeScript Standards

## Types
- Always use explicit types on function parameters and return values. Avoid `any` — use `unknown` when the type is truly unknown, then narrow it.
- Prefer `type` aliases for unions and intersections; use `interface` for object shapes that may be extended.
- Enable `strict` mode in `tsconfig.json`. Do not disable strict checks with `// @ts-ignore` or `// @ts-nocheck` without an explanation.

## Null Handling
- Use optional chaining (`?.`) and nullish coalescing (`??`) instead of manual null checks where appropriate.
- Do not use `!` (non-null assertion) without a comment explaining why the value is guaranteed to be non-null.

## Functions and Variables
- Prefer `const` over `let`. Use `let` only when the variable will be reassigned. Never use `var`.
- Use arrow functions for callbacks and short anonymous functions. Use named functions for complex logic.
- Avoid side effects in pure functions.

## Async
- Always `await` Promises or explicitly handle them with `.then()/.catch()`. Never ignore a returned Promise.
- Use `async/await` over raw Promise chains for readability.
- Catch errors from `async` functions — unhandled rejections are silent failures.

## Imports
- Use ES module imports (`import`/`export`), not CommonJS (`require`/`module.exports`).
- Organize imports: external packages → internal aliases → relative paths. Separate groups with a blank line.
- No barrel re-exports that include unrelated modules.

## Error Handling
- Do not `catch` errors and swallow them silently. At minimum, log the error.
- Use typed error classes for domain errors; catch by type where possible.

## React (when applicable)
- See `standards/react.md` for React-specific standards.

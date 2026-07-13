# ADR-011 — Error Handling and Error Response Schema

## Status
Accepted

## Context
Error responses from our API were inconsistent — some returned plain strings, some returned HTML error pages, some returned structured JSON with different field names. This made client-side error handling fragile and unpredictable.

## Decision
All API error responses must follow a standard JSON schema:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "A human-readable description of the error",
    "details": {}
  }
}
```

Rules:
- `code` is a machine-readable string constant in SCREAMING_SNAKE_CASE.
- `message` is a human-readable string suitable for logging; it may be shown to developers but not end users.
- `details` is optional — use it for structured context (e.g. field-level validation errors).
- HTTP status codes must be semantically correct: 400 for client errors, 500 for server errors, 404 for not found, etc.
- Never return a 200 response with an error body.
- Internal error details (stack traces, internal paths, database errors) must not appear in error responses.

## Consequences
- API clients can handle errors uniformly regardless of which endpoint they call.
- Any error response that does not follow this schema, or that returns a 200 with error content, violates this ADR.
- Stack traces and internal details must be logged server-side, not included in the response.

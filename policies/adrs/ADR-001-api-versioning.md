# ADR-001 — API Versioning

## Status
Accepted

## Context
As our API evolves, clients need stability guarantees. Without versioning, any change to a response shape or endpoint URL is a breaking change for all consumers simultaneously. We need a strategy that lets us evolve the API while maintaining backwards compatibility for existing clients.

## Decision
All public API endpoints must include a version prefix in the URL path, e.g. `/api/v1/users`, `/api/v2/orders`.

Rules:
- New endpoints must be created under the current major version prefix.
- Breaking changes (removed fields, changed types, removed endpoints) require a new major version.
- Additive changes (new optional fields, new endpoints) may be made within the existing version.
- Old versions must be supported for at least 6 months after a new version is released, with deprecation notices in responses.
- Version number must appear in the URL path, not in headers or query parameters.

## Consequences
- Clients can pin to a specific API version and upgrade on their own schedule.
- We maintain multiple versions simultaneously during transition periods.
- New API routes must always include the version prefix.

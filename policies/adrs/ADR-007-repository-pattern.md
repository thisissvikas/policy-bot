# ADR-007 — Repository Pattern for Database Access

## Status
Accepted

## Context
Database access was scattered across views, serializers, and utility functions. This made it hard to understand the data access layer, test business logic in isolation, or swap the storage backend. Direct use of `db.session`, ORM query methods, or raw SQL in business logic creates tight coupling.

## Decision
All database access must go through a repository class. Direct access to `db.session`, ORM query methods (e.g. `Model.objects.filter()`), or raw SQL is not permitted outside of repository classes.

Rules:
- Each domain entity has a corresponding repository class (e.g. `UserRepository`, `InvoiceRepository`).
- Repository classes are the only place that constructs and executes database queries.
- Business logic receives repository instances via dependency injection.
- Repositories may not contain business logic — they may only translate between the domain model and the persistence layer.

## Consequences
- Business logic can be tested with a mock or in-memory repository.
- Database queries are centralized and easy to audit.
- Any code that accesses `db.session` or calls ORM methods directly (outside a repository class) violates this ADR.

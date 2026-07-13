# Django Standards

## Views
- Views must not contain business logic. Extract business logic into service functions or model methods.
- Keep views thin: validate input, call a service, return a response.
- Use class-based views for standard CRUD operations; use function-based views for simple or one-off endpoints.

## Models
- All database access must go through the ORM — do not write raw SQL except for genuinely complex queries where the ORM cannot express the intent clearly.
- Use model managers for common query patterns rather than scattering filter/exclude calls across the codebase.
- Add `db_index=True` to fields that are frequently filtered or ordered by.
- Define `__str__` on every model.

## Forms and Serializers
- Validate all user input using Django forms or DRF serializers — do not validate manually in views.
- Never trust data from `request.POST` or `request.GET` without validation.

## URL Configuration
- URL names must be namespaced by app.
- Avoid hardcoded URL strings in views or templates — use `reverse()` or `{% url %}`.

## Settings
- Do not hardcode secrets in settings files. Use environment variables via `django-environ` or equivalent.
- `DEBUG = True` must never reach production. Guard it explicitly.
- Separate settings by environment: `base.py`, `local.py`, `production.py`.

## Migrations
- Run `makemigrations` and `migrate` before committing schema changes.
- Never edit a migration after it has been applied in any shared environment.
- Squash migrations periodically to keep the migration history manageable.

## Security
- Use Django's CSRF protection — do not exempt views from CSRF without a specific reason.
- Use `get_object_or_404` instead of `Model.objects.get()` in views to avoid leaking stack traces on missing objects.
- Do not expose admin at the default `/admin/` URL in production.

# Python Standards

## Error Handling
- Always catch specific exception types. Never use bare `except:`.
- At minimum, catch `except Exception:` — never silence all exceptions including `KeyboardInterrupt` and `SystemExit`.
- Log exceptions with context before re-raising or swallowing them.
- Use custom exception classes for domain errors rather than generic `ValueError` or `RuntimeError`.
- Do not use `pass` in except blocks without a comment explaining why.

## Imports
- Group imports in this order: stdlib → third-party → internal. Separate each group with a blank line.
- No wildcard imports (`from module import *`).
- Prefer explicit imports over importing entire modules when only a few names are needed.

## Functions and Methods
- Functions should do one thing. If you need "and" to describe what it does, consider splitting it.
- Maximum function length: 40 lines. Longer functions are a signal to refactor.
- Use descriptive names — avoid abbreviations unless universally understood (e.g. `i`, `url`, `id`).
- All public functions and methods must have type annotations on all parameters and return values.

## Classes
- Prefer dataclasses or Pydantic models over plain classes for data containers.
- Keep `__init__` focused on assignment — move complex initialization to class methods or factory functions.
- Avoid mutable default arguments in function signatures.

## Testing
- Every public function should have at least one unit test.
- Test the behaviour, not the implementation — avoid asserting on private state.
- Use `pytest` fixtures for shared setup; avoid `setUp`/`tearDown` from `unittest`.
- Mock at the boundary, not deep inside the unit under test.

## Logging
- Use structured logging (structlog or standard `logging` with extra fields).
- Never use `print()` for application logs — use the logger.
- Log at the appropriate level: `debug` for tracing, `info` for state changes, `warning` for recoverable issues, `error` for failures.

## Security
- Never log sensitive data (passwords, tokens, PII).
- Do not construct SQL queries or shell commands by string concatenation — use parameterized queries or `subprocess` with a list argument.
- Validate all external input at system boundaries.

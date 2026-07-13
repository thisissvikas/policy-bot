# PolicyBot — Implementation Plan

## Context

PolicyBot is an AI-powered GitHub bot that enforces coding standards and ADRs on every PR. This is a monorepo: the bot implementation and the reference standards/ADRs live side-by-side. The standards source is pluggable — start local, move to a separate repo with a one-line config change.

---

## Tech Stack

| Concern | Choice |
|---|---|
| Package manager | `uv` |
| Python | 3.12+ |
| Linting + formatting | `ruff` |
| Type checking | `mypy` (strict) |
| Validation | `pydantic` v2 |
| HTTP | `httpx` (async) |
| LLM | `anthropic` SDK — Claude Sonnet, tool use for structured output |
| YAML | `ruamel.yaml` |
| Glob matching | `pathspec` |
| Testing | `pytest` + `pytest-asyncio` + `respx` |
| GitHub Action | Composite action (uv + python, no Docker) |

---

## Architecture: Pluggable Standards Provider

```
policybot.yaml
  └── source.type: "local" | "github"
        │
        ▼
StandardsProvider (Protocol)
  ├── LocalProvider   — reads from local filesystem (default)
  └── GitHubProvider  — fetches from a remote GitHub repo
        │
        ▼
fetcher.py → reviewer.py → commenter.py
```

Switching from local to remote standards is a one-line change in `policybot.yaml`.

---

## Project Structure

```
policy-bot/
├── action.yml                  # GitHub Action (composite, no Docker)
├── policybot.yaml              # root config: source + rules
├── pyproject.toml              # uv project + ruff/mypy/pytest config
├── uv.lock
│
├── policies/                   # default standards content (segregated from bot code)
│   ├── standards/              # coding standards — edit these
│   │   ├── python.md
│   │   ├── typescript.md
│   │   ├── django.md
│   │   └── react.md
│   └── adrs/                   # architectural decision records — edit these
│       ├── ADR-001-api-versioning.md
│       ├── ADR-007-repository-pattern.md
│       └── ADR-011-error-handling.md
│
├── policybot/                  # bot implementation
│   ├── models.py               # Pydantic v2 models (Violation, ReviewResult, …)
│   ├── config.py               # policybot.yaml loader + glob matching
│   ├── detector.py             # language/framework detection from diff
│   ├── providers/
│   │   ├── base.py             # StandardsProvider Protocol
│   │   ├── local.py            # LocalProvider
│   │   └── github.py          # GitHubProvider
│   ├── fetcher.py              # concurrent doc fetching
│   ├── github_client.py        # httpx GitHub REST client
│   ├── reviewer.py             # Claude integration (tool-use structured output)
│   ├── commenter.py            # inline comment formatting + posting
│   └── cli.py                  # `policybot review` entry point
│
└── tests/                      # 88 tests, 85.79% coverage
    ├── conftest.py
    ├── fixtures/
    └── test_*.py
```

---

## Phase Status

### ✅ Phase 1 — Core MVP (complete)

All items shipped and verified:

- [x] `pyproject.toml` — `uv`, `ruff`, `mypy` (strict), `pytest`, coverage ≥80%
- [x] `policybot/models.py` — all Pydantic v2 models
- [x] `policybot/providers/` — `StandardsProvider` protocol + `LocalProvider` + `GitHubProvider`
- [x] `policybot/config.py` — `policybot.yaml` loader, glob matching, severity lookup
- [x] `policybot/detector.py` — language + framework detection from unified diff
- [x] `policybot/github_client.py` — `httpx` GitHub REST client
- [x] `policybot/fetcher.py` — concurrent doc fetching via provider
- [x] `policybot/reviewer.py` — Claude tool-use integration, structured `ReviewResult`
- [x] `policybot/commenter.py` — comment formatting, single-review batch posting
- [x] `policybot/cli.py` — `policybot review --dry-run` and live posting
- [x] `action.yml` — composite GitHub Action (uv + python, no Docker)
- [x] `policies/standards/` — Python, TypeScript, Django, React starter standards
- [x] `policies/adrs/` — ADR-001 (API versioning), ADR-007 (repository pattern), ADR-011 (error handling)
- [x] `policybot.yaml` — root config with local source
- [x] `.github/workflows/ci.yml` — lint + typecheck + test on every push/PR
- [x] 88 tests passing, 85.79% coverage, `mypy --strict` clean

---

### 🔲 Phase 2 — Org-wide + Severity + Deduplication

**GitHub App** (replaces the Action runner for org-wide install):
- [ ] `policybot/app.py` — FastAPI webhook server, `/webhook` endpoint with HMAC verification
- [ ] `policybot/github_app.py` — JWT generation, installation token exchange
- [ ] `Dockerfile` — `FROM python:3.12-slim`, install with `uv pip install --system`
- [ ] Deployment config (`fly.toml` or `railway.toml`)

**Severity enforcement** (models already support `severity`):
- [ ] `policybot.yaml` `severity: error` causes exit code 2 → blocks merge in CI
- [ ] Wire exit code through Action

**Comment deduplication**:
- [ ] Fingerprint posted violations by `(file, line, source_doc hash)`
- [ ] Fetch existing review comments before posting; skip already-posted findings

**Compliance summary**:
- [ ] `policybot status` CLI command — aggregate violation counts across repos

---

### 🔲 Phase 3 — Intelligence

- [ ] Learn from dismissed comments — if reviewers consistently dismiss a finding, surface the standard for review
- [ ] Standards coverage report — which standards have never triggered?
- [ ] Auto-suggest standard updates when merged code diverges from stated standards
- [ ] Team/repo-scoped private standards (applies_to specific teams or repos only)

---

## Verification

```bash
# Install
uv sync

# Lint
uv run ruff check policybot/ tests/

# Type check
uv run mypy policybot/

# Tests + coverage
uv run pytest --cov=policybot --cov-report=term-missing

# Local dry-run against a real diff
uv run policybot review \
  --config policybot.yaml \
  --diff path/to/your.diff \
  --dry-run
```

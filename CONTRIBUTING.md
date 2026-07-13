# PolicyBot — Usage & Contributing Guide

## Overview

PolicyBot reviews pull requests against your org's coding standards and ADRs, posting inline GitHub comments. This repo contains both the bot implementation (`policybot/`) and the reference standards (`standards/`, `adrs/`).

---

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — install with `curl -LsSf https://astral.sh/uv/install.sh | sh`
- An [Anthropic API key](https://console.anthropic.com/) for running reviews

---

## Local Setup

```bash
git clone https://github.com/thisissvikas/policy-bot.git
cd policy-bot

# Install all dependencies (creates .venv automatically)
uv sync

# Verify everything works
uv run policybot --help
```

---

## Running a Review Locally

### Against a local diff file

The fastest way to test without a GitHub token:

```bash
# Generate a diff from your changes
git diff HEAD~1 > changes.diff

# Run a dry-run review (prints comments, doesn't post)
ANTHROPIC_API_KEY=sk-ant-... uv run policybot review \
  --config policybot.yaml \
  --diff changes.diff \
  --dry-run
```

Output looks like:

```
PolicyBot found 2 violation(s):

  payments/src/invoice.py:42
  🏗️ **ADR — Repository Pattern**
  This function accesses `db.session` directly. Per ADR-007, all database
  access must go through a repository class.
  → Source: `adrs/ADR-007-repository-pattern.md`

  payments/src/invoice.py:67
  📋 **Standards — Error Handling**
  Bare `except:` catches everything including KeyboardInterrupt. Catch a
  specific exception type or `except Exception:` at minimum.
  → Source: `standards/python.md`
```

### Against a live GitHub PR

Requires `GITHUB_TOKEN` with `pull_requests: write` permission:

```bash
ANTHROPIC_API_KEY=sk-ant-... \
GITHUB_TOKEN=ghp_... \
uv run policybot review \
  --config policybot.yaml \
  --pr 42 \
  --repo your-org/your-repo \
  --dry-run   # remove --dry-run to actually post comments
```

### CLI reference

```
policybot review [OPTIONS]

Options:
  --config PATH    Path to policybot.yaml (default: policybot.yaml)
  --diff PATH      Path to a local unified diff file
  --pr INTEGER     GitHub PR number (fetches diff from GitHub)
  --repo TEXT      GitHub repo as owner/repo (required with --pr)
  --dry-run        Print violations to stdout, do not post to GitHub
  --model TEXT     Claude model to use (default: claude-sonnet-4-5)
  -v, --verbose    Enable debug logging
```

**Exit codes:**
- `0` — success, no violations (or violations posted as comments)
- `1` — fatal error (config missing, API failure, etc.)
- `2` — review completed but `error`-severity violations found (use to block CI)

---

## Configuring PolicyBot

### `policybot.yaml` structure

```yaml
# Where standards docs live
source:
  type: local          # read from this repo (default)
  # type: github
  # repo: my-org/engineering-standards
  # ref: main

# Map file globs to standards documents
standards:
  - match: "**/*.py"
    docs:
      - standards/python.md
    severity: warning   # "warning" (default) or "error"

# Map ADR documents to the file patterns they apply to
adrs:
  - path: adrs/ADR-007-repository-pattern.md
    applies_to:
      - "**/*.py"
    severity: error
```

**Glob patterns** follow `.gitignore` syntax: `**/*.py`, `**/views.py`, `src/**/*.ts`, etc.

**Severity:**
- `warning` — posts a comment, exits 0 (doesn't block merge)
- `error` — posts a comment, exits 2 (can be used to block merge in CI)

### Moving standards to a separate repo

Change `source` — nothing else changes:

```yaml
source:
  type: github
  repo: my-org/engineering-standards
  ref: main
```

---

## Writing Standards

Standards and ADRs are plain markdown files. No special syntax required.

**Standards** (in `standards/`): describe rules for a language or framework.

```markdown
# Python Standards

## Error Handling
- Always catch specific exception types. Never use bare `except:`.
- Log exceptions with context before re-raising or swallowing them.
```

**ADRs** (in `adrs/`): describe an architectural decision. PolicyBot reads the Context and Decision sections and applies them.

```markdown
# ADR-007 — Repository Pattern

## Decision
All database access must go through a repository class. Direct use of
`db.session` or ORM query methods outside of repositories is not permitted.
```

Both are reviewed as-is — Claude reads the natural language and understands what it requires of new code.

---

## Adding the GitHub Action to a Repo

Create `.github/workflows/policybot.yml` in the target repo:

```yaml
name: PolicyBot Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: thisissvikas/policy-bot@v1
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

**Secrets to add to the repo:**
- `ANTHROPIC_API_KEY` — get one at [console.anthropic.com](https://console.anthropic.com/)

The `github-token` input defaults to `${{ github.token }}` (the built-in Actions token) which already has `pull_requests: write` for PRs in the same repo.

---

## Development

### Running tests

```bash
uv run pytest                                        # run all tests
uv run pytest tests/test_reviewer.py -v             # single file, verbose
uv run pytest --cov=policybot --cov-report=term-missing  # with coverage
```

### Linting and formatting

```bash
uv run ruff check policybot/ tests/    # lint
uv run ruff format policybot/ tests/   # format
uv run mypy policybot/                 # type check (strict)
```

Or run everything at once:

```bash
uv run ruff check policybot/ tests/ && \
uv run ruff format --check policybot/ tests/ && \
uv run mypy policybot/ && \
uv run pytest --cov=policybot -q
```

### Code structure

| File | What it does |
|---|---|
| `policybot/models.py` | All shared Pydantic v2 models — start here |
| `policybot/config.py` | Loads and validates `policybot.yaml` |
| `policybot/detector.py` | Detects languages + frameworks from a unified diff |
| `policybot/providers/base.py` | `StandardsProvider` Protocol — the pluggability seam |
| `policybot/providers/local.py` | Reads docs from the local filesystem |
| `policybot/providers/github.py` | Fetches docs from a remote GitHub repo |
| `policybot/fetcher.py` | Fetches multiple docs concurrently via a provider |
| `policybot/github_client.py` | `httpx`-based async GitHub REST API client |
| `policybot/reviewer.py` | Builds the Claude prompt and parses structured violations |
| `policybot/commenter.py` | Formats violations and posts a single GitHub review |
| `policybot/cli.py` | `policybot review` command — ties everything together |

### Good first contributions

- **Language detection** ([detector.py](policybot/detector.py)) — add more extension mappings or framework signals
- **Prompt engineering** ([reviewer.py](policybot/reviewer.py)) — improve how standards are presented to the model
- **Comment formatting** ([commenter.py](policybot/commenter.py)) — make inline comments clearer
- **Standards content** ([standards/](standards/), [adrs/](adrs/)) — improve or add new standards docs
- **Test coverage** ([tests/](tests/)) — `cli.py` and `github_client.py` have room for more coverage

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes (for review) | Your Anthropic API key |
| `GITHUB_TOKEN` | Yes (for live PR) | GitHub token with `pull_requests: write` |
| `POLICYBOT_MODEL` | No | Override the Claude model (default: `claude-sonnet-4-5`) |

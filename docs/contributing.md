# Development Guide

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- An [Anthropic API key](https://console.anthropic.com/) for running live reviews

---

## Setup

```bash
git clone https://github.com/thisissvikas/policy-bot.git
cd policy-bot
uv sync
uv run policybot --help
```

---

## Running a review locally

### Dry-run against a local diff

```bash
git diff HEAD~1 > changes.diff

ANTHROPIC_API_KEY=sk-ant-... uv run policybot review \
  --config policybot.yaml \
  --diff changes.diff \
  --dry-run
```

Output:

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

```bash
ANTHROPIC_API_KEY=sk-ant-... \
GITHUB_TOKEN=ghp_... \
uv run policybot review \
  --config policybot.yaml \
  --pr 42 \
  --repo your-org/your-repo \
  --dry-run
```

Remove `--dry-run` to post inline comments on the actual PR.

### CLI reference

```
policybot review [OPTIONS]

  --config PATH    Path to policybot.yaml (default: policybot.yaml)
  --diff PATH      Path to a local unified diff file
  --pr INTEGER     GitHub PR number
  --repo TEXT      GitHub repo as owner/repo (required with --pr)
  --dry-run        Print violations, do not post to GitHub
  --model TEXT     Claude model (default: claude-sonnet-4-5)
  -v, --verbose    Debug logging
```

**Exit codes:** `0` success · `1` fatal error · `2` error-severity violations found

**Flag notes:**
- `--repo` must be in `owner/repo` format (with a slash). A plain repo name without an owner causes an error.
- `--repo` is required whenever `--pr` is used. Omitting it produces a generic "provide diff or PR" error, not a specific message about `--repo`.
- When both `--diff` and `--pr` are supplied, `--diff` takes precedence and `--pr` is silently ignored. Use one or the other.

---

## Tests

```bash
uv run pytest                                              # all tests
uv run pytest tests/test_reviewer.py -v                   # single file
uv run pytest --cov=policybot --cov-report=term-missing   # coverage
```

## Lint & type check

```bash
uv run ruff check policybot/ tests/
uv run ruff format policybot/ tests/
uv run mypy policybot/
```

Run everything at once:

```bash
uv run ruff check policybot/ tests/ && \
uv run ruff format --check policybot/ tests/ && \
uv run mypy policybot/ && \
uv run pytest --cov=policybot -q
```

---

## Code structure

| File | What it does |
|---|---|
| `policybot/models.py` | All shared Pydantic v2 models — start here |
| `policybot/config.py` | Loads and validates `policybot.yaml` |
| `policybot/detector.py` | Detects languages + frameworks from a unified diff |
| `policybot/providers/base.py` | `StandardsProvider` Protocol — the pluggability seam |
| `policybot/providers/local.py` | Reads docs from the local filesystem |
| `policybot/providers/github.py` | Fetches docs from a remote GitHub repo via API |
| `policybot/fetcher.py` | Fetches multiple docs concurrently via a provider |
| `policybot/github_client.py` | Async `httpx`-based GitHub REST API client |
| `policybot/reviewer.py` | Builds the Claude prompt, parses structured violations |
| `policybot/commenter.py` | Formats violations, posts a single GitHub review |
| `policybot/cli.py` | `policybot review` command — ties everything together |

---

## Good first contributions

- **Language detection** (`policybot/detector.py`) — add extension mappings or framework signals
- **Prompt engineering** (`policybot/reviewer.py`) — improve how standards are presented to Claude
- **Comment formatting** (`policybot/commenter.py`) — make inline comments clearer
- **Standards content** (`policies/standards/`, `policies/adrs/`) — improve or add new standards docs
- **Test coverage** (`tests/`) — `cli.py` and `github_client.py` have room for more tests

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes (for review) | Anthropic API key |
| `GITHUB_TOKEN` | Yes (live PR) | GitHub token with `pull-requests: write` scope |

To override the Claude model, use the `--model` CLI flag — there is no environment variable for this.

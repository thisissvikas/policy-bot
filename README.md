# PolicyBot

**AI-powered code review that enforces your org's specific standards and architectural decisions — not generic best practices, yours.**

GitHub Copilot knows how code is generally written. PolicyBot knows how *your org* decided to write it. You define your standards and ADRs once, in plain markdown. PolicyBot reads them and reviews every PR against them — posting inline comments like "this violates ADR-007, the repository pattern your team adopted last March" rather than generic advice that doesn't know your context.

No linter config to replicate across repos. No human who has to remember to check. No AI hallucinating advice that contradicts your actual architectural decisions.

> Status: **Early Development** — GitHub Action and core review pipeline being built. Contributions welcome.

---

## The problem

Your org has coding standards. They live in a wiki page nobody reads, a Confluence doc that's three years out of date, or a Notion page the team agreed on once. Your org also has ADRs — architectural decisions that were made deliberately and should shape how new code is written.

Neither gets enforced. Code review is inconsistent. New engineers don't know the standards exist. Existing engineers forget them under deadline pressure. The gap between "what we decided" and "what gets merged" grows quietly.

Generic AI review tools can flag plausible problems — but they don't know *your* decisions. They don't know that ADR-007 requires all database access to go through repository classes, or that your team specifically banned business logic in Django views. They make their best guess based on training data from the open internet.

PolicyBot closes the gap differently: it reviews against the documents you wrote, not a probability distribution over public code.

---

## How it works

```
  This repo (standards + bot)          Any org repo (PR opened)
  ┌──────────────────────────┐
  │ policies/                │          ┌─────────────────────────┐
  │   standards/             │          │  PR diff                │
  │     python.md            ├────────► │  + detected languages   │
  │     typescript.md        │          │  + changed file paths   │
  │     django.md            │          └────────────┬────────────┘
  │   adrs/                  │                       │
  │     ADR-001-api.md       │                       ▼
  │     ADR-007-repo.md      ├────────► ┌─────────────────────────┐
  │     ADR-011-errors.md    │          │   PolicyBot             │
  │                          │          │                         │
  │ policybot.yaml           │          │ 1. detect languages     │
  │   source: local          │          │ 2. fetch relevant docs  │
  │   root: policies         │          │ 3. review diff vs docs  │
  └──────────────────────────┘          │ 4. post inline comments │
                                        └─────────────────────────┘
```

PolicyBot fetches only the standards and ADRs relevant to the languages and frameworks changed in the PR. A Python-only PR doesn't get your React standards. A PR that doesn't touch database code doesn't get ADR-007.

Standards live in this repo by default, but the source is pluggable — move them to a separate repo with a one-line config change.

---

## What the review looks like

```
┌─────────────────────────────────────────────────────────────┐
│ PolicyBot                                          [bot]     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  payments/src/invoice.py  line 42                           │
│  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄    │
│  🏗️  ADR-007 — Repository Pattern                           │
│  This function accesses `db.session` directly. Per          │
│  ADR-007, all database access should go through a           │
│  repository class. Consider moving this to                  │
│  `InvoiceRepository`.                                       │
│  → Source: adrs/ADR-007-repository-pattern.md               │
│                                                             │
│  payments/src/invoice.py  line 67                           │
│  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄    │
│  📋  Python Standards — Error Handling                      │
│  Bare `except:` catches all exceptions including            │
│  `KeyboardInterrupt` and `SystemExit`. Per our              │
│  standards, catch specific exception types or use           │
│  `except Exception:` at minimum.                            │
│  → Source: standards/python.md#error-handling               │
└─────────────────────────────────────────────────────────────┘
```

Two comment types, both from the same review pass:
- `🏗️ ADR` — architectural decision violated. Links back to the ADR.
- `📋 Standards` — coding standard violated. Links back to the standards doc.

Every comment cites the exact document it's enforcing. Reviewers can follow the link to understand the reasoning, not just the rule.

---

## Setup

### 1. This repo is your standards repo

Standards and ADRs live under `policies/` alongside the bot code in this monorepo:

```
policy-bot/
├── policies/                  # default standards content (edit these)
│   ├── standards/
│   │   ├── python.md
│   │   ├── typescript.md
│   │   ├── django.md
│   │   └── react.md
│   └── adrs/
│       ├── ADR-001-api-versioning.md
│       ├── ADR-007-repository-pattern.md
│       └── ADR-011-error-handling.md
└── policybot.yaml             # maps file patterns to standards + declares source
```

Edit the markdown files directly — no special syntax required.

### 2. `policybot.yaml` — configure rules and source

```yaml
# Standards are in policies/ within this same repo
source:
  type: local
  root: policies        # all doc paths are relative to this folder

standards:
  - match: "**/*.py"
    docs:
      - standards/python.md
  - match: "**/*.ts"
    docs:
      - standards/typescript.md
  - match: "**/views.py"
    docs:
      - standards/django.md

adrs:
  - path: adrs/ADR-001-api-versioning.md
    applies_to: ["**/routes/**", "**/api/**", "**/views.py"]
  - path: adrs/ADR-007-repository-pattern.md
    applies_to: ["**/*.py"]
  - path: adrs/ADR-011-error-handling.md
    applies_to: ["**/*.py", "**/*.ts"]
```

To move standards to a separate repo later, change `source` — nothing else changes:

```yaml
source:
  type: github
  repo: my-org/engineering-standards
  ref: main
```

### 3. Add the GitHub Action to any repo

```yaml
# .github/workflows/policybot.yml
name: PolicyBot Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write  # required: PolicyBot posts inline review comments
    steps:
      - uses: actions/checkout@v4  # required for source.type: local

      - uses: my-org/policybot@v1
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

> **Required:** The `permissions: pull-requests: write` declaration is mandatory. GitHub's default token does not have write access to pull requests unless the job explicitly grants it. Without it, PolicyBot will fail with a `403` when attempting to post review comments. The `ANTHROPIC_API_KEY` secret must also be added to your repo or org secrets before using this action.
>
> **`actions/checkout` is required** when `source.type: local` (the default). Without it, the runner workspace has no files, PolicyBot cannot find `policybot.yaml` or any local standards docs, and falls back to the action's own built-in defaults silently. GitHub's default token does not have write access to pull requests unless the job explicitly grants it. Without it, PolicyBot will fail with a `403` when attempting to post review comments. The `ANTHROPIC_API_KEY` secret must also be added to your repo or org secrets before using this action.

That's it. One file per repo. When standards are updated in this repo, every repo picks them up on the next PR.

### 4. (Optional) Org-wide via GitHub App

Install the PolicyBot GitHub App at the org level and it automatically runs on every repo without adding the workflow file to each one.

---

## Writing standards

Standards are plain markdown. PolicyBot reads them as-is — no special syntax required.

```markdown
# Python Standards

## Error Handling
- Always catch specific exception types. Never use bare `except:`.
- Log exceptions with context before re-raising or swallowing.
- Use custom exception classes for domain errors rather than generic `ValueError`.

## Imports
- Group imports: stdlib → third-party → internal. Separate groups with a blank line.
- No wildcard imports (`from module import *`).

## Functions
- Functions should do one thing. If you need "and" to describe it, consider splitting.
- Maximum function length: 40 lines. Longer functions are a prompt to refactor.
```

ADRs work as-is — PolicyBot reads the context and decision sections and understands what they require of new code. No reformatting needed.

---

## How does this compare to tools I already have?

### vs. GitHub Copilot and AI code review bots

GitHub Copilot, CodeRabbit, and similar tools are trained on public code. They know general best practices. They don't know:

- That your team decided in ADR-007 to always route database access through repository classes
- That your Python standards require domain exceptions instead of generic `ValueError`
- That business logic belongs in services, not views — because your team made that call specifically

When a generic AI reviewer sees `db.session.query(...)` in a view, it might flag it or might not — it depends on whatever training data shaped its opinion that day, and the feedback changes with every model update. When PolicyBot sees the same code, it flags it against ADR-007, the decision record your team wrote, and links back to it.

The difference: **generic AI reviews what's plausibly wrong. PolicyBot enforces what you decided is wrong for your codebase.**

| | Generic AI review (Copilot, CodeRabbit) | PolicyBot |
|---|---|---|
| Source of authority | Training data (public code) | Your standards + ADRs |
| Knows your ADRs | No | Yes |
| Consistent across model updates | No — drifts | Yes — your docs are the truth |
| You control what it enforces | No | Yes |
| Explains why with your reasoning | No | Yes — cites the doc |
| Contradicts your actual decisions | Sometimes | Never |

Use both. Generic AI review catches problems nobody thought to write a standard for. PolicyBot enforces the decisions you did make deliberately.

### vs. linters

Linters enforce syntax and patterns. They can't enforce intent.

| Standard | Linter | PolicyBot |
|---|---|---|
| "Use `const` over `let`" | Yes (ESLint rule) | Yes |
| "No bare `except:`" | Yes (Pylint) | Yes |
| "DB access through repository classes only" | Partial (Semgrep pattern) | Yes |
| "All API responses must follow our error schema" | No | Yes |
| "No business logic in Django views" | No | Yes |
| "Follow the architectural decision in ADR-007" | No | Yes |

Linters require: writing rules in a custom DSL, replicating config across repos, and expressing every constraint as an AST pattern. Standards that require understanding context — "this service layer is too thick", "this bypasses the abstraction we agreed on" — can't be expressed as linter rules.

Run linters alongside PolicyBot. Linters handle the mechanical rules fast and free. PolicyBot handles the semantic and architectural rules that require reading comprehension.

### vs. human code reviewers enforcing standards

Human reviewers forget. They're under deadline pressure. They review in different mental states. They leave the company. Standards that exist only in humans' heads degrade the moment those humans are busy.

PolicyBot is the reviewer who has read all the standards, never forgets them, and shows up for every PR.

---

## Tech Stack

| Component | Technology | Why |
|---|---|---|
| Language | Python 3.12+ with `uv` | Modern, fast tooling |
| CI integration | GitHub Actions + GitHub App | Zero-friction adoption |
| LLM | [Claude API](https://docs.anthropic.com/) | Long context, instruction-following, inline citation |
| Config format | YAML + Markdown | Standards stay human-readable and editable |
| Standards source | Pluggable provider (`local` or `github`) | Start in-repo, move later without changing the bot |
| Language detection | File extension + import pattern matching | Lightweight, no AST needed |
| PR interaction | GitHub REST API | Post inline review comments on specific lines |

---

## Project Structure

```
policy-bot/
├── action.yml                  # GitHub Action definition (composite)
├── policybot.yaml              # maps file patterns → standards/ADRs
├── pyproject.toml              # uv-managed project + tool config
│
├── policies/                   # default standards content (edit or replace these)
│   ├── standards/
│   │   ├── python.md
│   │   ├── typescript.md
│   │   ├── django.md
│   │   └── react.md
│   └── adrs/
│       ├── ADR-001-api-versioning.md
│       └── ...
│
├── docs/                       # documentation (deployment, contributing, etc.)
│
├── policybot/                  # bot implementation
│   ├── models.py               # shared Pydantic v2 models
│   ├── config.py               # policybot.yaml loader + validation
│   ├── detector.py             # language/framework detection from diff
│   ├── providers/
│   │   ├── base.py             # StandardsProvider protocol
│   │   ├── local.py            # reads from local filesystem
│   │   └── github.py          # fetches from a remote GitHub repo
│   ├── fetcher.py              # resolves provider + fetches docs
│   ├── github_client.py        # httpx wrapper for GitHub REST API
│   ├── reviewer.py             # build prompt, call Claude, parse response
│   ├── commenter.py            # post inline comments via GitHub API
│   └── cli.py                  # local dry-run: policybot review --dry-run
│
└── tests/
```

---

## Roadmap

### Phase 1 — Core (current)
- [ ] GitHub Action: fetch standards + ADRs, call Claude, post inline comments
- [ ] `policybot.yaml` config schema — file pattern → standards/ADR mapping
- [ ] Pluggable standards source: `local` (in-repo) and `github` (remote repo)
- [ ] Two comment types: `📋 Standards` and `🏗️ ADR`
- [ ] Link each comment back to the source document
- [ ] `policybot review --dry-run` CLI for local testing

### Phase 2 — Org-wide
- [ ] GitHub App — install once at org level, no per-repo workflow file
- [ ] Severity levels: `error` (blocks merge) vs `warning` (informational)
- [ ] Comment deduplication — don't re-post the same violation on re-push
- [ ] Compliance summary across repos

### Phase 3 — Intelligence
- [ ] Learn from dismissed comments — if reviewers consistently dismiss a finding, flag the standard for review
- [ ] Standards coverage report — which standards have never triggered?
- [ ] Auto-suggest standard updates when merged code patterns diverge from the standard
- [ ] Support for private standards scoped to specific teams or repos

---

## Contributing

Good first areas:
- **Language detection** — improve framework detection from file paths and imports
- **Prompt engineering** — improve how standards + ADRs are presented to the model
- **Comment formatting** — make inline comments clearer and more actionable
- **Standards** — improve the reference standards in `policies/standards/` and `policies/adrs/`
- **Tests** — unit tests for config loading, language detection, comment posting

See [docs/contributing.md](docs/contributing.md) for setup instructions, or [docs/deployment.md](docs/deployment.md) for deployment options.

---

## License

MIT

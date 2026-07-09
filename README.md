# PolicyBot

**AI-powered code review that enforces your coding standards and architectural decisions — automatically, on every PR, across every repo.**

You define your standards and ADRs once in a central place. PolicyBot reads them, understands them, and reviews every pull request against them — posting inline comments that distinguish "this violates our Python style guide" from "this conflicts with ADR-007 on the repository pattern." No linter config to copy across repos. No human has to remember to check.

> Status: **Early Development** — GitHub Action and core review pipeline being built. Contributions welcome.

---

## The problem

Your org has coding standards. They live in a wiki page nobody reads, a Confluence doc that's three years out of date, or a Notion page the team agreed on once. Your org also has ADRs — architectural decisions that were made deliberately and should shape how new code is written.

Neither gets enforced. Code review is inconsistent. New engineers don't know the standards exist. Existing engineers forget them under deadline pressure. The gap between "what we decided" and "what gets merged" grows quietly.

PolicyBot closes that gap by making your standards and ADRs active participants in every code review.

---

## How it works

```
  Central standards repo             Any org repo (PR opened)
  ┌─────────────────────┐
  │ standards/          │            ┌─────────────────────────┐
  │   python.md         │            │  PR diff                │
  │   typescript.md     ├──────────► │  + detected languages   │
  │   django.md         │            │  + changed file paths   │
  │   react.md          │            └────────────┬────────────┘
  │                     │                         │
  │ adrs/               │                         ▼
  │   ADR-001-api.md    │            ┌─────────────────────────┐
  │   ADR-007-repo.md   ├──────────► │   PolicyBot             │
  │   ADR-011-errors.md │            │                         │
  └─────────────────────┘            │ 1. detect languages     │
                                     │ 2. fetch relevant docs  │
                                     │ 3. review diff vs docs  │
                                     │ 4. post inline comments │
                                     └─────────────────────────┘
```

PolicyBot fetches only the standards and ADRs relevant to the languages and frameworks changed in the PR. A Python-only PR doesn't get your React standards. A PR that doesn't touch database code doesn't get ADR-007.

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

---

## Setup

### 1. Create your central standards repo

```
my-org/engineering-standards
├── standards/
│   ├── python.md
│   ├── typescript.md
│   ├── django.md          # framework-specific
│   └── react.md
├── adrs/
│   ├── ADR-001-api-versioning.md
│   ├── ADR-007-repository-pattern.md
│   └── ADR-011-error-handling.md
└── policybot.yaml         # maps file patterns to standards
```

### 2. Define your `policybot.yaml`

```yaml
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
    steps:
      - uses: my-org/policybot@v1
        with:
          standards-repo: my-org/engineering-standards
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

That's it. One file per repo. When the central standards repo updates, every repo picks up the new standards on the next PR — nothing to change in each repo.

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

## Why not just use a linter?

Linters enforce syntax and patterns. They can't enforce intent.

| Standard | Linter | PolicyBot |
|---|---|---|
| "Use `const` over `let`" | Yes (ESLint rule) | Yes |
| "No bare `except:`" | Yes (Pylint) | Yes |
| "DB access through repository classes only" | Partial (Semgrep pattern) | Yes |
| "All API responses must follow our error schema" | No | Yes |
| "No business logic in Django views" | No | Yes |
| "Follow the architectural decision in ADR-007" | No | Yes |

PolicyBot is not a replacement for linters — run both. Linters handle the mechanical rules fast and free. PolicyBot handles the semantic and architectural rules that require understanding context.

---

## Tech Stack

| Component | Technology | Why |
|---|---|---|
| CI integration | GitHub Actions + GitHub App | Zero-friction adoption |
| LLM | [Claude API](https://docs.anthropic.com/) | Long context, instruction-following, inline citation |
| Config format | YAML + Markdown | Standards stay human-readable and editable |
| Language detection | `linguist` / file extension mapping | Lightweight, no AST needed |
| PR interaction | GitHub REST API | Post inline review comments on specific lines |

---

## Roadmap

### Phase 1 — Core (current)
- [ ] GitHub Action: fetch standards + ADRs, call Claude, post inline comments
- [ ] `policybot.yaml` config schema — file pattern → standards/ADR mapping
- [ ] Two comment types: `📋 Standards` and `🏗️ ADR`
- [ ] Link each comment back to the source document and line

### Phase 2 — Org-wide
- [ ] GitHub App — install once at org level, no per-repo workflow file
- [ ] `agentmesh policy status` equivalent — compliance summary across repos
- [ ] Severity levels: `error` (blocks merge) vs `warning` (informational)
- [ ] Comment deduplication — don't re-post the same violation on re-push

### Phase 3 — Intelligence
- [ ] Learn from dismissed comments — if reviewers consistently dismiss a finding, flag the standard for review
- [ ] Standards coverage report — which standards have never triggered? May be redundant or too vague.
- [ ] Auto-suggest standard updates when code patterns in merged PRs diverge from the standard
- [ ] Support for private standards that apply to specific teams or repos only

---

## Project Structure

```
policybot/
├── action.yml                  # GitHub Action definition
├── policybot/
│   ├── config.py               # policybot.yaml loader + validation
│   ├── detector.py             # language/framework detection from diff
│   ├── fetcher.py              # fetch standards + ADRs from central repo
│   ├── reviewer.py             # build prompt, call Claude, parse response
│   ├── commenter.py            # post inline comments via GitHub API
│   └── cli.py                  # local dry-run: policybot review <diff>
├── tests/
└── pyproject.toml
```

---

## Contributing

Good first areas:
- **Language detection** — improve framework detection from file paths and imports
- **Prompt engineering** — improve how standards + ADRs are presented to the model
- **Comment formatting** — make inline comments clearer and more actionable
- **Tests** — unit tests for config loading, language detection, comment posting

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions.

---

## License

MIT

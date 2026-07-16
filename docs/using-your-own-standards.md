# Using Your Own Standards & ADRs

By default PolicyBot uses the standards and ADRs in this repo under `policies/` (`policies/standards/`, `policies/adrs/`). This page covers how to replace them entirely with your org's own documents — and how the `policybot.yaml` config file controls all of it.

---

## How it works

The `policybot.yaml` in the **target repo being reviewed** is the control plane. It tells PolicyBot:

1. **Where** to fetch standards from (`source`)
2. **Which** files trigger which standards (`standards[].match`)
3. **Which** ADRs apply to which files (`adrs[].applies_to`)
4. **How severe** each violation is (`severity: warning | error`)

If the target repo has no `policybot.yaml`, PolicyBot falls back to the action's own built-in config (this repo's defaults). To use your own standards, you just provide a `policybot.yaml` — the defaults are automatically overridden.

---

## Option A — Separate standards repo (recommended for orgs)

Create `my-org/engineering-standards` with your own markdown files and a `policybot.yaml`. Each target repo points to it.

### 1. Create your standards repo

```
my-org/engineering-standards/
├── standards/
│   ├── python.md           # your Python standards
│   ├── typescript.md
│   └── java.md
├── adrs/
│   ├── ADR-001-api-design.md
│   └── ADR-042-database-access.md
└── (no policybot.yaml needed here — it lives in the target repos)
```

Standards are plain markdown — write them however your team documents decisions today.

### 2. Add `policybot.yaml` to each target repo

```yaml
# policybot.yaml (in the repo being reviewed)
source:
  type: github
  repo: my-org/engineering-standards
  ref: main                       # or a specific tag for stability

standards:
  - match: "**/*.py"
    docs:
      - standards/python.md
    severity: warning

  - match: "**/*.ts"
    docs:
      - standards/typescript.md
    severity: warning

adrs:
  - path: adrs/ADR-042-database-access.md
    applies_to: ["**/*.py", "**/*.java"]
    severity: error               # error = blocks merge
```

### 3. Give the action read access to your standards repo

If `my-org/engineering-standards` is **public** — no extra setup needed.

If it's **private**, a single `github.token` cannot cross repository boundaries. You must supply a token that covers both the target repo (to read the diff and post comments) and the standards repo (to fetch docs):

```yaml
# in the target repo's workflow
- uses: thisissvikas/policy-bot@v1
  with:
    anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
    github-token: ${{ secrets.ORG_STANDARDS_PAT }}
```

**What the token needs:**

| Scope | Why |
|---|---|
| `pull-requests: write` on the **target repo** | Post inline review comments |
| `contents: read` on the **standards repo** | Fetch standards and ADR docs |

**Classic PAT:** the `repo` scope grants both (but is broader than needed — it includes write access to all repos).

**Fine-grained PAT:** set `Contents: Read-only` on the standards repo and `Pull requests: Read and write` on the target repo. If the two repos are in **different organisations**, a personal fine-grained PAT is required — org-scoped fine-grained PATs cannot span organisations.

> **Silent failure mode:** if the token lacks `contents: read` on the standards repo, every doc fetch returns a 404. PolicyBot treats 404 as "doc not found" and skips silently. The review runs with zero standards loaded and reports "no violations found" — a false clean result with no error message. Always verify the token has the right scopes before relying on review results.

### Updating standards

Edit markdown files in `my-org/engineering-standards` → push → all target repos pick up the new standards on the next PR. Nothing to change in the target repos.

---

## Option B — Each repo owns its own standards (local)

Best for teams with very different codebases and no shared standards.

```yaml
# policybot.yaml
source:
  type: local              # read from this same repo

standards:
  - match: "**/*.py"
    docs:
      - docs/standards/python.md   # your own standards file, anywhere in the repo
```

```
my-service/
├── docs/
│   └── standards/
│       └── python.md       # this team's Python rules
└── policybot.yaml
```

---

## Option C — Fork PolicyBot and own the whole thing

Best if you want full control over the action code itself, not just the standards.

```bash
# Fork on GitHub, then:
git clone https://github.com/MY-ORG/policy-bot.git
cd policy-bot

# Replace the default standards content with yours
rm -rf policies/standards/ policies/adrs/
cp -r /path/to/your/standards policies/standards/
cp -r /path/to/your/adrs policies/adrs/

# Update policybot.yaml rules to match (source.root stays as "policies")
vim policybot.yaml

git add . && git commit -m "Replace with org standards"
git tag v1 && git push origin v1
```

Target repos reference your fork:

```yaml
- uses: my-org/policy-bot@v1    # your fork, not thisissvikas/policy-bot
```

Future updates to upstream policy-bot are pulled in manually by merging from upstream.

---

## Disabling specific default rules

If you use the action without a `policybot.yaml`, all default rules run. To selectively disable some, provide your own `policybot.yaml` and simply omit the rules you don't want:

```yaml
# policybot.yaml — only enforce Python standards, skip everything else
source:
  type: github
  repo: my-org/engineering-standards

standards:
  - match: "**/*.py"
    docs:
      - standards/python.md
    severity: warning

adrs: []   # no ADRs enforced in this repo
```

---

## Severity: controlling what blocks a merge

Every standard and ADR can be `warning` or `error`:

```yaml
standards:
  - match: "**/*.py"
    docs: [standards/python.md]
    severity: warning        # posts comment, does not block merge

adrs:
  - path: adrs/ADR-042-database-access.md
    applies_to: ["**/*.py"]
    severity: error          # posts comment AND exits 2 → blocks merge in CI
```

To wire `error` violations to block a merge, set the workflow step to fail the check:

```yaml
- uses: thisissvikas/policy-bot@v1
  with:
    anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
# Exit code 2 = error violations found → the step fails → check fails → merge blocked
# (this is the default behaviour — no extra config needed)
```

In GitHub branch protection: enable **"Require status checks to pass"** and add the PolicyBot check. Any `error`-severity violation now blocks the PR.

---

## policybot.yaml reference

```yaml
# Source: where to fetch standards docs from
source:
  type: local | github          # required, default: local

  # local options
  root: .                       # path relative to policybot.yaml, default: .

  # github options
  repo: owner/repo              # required for type: github
  ref: main                     # branch/tag/SHA, default: main (see warning below)

# Standards: map file globs → docs
standards:
  - match: "**/*.py"            # gitignore-style glob
    docs:
      - standards/python.md     # path within the source root/repo
      - standards/django.md     # multiple docs allowed
    severity: warning           # warning | error, default: warning

# ADRs: map docs → file globs they apply to
adrs:
  - path: adrs/ADR-007.md       # path within the source root/repo
    applies_to:
      - "**/*.py"               # list of globs
      - "**/services/**"
    severity: error
```

**Glob syntax** follows `.gitignore` rules: `**` matches any depth, `*` matches within one segment, `?` matches a single character.

> **`ref` default is `main` — silent failure if wrong.** If your standards repo's default branch is `master`, `trunk`, or anything other than `main`, every doc fetch returns a 404. PolicyBot treats these as "doc not found" and skips silently — the review runs with zero standards and reports "no violations found." Always set `ref` explicitly to match your standards repo's actual default branch.

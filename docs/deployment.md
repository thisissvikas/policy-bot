# Deploying & Distributing PolicyBot

There are three ways to make PolicyBot available to repos in your org. They differ in setup effort and how much control repos have.

---

## Option 1 — Public repo + per-repo workflow file

**Effort:** low. **Marketplace:** not required.

Any public GitHub repo with an `action.yml` is immediately usable. You don't need to publish to the marketplace — that's optional discoverability only.

### Step 1 — Tag a release

```bash
git tag v1.0.0
git push origin v1.0.0

# Also maintain a floating major-version tag (most users reference this)
git tag -f v1 v1.0.0
git push origin v1 --force
```

### Step 2 — Users add one workflow file to their repo

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
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - uses: thisissvikas/policy-bot@v1
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Step 3 — Add the secret

In the target repo (or at org level for all repos): **Settings → Secrets → ANTHROPIC_API_KEY**

That's it. Every PR in that repo now gets reviewed.

### Updating

When you push a new release and move the `v1` tag, all repos using `@v1` pick up the new version on their next PR — they don't change anything.

### (Optional) Publish to GitHub Marketplace

Publishing adds a listing on marketplace.github.com so teams can discover the action by searching. It doesn't change how it works — just visibility.

1. Go to the action repo on GitHub
2. Edit a release → check "Publish this Action to the GitHub Marketplace"
3. Fill in categories and description

---

## Option 2 — Org-wide required workflow (no per-repo file)

**Effort:** medium (org admin required). **Per-repo setup:** zero.

GitHub orgs can define workflows that automatically run on every repo, without any file in those repos.

### Setup

1. Go to **github.com/orgs/YOUR-ORG/settings/actions**
2. Under **Required workflows**, click **Add workflow**
3. Select your policy-bot repo and the workflow file path (`.github/workflows/ci.yml` or create a dedicated one)
4. Save — the workflow now runs on every PR across the org

### Add the secret at org level

**Org Settings → Secrets → Actions → New org secret**

Add `ANTHROPIC_API_KEY` and set access to "All repositories" (or selected repos).

### Notes

- Requires GitHub Team or Enterprise
- Each target repo can still add its own `policybot.yaml` to customize which standards apply (see [using-your-own-standards.md](using-your-own-standards.md))
- If a repo has no `policybot.yaml`, PolicyBot falls back to the action's built-in defaults

---

## Option 3 — GitHub App (org-wide, zero config per repo)

**Effort:** high (requires a running server). **Per-repo setup:** zero. **Admin:** install once at org level.

This is the cleanest end-user experience. An org admin installs the app once and every repo is covered — no workflow files, no required-workflow config.

**This is Phase 2 in the roadmap** — not yet implemented.

### How it works (when built)

```
GitHub App (installed at org level)
       │
       │  pull_request webhook
       ▼
PolicyBot server (your deployment)
       │
       ├── reads policybot.yaml from the PR's repo (or uses defaults)
       ├── fetches relevant standards
       ├── calls Claude
       └── posts inline review comments
```

### What needs to be built

- `policybot/app.py` — FastAPI webhook server with HMAC signature verification
- `policybot/github_app.py` — GitHub App JWT auth + installation token exchange
- `Dockerfile` + deployment config

### Deployment options when ready

| Platform | Command |
|---|---|
| [Fly.io](https://fly.io) | `fly launch && fly deploy` |
| [Railway](https://railway.app) | Connect repo → auto-deploy |
| Any container host | `docker build && docker push` |

---

## Comparison

| | Option 1 | Option 2 | Option 3 |
|---|---|---|---|
| Per-repo setup | 1 workflow file | None | None |
| Org admin required | No | Yes | Yes |
| Requires running server | No | No | Yes |
| Per-repo customization | Yes | Yes (via `policybot.yaml`) | Yes (via `policybot.yaml`) |
| Available now | ✅ | ✅ | 🔲 Phase 2 |

For most orgs, **Option 1** is the right starting point. Migrate to **Option 2** once the action is proven, and consider **Option 3** only when you want zero-friction onboarding for a large number of repos.

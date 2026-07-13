import argparse
import asyncio
import os
import sys
from pathlib import Path

import structlog

from policybot.commenter import format_comment, post_review
from policybot.config import ConfigError, get_relevant_docs, get_rule_severity, load_config
from policybot.fetcher import fetch_docs
from policybot.github_client import GitHubClient, GitHubError
from policybot.models import PolicyBotConfig
from policybot.providers.github import GitHubProvider
from policybot.providers.local import LocalProvider
from policybot.reviewer import DEFAULT_MODEL, apply_severity, review_diff

log = structlog.get_logger()


def _configure_logging(verbose: bool) -> None:
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(10 if verbose else 20),
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if sys.stderr.isatty()
            else structlog.processors.JSONRenderer(),
        ],
    )


def _build_provider(
    config: PolicyBotConfig,
    github_token: str | None,
    config_path: Path,
) -> LocalProvider | GitHubProvider:
    if config.source.type == "local":
        root = (config_path.parent / config.source.root).resolve()
        return LocalProvider(root)
    if config.source.type == "github":
        if not github_token:
            raise ValueError("GITHUB_TOKEN is required when source.type is 'github'")
        client = GitHubClient(github_token)
        return GitHubProvider(client, config.source.repo, config.source.ref)
    raise ValueError(f"Unknown source type: {config.source.type}")


async def _run_review(args: argparse.Namespace) -> int:
    _configure_logging(args.verbose)

    config_path = Path(args.config)
    try:
        config = load_config(config_path)
    except ConfigError as exc:
        log.error("config_error", error=str(exc))
        return 1

    github_token = os.environ.get("GITHUB_TOKEN", "")

    if args.diff:
        diff = Path(args.diff).read_text(encoding="utf-8")
        changed_files = [line[6:] for line in diff.splitlines() if line.startswith("+++ b/")]
    elif args.pr and args.repo:
        if not github_token:
            log.error("missing_github_token")
            return 1
        owner, repo_name = args.repo.split("/", 1)
        async with GitHubClient(github_token) as gh:
            try:
                diff = await gh.get_pr_diff(owner, repo_name, args.pr)
                changed_files = await gh.get_pr_files(owner, repo_name, args.pr)
            except GitHubError as exc:
                log.error("github_error", error=str(exc))
                return 1
    else:
        log.error("provide_diff_or_pr")
        return 1

    standard_paths, adr_paths = get_relevant_docs(config, changed_files)
    if not standard_paths and not adr_paths:
        log.info("no_relevant_docs", changed_files=changed_files)
        print("PolicyBot: no relevant standards or ADRs for the changed files.")
        return 0

    provider = _build_provider(config, github_token or None, config_path)
    standards_docs = await fetch_docs(provider, standard_paths)
    adr_docs = await fetch_docs(provider, adr_paths)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    try:
        result = await review_diff(
            diff=diff,
            standards_docs=standards_docs,
            adr_docs=adr_docs,
            api_key=api_key,
            model=args.model,
        )
    except Exception as exc:
        log.error("review_failed", error=str(exc))
        return 1

    severity_map = {
        doc: get_rule_severity(config, doc) for doc in list(standards_docs) + list(adr_docs)
    }
    result = apply_severity(result, severity_map)

    if not result.violations:
        print("PolicyBot: no violations found.")
        return 0

    if args.dry_run:
        print(f"\nPolicyBot found {len(result.violations)} violation(s):\n")
        for v in result.violations:
            print(f"  {v.file}:{v.line}")
            print(f"  {format_comment(v)}")
            print()
        has_errors = any(v.severity == "error" for v in result.violations)
        return 2 if has_errors else 0

    if not args.repo or not args.pr:
        log.error("repo_and_pr_required_to_post")
        return 1

    owner, repo_name = args.repo.split("/", 1)
    async with GitHubClient(github_token) as gh:
        try:
            commit_sha = await gh.get_pr_head_sha(owner, repo_name, args.pr)
            await post_review(gh, owner, repo_name, args.pr, commit_sha, result.violations)
        except GitHubError as exc:
            log.error("post_review_failed", error=str(exc))
            return 1

    has_errors = any(v.severity == "error" for v in result.violations)
    return 2 if has_errors else 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="policybot",
        description="AI-powered PR review against your coding standards and ADRs",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    review = sub.add_parser("review", help="Review a PR or diff file")
    review.add_argument(
        "--config",
        default="policybot.yaml",
        help="Path to policybot.yaml (default: policybot.yaml)",
    )
    review.add_argument("--diff", help="Path to a local unified diff file")
    review.add_argument("--pr", type=int, help="GitHub PR number")
    review.add_argument("--repo", help="GitHub repo (owner/repo), required with --pr")
    review.add_argument(
        "--dry-run",
        action="store_true",
        help="Print violations to stdout without posting to GitHub",
    )
    review.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Claude model to use (default: {DEFAULT_MODEL})",
    )
    review.add_argument("--verbose", "-v", action="store_true", help="Debug logging")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    sys.exit(asyncio.run(_run_review(args)))


if __name__ == "__main__":
    main()

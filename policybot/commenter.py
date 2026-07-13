import structlog

from policybot.github_client import GitHubClient
from policybot.models import ReviewComment, Violation

log = structlog.get_logger()

ADR_ICON = "🏗️"
STANDARDS_ICON = "📋"


def format_comment(violation: Violation) -> str:
    """Render a GitHub inline comment body for a violation."""
    icon = ADR_ICON if violation.type == "adr" else STANDARDS_ICON
    label = "ADR" if violation.type == "adr" else "Standards"
    section = f" — {violation.source_section}" if violation.source_section else ""
    severity_tag = " ⚠️ **[error]**" if violation.severity == "error" else ""

    lines = [
        f"{icon} **{label}{section}**{severity_tag}",
        "",
        violation.message,
        "",
        f"→ Source: `{violation.source_doc}`",
    ]
    return "\n".join(lines)


async def post_review(
    client: GitHubClient,
    owner: str,
    repo: str,
    pr_number: int,
    commit_sha: str,
    violations: list[Violation],
) -> None:
    """Post all violations as a single GitHub PR review with inline comments."""
    if not violations:
        log.info("no_violations_to_post")
        return

    comments = [
        ReviewComment(
            path=v.file,
            line=v.line,
            body=format_comment(v),
        )
        for v in violations
    ]

    await client.create_review(
        owner=owner,
        repo=repo,
        pr_number=pr_number,
        commit_sha=commit_sha,
        comments=comments,
        body=(f"PolicyBot found {len(violations)} violation(s). See inline comments for details."),
    )

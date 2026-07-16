import re

import structlog

from policybot.github_client import GitHubClient
from policybot.models import ReviewComment, Violation

log = structlog.get_logger()

ADR_ICON = "🏗️"
STANDARDS_ICON = "📋"


def get_diff_right_lines(diff: str) -> dict[str, set[int]]:
    """Parse a unified diff and return valid right-side line numbers per file.

    Only lines that exist in the new version of the file (added '+' or context ' ')
    are valid targets for a RIGHT-side review comment. Posting a comment on a
    removed line ('-') with side='RIGHT' causes GitHub to return a 422 for the
    entire review, discarding all comments.
    """
    valid: dict[str, set[int]] = {}
    current_file: str | None = None
    right_line = 0

    for raw in diff.splitlines():
        if raw.startswith("+++ b/"):
            current_file = raw[6:]
            valid.setdefault(current_file, set())
            right_line = 0
        elif current_file is not None and raw.startswith("@@ "):
            m = re.search(r"\+(\d+)", raw)
            if m:
                right_line = int(m.group(1)) - 1
        elif current_file is not None:
            if raw.startswith("+"):
                right_line += 1
                valid[current_file].add(right_line)
            elif raw.startswith("-"):
                pass  # left-side only — not a valid RIGHT comment target
            elif not raw.startswith("\\"):  # context line (not "\ No newline at end of file")
                right_line += 1
                valid[current_file].add(right_line)

    return valid


def filter_postable_violations(
    violations: list[Violation], diff: str
) -> tuple[list[Violation], int]:
    """Return only violations whose line exists on the right side of the diff.

    Returns (postable_violations, skipped_count).
    """
    right_lines = get_diff_right_lines(diff)
    postable = [v for v in violations if v.line in right_lines.get(v.file, set())]
    return postable, len(violations) - len(postable)


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

import os

import structlog
from anthropic import AsyncAnthropic
from anthropic.types import MessageParam, ToolChoiceToolParam, ToolParam

from policybot.models import ReviewResult, Violation

log = structlog.get_logger()

DEFAULT_MODEL = "claude-sonnet-4-5"
DEFAULT_MAX_TOKENS = 4096

_SYSTEM_PROMPT = """\
You are PolicyBot, an automated code reviewer. Your job is to check a PR diff \
against the team's coding standards and architectural decisions (ADRs).

When reviewing, follow these rules:
- Only flag violations explicitly covered in the provided standards or ADRs
- Do not flag subjective preferences or anything not mentioned in the standards
- Be specific: reference the exact line and the exact section of the standard violated
- Keep messages concise and actionable — tell the author what to change and why
- If no violations are found, call report_violations with an empty list
"""


def build_prompt(
    diff: str,
    standards_docs: dict[str, str],
    adr_docs: dict[str, str],
) -> str:
    parts: list[str] = []

    if standards_docs:
        parts.append("## Coding Standards in scope\n")
        for doc_path, content in standards_docs.items():
            parts.append(f"### {doc_path}\n\n{content}\n")

    if adr_docs:
        parts.append("## Architectural Decision Records (ADRs) in scope\n")
        for doc_path, content in adr_docs.items():
            parts.append(f"### {doc_path}\n\n{content}\n")

    parts.append("## PR Diff\n\n```diff\n" + diff + "\n```\n")
    parts.append(
        "Review this diff against the standards and ADRs above. "
        "Call `report_violations` with every violation you find — "
        "or with an empty list if there are none."
    )
    return "\n".join(parts)


async def review_diff(
    diff: str,
    standards_docs: dict[str, str],
    adr_docs: dict[str, str],
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> ReviewResult:
    """Call Claude with the diff and relevant docs, return structured violations."""
    if not diff.strip():
        log.info("empty_diff_skipped")
        return ReviewResult()

    resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not resolved_key:
        raise ValueError("ANTHROPIC_API_KEY is required")

    client = AsyncAnthropic(api_key=resolved_key)
    prompt = build_prompt(diff, standards_docs, adr_docs)

    tool_schema: ToolParam = {
        "name": "report_violations",
        "description": "Report all policy violations found in the PR diff",
        "input_schema": ReviewResult.model_json_schema(),
    }

    log.info(
        "calling_claude",
        model=model,
        standards=list(standards_docs.keys()),
        adrs=list(adr_docs.keys()),
    )

    tool_choice: ToolChoiceToolParam = {"type": "tool", "name": "report_violations"}
    messages: list[MessageParam] = [{"role": "user", "content": prompt}]

    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=_SYSTEM_PROMPT,
        tools=[tool_schema],
        tool_choice=tool_choice,
        messages=messages,
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "report_violations":
            result = ReviewResult.model_validate(block.input)
            log.info("violations_found", count=len(result.violations))
            return result

    log.warning("no_tool_use_block_in_response")
    return ReviewResult()


def apply_severity(
    result: ReviewResult,
    severity_map: dict[str, str],
) -> ReviewResult:
    """Annotate violations with severity from config rules."""
    updated: list[Violation] = []
    for v in result.violations:
        severity = severity_map.get(v.source_doc, "warning")
        updated.append(v.model_copy(update={"severity": severity}))
    return ReviewResult(violations=updated)

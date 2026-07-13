from unittest.mock import AsyncMock, MagicMock

from policybot.commenter import format_comment, post_review
from policybot.models import Violation


def _make_violation(
    type: str = "standard",
    section: str = "Error Handling",
    severity: str = "warning",
    source_doc: str = "standards/python.md",
) -> Violation:
    return Violation(
        file="app/service.py",
        line=42,
        type=type,  # type: ignore[arg-type]
        message="Bare `except:` catches everything including KeyboardInterrupt.",
        source_doc=source_doc,
        source_section=section,
        severity=severity,  # type: ignore[arg-type]
    )


def test_format_comment_standards_icon() -> None:
    comment = format_comment(_make_violation(type="standard"))
    assert "📋" in comment
    assert "Standards" in comment


def test_format_comment_adr_icon() -> None:
    comment = format_comment(_make_violation(type="adr", source_doc="adrs/ADR-007.md"))
    assert "🏗️" in comment
    assert "ADR" in comment


def test_format_comment_includes_section() -> None:
    comment = format_comment(_make_violation(section="Error Handling"))
    assert "Error Handling" in comment


def test_format_comment_no_section() -> None:
    comment = format_comment(_make_violation(section=""))
    assert "📋 **Standards**" in comment


def test_format_comment_includes_message() -> None:
    v = _make_violation()
    comment = format_comment(v)
    assert v.message in comment


def test_format_comment_includes_source_doc() -> None:
    v = _make_violation()
    comment = format_comment(v)
    assert v.source_doc in comment


def test_format_comment_error_severity_tag() -> None:
    comment = format_comment(_make_violation(severity="error"))
    assert "[error]" in comment


def test_format_comment_warning_no_error_tag() -> None:
    comment = format_comment(_make_violation(severity="warning"))
    assert "[error]" not in comment


def test_format_comment_adr_with_source_section() -> None:
    v = _make_violation(type="adr", section="Repository Pattern", source_doc="adrs/ADR-007.md")
    comment = format_comment(v)
    assert "ADR — Repository Pattern" in comment
    assert "adrs/ADR-007.md" in comment


async def test_post_review_calls_create_review() -> None:
    mock_client = MagicMock()
    mock_client.create_review = AsyncMock()

    violations = [_make_violation(), _make_violation(type="adr", source_doc="adrs/ADR-007.md")]
    await post_review(mock_client, "owner", "repo", 1, "abc123", violations)

    mock_client.create_review.assert_called_once()
    call_kwargs = mock_client.create_review.call_args.kwargs
    assert call_kwargs["owner"] == "owner"
    assert call_kwargs["pr_number"] == 1
    assert len(call_kwargs["comments"]) == 2


async def test_post_review_no_violations() -> None:
    mock_client = MagicMock()
    mock_client.create_review = AsyncMock()
    await post_review(mock_client, "owner", "repo", 1, "abc123", [])
    mock_client.create_review.assert_not_called()

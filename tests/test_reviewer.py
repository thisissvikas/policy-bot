from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from policybot.models import ReviewResult, Violation
from policybot.reviewer import apply_severity, build_prompt, review_diff


def test_build_prompt_includes_standards() -> None:
    prompt = build_prompt(
        diff="--- a/file.py\n+++ b/file.py\n+def foo(): pass\n",
        standards_docs={"standards/python.md": "# Python\n## Error Handling\n- catch specific"},
        adr_docs={},
    )
    assert "standards/python.md" in prompt
    assert "catch specific" in prompt
    assert "PR Diff" in prompt


def test_build_prompt_includes_adrs() -> None:
    prompt = build_prompt(
        diff="--- a/file.py\n+++ b/file.py\n",
        standards_docs={},
        adr_docs={"adrs/ADR-007.md": "# ADR-007\nUse repositories"},
    )
    assert "ADR-007" in prompt
    assert "Use repositories" in prompt


def test_build_prompt_empty_docs() -> None:
    prompt = build_prompt(
        diff="+++ b/file.py\n+x = 1\n",
        standards_docs={},
        adr_docs={},
    )
    assert "PR Diff" in prompt
    assert "report_violations" in prompt


def test_build_prompt_multiple_docs() -> None:
    prompt = build_prompt(
        diff="diff",
        standards_docs={"a.md": "# A", "b.md": "# B"},
        adr_docs={"adr1.md": "# ADR1"},
    )
    assert "### a.md" in prompt
    assert "### b.md" in prompt
    assert "### adr1.md" in prompt


async def test_review_diff_empty_diff_returns_empty() -> None:
    result = await review_diff(
        diff="",
        standards_docs={},
        adr_docs={},
        api_key="test-key",
    )
    assert result.violations == []


async def test_review_diff_calls_claude() -> None:
    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.name = "report_violations"
    mock_block.input = {
        "violations": [
            {
                "file": "app/service.py",
                "line": 10,
                "type": "standard",
                "message": "Bare except caught",
                "source_doc": "standards/python.md",
                "source_section": "Error Handling",
                "severity": "warning",
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.content = [mock_block]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    with patch("policybot.reviewer.AsyncAnthropic", return_value=mock_client):
        result = await review_diff(
            diff="+++ b/app/service.py\n+except:\n+    pass\n",
            standards_docs={"standards/python.md": "# Python"},
            adr_docs={},
            api_key="test-key",
        )

    assert len(result.violations) == 1
    assert result.violations[0].file == "app/service.py"
    assert result.violations[0].type == "standard"


async def test_review_diff_no_tool_use_returns_empty() -> None:
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = "No violations found."

    mock_response = MagicMock()
    mock_response.content = [mock_block]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    with patch("policybot.reviewer.AsyncAnthropic", return_value=mock_client):
        result = await review_diff(
            diff="+++ b/clean.py\n+x = 1\n",
            standards_docs={"standards/python.md": "# Python"},
            adr_docs={},
            api_key="test-key",
        )

    assert result.violations == []


async def test_review_diff_missing_api_key() -> None:
    import os

    os.environ.pop("ANTHROPIC_API_KEY", None)
    with (
        pytest.raises(ValueError, match="ANTHROPIC_API_KEY"),
        patch.dict("os.environ", {}, clear=True),
    ):
        await review_diff(
            diff="+++ b/file.py\n+x = 1\n",
            standards_docs={},
            adr_docs={},
            api_key=None,
        )


def test_apply_severity_maps_from_config() -> None:
    result = ReviewResult(
        violations=[
            Violation(
                file="app.py",
                line=1,
                type="adr",
                message="violation",
                source_doc="adrs/ADR-007.md",
                source_section="",
                severity="warning",
            ),
            Violation(
                file="app.py",
                line=2,
                type="standard",
                message="violation",
                source_doc="standards/python.md",
                source_section="",
                severity="warning",
            ),
        ]
    )
    severity_map = {"adrs/ADR-007.md": "error", "standards/python.md": "warning"}
    updated = apply_severity(result, severity_map)
    assert updated.violations[0].severity == "error"
    assert updated.violations[1].severity == "warning"


def test_apply_severity_defaults_to_warning() -> None:
    result = ReviewResult(
        violations=[
            Violation(
                file="app.py",
                line=1,
                type="standard",
                message="x",
                source_doc="unknown.md",
                source_section="",
                severity="warning",
            )
        ]
    )
    updated = apply_severity(result, {})
    assert updated.violations[0].severity == "warning"

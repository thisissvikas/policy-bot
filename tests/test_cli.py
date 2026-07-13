import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from policybot.cli import _build_parser, _build_provider
from policybot.models import PolicyBotConfig, ReviewResult, SourceConfig


def test_parser_review_subcommand() -> None:
    parser = _build_parser()
    args = parser.parse_args(["review", "--diff", "file.diff", "--dry-run"])
    assert args.command == "review"
    assert args.diff == "file.diff"
    assert args.dry_run is True


def test_parser_review_defaults() -> None:
    parser = _build_parser()
    args = parser.parse_args(["review", "--diff", "x.diff"])
    assert args.config == "policybot.yaml"
    assert args.dry_run is False
    assert args.verbose is False


def test_parser_requires_subcommand() -> None:
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_build_provider_local(tmp_path: Path) -> None:
    cfg_path = tmp_path / "policybot.yaml"
    config = PolicyBotConfig(source=SourceConfig(type="local", root="."))
    provider = _build_provider(config, None, cfg_path)
    from policybot.providers.local import LocalProvider

    assert isinstance(provider, LocalProvider)


def test_build_provider_github_requires_token(tmp_path: Path) -> None:
    config = PolicyBotConfig(source=SourceConfig(type="github", repo="owner/repo"))
    with pytest.raises(ValueError, match="GITHUB_TOKEN"):
        _build_provider(config, None, tmp_path / "policybot.yaml")


def test_build_provider_github_with_token(tmp_path: Path) -> None:
    config = PolicyBotConfig(source=SourceConfig(type="github", repo="owner/repo"))
    provider = _build_provider(config, "test-token", tmp_path / "policybot.yaml")
    from policybot.providers.github import GitHubProvider

    assert isinstance(provider, GitHubProvider)


async def test_run_review_dry_run_no_violations(tmp_path: Path, sample_diff: str) -> None:
    diff_path = tmp_path / "test.diff"
    diff_path.write_text(sample_diff)

    cfg = tmp_path / "policybot.yaml"
    cfg.write_text("source:\n  type: local\n  root: .\nstandards: []\nadrs: []\n")

    with (
        patch("policybot.cli.review_diff", new=AsyncMock(return_value=ReviewResult())),
        patch("policybot.cli.fetch_docs", new=AsyncMock(return_value={})),
    ):
        from policybot.cli import _run_review

        parser = _build_parser()
        args = parser.parse_args(
            [
                "review",
                "--config",
                str(cfg),
                "--diff",
                str(diff_path),
                "--dry-run",
            ]
        )
        result = await _run_review(args)

    assert result == 0


async def test_run_review_missing_config(tmp_path: Path) -> None:
    from policybot.cli import _run_review

    parser = _build_parser()
    args = parser.parse_args(
        [
            "review",
            "--config",
            str(tmp_path / "missing.yaml"),
            "--diff",
            "x.diff",
        ]
    )
    result = await _run_review(args)
    assert result == 1


async def test_run_review_no_diff_no_pr() -> None:
    import os
    import tempfile

    from policybot.cli import _run_review

    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
        f.write("source:\n  type: local\nstandards: []\nadrs: []\n")
        cfg_path = f.name
    try:
        parser = _build_parser()
        args = parser.parse_args(["review", "--config", cfg_path])
        result = await _run_review(args)
        assert result == 1
    finally:
        os.unlink(cfg_path)


def test_main_entrypoint_exists() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "policybot.cli", "review", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "review" in result.stdout

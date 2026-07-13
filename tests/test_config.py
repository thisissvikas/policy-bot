from pathlib import Path

import pytest

from policybot.config import ConfigError, get_relevant_docs, get_rule_severity, load_config
from policybot.models import PolicyBotConfig, SourceConfig


def test_load_config_from_fixture(fixtures_dir: Path) -> None:
    config = load_config(fixtures_dir / "policybot_config.yaml")
    assert config.source.type == "local"
    assert len(config.standards) == 2
    assert len(config.adrs) == 2


def test_load_config_defaults(tmp_path: Path) -> None:
    cfg = tmp_path / "policybot.yaml"
    cfg.write_text("standards: []\nadrs: []\n")
    config = load_config(cfg)
    assert config.source.type == "local"
    assert config.standards == []


def test_load_config_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "missing.yaml")


def test_load_config_invalid_yaml(tmp_path: Path) -> None:
    cfg = tmp_path / "policybot.yaml"
    cfg.write_text("standards: [unclosed\n")
    with pytest.raises(ConfigError):
        load_config(cfg)


def test_load_config_invalid_schema(tmp_path: Path) -> None:
    cfg = tmp_path / "policybot.yaml"
    cfg.write_text("standards:\n  - match: 123\n    docs: not_a_list\n")
    with pytest.raises(ConfigError):
        load_config(cfg)


def test_get_relevant_docs_python_files(fixtures_dir: Path) -> None:
    config = load_config(fixtures_dir / "policybot_config.yaml")
    standards, adrs = get_relevant_docs(config, ["app/service.py", "app/models.py"])
    assert "standards/python.md" in standards
    assert "adrs/ADR-007-repository-pattern.md" in adrs
    assert "adrs/ADR-011-error-handling.md" in adrs


def test_get_relevant_docs_typescript_only(fixtures_dir: Path) -> None:
    config = load_config(fixtures_dir / "policybot_config.yaml")
    standards, adrs = get_relevant_docs(config, ["src/api.ts"])
    assert "standards/typescript.md" in standards
    assert "standards/python.md" not in standards
    assert "adrs/ADR-011-error-handling.md" in adrs
    assert "adrs/ADR-007-repository-pattern.md" not in adrs


def test_get_relevant_docs_no_match() -> None:
    config = PolicyBotConfig(
        source=SourceConfig(),
        standards=[],
        adrs=[],
    )
    standards, adrs = get_relevant_docs(config, ["README.md"])
    assert standards == []
    assert adrs == []


def test_get_relevant_docs_deduplicates(fixtures_dir: Path) -> None:
    config = load_config(fixtures_dir / "policybot_config.yaml")
    standards, adrs = get_relevant_docs(config, ["app/a.py", "app/b.py", "app/c.py"])
    assert standards.count("standards/python.md") == 1


def test_get_rule_severity_standard(fixtures_dir: Path) -> None:
    config = load_config(fixtures_dir / "policybot_config.yaml")
    assert get_rule_severity(config, "standards/python.md") == "warning"


def test_get_rule_severity_adr_error(fixtures_dir: Path) -> None:
    config = load_config(fixtures_dir / "policybot_config.yaml")
    assert get_rule_severity(config, "adrs/ADR-007-repository-pattern.md") == "error"


def test_get_rule_severity_unknown() -> None:
    config = PolicyBotConfig()
    assert get_rule_severity(config, "unknown/doc.md") == "warning"

from pathlib import Path
from typing import Any

import pathspec
import structlog
from ruamel.yaml import YAML

from policybot.models import AdrRule, PolicyBotConfig, SourceConfig, StandardRule

log = structlog.get_logger()


class ConfigError(Exception):
    pass


def load_config(path: Path) -> PolicyBotConfig:
    """Load and validate a policybot.yaml file."""
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    yaml = YAML()
    yaml.preserve_quotes = True
    try:
        data: dict[str, Any] = yaml.load(path)
    except Exception as exc:
        raise ConfigError(f"Failed to parse {path}: {exc}") from exc

    if data is None:
        data = {}

    try:
        source_data: dict[str, Any] = data.get("source", {})
        source = SourceConfig.model_validate(source_data)

        standards: list[StandardRule] = [
            StandardRule.model_validate(r) for r in data.get("standards", [])
        ]
        adrs: list[AdrRule] = [AdrRule.model_validate(r) for r in data.get("adrs", [])]
        return PolicyBotConfig(source=source, standards=standards, adrs=adrs)
    except Exception as exc:
        raise ConfigError(f"Invalid config in {path}: {exc}") from exc


def get_relevant_docs(
    config: PolicyBotConfig,
    changed_files: list[str],
) -> tuple[list[str], list[str]]:
    """Return (standard_doc_paths, adr_doc_paths) relevant to the changed files."""
    standard_docs: list[str] = []
    adr_docs: list[str] = []
    seen_standards: set[str] = set()
    seen_adrs: set[str] = set()

    for rule in config.standards:
        spec = pathspec.PathSpec.from_lines("gitignore", [rule.match])
        if any(spec.match_file(f) for f in changed_files):
            for doc in rule.docs:
                if doc not in seen_standards:
                    seen_standards.add(doc)
                    standard_docs.append(doc)

    for adr_rule in config.adrs:
        spec = pathspec.PathSpec.from_lines("gitignore", adr_rule.applies_to)
        if any(spec.match_file(f) for f in changed_files) and adr_rule.path not in seen_adrs:
            seen_adrs.add(adr_rule.path)
            adr_docs.append(adr_rule.path)

    log.debug(
        "relevant_docs",
        standards=standard_docs,
        adrs=adr_docs,
        changed_files=len(changed_files),
    )
    return standard_docs, adr_docs


def get_rule_severity(config: PolicyBotConfig, doc_path: str) -> str:
    """Return the severity configured for a given doc path."""
    for rule in config.standards:
        if doc_path in rule.docs:
            return rule.severity
    for adr_rule in config.adrs:
        if adr_rule.path == doc_path:
            return adr_rule.severity
    return "warning"

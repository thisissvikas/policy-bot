from typing import Literal

from pydantic import BaseModel, Field


class SourceConfig(BaseModel):
    type: Literal["local", "github"] = "local"
    root: str = "."
    repo: str = ""
    ref: str = "main"


class StandardRule(BaseModel):
    match: str
    docs: list[str]
    severity: Literal["error", "warning"] = "warning"


class AdrRule(BaseModel):
    path: str
    applies_to: list[str]
    severity: Literal["error", "warning"] = "warning"


class PolicyBotConfig(BaseModel):
    source: SourceConfig = Field(default_factory=SourceConfig)
    standards: list[StandardRule] = Field(default_factory=list)
    adrs: list[AdrRule] = Field(default_factory=list)


class Violation(BaseModel):
    file: str
    line: int
    type: Literal["adr", "standard"]
    message: str
    source_doc: str
    source_section: str = ""
    severity: Literal["error", "warning"] = "warning"


class ReviewResult(BaseModel):
    violations: list[Violation] = Field(default_factory=list)


class ReviewComment(BaseModel):
    path: str
    line: int
    side: str = "RIGHT"
    body: str

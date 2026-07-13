import re

EXTENSION_MAP: dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".rb": "ruby",
    ".go": "go",
    ".java": "java",
    ".kt": "kotlin",
    ".rs": "rust",
    ".cs": "csharp",
    ".php": "php",
    ".swift": "swift",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".sh": "shell",
    ".bash": "shell",
}

FRAMEWORK_SIGNALS: dict[str, list[str]] = {
    "django": [
        r"from django",
        r"import django",
        r"views\.py$",
        r"models\.py$",
        r"urls\.py$",
        r"settings\.py$",
    ],
    "fastapi": [
        r"from fastapi",
        r"import fastapi",
        r"@app\.(get|post|put|delete|patch)",
        r"APIRouter",
    ],
    "flask": [
        r"from flask",
        r"import flask",
        r"@app\.route",
    ],
    "react": [
        r"from react",
        r"import React",
        r"from 'react'",
        r'from "react"',
        r"\.tsx$",
        r"\.jsx$",
    ],
    "nextjs": [
        r"from next/",
        r"getServerSideProps",
        r"getStaticProps",
        r"pages/",
        r"app/",
    ],
    "sqlalchemy": [
        r"from sqlalchemy",
        r"import sqlalchemy",
        r"db\.session",
        r"Base\.metadata",
    ],
    "pydantic": [
        r"from pydantic",
        r"import pydantic",
        r"BaseModel",
    ],
}

_DIFF_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)


def detect_languages(diff: str) -> set[str]:
    """Extract language names from file paths in a unified diff."""
    languages: set[str] = set()
    for match in _DIFF_FILE_RE.finditer(diff):
        path = match.group(1)
        ext = "." + path.rsplit(".", 1)[-1] if "." in path else ""
        lang = EXTENSION_MAP.get(ext.lower())
        if lang:
            languages.add(lang)
    return languages


def detect_frameworks(diff: str, changed_files: list[str]) -> set[str]:
    """Detect frameworks from diff content and changed file paths."""
    frameworks: set[str] = set()
    combined = diff + "\n" + "\n".join(changed_files)
    for framework, patterns in FRAMEWORK_SIGNALS.items():
        for pattern in patterns:
            if re.search(pattern, combined, re.MULTILINE | re.IGNORECASE):
                frameworks.add(framework)
                break
    return frameworks

from policybot.detector import detect_frameworks, detect_languages


def test_detect_languages_python(python_diff: str) -> None:
    langs = detect_languages(python_diff)
    assert "python" in langs


def test_detect_languages_typescript(typescript_diff: str) -> None:
    langs = detect_languages(typescript_diff)
    assert "typescript" in langs


def test_detect_languages_mixed(mixed_diff: str) -> None:
    langs = detect_languages(mixed_diff)
    assert "python" in langs
    assert "typescript" in langs


def test_detect_languages_empty() -> None:
    assert detect_languages("") == set()


def test_detect_languages_unknown_extension() -> None:
    diff = "+++ b/some/file.xyz\n"
    assert detect_languages(diff) == set()


def test_detect_languages_multiple_py_files(sample_diff: str) -> None:
    langs = detect_languages(sample_diff)
    assert "python" in langs


def test_detect_frameworks_django(sample_diff: str) -> None:
    frameworks = detect_frameworks(sample_diff, ["payments/src/views.py"])
    assert "django" in frameworks


def test_detect_frameworks_react(mixed_diff: str) -> None:
    frameworks = detect_frameworks(mixed_diff, ["frontend/App.tsx"])
    assert "react" in frameworks


def test_detect_frameworks_flask(mixed_diff: str) -> None:
    frameworks = detect_frameworks(mixed_diff, ["backend/app.py"])
    assert "flask" in frameworks


def test_detect_frameworks_no_signals() -> None:
    diff = "+++ b/plain.py\n+def hello(): pass\n"
    frameworks = detect_frameworks(diff, ["plain.py"])
    assert "django" not in frameworks
    assert "react" not in frameworks


def test_detect_frameworks_from_imports() -> None:
    diff = "+++ b/app.py\n+from django.views import View\n"
    frameworks = detect_frameworks(diff, ["app.py"])
    assert "django" in frameworks


def test_detect_frameworks_fastapi() -> None:
    diff = "+++ b/main.py\n+from fastapi import FastAPI\n+app = FastAPI()\n"
    frameworks = detect_frameworks(diff, ["main.py"])
    assert "fastapi" in frameworks

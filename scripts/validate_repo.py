#!/usr/bin/env python3
"""Repository validation guardrail.

Checks for common secret patterns, tracked credential-like files,
required documentation, and local working-tree state.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = [
    re.compile(r"GOCSPX-[A-Za-z0-9_-]+"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"BEGIN (RSA|OPENSSH|PRIVATE) KEY"),
]
SENSITIVE_NAME = re.compile(
    r"(^|/)(\.env(\..*)?|\.env\.keys|client_secret.*\.json|credentials.*\.json|token.*\.json|tokens.*\.json|google[-_]ads\.ya?ml|logs/.*|state/.*|briefing_latest\.txt|archive/.*)$",
    re.IGNORECASE,
)
ALLOW_TRACKED = {
    ".envrc",
    ".env.example",
}
SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".sh", ".css", ".js", ".ts", ".html"}
LOCAL_PATH_PATTERN = re.compile(r"/Users/[A-Za-z0-9._-]+/")

def git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)

def tracked_files() -> list[str]:
    result = git(["ls-files"])
    return [line for line in result.stdout.splitlines() if line.strip()]

def is_text_candidate(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in {"Makefile", "README", "CLAUDE.md", ".envrc"}

def main() -> int:
    failures: list[str] = []
    tracked = tracked_files()

    if not (ROOT / "README.md").exists():
        failures.append("Missing README.md")

    for rel in tracked:
        base = Path(rel).name
        if SENSITIVE_NAME.search(rel) and base not in ALLOW_TRACKED:
            normalized = rel.replace("\\", "/")
            if not (
                normalized.startswith("design-tokens/")
                or normalized.startswith("design-system/")
                or normalized.startswith("examples/example-token")
                or "token-output" in normalized
            ):
                failures.append(f"Tracked sensitive-looking file: {rel}")

    for rel in tracked:
        path = ROOT / rel
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.exists() or not path.is_file() or not is_text_candidate(path):
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"Secret-like pattern in {rel}: {pattern.pattern}")
                break

        if LOCAL_PATH_PATTERN.search(text):
            failures.append(f"Local absolute path found in {rel}")

        if rel.endswith(".md"):
            for lineno, line in enumerate(text.splitlines(), 1):
                if "python hub.py clean" in line and "--confirm" not in line:
                    failures.append(
                        f"Write-capable clean command missing --confirm in {rel}:{lineno}"
                    )
                    break

    status = git(["status", "--short"]).stdout.strip()
    if status:
        failures.append("Working tree is not clean")

    if failures:
        print("VALIDATION FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("VALIDATION PASSED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

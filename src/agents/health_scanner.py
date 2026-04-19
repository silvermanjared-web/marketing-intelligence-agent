#!/usr/bin/env python3
"""
Project Health Scanner Agent
==============================
Scans all configured project directories for health metrics:

- Git status, branch, uncommitted changes
- Stale files (no Python changes in 14+ days)
- Credential exposure (files that should be gitignored but aren't)
- Dependency health (missing requirements.txt)
- File counts and size distribution

Designed to catch drift before it becomes technical debt.
"""

import os
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Patterns that indicate credential files — these should always be gitignored.
CREDENTIAL_PATTERNS = [
    "credentials*.json",
    "token*.json",
    "client_secret_*",
    "*.pem",
    "*.key",
]

# Directories to skip during recursive scans.
SKIP_DIRS = {"venv", ".venv", "node_modules", ".git", "__pycache__", ".DS_Store"}


def scan_project(name: str, path: Path) -> dict:
    """Run a full health scan on a single project directory.

    Returns a report dict with 'issues' (list of problems) and
    'stats' (metrics about the project).
    """
    report = {"name": name, "path": str(path), "issues": [], "stats": {}}

    if not path.exists():
        report["issues"].append("Directory does not exist")
        return report

    # ------------------------------------------------------------------
    # File statistics
    # ------------------------------------------------------------------
    file_counts: dict[str, int] = defaultdict(int)
    total_size = 0
    py_files: list[Path] = []

    for item in path.rglob("*"):
        if any(skip in item.parts for skip in SKIP_DIRS):
            continue
        if item.is_file():
            file_counts[item.suffix.lower() or "(none)"] += 1
            total_size += item.stat().st_size
            if item.suffix == ".py":
                py_files.append(item)

    report["stats"]["total_files"] = sum(file_counts.values())
    report["stats"]["total_size_mb"] = round(total_size / (1024 * 1024), 1)
    report["stats"]["python_files"] = len(py_files)
    report["stats"]["file_types"] = dict(
        sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    )

    # ------------------------------------------------------------------
    # Git health
    # ------------------------------------------------------------------
    has_git = (path / ".git").exists()
    if has_git:
        try:
            branch = subprocess.run(
                ["git", "-C", str(path), "branch", "--show-current"],
                capture_output=True, text=True, timeout=5,
            ).stdout.strip()

            status = subprocess.run(
                ["git", "-C", str(path), "status", "--porcelain"],
                capture_output=True, text=True, timeout=5,
            ).stdout.strip()

            dirty = len([l for l in status.split("\n") if l.strip()])
            report["stats"]["git_branch"] = branch or "HEAD detached"
            report["stats"]["uncommitted"] = dirty

            if dirty > 10:
                report["issues"].append(f"{dirty} uncommitted changes")
        except Exception:
            report["issues"].append("Git error")
    else:
        report["stats"]["git_branch"] = "none"
        report["issues"].append("Not a git repository")

    # ------------------------------------------------------------------
    # .gitignore presence
    # ------------------------------------------------------------------
    if not (path / ".gitignore").exists():
        report["issues"].append("Missing .gitignore")

    # ------------------------------------------------------------------
    # Dependency manifest
    # ------------------------------------------------------------------
    if py_files and not (path / "requirements.txt").exists():
        report["issues"].append("Missing requirements.txt")

    # ------------------------------------------------------------------
    # Credential exposure check
    # ------------------------------------------------------------------
    exposed = []
    for pattern in CREDENTIAL_PATTERNS:
        for match in path.glob(pattern):
            if not match.is_file() or match.stat().st_size == 0:
                continue

            is_ignored = False
            if has_git:
                # Authoritative: ask git if this file is ignored.
                try:
                    result = subprocess.run(
                        ["git", "-C", str(path), "check-ignore", "-q", str(match)],
                        capture_output=True, timeout=5,
                    )
                    is_ignored = result.returncode == 0
                except Exception:
                    pass
            else:
                # Fallback: naive .gitignore string check.
                gitignore = path / ".gitignore"
                if gitignore.exists():
                    with open(gitignore) as f:
                        ignores = f.read()
                    if match.name in ignores or any(
                        p.strip() in match.name
                        for p in ignores.split("\n")
                        if p.strip() and not p.startswith("#")
                    ):
                        is_ignored = True

            if is_ignored:
                exposed.append(f"{match.name} (gitignored)")
            else:
                exposed.append(f"{match.name} (EXPOSED)")
                report["issues"].append(
                    f"Credential file not gitignored: {match.name}"
                )

    report["stats"]["credential_files"] = exposed

    # ------------------------------------------------------------------
    # Staleness detection
    # ------------------------------------------------------------------
    now = datetime.now()
    newest = None
    for item in path.rglob("*.py"):
        if any(skip in item.parts for skip in SKIP_DIRS):
            continue
        try:
            mtime = datetime.fromtimestamp(item.stat().st_mtime)
            if newest is None or mtime > newest:
                newest = mtime
        except (PermissionError, OSError):
            continue

    if newest:
        days_since = (now - newest).days
        report["stats"]["last_py_change"] = (
            f"{days_since}d ago" if days_since > 0 else "today"
        )
        if days_since > 14:
            report["issues"].append(f"No Python changes in {days_since} days")

    # ------------------------------------------------------------------
    # __pycache__ exposure
    # ------------------------------------------------------------------
    if has_git:
        for cache_dir in path.rglob("__pycache__"):
            if "venv" in str(cache_dir):
                continue
            try:
                result = subprocess.run(
                    ["git", "-C", str(path), "check-ignore", "-q", str(cache_dir)],
                    capture_output=True, timeout=5,
                )
                if result.returncode != 0:  # NOT ignored — real issue
                    report["issues"].append("__pycache__ not gitignored")
            except Exception:
                pass
            break  # Only check the first one.

    return report


def run(*args) -> dict:
    """Run the health scanner across all configured projects.

    Loads project paths from config and scans each one, printing
    a formatted report to stdout.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))
    from config import PROJECTS

    all_issues = 0

    if not PROJECTS:
        print("\n     No projects configured.")
        print("     Copy config/projects.example.json to config/projects.json")
        return {"total_issues": 0}

    for name, path in PROJECTS.items():
        report = scan_project(name, path)

        status_icon = (
            "[OK]" if not report["issues"]
            else f"[{len(report['issues'])} issues]"
        )
        print(f"\n     {name} {status_icon}")
        print(f"     {'~' * 50}")

        stats = report.get("stats", {})
        if stats:
            parts = []
            if "total_files" in stats:
                parts.append(f"{stats['total_files']} files ({stats['total_size_mb']} MB)")
            if "python_files" in stats:
                parts.append(f"{stats['python_files']} .py")
            if "git_branch" in stats:
                parts.append(f"git: {stats['git_branch']}")
            if stats.get("uncommitted", 0) > 0:
                parts.append(f"{stats['uncommitted']} uncommitted")
            if "last_py_change" in stats:
                parts.append(f"last change: {stats['last_py_change']}")
            print(f"       {' | '.join(parts)}")

            if stats.get("credential_files"):
                for cf in stats["credential_files"]:
                    print(f"       cred: {cf}")

        if report["issues"]:
            all_issues += len(report["issues"])
            for issue in report["issues"]:
                print(f"       !! {issue}")

    print(f"\n     Total issues found: {all_issues}")
    if all_issues == 0:
        print(f"     All projects healthy.\n")

    return {"total_issues": all_issues}

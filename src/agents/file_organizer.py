#!/usr/bin/env python3
"""
Smart File Organizer Agent
============================
Intelligently organizes Desktop and Downloads by:

- Moving files into categorized subdirectories
- Identifying and flagging potential duplicates
- Archiving old files (>30 days)
- Reporting what was moved (or would be moved in dry-run mode)

Default behavior is dry-run (preview only). Pass --clean for live execution.
"""

import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HOME = Path.home()

# Directories to organize.
ORGANIZE_DIRS = {
    "Desktop": HOME / "Desktop",
    "Downloads": HOME / "Downloads",
}

# File type categories — maps a category name to its file extensions.
CATEGORIES = {
    "Documents": {
        ".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt",
        ".pages", ".md", ".csv", ".xlsx", ".xls", ".pptx", ".ppt",
    },
    "Images": {
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
        ".ico", ".bmp", ".tiff", ".heic",
    },
    "Videos": {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"},
    "Archives": {".zip", ".tar", ".gz", ".rar", ".7z", ".dmg", ".pkg", ".iso"},
    "Code": {
        ".py", ".js", ".ts", ".html", ".css", ".json",
        ".yaml", ".yml", ".sh", ".sql", ".rb", ".go", ".rs",
    },
    "Data": {".sqlite", ".db", ".xml", ".log", ".dat"},
}

# Never touch these files.
SKIP_FILES = {".DS_Store", ".localized", "desktop.ini", "Thumbs.db"}
SKIP_PREFIXES = {".", "~"}


def categorize_file(filepath: Path) -> str:
    """Determine the category for a file based on its extension."""
    ext = filepath.suffix.lower()
    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category
    return "Other"


def get_file_age_days(filepath: Path) -> int:
    """Return the age of a file in days since last modification."""
    mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
    return (datetime.now() - mtime).days


def find_potential_duplicates(directory: Path) -> dict[int, list[Path]]:
    """Find files with identical sizes (potential duplicates).

    Only flags files larger than 1KB to avoid false positives
    on small/empty files.
    """
    by_size: dict[int, list[Path]] = defaultdict(list)
    for item in directory.iterdir():
        if item.is_file() and item.name not in SKIP_FILES:
            size = item.stat().st_size
            by_size[size].append(item)
    return {
        size: files
        for size, files in by_size.items()
        if len(files) > 1 and size > 1024
    }


def organize_directory(
    dir_name: str,
    dir_path: Path,
    dry_run: bool = True,
) -> dict:
    """Organize files in a directory into category subdirectories.

    Args:
        dir_name: Display name for reporting.
        dir_path: Path to the directory to organize.
        dry_run: If True, report what would happen without moving files.

    Returns:
        Dict with 'moved', 'old_files', 'duplicates', and 'skipped' lists.
    """
    if not dir_path.exists():
        return {"skipped": f"{dir_name} does not exist"}

    results: dict = {
        "moved": [],
        "old_files": [],
        "duplicates": [],
        "skipped": [],
    }

    files = [
        f for f in dir_path.iterdir()
        if f.is_file()
        and f.name not in SKIP_FILES
        and not any(f.name.startswith(p) for p in SKIP_PREFIXES)
    ]

    if not files:
        return results

    for filepath in files:
        category = categorize_file(filepath)
        age = get_file_age_days(filepath)

        # Flag old files regardless of dry-run mode.
        if age > 30:
            results["old_files"].append({
                "name": filepath.name,
                "age_days": age,
                "size_mb": round(filepath.stat().st_size / (1024 * 1024), 2),
            })

        # Move into category subfolder.
        target_dir = dir_path / f"_{category}"
        target_path = target_dir / filepath.name

        if not dry_run:
            target_dir.mkdir(exist_ok=True)
            if not target_path.exists():
                shutil.move(str(filepath), str(target_path))
                results["moved"].append({
                    "name": filepath.name,
                    "to": f"_{category}/",
                })
            else:
                results["skipped"].append(
                    f"{filepath.name} (already exists in _{category}/)"
                )
        else:
            results["moved"].append({
                "name": filepath.name,
                "to": f"_{category}/",
                "dry_run": True,
            })

    # Check for potential duplicates.
    dupes = find_potential_duplicates(dir_path)
    for size, files_list in dupes.items():
        results["duplicates"].append({
            "size_bytes": size,
            "files": [f.name for f in files_list],
        })

    return results


def run(*args) -> dict:
    """Run the smart file organizer.

    Defaults to dry-run mode (preview). Pass '--clean' to execute moves.
    """
    clean_mode = "--clean" in args
    dry_run = not clean_mode

    mode_str = "LIVE" if not dry_run else "DRY RUN (preview)"
    print(f"\n     Mode: {mode_str}")
    print(f"     {'~' * 50}")

    total_movable = 0
    total_old = 0

    for dir_name, dir_path in ORGANIZE_DIRS.items():
        results = organize_directory(dir_name, dir_path, dry_run=dry_run)

        if isinstance(results.get("skipped"), str):
            print(f"\n     {dir_name}: {results['skipped']}")
            continue

        moved = results.get("moved", [])
        old = results.get("old_files", [])
        dupes = results.get("duplicates", [])

        total_movable += len(moved)
        total_old += len(old)

        print(f"\n     {dir_name}:")
        if moved:
            # Group by category for cleaner output.
            by_cat: dict[str, list[str]] = defaultdict(list)
            for m in moved:
                by_cat[m["to"]].append(m["name"])

            for cat, files in sorted(by_cat.items()):
                print(f"       -> {cat:15s} {len(files)} files")
                for f in files[:3]:
                    print(f"          {f[:50]}")
                if len(files) > 3:
                    print(f"          ... and {len(files) - 3} more")
        else:
            print(f"       (already organized)")

        if old:
            print(f"       Old files (>30 days): {len(old)}")
            for f in old[:3]:
                print(
                    f"         {f['name'][:40]:40s} "
                    f"{f['age_days']}d  {f['size_mb']} MB"
                )
            if len(old) > 3:
                print(f"         ... and {len(old) - 3} more")

        if dupes:
            print(f"       Potential duplicates: {len(dupes)} groups")

    print(f"\n     Summary: {total_movable} files to organize, {total_old} old files flagged")

    if dry_run and total_movable > 0:
        print(f"     Run with --clean flag to execute organization.\n")
    else:
        print()

    return {"moved": total_movable, "old": total_old}

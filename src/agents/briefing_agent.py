#!/usr/bin/env python3
"""
Morning Intelligence Briefing Agent
====================================
Synthesizes email, calendar, and project data into a decision-ready
intelligence report. Designed for marketing operations leaders who need
signal, not noise.

Data flow:
    Gmail API  ─┐
    IMAP source ─┤──> score & classify ──> theme detection ──> formatted report
    Calendar    ─┘

Output sections:
    - TL;DR          — one-line executive summary
    - Critical        — items requiring immediate action
    - Important       — meaningful but not urgent
    - Risks / Flags   — systemic patterns or data quality issues
    - Implications    — what this means for your day

Confidence tiers:
    High        — structured API data with full metadata
    Moderate    — reconstructed from partial sources (forwarded threads, etc.)
    Directional — pattern-matched fragments, needs manual verification
"""

import os
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Scoring engine — pattern-based triage with weighted signals.
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))
from scoring import triage_score, WORK_DOMAINS, NOISE_DOMAINS

HOME = Path.home()

# Directories to monitor for clutter metrics.
WATCH_DIRS = {
    "Desktop": HOME / "Desktop",
    "Downloads": HOME / "Downloads",
    "Documents": HOME / "Documents",
}

# Triage thresholds — calibrated to avoid false positives.
# Critical requires real urgency signals, not just source weighting.
CRITICAL_THRESHOLD = 10
IMPORTANT_THRESHOLD = 5


# ---------------------------------------------------------------------------
# Data source interfaces
# ---------------------------------------------------------------------------

def get_gmail_summary() -> dict | None:
    """Fetch inbox stats via Gmail API using existing OAuth credentials.

    Returns unread count and today's message count, or None if
    credentials are unavailable. Read-only — never modifies the inbox.
    """
    credential_dir = Path(
        os.environ.get("MIA_GMAIL_CREDENTIAL_DIR", str(HOME / "gmail-processor"))
    )
    token_path = credential_dir / "token.json"
    creds_path = credential_dir / "credentials.json"

    if not token_path.exists() or not creds_path.exists():
        return None

    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(
            str(token_path),
            ["https://www.googleapis.com/auth/gmail.readonly"],
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        service = build("gmail", "v1", credentials=creds)

        # Unread count
        results = service.users().messages().list(
            userId="me", q="is:unread in:inbox", maxResults=1
        ).execute()
        unread = results.get("resultSizeEstimate", 0)

        # Today's messages
        today = datetime.now().strftime("%Y/%m/%d")
        today_results = service.users().messages().list(
            userId="me", q=f"after:{today} in:inbox", maxResults=1
        ).execute()
        today_count = today_results.get("resultSizeEstimate", 0)

        return {
            "unread": unread,
            "today": today_count,
        }
    except Exception as e:
        return {"error": str(e)}


def get_imap_messages() -> list[dict] | None:
    """Fetch recent unread messages via IMAP.

    This is a placeholder interface demonstrating the data contract.
    In production, connect to your mail server or local mail store.

    Each message dict should contain:
        - source: str (data source identifier)
        - from: str (sender display name or address)
        - domain: str (sender domain)
        - subject: str
        - body: str (preview text)
        - time: str (formatted time)
        - attachments: int
        - starred: bool
    """
    # To implement: connect via imaplib or a local mail DB.
    # Return a list of message dicts matching the schema above.
    return None


# ---------------------------------------------------------------------------
# Theme detection
# ---------------------------------------------------------------------------

def _detect_work_themes(items: list[dict]) -> list[str]:
    """Extract broad themes from scored email subjects.

    Groups messages into operational categories so the briefing can
    summarize patterns instead of listing individual subjects.
    """
    import re

    theme_patterns = [
        ("reporting", re.compile(r"(?:report|delivery|weekly|dashboard)", re.I)),
        ("campaigns", re.compile(r"(?:campaign|optimizer|ads?|creative|media|roas)", re.I)),
        ("coordination", re.compile(r"(?:availab|meet|call|sync|schedule)", re.I)),
        ("strategy", re.compile(r"(?:strategy|planning|forecast|budget)", re.I)),
        ("vendors", re.compile(r"(?:agency|vendor|partner|delivery|invoice)", re.I)),
        ("performance", re.compile(r"(?:conversion|cpa|cpl|roi|spend|pacing)", re.I)),
    ]

    counts: Counter = Counter()
    for item in items:
        subj = item.get("subject", "").lower()
        for theme_name, pattern in theme_patterns:
            if pattern.search(subj):
                counts[theme_name] += 1

    # Only return themes with 2+ hits — avoids spurious one-off mentions.
    return [name for name, _ in counts.most_common() if counts[name] >= 2]


# ---------------------------------------------------------------------------
# Project and system health
# ---------------------------------------------------------------------------

def _get_git_status(project_path: Path) -> dict:
    """Quick git health check for a project directory."""
    if not (project_path / ".git").exists():
        return {"status": "not a git repo"}
    try:
        result = subprocess.run(
            ["git", "-C", str(project_path), "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        )
        lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
        log_result = subprocess.run(
            ["git", "-C", str(project_path), "log", "--oneline", "-3",
             "--format=%h %s (%ar)"],
            capture_output=True, text=True, timeout=10,
        )
        commits = [l.strip() for l in log_result.stdout.strip().split("\n") if l.strip()]
        return {"dirty": len(lines), "recent_commits": commits}
    except Exception:
        return {"status": "git error"}


def _get_disk_info() -> dict | None:
    """Return disk usage stats for the root volume."""
    try:
        result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")
        if len(lines) > 1:
            parts = lines[1].split()
            return {
                "total": parts[1],
                "used": parts[2],
                "available": parts[3],
                "percent": parts[4],
            }
    except Exception:
        pass
    return None


def _count_dir_files(directory: Path) -> tuple[dict, int]:
    """Count files by extension and total size in a directory."""
    counts: dict[str, int] = defaultdict(int)
    total_size = 0
    try:
        for item in directory.iterdir():
            if item.is_file() and not item.name.startswith("."):
                counts[item.suffix.lower() or "(none)"] += 1
                total_size += item.stat().st_size
    except (PermissionError, OSError):
        pass
    return dict(counts), total_size


def _get_recent_files(directory: Path, hours: int = 24) -> list[dict]:
    """Find recently modified files in a directory tree."""
    cutoff = datetime.now() - timedelta(hours=hours)
    recent = []
    try:
        for item in directory.rglob("*"):
            if not item.is_file():
                continue
            rel_parts = item.parts[len(directory.parts):]
            if any(p.startswith(".") for p in rel_parts):
                continue
            if "venv" in item.parts or "node_modules" in item.parts:
                continue
            try:
                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                if mtime > cutoff:
                    recent.append({
                        "name": item.name,
                        "modified": mtime.strftime("%H:%M"),
                        "size_mb": round(item.stat().st_size / (1024 * 1024), 2),
                    })
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError):
        pass
    return sorted(recent, key=lambda x: x["modified"], reverse=True)


# ---------------------------------------------------------------------------
# Report formatter
# ---------------------------------------------------------------------------

def _format_item(item: dict) -> str:
    """Format a single triage item with confidence-appropriate hedging."""
    subj = item.get("subject", "")[:65]
    confidence = item.get("_confidence", "")
    is_work = item.get("source") in ("work", "internal")

    if confidence == "Directional" and is_work:
        return f"Likely: {subj}"
    return subj


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run(*args) -> dict:
    """Generate the morning intelligence briefing.

    Collects data from all available sources, scores and classifies
    messages, detects themes, flags risks, and produces a formatted
    report to stdout.
    """
    now = datetime.now()
    w = 60

    print(f"\n  {'=' * w}")
    print(f"  DAILY BRIEFING  |  {now.strftime('%A, %B %d, %Y  %I:%M %p')}")
    print(f"  {'=' * w}")

    # ------------------------------------------------------------------
    # Inbox triage
    # ------------------------------------------------------------------
    print(f"\n  >> INBOX TRIAGE")

    gmail = get_gmail_summary()
    imap_messages = get_imap_messages()

    # Source status reporting
    src_lines = []
    if gmail and "error" not in gmail:
        src_lines.append(f"Gmail API: {gmail['unread']} unread (account configured)")
    elif gmail and "error" in gmail:
        src_lines.append(f"Gmail API: {gmail['error']}")
    if imap_messages is not None:
        src_lines.append(f"IMAP: {len(imap_messages)} messages loaded")
    else:
        src_lines.append("IMAP: not configured (see get_imap_messages())")
    for sl in src_lines:
        print(f"     {sl}")

    # Score and classify all messages
    critical: list[dict] = []
    important: list[dict] = []
    risk_flags: list[str] = []
    noise_count = 0
    noise_domains: Counter = Counter()
    all_scored: list[dict] = []

    # Score IMAP messages (high confidence — structured metadata).
    if imap_messages:
        for msg in imap_messages:
            score, reasons = triage_score(
                msg["subject"], msg["body"], msg.get("source", "imap"), msg["domain"]
            )
            msg["_score"] = score
            msg["_reasons"] = reasons
            msg["_confidence"] = "High"
            all_scored.append(msg)

            if score >= CRITICAL_THRESHOLD:
                critical.append(msg)
            elif score >= IMPORTANT_THRESHOLD:
                important.append(msg)
            else:
                noise_count += 1
                if msg.get("domain"):
                    noise_domains[msg["domain"]] += 1

    # Sort by score descending, work items first within same score.
    def _sort_key(item):
        return (
            -(item.get("_score", 0)),
            0 if item.get("source") in ("work", "internal") else 1,
        )
    critical.sort(key=_sort_key)
    important.sort(key=_sort_key)

    # Detect systemic risk patterns across all scored items.
    security_items = [
        i for i in all_scored
        if any(r in ("security alert", "sign-in alert") for r in i.get("_reasons", []))
    ]
    if security_items:
        n = len(security_items)
        risk_flags.append(
            f"{n} security alert{'s' if n != 1 else ''} detected "
            f"across accounts -- verify no unauthorized access"
        )

    # Repeated sender detection (possible escalation or misconfigured alerts).
    sender_counts: Counter = Counter()
    for msg in all_scored:
        domain = msg.get("domain", "")
        if domain:
            sender_counts[domain] += 1
    for sender, count in sender_counts.most_common(5):
        if count >= 4:
            risk_flags.append(
                f"{sender} sent {count} messages recently -- "
                f"likely misconfigured notifications or escalation"
            )

    total_analyzed = len(all_scored)

    # Theme detection for work items
    work_important = [i for i in important if i.get("source") in ("work", "internal")]
    work_critical = [i for i in critical if i.get("source") in ("work", "internal")]
    work_themes = _detect_work_themes(work_critical + work_important)

    if work_themes:
        if len(work_themes) > 1:
            themes_str = ", ".join(work_themes[:-1]) + f", and {work_themes[-1]}"
        else:
            themes_str = work_themes[0]
    else:
        themes_str = "general work threads"

    # ------------------------------------------------------------------
    # TL;DR
    # ------------------------------------------------------------------
    print(f"\n     TL;DR")
    tldr = []
    if critical:
        if work_critical:
            tldr.append("Urgent work items surfaced -- check inbox first.")
        else:
            tldr.append("Urgent personal items flagged -- see below.")
    elif work_important:
        tldr.append(
            f"Work inbox shows activity across {themes_str}, "
            f"but no clear escalation signal."
        )
    else:
        tldr.append("No urgent inbox issues surfaced.")

    if security_items:
        n_sec = len(security_items)
        tldr.append(
            f"Repeated security alert{'s' if n_sec != 1 else ''} ({n_sec}x) "
            f"should be verified once, then ignored if expected."
        )

    if not critical and not work_important and noise_count > 10:
        tldr.append("Inbox is mostly noise today -- safe to skip.")

    for t in tldr[:4]:
        print(f"       - {t}")

    # ------------------------------------------------------------------
    # Critical
    # ------------------------------------------------------------------
    print(f"\n     CRITICAL")
    if critical:
        for item in critical[:3]:
            print(f"       - {_format_item(item)}")
    else:
        print(f"       No critical items.")

    # ------------------------------------------------------------------
    # Important
    # ------------------------------------------------------------------
    print(f"\n     IMPORTANT")
    if important:
        shown = important[:3]
        for item in shown:
            print(f"       - {_format_item(item)}")
        remaining = len(important) - len(shown)
        if remaining > 0:
            if work_themes:
                print(f"       Remaining work signal concentrated in {themes_str}.")
            else:
                print(f"       {remaining} additional items -- routine coordination and updates.")
    else:
        print(f"       Nothing pressing beyond routine.")

    # ------------------------------------------------------------------
    # Risks / Flags
    # ------------------------------------------------------------------
    print(f"\n     RISKS / FLAGS")
    if risk_flags:
        for flag in risk_flags[:5]:
            print(f"       - {flag}")
    else:
        print(f"       No flags.")

    # ------------------------------------------------------------------
    # Noise summary (only if inbox is dominated by noise)
    # ------------------------------------------------------------------
    if noise_count > 0 and not critical and not important:
        print(f"\n     NOISE")
        print(f"       {noise_count} low-priority items suppressed.")

    # ------------------------------------------------------------------
    # Implications
    # ------------------------------------------------------------------
    print(f"\n     WHAT THIS MEANS FOR YOU TODAY")
    implications = []
    if critical:
        implications.append("Handle critical items before anything else.")
    if work_important:
        implications.append("Scan work inbox for response-needed threads.")
    if security_items:
        implications.append(
            "Confirm security notices are expected, then ignore further repeats."
        )
    if any(
        "payment" in r or "invoice" in r
        for item in critical + important
        for r in item.get("_reasons", [])
    ):
        implications.append("Check pending financial items before EOD.")
    if not critical and not important and noise_count > 10:
        implications.append("Nothing needs your attention. Start your deep work.")
    if not implications:
        implications.append("No meaningful inbox signal. Proceed with planned priorities.")
    for imp in implications[:5]:
        print(f"       - {imp}")

    # ------------------------------------------------------------------
    # Disk
    # ------------------------------------------------------------------
    print(f"\n  >> DISK")
    disk = _get_disk_info()
    if disk:
        pct = int(disk["percent"].replace("%", ""))
        bar_len = 35
        filled = int(bar_len * pct / 100)
        bar = "#" * filled + "-" * (bar_len - filled)
        warn = "  !! LOW SPACE" if pct > 85 else ""
        print(f"     [{bar}] {disk['percent']}{warn}")
        print(f"     Used: {disk['used']} / {disk['total']}  |  Free: {disk['available']}")

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------
    try:
        from config import PROJECTS
    except ImportError:
        # Fallback: load config from expected location.
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))
        from config import PROJECTS

    if PROJECTS:
        print(f"\n  >> PROJECTS")
        for name, path in PROJECTS.items():
            if not path.exists():
                continue
            recent = _get_recent_files(path, hours=24)
            git = _get_git_status(path)
            parts = []
            if recent:
                parts.append(f"{len(recent)} changed (24h)")
            if isinstance(git, dict) and "dirty" in git:
                if git["dirty"] > 0:
                    parts.append(f"{git['dirty']} uncommitted")
            elif isinstance(git, dict) and git.get("status") == "not a git repo":
                parts.append("no git")
            status = " | ".join(parts) if parts else "quiet"
            print(f"     {name:22s} {status}")

    # ------------------------------------------------------------------
    # Clutter check
    # ------------------------------------------------------------------
    print(f"\n  >> CLUTTER CHECK")
    for name, path in WATCH_DIRS.items():
        if not path.exists():
            continue
        counts, total_size = _count_dir_files(path)
        total_files = sum(counts.values())
        size_mb = total_size / (1024 * 1024)
        if total_files > 30:
            level = "CLUTTERED"
        elif total_files > 15:
            level = "moderate"
        else:
            level = "clean"
        print(f"     {name:12s} {total_files:4d} files ({size_mb:>7.0f} MB)  [{level}]")

    # ------------------------------------------------------------------
    # Actionable suggestions
    # ------------------------------------------------------------------
    suggestions = []
    if disk and int(disk["percent"].replace("%", "")) > 90:
        suggestions.append("Disk above 90% -- run cleanup")
    if suggestions:
        print(f"\n  >> ACTION NEEDED")
        for s in suggestions:
            print(f"     {s}")

    print(f"\n  {'=' * w}\n")
    return {"status": "ok", "analyzed": total_analyzed}

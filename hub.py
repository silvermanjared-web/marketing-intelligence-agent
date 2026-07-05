#!/usr/bin/env python3
"""
Marketing Intelligence Hub v2.0 — Master Orchestrator
=======================================================
Central nervous system for all marketing intelligence agents.

Usage:
    python hub.py                   # Interactive menu
    python hub.py briefing          # Morning intelligence report
    python hub.py scan              # Project health check
    python hub.py organize          # Smart file organizer (dry run)
    python hub.py clean --confirm   # Execute file organization
    python hub.py focus [minutes]   # Focus mode via AppleScript
    python hub.py launch [profile]  # Launch app profile (work/dev/comms)
    python hub.py tile              # Tile windows into grid
    python hub.py status            # Full workspace status
    python hub.py mode [name]       # Run a workspace mode
    python hub.py audit             # System health audit
"""

import argparse
import importlib
import io
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

WORKSPACE_ROOT = Path(__file__).parent
AGENTS_DIR = WORKSPACE_ROOT / "src" / "agents"
SCRIPTS_DIR = WORKSPACE_ROOT / "scripts"
CONFIG_DIR = WORKSPACE_ROOT / "config"
LOGS_DIR = WORKSPACE_ROOT / "logs"

HOME = Path.home()

# Ensure the agents and core directories are importable.
sys.path.insert(0, str(WORKSPACE_ROOT / "src" / "agents"))
sys.path.insert(0, str(WORKSPACE_ROOT / "src" / "core"))

BANNER = r"""
  +============================================================+
  |       MARKETING INTELLIGENCE HUB  v2.0                     |
  |       Multi-Agent Workspace Orchestrator                   |
  +============================================================+
"""


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(msg: str, level: str = "INFO") -> None:
    """Log a message to both stdout and the daily log file."""
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = {
        "INFO": "  ->",
        "OK": "  [OK]",
        "WARN": "  [!!]",
        "ERR": "  [ERR]",
        "RUN": "  [>>]",
    }
    symbol = prefix.get(level, "  ->")
    print(f"{symbol} [{ts}] {msg}")

    LOGS_DIR.mkdir(exist_ok=True)
    log_file = LOGS_DIR / f"hub_{datetime.now().strftime('%Y%m%d')}.log"
    with open(log_file, "a") as f:
        f.write(f"[{ts}] [{level}] {msg}\n")


# ---------------------------------------------------------------------------
# Agent runner
# ---------------------------------------------------------------------------

def run_agent(name: str, *args):
    """Import and run an agent module by name.

    Agents are loaded dynamically via importlib, enabling a plugin-style
    architecture where new agents can be added without modifying the hub.
    """
    log(f"Starting agent: {name}", "RUN")
    start = time.time()
    try:
        if name in sys.modules:
            mod = importlib.reload(sys.modules[name])
        else:
            mod = importlib.import_module(name)
        result = mod.run(*args)
        elapsed = time.time() - start
        log(f"Agent '{name}' completed in {elapsed:.1f}s", "OK")
        return result
    except Exception as e:
        log(f"Agent '{name}' failed: {e}", "ERR")
        import traceback
        traceback.print_exc()
        return None


def run_applescript(script_name: str, *args):
    """Run an AppleScript from the scripts directory.

    Used for macOS-native automation: window tiling, app launching,
    focus mode activation.
    """
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        log(f"Script not found: {script_path}", "ERR")
        return None

    cmd = ["osascript", str(script_path)] + [str(a) for a in args]
    log(f"Running: {script_name}", "RUN")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            log("AppleScript completed", "OK")
            return result.stdout.strip()
        else:
            log(f"AppleScript error: {result.stderr.strip()}", "ERR")
            return None
    except subprocess.TimeoutExpired:
        log("AppleScript timed out", "ERR")
        return None


# ---------------------------------------------------------------------------
# Output capture — tee stdout for briefing delivery
# ---------------------------------------------------------------------------

class _TeeWriter:
    """Write to both the real stdout and a string buffer."""

    def __init__(self, original):
        self._original = original
        self._buffer = io.StringIO()

    def write(self, s):
        self._original.write(s)
        self._buffer.write(s)

    def flush(self):
        self._original.flush()

    def getvalue(self):
        return self._buffer.getvalue()


def deliver_briefing(output: str) -> None:
    """Save briefing output to log files, with optional Desktop delivery."""
    now = datetime.now()
    LOGS_DIR.mkdir(exist_ok=True)

    # Save latest (overwrite).
    latest = LOGS_DIR / "briefing_latest.txt"
    latest.write_text(output)

    # Save timestamped archive.
    archive_dir = LOGS_DIR / "archive"
    archive_dir.mkdir(exist_ok=True)
    archive = archive_dir / f"briefing_{now.strftime('%Y%m%d_%H%M')}.txt"
    archive.write_text(output)

    saved_locations = [latest.name, archive.name]

    # Desktop delivery is opt-in because it writes outside the repo.
    if os.environ.get("MIA_OPEN_DESKTOP_BRIEFING", "").lower() in {"1", "true", "yes"}:
        desktop_path = HOME / "Desktop" / "Daily Briefing.txt"
        desktop_path.write_text(output)
        saved_locations.append("Desktop")

        try:
            subprocess.Popen(
                ["open", str(desktop_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass  # Non-critical — user can open manually.

    log(f"Briefing saved: {', '.join(saved_locations)}", "OK")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_briefing():
    print("\n  === MORNING BRIEFING ============================================")
    tee = _TeeWriter(sys.stdout)
    sys.stdout = tee
    start = time.time()
    try:
        run_agent("briefing_agent")
    finally:
        sys.stdout = tee._original
    elapsed = time.time() - start
    summary = f"  Run completed in {elapsed:.1f}s\n"
    print(summary)
    output = tee.getvalue() + summary
    deliver_briefing(output)


def cmd_scan():
    print("\n  === PROJECT SCAN ================================================")
    run_agent("health_scanner")


def cmd_organize():
    print("\n  === SMART ORGANIZER =============================================")
    run_agent("file_organizer")


def cmd_focus(minutes: int = 90):
    print(f"\n  === FOCUS MODE ({minutes} min) ========================================")
    run_applescript("focus_mode.applescript", str(minutes))


def cmd_launch(profile: str = "work"):
    print(f"\n  === LAUNCHING: {profile.upper()} ==========================================")
    run_applescript("app_launcher.applescript", profile)


def cmd_tile():
    print("\n  === TILING WINDOWS ==============================================")
    run_applescript("window_tiler.applescript")


def cmd_status():
    print("\n  === WORKSPACE STATUS ============================================")
    run_agent("health_scanner")
    usage = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
    lines = usage.stdout.strip().split("\n")
    if len(lines) > 1:
        parts = lines[1].split()
        log(f"Disk: {parts[4]} used ({parts[3]} available)")
    ps = subprocess.run(["ps", "aux"], capture_output=True, text=True)
    proc_count = len(ps.stdout.strip().split("\n")) - 1
    log(f"Running processes: {proc_count}")


def cmd_clean(confirm: str | None = None):
    print("\n  === DECLUTTER ===================================================")
    if confirm != "--confirm":
        print("  Live organization requires: python hub.py clean --confirm")
        print("  Running preview instead.\n")
        run_agent("file_organizer")
        return
    run_agent("file_organizer", "--clean")


# ---------------------------------------------------------------------------
# Machine state — lightweight checks for smart orchestration
# ---------------------------------------------------------------------------

def _check_clutter_level() -> int:
    """Return total file count across Desktop + Downloads."""
    total = 0
    for dirname in ("Desktop", "Downloads"):
        dirpath = HOME / dirname
        if dirpath.exists():
            total += sum(
                1 for f in dirpath.iterdir()
                if f.is_file() and not f.name.startswith(".")
            )
    return total


def _check_disk_pressure() -> int | None:
    """Return disk usage percentage, or None on error."""
    try:
        result = subprocess.run(
            ["df", "-h", "/"], capture_output=True, text=True, timeout=5
        )
        parts = result.stdout.strip().split("\n")[1].split()
        return int(parts[4].replace("%", ""))
    except Exception:
        return None


def _briefing_ran_recently(minutes: int = 30) -> bool:
    """Check if briefing was delivered within the last N minutes."""
    latest = LOGS_DIR / "briefing_latest.txt"
    if not latest.exists():
        return False
    age_sec = time.time() - latest.stat().st_mtime
    return age_sec < (minutes * 60)


def _get_machine_state() -> dict:
    """Snapshot of current machine state for mode decisions.

    Used by the mode runner to skip redundant steps — e.g., don't
    re-run briefing if it completed 10 minutes ago.
    """
    clutter = _check_clutter_level()
    disk_pct = _check_disk_pressure()
    return {
        "clutter": clutter,
        "clutter_high": clutter > 30,
        "disk_pct": disk_pct,
        "disk_pressure": (disk_pct or 0) > 85,
        "briefing_recent": _briefing_ran_recently(),
    }


# ---------------------------------------------------------------------------
# Workspace modes — config-driven orchestration
# ---------------------------------------------------------------------------

def _load_modes() -> dict:
    """Load mode definitions from config/modes.json."""
    modes_path = CONFIG_DIR / "modes.json"
    if not modes_path.exists():
        return {}
    with open(modes_path) as f:
        return json.load(f).get("modes", {})


def cmd_mode(mode_name: str):
    """Run a workspace mode — coordinated, state-aware execution.

    Modes are defined in config/modes.json as sequences of agent steps
    with optional conditions. The runner checks machine state before
    each step and skips redundant work.
    """
    modes = _load_modes()

    if mode_name not in modes:
        available = ", ".join(modes.keys()) if modes else "(none defined)"
        print(f"\n  Unknown mode: {mode_name}")
        print(f"  Available: {available}\n")
        return

    mode = modes[mode_name]
    steps = mode.get("steps", [])
    desc = mode.get("description", "")

    print(f"\n  +{'=' * 58}+")
    print(f"  |  MODE: {mode_name.upper():50s}|")
    print(f"  |  {desc:56s}|")
    print(f"  +{'=' * 58}+")

    # Get machine state once for all condition checks.
    state = _get_machine_state()

    state_notes = []
    if state["briefing_recent"]:
        state_notes.append("briefing is recent")
    if state["clutter_high"]:
        state_notes.append(f"clutter: {state['clutter']} files")
    if state["disk_pressure"]:
        state_notes.append(f"disk: {state['disk_pct']}%")
    if state_notes:
        print(f"  State: {', '.join(state_notes)}")

    mode_start = time.time()
    completed = []
    skipped = []

    # Action dispatch — maps config action names to callables.
    action_map = {
        "briefing": lambda step: cmd_briefing(),
        "scan": lambda step: cmd_scan(),
        "organize": lambda step: cmd_organize(),
        "clean": lambda step: cmd_clean(step.get("confirm")),
        "launch": lambda step: cmd_launch(step.get("profile", "work")),
        "tile": lambda step: cmd_tile(),
        "focus": lambda step: cmd_focus(step.get("minutes", 90)),
    }

    for i, step in enumerate(steps, 1):
        action = step.get("action")
        condition = step.get("condition")

        # Evaluate conditions against machine state.
        if condition:
            if condition == "clutter_high" and not state["clutter_high"]:
                skipped.append(f"{action} (clutter is low)")
                log(
                    f"Mode '{mode_name}' step {i}: skip {action} "
                    f"-- clutter low ({state['clutter']} files)",
                    "INFO",
                )
                continue
            if condition == "disk_pressure" and not state["disk_pressure"]:
                skipped.append(f"{action} (disk OK)")
                continue

        # Smart skip: briefing ran recently.
        if action == "briefing" and state["briefing_recent"]:
            skipped.append("briefing (ran recently)")
            log(
                f"Mode '{mode_name}' step {i}: skip briefing -- ran within 30m",
                "INFO",
            )
            continue

        handler = action_map.get(action)
        if not handler:
            log(f"Mode '{mode_name}': unknown action '{action}'", "WARN")
            continue

        log(f"Mode '{mode_name}' [{i}/{len(steps)}]: {action}", "RUN")
        try:
            handler(step)
            completed.append(action)
        except Exception as e:
            log(f"Mode '{mode_name}' step {action} failed: {e}", "ERR")
            completed.append(f"{action} (failed)")

    # Summary.
    elapsed = time.time() - mode_start
    print(f"\n  {'_' * 60}")
    print(f"  MODE COMPLETE: {mode_name}")
    print(f"  Completed: {', '.join(completed) if completed else '(none)'}")
    if skipped:
        print(f"  Skipped:   {', '.join(skipped)}")
    print(f"  Duration:  {elapsed:.1f}s")
    print(f"  {'_' * 60}\n")

    log(
        f"Mode '{mode_name}' finished in {elapsed:.1f}s "
        f"-- {len(completed)} done, {len(skipped)} skipped",
        "OK",
    )


# ---------------------------------------------------------------------------
# System audit
# ---------------------------------------------------------------------------

def cmd_audit():
    """Lightweight system audit — check for drift, noise, and staleness.

    Verifies that the system is healthy: configs exist, no unexpected
    agents have appeared, logs aren't accumulating excessively.
    """
    print("\n  === SYSTEM AUDIT ================================================")
    issues = []
    notes = []

    # Check for expected config files.
    for cfg_name in ("projects.json", "modes.json"):
        cfg_path = CONFIG_DIR / cfg_name
        if not cfg_path.exists():
            issues.append(f"Missing config: {cfg_name}")

    # Check agent count — flag unexpected additions.
    agent_files = list(AGENTS_DIR.glob("*.py"))
    agent_names = [a.stem for a in agent_files if a.stem != "__pycache__"]
    expected = {"briefing_agent", "health_scanner", "file_organizer", "__init__"}
    unexpected = set(agent_names) - expected
    if unexpected:
        issues.append(
            f"Unexpected agents: {', '.join(unexpected)} -- review if needed"
        )
    notes.append(
        f"Agents: {len(agent_names)} ({', '.join(sorted(agent_names))})"
    )

    # Check mode count.
    modes = _load_modes()
    notes.append(f"Modes: {len(modes)} ({', '.join(modes.keys())})")

    # Check log accumulation.
    log_files = list(LOGS_DIR.glob("hub_*.log")) if LOGS_DIR.exists() else []
    archive_dir = LOGS_DIR / "archive"
    archive_files = (
        list(archive_dir.glob("briefing_*.txt")) if archive_dir.exists() else []
    )
    if len(archive_files) > 30:
        issues.append(
            f"Briefing archive has {len(archive_files)} files -- consider pruning"
        )
    notes.append(
        f"Log files: {len(log_files)}, archived briefings: {len(archive_files)}"
    )

    # Delegation check.
    notes.append("Overlap check: 'all' delegates to 'mode morning' (no duplication)")

    # Report.
    if issues:
        print(f"\n  Issues ({len(issues)}):")
        for issue in issues:
            print(f"    !! {issue}")
    else:
        print(f"\n  No issues found.")

    print(f"\n  System state:")
    for note in notes:
        print(f"    {note}")

    state = _get_machine_state()
    print(f"    Clutter: {state['clutter']} files (Desktop + Downloads)")
    print(f"    Disk: {state['disk_pct']}%")
    print(f"    Briefing recent: {'yes' if state['briefing_recent'] else 'no'}")
    print()

    return {"issues": len(issues)}


# ---------------------------------------------------------------------------
# Interactive menu
# ---------------------------------------------------------------------------

def interactive_menu():
    print(BANNER)
    commands = [
        ("1", "Morning Briefing", cmd_briefing),
        ("2", "Project Scan", cmd_scan),
        ("3", "Smart Organize", cmd_organize),
        ("4", "Focus Mode (90 min)", lambda: cmd_focus(90)),
        ("5", "Launch Work Apps", lambda: cmd_launch("work")),
        ("6", "Tile Windows", cmd_tile),
        ("7", "Workspace Status", cmd_status),
        ("8", "Declutter Desktop/Downloads (preview)", lambda: cmd_clean(None)),
        ("9", "FULL MORNING BOOT", lambda: cmd_mode("morning")),
        ("d", "System Audit", cmd_audit),
        ("q", "Quit", None),
    ]

    # Show available modes.
    modes = _load_modes()
    if modes:
        print("  Modes:")
        for name, cfg in modes.items():
            print(f"    [m]  mode {name:12s} -- {cfg.get('description', '')}")
        print()

    for key, label, _ in commands:
        marker = " <<" if key == "9" else ""
        print(f"    [{key}]  {label}{marker}")

    print()
    choice = input("  Select command -> ").strip().lower()

    if choice == "q":
        print("  Exiting hub.\n")
        return

    # Handle inline mode selection: "m morning" or "mode morning".
    if choice.startswith("m ") or choice.startswith("mode "):
        mode_name = choice.split(None, 1)[1].strip()
        cmd_mode(mode_name)
        return

    for key, _, fn in commands:
        if key == choice and fn:
            fn()
            return

    print("  Invalid choice.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Marketing Intelligence Hub v2.0"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default=None,
        choices=[
            "briefing", "scan", "organize", "focus", "launch",
            "tile", "status", "clean", "all", "mode", "audit",
        ],
    )
    parser.add_argument("extra", nargs="*", default=[])
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm write-capable commands such as clean.",
    )

    args = parser.parse_args()

    dispatch = {
        "briefing": cmd_briefing,
        "scan": cmd_scan,
        "organize": cmd_organize,
        "focus": lambda: cmd_focus(int(args.extra[0]) if args.extra else 90),
        "launch": lambda: cmd_launch(args.extra[0] if args.extra else "work"),
        "tile": cmd_tile,
        "status": cmd_status,
        "clean": lambda: cmd_clean("--confirm" if args.confirm else None),
        "all": lambda: cmd_mode("morning"),
        "mode": lambda: cmd_mode(args.extra[0] if args.extra else "morning"),
        "audit": cmd_audit,
    }

    if args.command is None:
        interactive_menu()
    else:
        dispatch[args.command]()


if __name__ == "__main__":
    main()

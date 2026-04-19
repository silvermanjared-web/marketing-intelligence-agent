"""
Configuration loader for the marketing intelligence system.

Single source of truth for project paths and shared constants.
All agents import from here instead of defining their own paths.
"""

import json
from pathlib import Path

# Resolve paths relative to the repo root, not this file's location.
# Supports both direct execution and module imports.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG_DIR = _REPO_ROOT / "config"

HOME = Path.home()


def _load_projects() -> dict[str, Path]:
    """Load project definitions from config/projects.json.

    Returns a dict mapping project names to resolved filesystem paths.
    Expands ~ to the user's home directory for portability.
    """
    config_path = _CONFIG_DIR / "projects.json"
    if not config_path.exists():
        return {}
    with open(config_path) as f:
        data = json.load(f)
    return {
        name: Path(path).expanduser()
        for name, path in data.get("projects", {}).items()
    }


def _load_modes() -> dict:
    """Load workflow mode definitions from config/modes.json.

    Each mode defines a sequence of agent steps with optional
    conditions for state-aware execution.
    """
    modes_path = _CONFIG_DIR / "modes.json"
    if not modes_path.exists():
        return {}
    with open(modes_path) as f:
        return json.load(f).get("modes", {})


# Module-level singletons — loaded once on import.
PROJECTS = _load_projects()
MODES = _load_modes()

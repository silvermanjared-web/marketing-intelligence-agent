from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .receipts import make_receipt


CAPABILITIES: dict[str, dict[str, Any]] = {
    "intelligence.brief": {
        "description": "Generate a source-aware intelligence briefing.",
        "effect": "read",
        "requires_confirmation": False,
    },
    "health.scan": {
        "description": "Inspect configured project health and drift.",
        "effect": "read",
        "requires_confirmation": False,
    },
    "files.organize.preview": {
        "description": "Preview file-organization actions without mutation.",
        "effect": "read",
        "requires_confirmation": False,
    },
    "files.organize.apply": {
        "description": "Apply the bounded file-organization plan.",
        "effect": "write",
        "requires_confirmation": True,
    },
    "system.audit": {
        "description": "Run the repository/system audit path.",
        "effect": "read",
        "requires_confirmation": False,
    },
}


def discover() -> dict[str, dict[str, Any]]:
    return {name: dict(spec) for name, spec in CAPABILITIES.items()}


def invoke(capability: str, *, confirm: bool = False) -> dict[str, Any]:
    spec = CAPABILITIES.get(capability)
    if spec is None:
        return make_receipt(capability, "read", "refused", reason="unknown capability")
    if spec["requires_confirmation"] and not confirm:
        return make_receipt(
            capability,
            spec["effect"],
            "refused",
            reason="explicit confirmation required",
        )

    # Import only after capability admission so discovery remains lightweight.
    import hub

    dispatch = {
        "intelligence.brief": hub.cmd_briefing,
        "health.scan": hub.cmd_scan,
        "files.organize.preview": hub.cmd_organize,
        "files.organize.apply": lambda: hub.cmd_clean("--confirm"),
        "system.audit": hub.cmd_audit,
    }
    handler = dispatch[capability]
    result = handler()
    return make_receipt(
        capability,
        spec["effect"],
        "executed" if spec["effect"] == "write" else "observed",
        evidence={"handler_result": result},
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Marketing Intelligence capability interface")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("discover")
    run = sub.add_parser("invoke")
    run.add_argument("capability")
    run.add_argument("--confirm", action="store_true")
    args = parser.parse_args()

    if args.command == "discover":
        print(json.dumps(discover(), indent=2, sort_keys=True))
        return 0

    print(json.dumps(invoke(args.capability, confirm=args.confirm), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
import uuid


@dataclass(frozen=True)
class Receipt:
    run_id: str
    capability: str
    effect: str
    status: str
    evidence: dict[str, Any]
    reason: str | None = None


def make_receipt(
    capability: str,
    effect: str,
    status: str,
    evidence: dict[str, Any] | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    return asdict(
        Receipt(
            run_id=str(uuid.uuid4()),
            capability=capability,
            effect=effect,
            status=status,
            evidence=evidence or {},
            reason=reason,
        )
    )

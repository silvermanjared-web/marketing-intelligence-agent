from src.core.capabilities import discover


def main() -> int:
    capabilities = discover()
    required = {
        "intelligence.brief",
        "health.scan",
        "files.organize.preview",
        "files.organize.apply",
        "system.audit",
    }
    missing = sorted(required - set(capabilities))
    if missing:
        raise SystemExit(f"missing capabilities: {missing}")
    assert capabilities["files.organize.apply"]["effect"] == "write"
    assert capabilities["files.organize.apply"]["requires_confirmation"] is True
    print("marketing intelligence agent smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

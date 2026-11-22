#!/usr/bin/env python3
"""Verify the committed Entity Registry snapshot against its immutable upstream commit."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "metadata" / "entity-registry.lock.json"


def fail(message: str) -> None:
    raise SystemExit("ENTITY REGISTRY VERIFICATION FAILED: " + message)


def main() -> int:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    repository = lock.get("registry_repository")
    commit = lock.get("registry_commit", "")
    if repository != "dan-beranek/dio-odi-entity-registry":
        fail("unexpected registry repository")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        fail("registry_commit must be a full immutable commit SHA")

    snapshot_path = ROOT / lock["snapshot_path"]
    snapshot_bytes = snapshot_path.read_bytes()
    registry = json.loads(snapshot_bytes)
    if registry.get("status") != "canonical-approved":
        fail("snapshot is not canonical-approved")
    if registry.get("registry_version") != lock.get("registry_version"):
        fail("snapshot version differs from the lock")

    source_url = f"https://raw.githubusercontent.com/{repository}/{commit}/{lock['source_path']}"
    request = Request(source_url, headers={"User-Agent": "DIO-ODI-Reference-Model/Entity-Registry-Check"})
    try:
        with urlopen(request, timeout=20) as response:
            upstream_bytes = response.read()
    except Exception as exc:
        fail(f"cannot retrieve immutable upstream source: {exc}")
    if upstream_bytes != snapshot_bytes:
        fail("committed Entity Registry snapshot differs from immutable upstream source")

    keys = {entity.get("key") for entity in registry.get("entities", [])}
    missing = set(lock.get("consumed_entities", [])) - keys
    if missing:
        fail("snapshot is missing consumed identities: " + ", ".join(sorted(missing)))

    print(f"Verified DIO/ODI Entity Registry v{registry['registry_version']} at {commit}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

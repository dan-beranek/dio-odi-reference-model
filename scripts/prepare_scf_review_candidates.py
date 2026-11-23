#!/usr/bin/env python3
"""Prepare a review-only intake report for possible SCF events.

The scanner detects changes in authoritative project registries. It does not
decide whether a change is semantically significant and never writes events.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# Only source registries whose records can provide evidence for a possible
# Semantic Change Feed event are monitored. Derived outputs are excluded.
SOURCE_COLLECTIONS = {
    "metadata/works.json": ("works", "id"),
    "metadata/distributions.json": ("works", "work"),
    "metadata/external-reception.json": ("entries", "id"),
    "metadata/application-mappings.json": ("mappings", "frontend"),
    "discovery/catalog-source.json": ("entries", "identifier"),
}


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout


def read_json_at(revision: str, relative_path: str) -> dict[str, Any] | None:
    try:
        raw = run_git("show", f"{revision}:{relative_path}")
    except subprocess.CalledProcessError:
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in {relative_path} at {revision}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {relative_path} at {revision}")
    return value


def record_identifier(
    record: dict[str, Any], primary_key: str, index: int
) -> str:
    value = record.get(primary_key)
    if value is None and primary_key == "frontend":
        value = record.get("path") or record.get("title")
    if value is None:
        raise ValueError(
            f"Registry record at index {index} has no usable {primary_key!r} identifier"
        )
    return str(value)


def extract_records(
    relative_path: str, document: dict[str, Any] | None
) -> dict[str, dict[str, Any]]:
    """Flatten a tracked registry into stable, comparable source records."""
    if document is None:
        return {}

    if relative_path not in SOURCE_COLLECTIONS:
        raise ValueError(f"Untracked SCF source registry: {relative_path}")

    collection_key, primary_key = SOURCE_COLLECTIONS[relative_path]
    collection = document.get(collection_key, [])
    if not isinstance(collection, list):
        raise ValueError(
            f"{relative_path}: expected {collection_key!r} to be an array"
        )

    records: dict[str, dict[str, Any]] = {}

    if relative_path == "metadata/distributions.json":
        for index, item in enumerate(collection):
            if not isinstance(item, dict):
                raise ValueError(f"{relative_path}: item {index} is not an object")
            work_id = record_identifier(item, primary_key, index)
            work_record = {
                key: value for key, value in item.items()
                if key != "representations"
            }
            records[f"work:{work_id}"] = work_record

            representations = item.get("representations", [])
            if not isinstance(representations, list):
                raise ValueError(
                    f"{relative_path}: representations for {work_id!r} are not an array"
                )
            for rep_index, representation in enumerate(representations):
                if not isinstance(representation, dict):
                    raise ValueError(
                        f"{relative_path}: representation {work_id}[{rep_index}] is not an object"
                    )
                rep_id = record_identifier(representation, "id", rep_index)
                if rep_id in records:
                    raise ValueError(
                        f"{relative_path}: duplicate record identifier {rep_id!r}"
                    )
                records[rep_id] = representation
    else:
        for index, item in enumerate(collection):
            if not isinstance(item, dict):
                raise ValueError(f"{relative_path}: item {index} is not an object")
            identifier = record_identifier(item, primary_key, index)
            if identifier in records:
                raise ValueError(
                    f"{relative_path}: duplicate record identifier {identifier!r}"
                )
            records[identifier] = item

    # Registry-level metadata changes (for example a version/status update)
    # are visible as a separate candidate rather than silently ignored.
    registry_metadata = {
        key: value for key, value in document.items() if key != collection_key
    }
    records["__registry_metadata__"] = registry_metadata
    return records


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def fingerprint(value: Any) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def compare_records(
    relative_path: str,
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return record deltas without assigning SCF eligibility or semantics."""
    candidates: list[dict[str, Any]] = []
    for record_id in sorted(set(before) | set(after)):
        old = before.get(record_id)
        new = after.get(record_id)
        if old == new:
            continue

        if old is None:
            change_kind = "added"
        elif new is None:
            change_kind = "removed"
        else:
            change_kind = "modified"

        display_record = new if new is not None else old
        assert display_record is not None
        title = str(
            display_record.get("title")
            or display_record.get("displayName")
            or display_record.get("name")
            or display_record.get("work")
            or record_id
        )

        before_hash = fingerprint(old)
        after_hash = fingerprint(new)
        change_fingerprint = fingerprint({
            "candidate_key": f"{relative_path}::{record_id}",
            "before_sha256": before_hash,
            "after_sha256": after_hash,
        })

        candidates.append({
            "candidate_key": f"{relative_path}::{record_id}",
            "source_path": relative_path,
            "source_record_id": record_id,
            "change_kind": change_kind,
            "title": title,
            "before_sha256": before_hash,
            "after_sha256": after_hash,
            "change_fingerprint": change_fingerprint,
            "before": old,
            "after": new,
        })
    return candidates


def changed_source_paths(base_sha: str, head_sha: str) -> list[str]:
    paths = run_git(
        "diff",
        "--name-only",
        "--no-renames",
        f"{base_sha}..{head_sha}",
        "--",
        *SOURCE_COLLECTIONS.keys(),
    ).splitlines()
    return sorted(path for path in set(paths) if path in SOURCE_COLLECTIONS)


def collect_candidates(
    base_sha: str, head_sha: str
) -> tuple[list[str], list[dict[str, Any]]]:
    changed = changed_source_paths(base_sha, head_sha)
    candidates: list[dict[str, Any]] = []
    for relative_path in changed:
        before_doc = read_json_at(base_sha, relative_path)
        after_doc = read_json_at(head_sha, relative_path)
        before_records = extract_records(relative_path, before_doc)
        after_records = extract_records(relative_path, after_doc)
        candidates.extend(
            compare_records(relative_path, before_records, after_records)
        )
    candidates.sort(
        key=lambda item: (item["source_path"], item["source_record_id"])
    )
    return changed, candidates


def commit_summary(revision: str) -> dict[str, str]:
    values = run_git(
        "show", "-s", "--format=%H%n%cs%n%s", revision
    ).splitlines()
    return {
        "sha": values[0],
        "commit_date": values[1] if len(values) > 1 else "",
        "subject": values[2] if len(values) > 2 else "",
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# SCF review-candidate intake",
        "",
        f"Generated: {report['generated_at']}",
        f"Base: `{report['comparison']['base_sha']}`",
        f"Head: `{report['comparison']['head_sha']}`",
        "",
        "> This is a review queue, not an SCF event generator. A source change is not",
        "> evidence of semantic significance by itself. No event is written, numbered,",
        "> classified, dated, or published automatically.",
        "",
        f"Changed source registries: **{len(report['changed_source_files'])}**  ",
        f"Changed source records: **{len(report['candidates'])}**",
        "",
    ]

    if not report["candidates"]:
        lines.extend([
            "No record-level changes were detected in the tracked source registries.",
            "",
        ])
    else:
        lines.extend(["## Candidate records", ""])
        for index, item in enumerate(report["candidates"], start=1):
            lines.extend([
                f"### {index}. {item['title']}",
                "",
                f"- Source: `{item['source_path']}`",
                f"- Record: `{item['source_record_id']}`",
                f"- Source change: **{item['change_kind']}**",
                f"- Change fingerprint: `{item['change_fingerprint']}`",
                "- SCF decision: **not assessed**",
                "",
            ])
        lines.extend([
            "## Editorial review before any SCF change",
            "",
            "- Is the change material to the documented DIO/ODI system, its publications, provenance, mappings, or public infrastructure?",
            "- Is the underlying event independently evidenced by the cited source, release, registry, or deployment record?",
            "- What is the defensible event date and corresponding `date_basis`? Do not substitute the Git commit date.",
            "- Are `before`, `after`, scope, impact, preserved invariants, and lineage accurately represented?",
            "- Does the change belong in the SCF, or only in its source registry?",
            "",
            "The JSON artifact contains the before/after source records for review.",
            "",
        ])

    lines.extend([
        "## Automation boundary",
        "",
        "- Canonical SCF records remain in `semantic-change-feed/events.json`.",
        "- The scanner only reports changes in the tracked source registries.",
        "- It does not infer conceptual intent, event dates, impact, or lineage.",
        "- It does not edit the feed, increment the feed version, create a release, or deploy the site.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-sha",
        default="",
        help="Base commit; defaults to the parent of HEAD.",
    )
    parser.add_argument(
        "--head-sha", default="HEAD", help="Head commit; defaults to HEAD."
    )
    parser.add_argument("--output-dir", default="scf-review-output")
    args = parser.parse_args()

    head_sha = run_git("rev-parse", args.head_sha).strip()
    base_ref = args.base_sha or f"{head_sha}^"
    base_sha = run_git("rev-parse", base_ref).strip()
    changed, candidates = collect_candidates(base_sha, head_sha)

    report = {
        "report_version": "0.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "comparison": {
            "base_sha": base_sha,
            "head_sha": head_sha,
            "head_commit": commit_summary(head_sha),
        },
        "changed_source_files": changed,
        "policy": {
            "review_required": True,
            "automatic_scf_writes": False,
            "git_diff_is_semantic_evidence": False,
            "event_dates_inferred": False,
            "event_classification_inferred": False,
        },
        "candidates": candidates,
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "scf-review-candidates.json"
    markdown_path = output_dir / "scf-review-candidates.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")

    print(f"Changed source registries: {len(changed)}")
    print(f"Review candidates: {len(candidates)}")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

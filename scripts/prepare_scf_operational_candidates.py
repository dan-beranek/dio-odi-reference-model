#!/usr/bin/env python3
"""Collect review-only deployment and GitHub Release observations for the SCF."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
API_BASE = "https://api.github.com"
API_VERSION = "2022-11-28"
USER_AGENT = "DIO-ODI-SCF-Operational-Intake/0.1"

# Exact workflow names observed in the public repositories. CI and validation
# workflows are intentionally excluded from the deployment allow-list.
SOURCES = (
    {
        "repository": "dan-beranek/dio-odi-reference-model",
        "deployment_workflows": ("pages build and deployment",),
    },
    {
        "repository": "dan-beranek/dio-odi-mcp",
        "deployment_workflows": ("Deploy Cloudflare Worker",),
    },
    {
        "repository": "dan-beranek-apps/agentic-entity-resolution-guardrail-planner",
        "deployment_workflows": ("Build and deploy product frontend",),
    },
    {
        "repository": "dan-beranek/dio-odi-autorsky-koncept",
        "deployment_workflows": ("Deploy static site to GitHub Pages",),
    },
    {
        "repository": "dan-beranek/dio-to-dio",
        "deployment_workflows": ("Build and deploy DIO to DIO",),
    },
    {
        "repository": "dan-beranek-apps/dan-beranek-apps.github.io",
        "deployment_workflows": ("pages build and deployment",),
    },
)


class ScanError(RuntimeError):
    """Raised when a public source cannot be inspected reliably."""


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def stable_fingerprint(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class GitHubClient:
    """Minimal unauthenticated client for public GitHub REST resources."""

    def get_json(
        self, path: str, params: dict[str, Any] | None = None
    ) -> Any:
        query = f"?{urlencode(params)}" if params else ""
        request = Request(
            f"{API_BASE}{path}{query}",
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": API_VERSION,
                "User-Agent": USER_AGENT,
            },
        )
        try:
            with urlopen(request, timeout=25) as response:
                payload = response.read()
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise ScanError(
                f"GitHub API returned HTTP {exc.code} for {path}: {detail}"
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ScanError(f"GitHub API request failed for {path}: {exc}") from exc

        try:
            return json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ScanError(f"GitHub API returned invalid JSON for {path}") from exc


def existing_evidence_index(feed: dict[str, Any]) -> dict[str, list[str]]:
    """Map exact evidence URLs already cited by SCF events to their event IDs."""
    result: dict[str, list[str]] = {}
    for event in feed.get("events", []):
        if not isinstance(event, dict) or not isinstance(event.get("id"), str):
            continue
        evidence = event.get("evidence", {})
        sources = evidence.get("sources", []) if isinstance(evidence, dict) else []
        if not isinstance(sources, list):
            continue
        for source in sources:
            if not isinstance(source, dict):
                continue
            url = source.get("url")
            if isinstance(url, str) and url:
                result.setdefault(url.rstrip("/"), []).append(event["id"])
    return result


def reference_status(
    source_url: str, evidence_index: dict[str, list[str]]
) -> tuple[str, list[str]]:
    event_ids = sorted(set(evidence_index.get(source_url.rstrip("/"), [])))
    return ("already-cited" if event_ids else "review-required", event_ids)


def normalise_deployment_run(
    repository: str,
    configured_workflows: tuple[str, ...],
    run: dict[str, Any],
    cutoff: datetime,
    evidence_index: dict[str, list[str]],
) -> dict[str, Any] | None:
    workflow_name = str(run.get("name") or "").strip()
    allow_list = {name.casefold() for name in configured_workflows}
    if workflow_name.casefold() not in allow_list:
        return None
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        return None
    if run.get("head_branch") not in (None, "", "main"):
        return None

    completed_at = parse_timestamp(run.get("updated_at"))
    created_at = parse_timestamp(run.get("created_at"))
    observed_at = completed_at or created_at
    if observed_at is None or observed_at < cutoff:
        return None

    run_id = run.get("id")
    source_url = run.get("html_url")
    head_sha = run.get("head_sha")
    if not run_id or not isinstance(source_url, str) or not head_sha:
        return None

    status, event_ids = reference_status(source_url, evidence_index)
    identity = {"kind": "deployment", "repository": repository, "run_id": int(run_id)}
    return {
        "candidate_id": f"github-deployment:{repository}:{run_id}",
        "candidate_fingerprint": stable_fingerprint(identity),
        "kind": "deployment",
        "repository": repository,
        "workflow_name": workflow_name,
        "workflow_event": run.get("event"),
        "workflow_conclusion": run.get("conclusion"),
        "run_id": int(run_id),
        "head_sha": str(head_sha),
        "workflow_created_at": run.get("created_at"),
        "workflow_completed_at": run.get("updated_at"),
        "date_candidate": observed_at.date().isoformat(),
        "date_basis_candidate": "deployment_date",
        "date_basis_note": (
            "Successful allow-listed deployment workflow. Workflow completion "
            "is an operational proxy; confirm the actual public deployment "
            "before using this date in the SCF."
        ),
        "source_url": source_url,
        "reference_status": status,
        "existing_event_ids": event_ids,
        "editorial_status": "not-assessed",
    }


def normalise_release(
    repository: str,
    release: dict[str, Any],
    cutoff: datetime,
    evidence_index: dict[str, list[str]],
) -> dict[str, Any] | None:
    if release.get("draft") is True or release.get("prerelease") is True:
        return None
    published_at = parse_timestamp(release.get("published_at"))
    if published_at is None or published_at < cutoff:
        return None

    release_id = release.get("id")
    tag_name = release.get("tag_name")
    source_url = release.get("html_url")
    if not release_id or not tag_name or not isinstance(source_url, str):
        return None

    status, event_ids = reference_status(source_url, evidence_index)
    identity = {
        "kind": "release",
        "repository": repository,
        "release_id": int(release_id),
        "tag_name": str(tag_name),
    }
    return {
        "candidate_id": f"github-release:{repository}:{release_id}",
        "candidate_fingerprint": stable_fingerprint(identity),
        "kind": "release",
        "repository": repository,
        "release_id": int(release_id),
        "tag_name": str(tag_name),
        "release_name": release.get("name") or str(tag_name),
        "target_commitish": release.get("target_commitish"),
        "published_at": release.get("published_at"),
        "date_candidate": published_at.date().isoformat(),
        "date_basis_candidate": "publication_date",
        "date_basis_note": (
            "GitHub records this release publication timestamp. Confirm that "
            "the release itself is an SCF-worthy event and is not already "
            "represented by another publication or archive record."
        ),
        "source_url": source_url,
        "reference_status": status,
        "existing_event_ids": event_ids,
        "editorial_status": "not-assessed",
    }


def fetch_all_pages(
    client: GitHubClient,
    path: str,
    cutoff: datetime,
    timestamp_field: str,
    per_page: int = 100,
    max_pages: int = 10,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        payload = client.get_json(path, {"per_page": per_page, "page": page})
        if isinstance(payload, dict):
            current = payload.get("workflow_runs")
        elif isinstance(payload, list):
            current = payload
        else:
            current = None
        if not isinstance(current, list):
            raise ScanError(f"GitHub API payload for {path} has no expected collection")

        items.extend(item for item in current if isinstance(item, dict))
        if len(current) < per_page:
            break

        timestamps = [
            parse_timestamp(item.get(timestamp_field))
            for item in current
        ]
        usable = [value for value in timestamps if value is not None]
        if usable and min(usable) < cutoff:
            break
    return items


def scan_sources(
    client: GitHubClient,
    sources: tuple[dict[str, Any], ...],
    cutoff: datetime,
    evidence_index: dict[str, list[str]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]], dict[str, int]]:
    candidates: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    stats = {
        "repositories_scanned": 0,
        "workflow_runs_inspected": 0,
        "release_records_inspected": 0,
    }

    for source in sources:
        repository = source["repository"]
        stats["repositories_scanned"] += 1

        try:
            runs = fetch_all_pages(
                client,
                f"/repos/{repository}/actions/runs",
                cutoff,
                timestamp_field="updated_at",
            )
            stats["workflow_runs_inspected"] += len(runs)
            for run in runs:
                candidate = normalise_deployment_run(
                    repository,
                    tuple(source.get("deployment_workflows", ())),
                    run,
                    cutoff,
                    evidence_index,
                )
                if candidate:
                    candidates.append(candidate)
        except ScanError as exc:
            errors.append({
                "repository": repository,
                "source": "workflow-runs",
                "error": str(exc),
            })

        try:
            releases = fetch_all_pages(
                client,
                f"/repos/{repository}/releases",
                cutoff,
                timestamp_field="published_at",
            )
            stats["release_records_inspected"] += len(releases)
            for release in releases:
                candidate = normalise_release(
                    repository, release, cutoff, evidence_index
                )
                if candidate:
                    candidates.append(candidate)
        except ScanError as exc:
            errors.append({
                "repository": repository,
                "source": "releases",
                "error": str(exc),
            })

    candidates.sort(
        key=lambda item: (
            item.get("date_candidate") or "",
            item["repository"],
            item["candidate_id"],
        ),
        reverse=True,
    )
    return candidates, errors, stats


def render_markdown(report: dict[str, Any]) -> str:
    candidates = report["candidates"]
    not_cited = [
        item for item in candidates
        if item["reference_status"] == "review-required"
    ]
    already_cited = [
        item for item in candidates
        if item["reference_status"] == "already-cited"
    ]
    lines = [
        "# SCF operational evidence intake",
        "",
        f"Generated: {report['generated_at']}",
        f"Lookback: {report['lookback_hours']} hours",
        f"Coverage starts: {report['coverage_starts_at']}",
        "",
        "> This is an operational evidence queue, not an SCF event generator. "
        "Successful deploys and published releases are candidate signals, "
        "not proof of a semantically material event.",
        "",
        f"Repositories scanned: **{report['stats']['repositories_scanned']}**  ",
        f"Workflow runs inspected: **{report['stats']['workflow_runs_inspected']}**  ",
        f"Release records inspected: **{report['stats']['release_records_inspected']}**  ",
        f"Candidate observations: **{len(candidates)}**  ",
        f"Not yet cited in SCF: **{len(not_cited)}**  ",
        f"Already cited by exact evidence URL: **{len(already_cited)}**",
        "",
    ]

    if not candidates:
        lines.extend([
            "No matching successful deployment or published release was found in the lookback window.",
            "",
        ])
    else:
        for item in candidates:
            title = (
                f"{item['repository']} — {item['workflow_name']}"
                if item["kind"] == "deployment"
                else f"{item['repository']} — {item['tag_name']}"
            )
            lines.extend([
                f"## {title}",
                "",
                f"- Observation: **{item['kind']}**",
                f"- Date candidate: **{item['date_candidate']}** ({item['date_basis_candidate']})",
                f"- Reference status: **{item['reference_status']}**",
                f"- Existing SCF event IDs: {', '.join(item['existing_event_ids']) or 'none found by exact evidence URL'}",
                f"- Candidate ID: {item['candidate_id']}",
                f"- Evidence: {item['source_url']}",
            ])
            if item["kind"] == "deployment":
                lines.extend([
                    f"- Workflow conclusion: {item['workflow_conclusion']}",
                    f"- Head commit: {item['head_sha']}",
                    f"- Workflow completed: {item['workflow_completed_at']}",
                ])
            else:
                lines.extend([
                    f"- Published: {item['published_at']}",
                    f"- Release name: {item['release_name']}",
                ])
            lines.extend([
                f"- Date note: {item['date_basis_note']}",
                "- Editorial decision: **not assessed**",
                "",
            ])

    if report["errors"]:
        lines.extend(["## Incomplete sources", ""])
        for error in report["errors"]:
            lines.append(
                f"- {error['repository']} ({error['source']}): {error['error']}"
            )
        lines.append("")

    lines.extend([
        "## Editorial boundary",
        "",
        "- Only successful, exact-name deployment workflows on main are collected.",
        "- Workflow completion time is a date candidate, not independent proof of public deployment.",
        "- Release publication time is retained, but release inclusion in the SCF requires editorial review.",
        "- Exact evidence URL matching helps identify observations already cited by existing events.",
        "- No event IDs are allocated; events.json, feed version, archives and public site are not modified.",
        "",
    ])
    return "\n".join(lines)


def build_report(
    client: GitHubClient,
    feed: dict[str, Any],
    lookback_hours: int,
    now: datetime | None = None,
    sources: tuple[dict[str, Any], ...] = SOURCES,
) -> dict[str, Any]:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    cutoff = now - timedelta(hours=lookback_hours)
    candidates, errors, stats = scan_sources(
        client, sources, cutoff, existing_evidence_index(feed)
    )
    return {
        "report_version": "0.1.0",
        "generated_at": now.isoformat(),
        "lookback_hours": lookback_hours,
        "coverage_starts_at": cutoff.isoformat(),
        "policy": {
            "review_required": True,
            "automatic_scf_writes": False,
            "workflow_completion_is_deployment_proof": False,
            "release_publication_is_automatic_scf_event": False,
            "existing_evidence_url_matching": "exact-url",
        },
        "stats": stats,
        "candidates": candidates,
        "errors": errors,
        "scan_complete": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lookback-hours", type=int, default=48)
    parser.add_argument("--output-dir", default="scf-operational-output")
    args = parser.parse_args()

    if not 1 <= args.lookback_hours <= 720:
        parser.error("--lookback-hours must be between 1 and 720")

    try:
        feed = json.loads(
            (ROOT / "semantic-change-feed/events.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read canonical SCF feed: {exc}", file=sys.stderr)
        return 2

    report = build_report(
        GitHubClient(), feed, lookback_hours=args.lookback_hours
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "scf-operational-candidates.json"
    markdown_path = output_dir / "scf-operational-candidates.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")

    print(f"Repositories scanned: {report['stats']['repositories_scanned']}")
    print(f"Workflow runs inspected: {report['stats']['workflow_runs_inspected']}")
    print(f"Release records inspected: {report['stats']['release_records_inspected']}")
    print(f"Candidate observations: {len(report['candidates'])}")
    print(f"Not yet cited in SCF: {sum(x['reference_status'] == 'review-required' for x in report['candidates'])}")
    print(f"Source errors: {len(report['errors'])}")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

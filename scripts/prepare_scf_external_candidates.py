#!/usr/bin/env python3
"""Collect review-only observations from external registries and publication APIs."""
from __future__ import annotations

import argparse
import email.utils
import hashlib
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
API_BASE = "https://api.github.com"
BIOREGISTRY_PATH = "src/bioregistry/data/bioregistry.json"
BIOREGISTRY_API = "https://bioregistry.io/api/registry/dio-odi?format=json"
SEMANTIC_FARM_API = "https://semantic.farm/api/registry/dio-odi?format=json"
BARTOC_API = "https://bartoc.org/api/data?uri=http%3A%2F%2Fbartoc.org%2Fen%2Fnode%2F21188"
HASHNODE_RSS = "https://dio-odi.hashnode.dev/rss.xml"
DEVTO_API = "https://dev.to/api/articles"
ARXIV_API = "https://export.arxiv.org/api/query?id_list=2610.37407"
USER_AGENT = "DIO-ODI-SCF-External-Intake/0.1 (+https://vocab.danielberanek.cz/)"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


class ScanError(RuntimeError):
    """Raised when a public source cannot be inspected reliably."""


def parse_timestamp(value: Any) -> datetime | None:
    if isinstance(value, list):
        parsed = [parse_timestamp(item) for item in value]
        parsed = [item for item in parsed if item is not None]
        return max(parsed) if parsed else None
    if isinstance(value, dict):
        for key in ("@value", "value", "date", "datetime"):
            if key in value:
                return parse_timestamp(value[key])
        return None
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = value.strip()
    try:
        parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = email.utils.parsedate_to_datetime(candidate)
        except (TypeError, ValueError, OverflowError):
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def stable_fingerprint(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def fetch_resource(
    url: str, accept: str = "application/json", retries: int = 3
) -> tuple[bytes, dict[str, str]]:
    last_error: Exception | None = None
    for attempt in range(retries):
        request = Request(
            url,
            headers={"Accept": accept, "User-Agent": USER_AGENT},
        )
        try:
            with urlopen(request, timeout=30) as response:
                body = response.read()
                if len(body) > 20_000_000:
                    raise ScanError(f"Response too large for {url}")
                headers = {key.lower(): value for key, value in response.headers.items()}
                return body, headers
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:400]
            last_error = ScanError(f"HTTP {exc.code} for {url}: {detail}")
            if exc.code not in (408, 425, 429, 500, 502, 503, 504):
                raise last_error from exc
        except (URLError, TimeoutError, OSError) as exc:
            last_error = ScanError(f"Request failed for {url}: {exc}")
        if attempt < retries - 1:
            time.sleep(1.5 * (attempt + 1))
    assert last_error is not None
    raise last_error


def fetch_json(url: str) -> tuple[Any, dict[str, str]]:
    body, headers = fetch_resource(url, "application/json")
    try:
        return json.loads(body.decode("utf-8")), headers
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScanError(f"Invalid JSON returned by {url}") from exc


def fetch_text(url: str, accept: str) -> str:
    body, _ = fetch_resource(url, accept)
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ScanError(f"Non-UTF-8 response returned by {url}") from exc


class GitHubClient:
    """Read-only client for public upstream GitHub metadata."""

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.environ.get("SCF_GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN")

    def get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query = f"?{urlencode(params)}" if params else ""
        request = Request(
            f"{API_BASE}{path}{query}",
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": USER_AGENT,
                **({"Authorization": f"Bearer {self.token}"} if self.token else {}),
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                payload = response.read()
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:400]
            raise ScanError(f"GitHub API HTTP {exc.code} for {path}: {detail}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ScanError(f"GitHub API request failed for {path}: {exc}") from exc
        try:
            return json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ScanError(f"GitHub API returned invalid JSON for {path}") from exc


def fetch_bioregistry_record(revision: str) -> dict[str, Any]:
    """Fetch one exact upstream dio-odi record from a versioned registry snapshot."""
    url = (
        "https://raw.githubusercontent.com/biopragmatics/bioregistry/"
        f"{revision}/{BIOREGISTRY_PATH}"
    )
    body, _ = fetch_resource(url, "application/json")
    try:
        document = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScanError(f"Invalid upstream BioRegistry snapshot at {revision}") from exc
    record = document.get("dio-odi") if isinstance(document, dict) else None
    if not isinstance(record, dict):
        raise ScanError(f"Upstream BioRegistry snapshot at {revision} has no dio-odi record")
    return record


def entry_by_id(registry: dict[str, Any], entry_id: str) -> dict[str, Any]:
    for entry in registry.get("entries", []):
        if isinstance(entry, dict) and entry.get("id") == entry_id:
            return entry
    raise ScanError(f"External-reception registry is missing entry {entry_id!r}")


def existing_evidence_index(feed: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for event in feed.get("events", []):
        if not isinstance(event, dict) or not isinstance(event.get("id"), str):
            continue
        evidence = event.get("evidence", {})
        sources = evidence.get("sources", []) if isinstance(evidence, dict) else []
        if not isinstance(sources, list):
            continue
        for source in sources:
            if isinstance(source, dict):
                url = source.get("url")
                if isinstance(url, str) and url:
                    result.setdefault(url.rstrip("/"), []).append(event["id"])
    return result


def reference_status(
    urls: list[str],
    evidence_index: dict[str, list[str]],
    changed: bool = False,
) -> tuple[str, list[str]]:
    event_ids = sorted({
        event_id
        for url in urls
        for event_id in evidence_index.get(url.rstrip("/"), [])
    })
    if event_ids and changed:
        return "previously-cited-source-updated", event_ids
    if event_ids:
        return "already-cited", event_ids
    return "review-required", []


def make_candidate(
    candidate_id: str,
    kind: str,
    source_url: str,
    evidence_urls: list[str],
    evidence_index: dict[str, list[str]],
    *,
    date_candidate: str | None = None,
    date_basis_candidate: str | None = None,
    date_basis_note: str = "",
    changed: bool = False,
    **details: Any,
) -> dict[str, Any]:
    status, event_ids = reference_status(evidence_urls, evidence_index, changed=changed)
    identity = {"candidate_id": candidate_id, "kind": kind, "source_url": source_url}
    return {
        "candidate_id": candidate_id,
        "candidate_fingerprint": stable_fingerprint(identity),
        "kind": kind,
        "source_url": source_url,
        "evidence_urls": sorted(set(evidence_urls)),
        "date_candidate": date_candidate,
        "date_basis_candidate": date_basis_candidate,
        "date_basis_note": date_basis_note,
        "reference_status": status,
        "existing_event_ids": event_ids,
        "editorial_status": "not-assessed",
        **details,
    }


def scan_bioregistry(
    registry: dict[str, Any],
    evidence_index: dict[str, list[str]],
    github: GitHubClient,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    entry = entry_by_id(registry, "bioregistry-dio-odi-prefix")
    reviewed_on = entry.get("provenance", {}).get("review_date")
    if not reviewed_on:
        raise ScanError("BioRegistry entry has no provenance.review_date baseline")
    current, _ = fetch_json(BIOREGISTRY_API)
    mirror, _ = fetch_json(SEMANTIC_FARM_API)
    if not isinstance(current, dict) or current.get("prefix") != "dio-odi":
        raise ScanError("BioRegistry API did not return the expected dio-odi record")
    if not isinstance(mirror, dict) or mirror.get("prefix") != "dio-odi":
        raise ScanError("Semantic Farm API did not return the expected dio-odi record")

    candidates: list[dict[str, Any]] = []
    divergence = current != mirror
    if divergence:
        keys = sorted(set(current) | set(mirror))
        different = [key for key in keys if current.get(key) != mirror.get(key)]
        candidates.append(make_candidate(
            "registry-surface-divergence:bioregistry-semantic-farm",
            "registry-surface-divergence",
            entry["url"],
            [entry["url"], "https://semantic.farm/registry/dio-odi"],
            evidence_index,
            changed=True,
            field_differences=different,
            bioregistry_fingerprint=stable_fingerprint(current),
            semantic_farm_fingerprint=stable_fingerprint(mirror),
            date_basis_note="The two public API surfaces expose different record payloads. This is a source-consistency observation, not evidence of two independent registry changes.",
        ))

    commits = github.get_json(
        "/repos/biopragmatics/bioregistry/commits",
        {
            "path": BIOREGISTRY_PATH,
            "since": f"{reviewed_on}T00:00:00Z",
            "per_page": 100,
        },
    )
    if not isinstance(commits, list):
        raise ScanError("BioRegistry commit-history response is not an array")
    if len(commits) >= 100:
        raise ScanError("BioRegistry history exceeded the 100-commit safety limit")
    prefix_changes = 0
    for commit in commits:
        sha = commit.get("sha")
        if not sha:
            continue
        detail = github.get_json(f"/repos/biopragmatics/bioregistry/commits/{sha}")
        files = detail.get("files", []) if isinstance(detail, dict) else []
        matching = [
            item for item in files
            if isinstance(item, dict) and item.get("filename") == BIOREGISTRY_PATH
        ]
        if not matching:
            continue
        parents = detail.get("parents", []) if isinstance(detail, dict) else []
        parent_sha = parents[0].get("sha") if parents and isinstance(parents[0], dict) else None
        if not parent_sha:
            raise ScanError(f"BioRegistry commit {sha} has no parent snapshot for comparison")
        before_record = fetch_bioregistry_record(parent_sha)
        after_record = fetch_bioregistry_record(sha)
        if before_record == after_record:
            continue
        prefix_changes += 1
        commit_data = detail.get("commit", {})
        authored = commit_data.get("author", {}) if isinstance(commit_data, dict) else {}
        committed = commit_data.get("committer", {}) if isinstance(commit_data, dict) else {}
        timestamp = (authored or {}).get("date") or (committed or {}).get("date")
        parsed = parse_timestamp(timestamp)
        candidates.append(make_candidate(
            f"bioregistry-record-change:{sha}",
            "external-registry-record-update",
            entry["url"],
            [entry["url"], f"https://github.com/biopragmatics/bioregistry/commit/{sha}"],
            evidence_index,
            date_candidate=parsed.date().isoformat() if parsed else None,
            date_basis_candidate="upstream-registry-commit-time",
            date_basis_note="The upstream commit timestamp identifies a change to the exact dio-odi record. Confirm the public registry refresh time and the semantic materiality of changed fields before using it as an SCF event.",
            changed=True,
            registry="BioRegistry",
            upstream_commit=sha,
            upstream_commit_url=f"https://github.com/biopragmatics/bioregistry/commit/{sha}",
            before_record=before_record,
            after_record=after_record,
        ))

    return candidates, {
        "source": "BioRegistry / Semantic Farm",
        "record_url": entry["url"],
        "api_surfaces": [BIOREGISTRY_API, SEMANTIC_FARM_API],
        "record_valid": True,
        "surfaces_match": not divergence,
        "upstream_commits_after_review": len(commits),
        "relevant_prefix_commits": prefix_changes,
        "reviewed_on": reviewed_on,
    }


def _walk_modified_values(value: Any, modified_keys: set[str]) -> list[Any]:
    found: list[Any] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).casefold() in modified_keys:
                found.append(child)
            found.extend(_walk_modified_values(child, modified_keys))
    elif isinstance(value, list):
        for child in value:
            found.extend(_walk_modified_values(child, modified_keys))
    return found


def extract_modified_timestamp(document: Any, headers: dict[str, str]) -> datetime:
    modified_keys = {
        "modified",
        "datemodified",
        "dct:modified",
        "http://purl.org/dc/terms/modified",
        "modifiedat",
    }
    values = _walk_modified_values(document, modified_keys)
    parsed = [parse_timestamp(value) for value in values]
    parsed = [value for value in parsed if value is not None]
    header_date = parse_timestamp(headers.get("last-modified"))
    if header_date is not None:
        parsed.append(header_date)
    if not parsed:
        raise ScanError("BARTOC JSKOS response has no parseable modified timestamp")
    return max(parsed)


def scan_bartoc(
    registry: dict[str, Any], evidence_index: dict[str, list[str]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    entry = entry_by_id(registry, "bartoc-dio-odi-vocabulary")
    reviewed_on = entry.get("provenance", {}).get("review_date")
    if not reviewed_on:
        raise ScanError("BARTOC entry has no provenance.review_date baseline")
    document, headers = fetch_json(BARTOC_API)
    if isinstance(document, list):
        records = [item for item in document if isinstance(item, dict)]
        if len(records) != 1:
            raise ScanError(
                "BARTOC JSKOS data endpoint did not return exactly one record "
                f"for the requested URI (received {len(records)})"
            )
        document = records[0]
    if not isinstance(document, dict):
        raise ScanError("BARTOC JSKOS endpoint did not return an object or a single-record array")
    modified = extract_modified_timestamp(document, headers)
    baseline = datetime.combine(
        date.fromisoformat(reviewed_on), datetime.min.time(), timezone.utc
    )
    candidates: list[dict[str, Any]] = []
    if modified > baseline:
        candidates.append(make_candidate(
            f"bartoc-record-update:{modified.isoformat()}",
            "external-registry-record-update",
            entry["url"],
            [entry["url"], BARTOC_API],
            evidence_index,
            date_candidate=modified.date().isoformat(),
            date_basis_candidate="registry-record-modified-time",
            date_basis_note="BARTOC exposes a record-modified timestamp. Confirm whether the edit materially changes the catalogue description or its relation to DIO/ODI before recording an SCF event.",
            changed=True,
            registry="BARTOC",
            modified_at=modified.isoformat(),
            source_record_fingerprint=stable_fingerprint(document),
            source_record=document,
        ))
    return candidates, {
        "source": "BARTOC",
        "record_url": entry["url"],
        "api_url": BARTOC_API,
        "modified_at": modified.isoformat(),
        "reviewed_on": reviewed_on,
        "record_retrieved": True,
        "newer_than_review_baseline": modified > baseline,
    }


def scan_arxiv(
    works: dict[str, Any],
    evidence_index: dict[str, list[str]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    work = next(
        (
            item for item in works.get("works", [])
            if isinstance(item, dict) and item.get("id") == "commit-boundary-paper"
        ),
        None,
    )
    arxiv = work.get("arxiv") if isinstance(work, dict) else None
    if not isinstance(arxiv, dict):
        raise ScanError("works.json has no arXiv metadata for commit-boundary-paper")
    expected_version = str(arxiv.get("current_version") or "")
    expected_date = parse_timestamp(
        arxiv.get("version_history_timestamp_utc") or arxiv.get("version_date")
    )
    if not expected_version or expected_date is None:
        raise ScanError("Canonical arXiv version metadata is incomplete in works.json")

    xml_text = fetch_text(ARXIV_API, "application/atom+xml")
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ScanError(f"arXiv returned invalid Atom XML: {exc}") from exc
    entry = root.find("atom:entry", ATOM_NS)
    if entry is None:
        raise ScanError("arXiv API returned no entry for 2610.37407")
    identifier = entry.findtext("atom:id", default="", namespaces=ATOM_NS)
    updated = parse_timestamp(
        entry.findtext("atom:updated", default="", namespaces=ATOM_NS)
    )
    if not updated or not identifier:
        raise ScanError("arXiv entry is missing its identifier or updated timestamp")
    version_match = re.search(r"v(\d+)$", identifier)
    if not version_match:
        raise ScanError(f"Cannot determine arXiv version from {identifier}")
    live_number = int(version_match.group(1))
    expected_match = re.search(r"v(\d+)$", expected_version)
    if not expected_match:
        raise ScanError(f"Canonical arXiv version is not in vN format: {expected_version}")
    expected_number = int(expected_match.group(1))
    candidates: list[dict[str, Any]] = []
    if live_number > expected_number or updated > expected_date:
        live_url = f"https://arxiv.org/abs/2610.37407v{live_number}"
        candidates.append(make_candidate(
            f"arxiv-version-observation:2610.37407:v{live_number}:{updated.date().isoformat()}",
            "publication-version-update",
            live_url,
            [live_url, "https://arxiv.org/abs/2610.37407"],
            evidence_index,
            date_candidate=updated.date().isoformat(),
            date_basis_candidate="publication_date",
            date_basis_note="arXiv's updated timestamp is a publication-version signal. Confirm the version history and update scope before adding or changing an SCF record.",
            changed=True,
            repository="arXiv",
            expected_version=expected_version,
            live_version=f"v{live_number}",
            arxiv_updated_at=updated.isoformat(),
        ))
    return candidates, {
        "source": "arXiv",
        "record_url": "https://arxiv.org/abs/2610.37407",
        "expected_version": expected_version,
        "live_version": f"v{live_number}",
        "expected_version_date": expected_date.isoformat(),
        "live_updated_at": updated.isoformat(),
        "version_matches": live_number == expected_number,
        "updated_timestamp_matches": updated <= expected_date,
    }


def _text_of(element: ET.Element | None) -> str:
    return "".join(element.itertext()).strip() if element is not None else ""


def parse_hashnode_rss(xml_text: str) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ScanError(f"Hashnode RSS returned invalid XML: {exc}") from exc
    items: list[dict[str, Any]] = []
    rss_items = root.findall(".//item")
    for item in rss_items:
        title = _text_of(item.find("title"))
        url = _text_of(item.find("link"))
        published = _text_of(item.find("pubDate")) or _text_of(item.find("published"))
        timestamp = parse_timestamp(published)
        if title and url and timestamp:
            items.append({
                "title": title,
                "canonical_url": url,
                "published_at": timestamp.isoformat(),
                "observed_on": "Hashnode RSS",
                "representation_urls": [url],
            })
    if not rss_items:
        for item in root.findall(".//atom:entry", ATOM_NS):
            title = _text_of(item.find("atom:title", ATOM_NS))
            link_element = item.find("atom:link[@rel='alternate']", ATOM_NS)
            if link_element is None:
                link_element = item.find("atom:link", ATOM_NS)
            url = link_element.attrib.get("href", "") if link_element is not None else ""
            published = _text_of(item.find("atom:published", ATOM_NS)) or _text_of(
                item.find("atom:updated", ATOM_NS)
            )
            timestamp = parse_timestamp(published)
            if title and url and timestamp:
                items.append({
                    "title": title,
                    "canonical_url": url,
                    "published_at": timestamp.isoformat(),
                    "observed_on": "Hashnode RSS",
                    "representation_urls": [url],
                })
    return items


def parse_devto_articles(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise ScanError("DEV.to API did not return an article array")
    articles: list[dict[str, Any]] = []
    for article in payload:
        if not isinstance(article, dict):
            continue
        canonical = article.get("canonical_url") or article.get("url")
        url = article.get("url")
        title = article.get("title")
        timestamp = parse_timestamp(article.get("published_at"))
        if not all(isinstance(value, str) and value for value in (canonical, url, title)):
            continue
        if timestamp is None:
            continue
        canonical_host = (urlparse(canonical).hostname or "").casefold()
        tags = article.get("tag_list", [])
        tag_text = " ".join(tags) if isinstance(tags, list) else ""
        combined_text = f"{title} {article.get('description', '')} {tag_text}".casefold()
        relevant = (
            canonical_host == "dio-odi.hashnode.dev"
            or "dio/odi" in combined_text
            or "agentic entity resolution" in combined_text
        )
        if not relevant:
            continue
        articles.append({
            "title": title,
            "canonical_url": canonical,
            "published_at": timestamp.isoformat(),
            "observed_on": "DEV.to API",
            "representation_urls": [url, canonical],
        })
    return articles


def scan_publications(
    evidence_index: dict[str, list[str]],
    cutoff: datetime,
) -> tuple[list[dict[str, Any]], dict[str, int], list[dict[str, str]]]:
    observations: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, str]] = []
    stats = {"hashnode_items_inspected": 0, "devto_articles_inspected": 0}
    try:
        xml_text = fetch_text(
            HASHNODE_RSS,
            "application/rss+xml, application/atom+xml, application/xml",
        )
        hashnode_items = parse_hashnode_rss(xml_text)
        stats["hashnode_items_inspected"] = len(hashnode_items)
        for item in hashnode_items:
            published_at = parse_timestamp(item["published_at"])
            if published_at is not None and published_at >= cutoff:
                observations[item["canonical_url"].rstrip("/")] = item
    except ScanError as exc:
        errors.append({"source": "Hashnode RSS", "error": str(exc)})

    try:
        devto_items: list[dict[str, Any]] = []
        for page in range(1, 6):
            query = urlencode({"username": "danielberanek", "per_page": 30, "page": page})
            payload, _ = fetch_json(f"{DEVTO_API}?{query}")
            page_items = parse_devto_articles(payload)
            stats["devto_articles_inspected"] += len(payload) if isinstance(payload, list) else 0
            devto_items.extend(page_items)
            if not isinstance(payload, list) or len(payload) < 30:
                break
            all_dates = [
                parse_timestamp(item.get("published_at"))
                for item in payload if isinstance(item, dict)
            ]
            dates = [item for item in all_dates if item is not None]
            if dates and min(dates) < cutoff:
                break
        for item in devto_items:
            published_at = parse_timestamp(item["published_at"])
            if published_at is None or published_at < cutoff:
                continue
            key = item["canonical_url"].rstrip("/")
            if key in observations:
                current = observations[key]
                existing_platforms = current.get("observed_on")
                if isinstance(existing_platforms, str):
                    existing_platforms = [existing_platforms]
                current["observed_on"] = sorted(set(existing_platforms or []) | {item["observed_on"]})
                current["representation_urls"] = sorted(
                    set(current.get("representation_urls", [])) | set(item["representation_urls"])
                )
            else:
                observations[key] = item
    except ScanError as exc:
        errors.append({"source": "DEV.to API", "error": str(exc)})

    candidates: list[dict[str, Any]] = []
    for item in observations.values():
        canonical = item["canonical_url"]
        urls = item.get("representation_urls", [canonical])
        published_at = parse_timestamp(item["published_at"])
        if published_at is None:
            continue
        observed_on = item.get("observed_on", [])
        if isinstance(observed_on, str):
            observed_on = [observed_on]
        candidates.append(make_candidate(
            f"web-publication:{stable_fingerprint({'canonical_url': canonical})[:16]}",
            "web-publication",
            canonical,
            urls,
            evidence_index,
            date_candidate=published_at.date().isoformat(),
            date_basis_candidate="publication_date",
            date_basis_note="Use the canonical publication date only after confirming the item is a distinct DIO/ODI or related research output. Canonical and syndicated copies are grouped as one work.",
            title=item["title"],
            observed_on=observed_on,
            representation_urls=urls,
            published_at=item["published_at"],
        ))
    candidates.sort(
        key=lambda item: (item.get("date_candidate") or "", item["source_url"]),
        reverse=True,
    )
    return candidates, stats, errors


def build_report(
    registry: dict[str, Any],
    works: dict[str, Any],
    feed: dict[str, Any],
    lookback_hours: int,
    now: datetime | None = None,
    github: GitHubClient | None = None,
) -> dict[str, Any]:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    cutoff = now - timedelta(hours=lookback_hours)
    evidence_index = existing_evidence_index(feed)
    candidates: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    source_checks: list[dict[str, Any]] = []
    gh = github or GitHubClient()

    scanners = (
        ("BioRegistry / Semantic Farm", lambda: scan_bioregistry(registry, evidence_index, gh)),
        ("BARTOC", lambda: scan_bartoc(registry, evidence_index)),
        ("arXiv", lambda: scan_arxiv(works, evidence_index)),
    )
    for source_name, scanner in scanners:
        try:
            found, status = scanner()
            candidates.extend(found)
            source_checks.append(status)
        except (ScanError, ValueError) as exc:
            errors.append({"source": source_name, "error": str(exc)})

    publication_candidates, publication_stats, publication_errors = scan_publications(
        evidence_index, cutoff
    )
    candidates.extend(publication_candidates)
    errors.extend(publication_errors)
    candidates.sort(
        key=lambda item: (item.get("date_candidate") or "", item["candidate_id"]),
        reverse=True,
    )
    return {
        "report_version": "0.1.0",
        "generated_at": now.isoformat(),
        "lookback_hours": lookback_hours,
        "publication_coverage_starts_at": cutoff.isoformat(),
        "policy": {
            "review_required": True,
            "automatic_scf_writes": False,
            "registry_api_payloads_are_independent_endorsements": False,
            "syndicated_publications_are_deduplicated_by_canonical_url": True,
            "exact_evidence_url_matching": True,
        },
        "stats": {
            "registry_sources_checked": len(source_checks),
            "candidates": len(candidates),
            **publication_stats,
        },
        "source_checks": source_checks,
        "candidates": candidates,
        "errors": errors,
        "scan_complete": not errors and len(source_checks) == len(scanners),
    }


def render_markdown(report: dict[str, Any]) -> str:
    candidates = report["candidates"]
    lines = [
        "# SCF external evidence intake",
        "",
        f"Generated: {report['generated_at']}",
        f"Publication lookback: {report['lookback_hours']} hours",
        f"Coverage starts: {report['publication_coverage_starts_at']}",
        "",
        "> Review-only collection. A source update, new publication, registry refresh, or version change is not automatically an SCF event.",
        "",
        f"Registry source groups checked: **{report['stats']['registry_sources_checked']}**  ",
        f"Hashnode items inspected: **{report['stats']['hashnode_items_inspected']}**  ",
        f"DEV.to articles inspected: **{report['stats']['devto_articles_inspected']}**  ",
        f"Candidate observations: **{len(candidates)}**",
        "",
        "## Source checks",
        "",
    ]
    for check in report["source_checks"]:
        lines.append(f"- **{check['source']}**: {json.dumps(check, ensure_ascii=False, sort_keys=True)}")
    lines.append("")
    if not candidates:
        lines.extend(["No new external-source observations require review in this run.", ""])
    else:
        lines.extend(["## Review candidates", ""])
        for item in candidates:
            lines.extend([
                f"### {item.get('title') or item['candidate_id']}",
                "",
                f"- Type: **{item['kind']}**",
                f"- Candidate date: **{item.get('date_candidate') or 'not established'}**",
                f"- Candidate date basis: {item.get('date_basis_candidate') or 'not established'}",
                f"- Source status: **{item['reference_status']}**",
                f"- Existing SCF events: {', '.join(item['existing_event_ids']) or 'none found by exact URL'}",
                f"- Canonical source: {item['source_url']}",
                f"- Evidence URLs: {', '.join(item['evidence_urls'])}",
                f"- Editorial decision: **not assessed**",
                f"- Date note: {item.get('date_basis_note', '')}",
                "",
            ])
    if report["errors"]:
        lines.extend(["## Incomplete sources", ""])
        for error in report["errors"]:
            lines.append(f"- **{error['source']}**: {error['error']}")
        lines.append("")
    lines.extend([
        "## Curation boundary",
        "",
        "- BioRegistry and Semantic Farm are checked as one upstream registry record with two API surfaces; a mirror is not a second independent integration.",
        "- BARTOC is monitored as a separate JSKOS catalogue record; its modified timestamp triggers review, not automatic inclusion.",
        "- arXiv version metadata is checked against the canonical Corpus Metadata Registry.",
        "- Hashnode and DEV.to publication copies are grouped by canonical URL; LinkedIn is not scraped.",
        "- No SCF event IDs are allocated and semantic-change-feed/events.json is not modified.",
        "- The scan does not update the External Reception Registry, version metadata, archives, or public site.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lookback-hours", type=int, default=168)
    parser.add_argument("--output-dir", default="scf-external-output")
    args = parser.parse_args()
    if not 1 <= args.lookback_hours <= 720:
        parser.error("--lookback-hours must be between 1 and 720")

    try:
        registry = json.loads(
            (ROOT / "metadata/external-reception.json").read_text(encoding="utf-8")
        )
        works = json.loads((ROOT / "metadata/works.json").read_text(encoding="utf-8"))
        feed = json.loads(
            (ROOT / "semantic-change-feed/events.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read a canonical source registry: {exc}", file=sys.stderr)
        return 2

    report = build_report(registry, works, feed, args.lookback_hours)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "scf-external-candidates.json"
    markdown_path = output_dir / "scf-external-candidates.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")

    print(f"Registry source groups checked: {report['stats']['registry_sources_checked']}")
    print(f"Candidate observations: {len(report['candidates'])}")
    print(f"External source errors: {len(report['errors'])}")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    return 0 if report["scan_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

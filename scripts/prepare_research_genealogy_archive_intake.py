#!/usr/bin/env python3
"""Prepare a review-only Internet Archive CDX inventory for SlideShare research items.

This script does not edit the canonical Research Genealogy registry. It reads the
public profile HTML and the registry, discovers links in those representations,
queries the public Wayback CDX index for the profile and each discovered
presentation URL, and writes a JSON/Markdown review report.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "metadata" / "research-genealogy.json"
DEFAULT_OUTPUT_DIR = ROOT / "research-genealogy-archive-output"
CDX_ENDPOINT = "https://web.archive.org/cdx/search/cdx"
TAVILY_ENDPOINT = "https://api.tavily.com/search"
TAVILY_QUERIES = [
    {"id": "profile-name", "query": 'site:slideshare.net/slideshow "Daniel Beránek"'},
    {"id": "profile-role", "query": 'site:slideshare.net/slideshow "SEO specialista a copywriter Daniel Beránek"'},
    {"id": "profile-eeat", "query": 'site:slideshare.net/slideshow "Daniel Beránek" E-E-A-T'},
    {"id": "profile-research", "query": 'site:slideshare.net/slideshow "Daniel Beránek" analysis OR research OR analýza'},
]
USER_AGENT = "DIO-ODI-Research-Genealogy-Archive-Intake/0.1 (+https://vocab.danielberanek.cz/)"
MAX_RESPONSE_BYTES = 25_000_000
SLIDESHOW_PATH_PREFIXES = ("/slideshow/", "/document/", "/infographics/", "/presentation/")
CDX_FIELDS = "timestamp,original,mimetype,statuscode,digest,length"


class IntakeError(RuntimeError):
    """Raised when a public resource cannot be inspected reliably."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalized_url(value: str) -> str:
    """Normalize harmless host/scheme/trailing-slash differences for matching."""
    parsed = urlsplit(value.strip())
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        return ""
    host = parsed.netloc.lower().split("@")[-1]
    if host.endswith(":80") and parsed.scheme.lower() == "http":
        host = host[:-3]
    elif host.endswith(":443") and parsed.scheme.lower() == "https":
        host = host[:-4]
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    query = parsed.query
    return urlunsplit(("https", host, path, query, ""))


def is_slideshare_url(value: str) -> bool:
    parsed = urlsplit(value)
    host = (parsed.hostname or "").lower()
    return (
        (host == "slideshare.net" or host.endswith(".slideshare.net"))
        and any(parsed.path.startswith(prefix) for prefix in SLIDESHOW_PATH_PREFIXES)
    )


class LinkExtractor(HTMLParser):
    """Extract visible anchors and labels from public profile HTML."""

    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.links: list[dict[str, str]] = []
        self._anchor: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): (value or "") for key, value in attrs}
        if tag.lower() == "a":
            href = values.get("href", "").strip()
            if href:
                self._anchor = {
                    "url": urljoin(self.base_url, html.unescape(href)),
                    "label": values.get("aria-label") or values.get("title") or values.get("alt") or "",
                }

    def handle_data(self, data: str) -> None:
        if self._anchor is not None and data.strip():
            current = self._anchor.get("label", "")
            self._anchor["label"] = (current + " " + data.strip()).strip()

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._anchor is not None:
            self.links.append(self._anchor)
            self._anchor = None


def extract_slideshow_links(document: str, base_url: str) -> list[dict[str, str]]:
    parser = LinkExtractor(base_url)
    parser.feed(document)
    parser.close()
    found: dict[str, dict[str, str]] = {}
    for item in parser.links:
        url = item["url"].split("#", 1)[0]
        if not is_slideshare_url(url):
            continue
        key = normalized_url(url)
        if key and key not in found:
            found[key] = {"url": url, "label": item.get("label", "")[:300]}
    # Some profile templates retain absolute links in inline JSON/script payloads.
    # These are treated as locators only; the visible uploader context still comes
    # from the public profile page or an author-maintained registry entry.
    for match in re.findall(
        r"https?://(?:www\.)?(?:[a-z0-9-]+\.)?slideshare\.net/(?:slideshow|document|infographics|presentation)/[^\s\"'<>\\]+",
        document,
        flags=re.IGNORECASE,
    ):
        url = html.unescape(match).rstrip("),;]")
        key = normalized_url(url)
        if key and key not in found and is_slideshare_url(url):
            found[key] = {"url": url, "label": ""}
    return list(found.values())


def fetch_bytes(url: str, accept: str = "text/html,application/json;q=0.9,*/*;q=0.8",
                retries: int = 3, timeout: int = 35) -> tuple[bytes, dict[str, str], int]:
    last_error: Exception | None = None
    for attempt in range(retries):
        request = Request(url, headers={"Accept": accept, "User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=timeout) as response:
                body = response.read(MAX_RESPONSE_BYTES + 1)
                if len(body) > MAX_RESPONSE_BYTES:
                    raise IntakeError(f"Response exceeds {MAX_RESPONSE_BYTES} bytes: {url}")
                headers = {key.lower(): value for key, value in response.headers.items()}
                return body, headers, response.status
        except HTTPError as exc:
            detail = exc.read(500).decode("utf-8", errors="replace")
            last_error = IntakeError(f"HTTP {exc.code} for {url}: {detail}")
            if exc.code not in (408, 425, 429, 500, 502, 503, 504):
                raise last_error from exc
        except (URLError, TimeoutError, OSError) as exc:
            last_error = IntakeError(f"Request failed for {url}: {exc}")
        if attempt < retries - 1:
            time.sleep(1.5 * (attempt + 1))
    assert last_error is not None
    raise last_error


def fetch_text(url: str, accept: str = "text/html") -> tuple[str, dict[str, str], int]:
    body, headers, status = fetch_bytes(url, accept)
    try:
        return body.decode("utf-8", errors="replace"), headers, status
    except UnicodeDecodeError as exc:
        raise IntakeError(f"Could not decode UTF-8 response: {url}") from exc


def parse_tavily_results(payload: Any, query: dict[str, str]) -> list[dict[str, Any]]:
    """Filter Tavily results to direct SlideShare presentation URLs only."""
    if not isinstance(payload, dict) or not isinstance(payload.get("results", []), list):
        raise IntakeError("Tavily response has no valid results array")
    candidates: dict[str, dict[str, Any]] = {}
    for result in payload.get("results", []):
        if not isinstance(result, dict):
            continue
        url = result.get("url")
        if not isinstance(url, str) or not is_slideshare_url(url):
            continue
        key = normalized_url(url)
        if not key:
            continue
        candidates[key] = {
            "url": url,
            "title": str(result.get("title") or "")[:300],
            "snippet": str(result.get("content") or "")[:1200],
            "published_date": result.get("published_date"),
            "query_id": query["id"],
            "query": query["query"],
        }
    return list(candidates.values())


def search_tavily(api_key: str | None, max_results: int = 20) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Search indexed web results for additional SlideShare presentation locators.

    Tavily results are discovery leads only. A search result does not establish
    author/uploader attribution, exact content, or the relationship to an
    existing underlying research output.
    """
    if not api_key:
        return [], {
            "provider": "Tavily Search",
            "enabled": False,
            "reason": "TAVILY_API_KEY is not configured",
            "queries_attempted": 0,
            "requests_succeeded": 0,
            "raw_results": 0,
            "slideshare_candidates": 0,
            "errors": [],
        }

    candidates: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    requests_succeeded = 0
    raw_results = 0
    for query in TAVILY_QUERIES:
        request = Request(
            TAVILY_ENDPOINT,
            data=json.dumps({
                "query": query["query"],
                "search_depth": "basic",
                "topic": "general",
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False,
                "include_published_date": True,
                "include_usage": True,
            }).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=45) as response:
                body = response.read(MAX_RESPONSE_BYTES + 1)
                if len(body) > MAX_RESPONSE_BYTES:
                    raise IntakeError("Tavily response exceeds the configured response-size limit")
            try:
                payload = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise IntakeError("Tavily returned invalid JSON") from exc
            requests_succeeded += 1
            results = payload.get("results", []) if isinstance(payload, dict) else []
            raw_results += len(results) if isinstance(results, list) else 0
            for candidate in parse_tavily_results(payload, query):
                key = normalized_url(candidate["url"])
                existing = candidates.get(key)
                if existing:
                    existing.setdefault("queries", []).append({
                        "id": query["id"],
                        "query": query["query"],
                    })
                else:
                    candidate["queries"] = [{"id": query["id"], "query": query["query"]}]
                    candidates[key] = candidate
        except HTTPError as exc:
            detail = exc.read(500).decode("utf-8", errors="replace")
            errors.append(f"{query['id']}: Tavily HTTP {exc.code}: {detail}")
        except (URLError, TimeoutError, OSError, IntakeError) as exc:
            errors.append(f"{query['id']}: {exc}")
        time.sleep(0.25)

    return list(candidates.values()), {
        "provider": "Tavily Search",
        "enabled": True,
        "queries_attempted": len(TAVILY_QUERIES),
        "requests_succeeded": requests_succeeded,
        "raw_results": raw_results,
        "slideshare_candidates": len(candidates),
        "errors": errors,
    }


def fetch_profile_with_browser(
    url: str, max_scrolls: int = 18, scroll_pause_ms: int = 900
) -> tuple[str, str, int | None]:
    """Render the public profile in Chromium and collect the loaded DOM.

    This uses ordinary browser navigation and scrolling only. It does not call
    private or undocumented SlideShare endpoints.
    """
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise IntakeError("Playwright is not installed; rendered profile discovery is unavailable") from exc

    response_status: int | None = None
    selector = (
        "a[href*='/slideshow/'], a[href*='/document/'], "
        "a[href*='/infographics/'], a[href*='/presentation/']"
    )
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            try:
                context = browser.new_context(
                    locale="en-US",
                    viewport={"width": 1440, "height": 1200},
                )
                page = context.new_page()
                response = page.goto(url, wait_until="domcontentloaded", timeout=90_000)
                response_status = response.status if response else None
                page.wait_for_timeout(3500)

                previous_count = -1
                stagnant_rounds = 0
                for _ in range(max_scrolls):
                    try:
                        visible_count = page.locator(selector).count()
                    except PlaywrightTimeoutError:
                        visible_count = 0
                    if visible_count == previous_count:
                        stagnant_rounds += 1
                    else:
                        stagnant_rounds = 0
                    if stagnant_rounds >= 3:
                        break
                    previous_count = visible_count
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(scroll_pause_ms)

                rendered_html = page.content()
                try:
                    body_text = page.locator("body").inner_text(timeout=10_000)
                except PlaywrightTimeoutError:
                    body_text = ""
                if not rendered_html.strip():
                    raise IntakeError(f"Chromium returned an empty rendered document for {url}")
                return rendered_html, body_text, response_status
            finally:
                browser.close()
    except IntakeError:
        raise
    except Exception as exc:
        raise IntakeError(f"Chromium profile rendering failed for {url}: {exc}") from exc


def derive_profile_discovery_status(
    profile_reported_count: int | None, discovered_url_count: int
) -> str:
    if discovered_url_count > 0:
        return (
            "profile-links-extracted"
            if profile_reported_count is not None
            else "profile-links-extracted-count-not-observed"
        )
    if profile_reported_count is not None and profile_reported_count > 0:
        return "profile-count-visible-but-links-not-extracted"
    return "no-profile-links-or-count-extracted"



def cdx_query(url: str, match_type: str = "exact", limit: int = 500) -> list[dict[str, str]]:
    """Return all available CDX columns requested, preserving each capture row."""
    params = [
        ("url", url),
        ("matchType", match_type),
        ("output", "json"),
        ("fl", CDX_FIELDS),
        ("gzip", "false"),
        ("limit", str(limit)),
    ]
    query_url = CDX_ENDPOINT + "?" + urlencode(params)
    body, _, _ = fetch_bytes(query_url, accept="application/json,text/plain;q=0.9")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IntakeError(f"CDX returned invalid JSON for {url}") from exc
    if not isinstance(payload, list) or not payload:
        return []
    header = payload[0]
    if not isinstance(header, list) or not all(isinstance(x, str) for x in header):
        raise IntakeError(f"CDX response has no valid header row for {url}")
    rows: list[dict[str, str]] = []
    for raw in payload[1:]:
        if isinstance(raw, list) and len(raw) == len(header):
            rows.append({header[i]: str(raw[i]) for i in range(len(header))})
    return rows


def timestamp_to_iso(value: str) -> str | None:
    if not re.fullmatch(r"\d{14}", value or ""):
        return None
    try:
        parsed = datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return parsed.isoformat().replace("+00:00", "Z")


def archive_replay_url(timestamp: str, original: str) -> str:
    return f"https://web.archive.org/web/{timestamp}/{original}"


def archive_raw_url(timestamp: str, original: str) -> str:
    return f"https://web.archive.org/web/{timestamp}id_/{original}"


def profile_count(document: str) -> int | None:
    match = re.search(r"\b(\d+)\s+Slideshows?\b", document, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IntakeError(f"Could not read Research Genealogy registry: {exc}") from exc
    if not isinstance(data, dict):
        raise IntakeError("Research Genealogy registry must be a JSON object")
    return data


def slideshare_registry_items(registry: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for item in registry.get("artefacts", []):
        if not isinstance(item, dict) or str(item.get("platform", "")).casefold() != "slideshare":
            continue
        if not is_slideshare_url(str(item.get("url", ""))):
            continue
        result.append(item)
    return result


def cdx_capture_record(row: dict[str, str]) -> dict[str, Any]:
    timestamp = row.get("timestamp", "")
    original = row.get("original", "")
    return {
        "timestamp": timestamp,
        "captured_at": timestamp_to_iso(timestamp),
        "original": original,
        "mimetype": row.get("mimetype", ""),
        "status_code": row.get("statuscode", ""),
        "digest": row.get("digest", ""),
        "length": row.get("length", ""),
        "replay_url": archive_replay_url(timestamp, original) if timestamp and original else None,
    }


def markdown_report(report: dict[str, Any]) -> str:
    stats = report["summary"]
    lines = [
        "# Research Genealogy — SlideShare discovery and Wayback CDX intake",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Profile: {report['profile_url']}",
        f"- Inventory coverage: **{report['inventory_completeness']}**",
        "",
        "## Summary",
        "",
        f"- SlideShare count reported by rendered public profile: {stats.get('profile_reported_count')}",
        f"- URLs discovered from current public profile sources: {stats['current_profile_urls']}",
        f"- URLs discovered in archived profile snapshots: {stats['archived_profile_urls']}",
        f"- Known SlideShare artefacts in the canonical registry: {stats['registered_artefacts']}",
        f"- Unique presentation URLs examined: {stats['unique_presentation_urls']}",
        f"- CDX queries completed: {stats['cdx_queries_succeeded']} / {stats['cdx_queries_attempted']}",
        f"- Capture records returned: {stats['capture_records']}",
        f"- URLs without a corresponding registry artefact: {stats['unregistered_urls']}",
        f"- Difference between the profile-reported total and extracted current-profile links (unreconciled): {stats['profile_count_to_html_link_gap'] if stats['profile_count_to_html_link_gap'] is not None else 'not measurable'}",
        f"- Profile discovery status: {stats['profile_discovery_status']}",
        f"- SlideShare URLs discovered by indexed-web search: {stats['indexed_search_slide_urls']}",
        f"- Indexed-search URLs not yet present in the registry: {stats['unregistered_indexed_search_urls']}",
        f"- Profile snapshot cap reached: {stats['profile_snapshot_limit_reached']}",
        f"- Presentation URL cap reached: {stats['presentation_url_limit_reached']}",
        "",
        "## Interpretation boundary",
        "",
        "This is a review-only discovery report. It does not modify the canonical Research Genealogy registry. Public SlideShare API access has been retired; this intake combines public profile HTML, rendered public profile pages, optional Tavily indexed-web search, and the Internet Archive CDX index. None of these sources alone provides an exhaustive profile inventory.",
        "",
        "Tavily results are candidate locators. They do not establish uploader attribution, authorship, exact output identity, or publication date; any `published_date` returned by the search index remains a candidate field until the original page is reviewed.",
        "CDX records are archive-index observations, not upload or creation dates. A timestamp identifies an archived capture. Multiple host aliases, redirects, or duplicate capture records must be reconciled before being attached to one research artefact.",
        "",
        "## Presentation URL inventory",
        "",
        "| URL | Discovery source | Registry item | Captures | First capture (UTC) | Last capture (UTC) |",
        "|---|---|---|---:|---|---|",
    ]
    for item in report["presentations"]:
        captures = item["captures"]
        dates = [c["captured_at"] for c in captures if c.get("captured_at")]
        ids = ", ".join(item["registry_artefact_ids"]) or "Unmatched candidate"
        sources = ", ".join(sorted({
            source.get("kind", "unknown") for source in item.get("discovery_sources", [])
        })) or "unknown"
        lines.append(
            f"| {item['url']} | {sources} | {ids} | {len(captures)} | "
            f"{min(dates) if dates else '—'} | {max(dates) if dates else '—'} |"
        )
    lines.extend(["", "## Indexed-web discovery provider", ""])
    for provider in report.get("discovery_providers", []):
        if provider.get("enabled"):
            lines.append(
                f"- {provider.get('provider')}: {provider.get('requests_succeeded', 0)} / "
                f"{provider.get('queries_attempted', 0)} searches succeeded; "
                f"{provider.get('slideshare_candidates', 0)} unique SlideShare candidates "
                f"from {provider.get('raw_results', 0)} raw results."
            )
            lines.extend(f"  - {error}" for error in provider.get("errors", []))
        else:
            lines.append(
                f"- {provider.get('provider')}: disabled "
                f"({provider.get('reason', 'not configured')})."
            )

    lines.extend(["", "## Source observations", ""])
    for obs in report["profile_observations"]:
        lines.append(
            f"- {obs['kind']}: {obs['url']} — HTTP {obs.get('http_status', 'n/a')}; "
            f"links extracted: {obs.get('links_extracted', 0)}; "
            f"profile count: {obs.get('profile_reported_count')}"
        )
    if report["errors"]:
        lines.extend(["", "## Errors and incomplete observations", ""])
        lines.extend(f"- {error}" for error in report["errors"])
    lines.extend([
        "",
        "## Next curation action",
        "",
        "Compare each unmatched presentation against the author's SlideShare profile and presentation page, verify uploader attribution, then attach only source-matched capture URLs and timestamps to the corresponding artefact. Keep unresolved matches in inventory leads rather than merging them by topic or URL similarity.",
        "",
    ])
    return "\n".join(lines)


def run_intake(profile_snapshot_limit: int = 40, url_limit: int = 150,
               delay_seconds: float = 0.15, tavily_api_key: str | None = None) -> dict[str, Any]:
    registry = load_registry()
    known = slideshare_registry_items(registry)
    profile_collection = next(
        (item for item in registry.get("source_collections", [])
         if item.get("id") == "slideshare-danielberanek"),
        None,
    )
    if not profile_collection:
        raise IntakeError("The canonical SlideShare source collection is missing")
    profile_url = profile_collection["url"].rstrip("/")
    profile_variants = [
        profile_url,
        profile_url + "?tab=presentations",
    ]

    errors: list[str] = []
    profile_observations: list[dict[str, Any]] = []
    urls: dict[str, dict[str, Any]] = {}

    def add_url(url: str, *, source_kind: str, source_url: str,
                label: str = "", registry_item: dict[str, Any] | None = None) -> None:
        key = normalized_url(url)
        if not key:
            return
        entry = urls.setdefault(key, {
            "url": url.split("#", 1)[0],
            "labels": [],
            "discovery_sources": [],
            "registry_artefact_ids": [],
        })
        if label and label not in entry["labels"]:
            entry["labels"].append(label[:300])
        evidence = {"kind": source_kind, "source_url": source_url}
        if evidence not in entry["discovery_sources"]:
            entry["discovery_sources"].append(evidence)
        if registry_item and registry_item.get("id") not in entry["registry_artefact_ids"]:
            entry["registry_artefact_ids"].append(registry_item.get("id"))

    # Indexed-web discovery is a fallback for presentation cards that are
    # omitted from both the server HTML and rendered profile DOM. Search hits
    # remain candidates and do not establish uploader attribution.
    tavily_candidates, tavily_status = search_tavily(tavily_api_key)
    for candidate in tavily_candidates:
        add_url(
            candidate["url"],
            source_kind="tavily-indexed-search",
            source_url="Tavily Search",
            label=candidate.get("title") or candidate.get("snippet", ""),
        )
        entry = urls[normalized_url(candidate["url"])]
        evidence = entry["discovery_sources"][-1]
        evidence["provider"] = "Tavily Search"
        evidence["queries"] = candidate.get("queries", [])
        evidence["published_date_candidate"] = candidate.get("published_date")
        evidence["snippet"] = candidate.get("snippet", "")

    # Start with the canonical registry: exact-URL CDX queries can still find
    # earlier captures even when a presentation has disappeared from the profile.
    for item in known:
        add_url(item["url"], source_kind="canonical-registry",
                source_url=REGISTRY_PATH.as_posix() if hasattr(REGISTRY_PATH, "as_posix") else str(REGISTRY_PATH),
                label=item.get("title", ""), registry_item=item)

    # Fetch both publicly visible profile variants and extract only presentation URLs.
    profile_reported_count: int | None = None
    for profile in profile_variants:
        try:
            document, _, status = fetch_text(profile)
            count = profile_count(document)
            if count is not None:
                profile_reported_count = max(profile_reported_count or 0, count)
            links = extract_slideshow_links(document, profile)
            profile_observations.append({
                "kind": "current-public-profile-html",
                "url": profile,
                "http_status": status,
                "profile_reported_count": count,
                "links_extracted": len(links),
            })
            for link in links:
                add_url(link["url"], source_kind="current-public-profile-html",
                        source_url=profile, label=link.get("label", ""))
        except IntakeError as exc:
            errors.append(f"Current profile fetch failed for {profile}: {exc}")

    # The server-side HTML returned HTTP 200 but exposed no presentation links.
    # Render only the presentation-tab profile through a normal browser session,
    # then scroll to trigger public lazy-loaded profile cards.
    rendered_profile_url = profile_url + "?tab=presentations"
    try:
        rendered_html, rendered_text, rendered_status = fetch_profile_with_browser(rendered_profile_url)
        rendered_links = extract_slideshow_links(rendered_html, rendered_profile_url)
        rendered_count = profile_count(rendered_text)
        if rendered_count is not None:
            profile_reported_count = max(profile_reported_count or 0, rendered_count)
        profile_observations.append({
            "kind": "current-public-profile-rendered-browser",
            "url": rendered_profile_url,
            "http_status": rendered_status,
            "profile_reported_count": rendered_count,
            "links_extracted": len(rendered_links),
        })
        for link in rendered_links:
            add_url(link["url"], source_kind="current-public-profile-rendered-browser",
                    source_url=rendered_profile_url, label=link.get("label", ""))
    except IntakeError as exc:
        errors.append(f"Rendered current profile fetch failed for {rendered_profile_url}: {exc}")

    indexed_search_keys = {
        normalized_url(candidate["url"]) for candidate in tavily_candidates
    }

    # Use only documented CDX query parameters. No undocumented SlideShare API is
    # called. Archive profile captures can reveal historical profile link sets.
    profile_captures: dict[str, dict[str, str]] = {}
    profile_cdx_queries_attempted = 0
    profile_cdx_queries_succeeded = 0
    for profile in profile_variants:
        parsed = urlsplit(profile)
        host_path = (parsed.netloc + parsed.path).rstrip("/")
        query_variants = [(host_path + (("?" + parsed.query) if parsed.query else ""), "exact"), (host_path + "/*", "prefix")]
        for query_url, match_type in query_variants:
            profile_cdx_queries_attempted += 1
            try:
                rows = cdx_query(query_url, match_type=match_type, limit=1000)
                profile_cdx_queries_succeeded += 1
                for row in rows:
                    if row.get("statuscode") != "200" or row.get("mimetype") != "text/html":
                        continue
                    key = "|".join((row.get("timestamp", ""), row.get("original", "")))
                    profile_captures[key] = row
            except IntakeError as exc:
                errors.append(f"Profile CDX query failed for {query_url}: {exc}")
            time.sleep(delay_seconds)

    profile_snapshot_limit_reached = len(profile_captures) > profile_snapshot_limit
    sorted_profile_captures = sorted(
        profile_captures.values(), key=lambda row: row.get("timestamp", ""), reverse=True
    )[:profile_snapshot_limit]
    archived_profile_urls: set[str] = set()
    for row in sorted_profile_captures:
        timestamp = row.get("timestamp", "")
        original = row.get("original", "")
        snapshot_url = archive_raw_url(timestamp, original)
        try:
            document, _, status = fetch_text(snapshot_url)
            links = extract_slideshow_links(document, original)
            profile_observations.append({
                "kind": "archived-profile-html",
                "url": archive_replay_url(timestamp, original),
                "http_status": status,
                "captured_at": timestamp_to_iso(timestamp),
                "profile_reported_count": profile_count(document),
                "links_extracted": len(links),
            })
            for link in links:
                key = normalized_url(link["url"])
                if key:
                    archived_profile_urls.add(key)
                add_url(link["url"], source_kind="archived-profile-html",
                        source_url=archive_replay_url(timestamp, original),
                        label=link.get("label", ""))
        except IntakeError as exc:
            errors.append(f"Archived profile fetch failed for {snapshot_url}: {exc}")
        time.sleep(delay_seconds)

    presentation_url_limit_reached = len(urls) > url_limit
    if len(urls) > url_limit:
        # Keep all registry-known URLs; truncate only extra discovered candidates.
        registry_keys = {
            normalized_url(item["url"]) for item in known
        }
        ordered_keys = sorted(
            urls,
            key=lambda key: (key not in registry_keys, key),
        )
        urls = {key: urls[key] for key in ordered_keys[:url_limit]}

    presentation_results: list[dict[str, Any]] = []
    query_successes = 0
    query_attempts = 0
    capture_total = 0
    for key, item in sorted(urls.items(), key=lambda pair: pair[1]["url"].casefold()):
        parsed = urlsplit(item["url"])
        target = parsed.netloc + parsed.path
        if parsed.query:
            target += "?" + parsed.query
        query_attempts += 1
        try:
            rows = cdx_query(target, match_type="exact", limit=1000)
            query_successes += 1
            captures = [cdx_capture_record(row) for row in rows]
            captures.sort(key=lambda capture: capture.get("timestamp", ""))
            capture_total += len(captures)
            presentation_results.append({
                **item,
                "captures": captures,
                "capture_count": len(captures),
                "first_capture": next((c["captured_at"] for c in captures if c.get("captured_at")), None),
                "last_capture": next((c["captured_at"] for c in reversed(captures) if c.get("captured_at")), None),
            })
        except IntakeError as exc:
            errors.append(f"Presentation CDX query failed for {item['url']}: {exc}")
            presentation_results.append({**item, "captures": [], "capture_count": 0,
                                         "query_error": str(exc)})
        time.sleep(delay_seconds)

    unmatched = [item for item in presentation_results if not item["registry_artefact_ids"]]
    current_profile_urls = {
        normalized_url(item["url"])
        for item in urls.values()
        if any(s["kind"] in {"current-public-profile-html", "current-public-profile-rendered-browser"} for s in item["discovery_sources"])
    }
    current_count = sum(
        1 for item in urls.values()
        if any(s["kind"] in {"current-public-profile-html", "current-public-profile-rendered-browser"} for s in item["discovery_sources"])
    )
    summary = {
        "profile_reported_count": profile_reported_count,
        "current_profile_urls": current_count,
        "archived_profile_urls": len(archived_profile_urls),
        "registered_artefacts": len(known),
        "unique_presentation_urls": len(presentation_results),
        "cdx_queries_attempted": query_attempts + profile_cdx_queries_attempted,
        "cdx_queries_succeeded": query_successes + profile_cdx_queries_succeeded,
        "capture_records": capture_total,
        "unregistered_urls": len(unmatched),
        "profile_snapshots_inspected": len(sorted_profile_captures),
        "profile_snapshot_limit_reached": profile_snapshot_limit_reached,
        "presentation_url_limit_reached": presentation_url_limit_reached,
        "profile_count_to_html_link_gap": (max(0, profile_reported_count - current_count) if profile_reported_count is not None else None),
        "profile_discovery_status": derive_profile_discovery_status(profile_reported_count, current_count),
        "indexed_search_slide_urls": len(indexed_search_keys),
        "unregistered_indexed_search_urls": sum(
            1 for key in indexed_search_keys
            if key in urls and not urls[key]["registry_artefact_ids"]
        ),
    }
    report = {
        "report_version": "0.1.0",
        "generated_at": utc_now(),
        "source_collection_id": profile_collection["id"],
        "profile_url": profile_url,
        "profile_variants": profile_variants,
        "registry_version": registry.get("registry_version"),
        "inventory_completeness": "partial",
        "completeness_note": (
            "The report is limited to canonical registry URLs plus links visible in the current "
            "public profile HTML, rendered public profile DOM, indexed-web search results, and inspected Wayback snapshots. "
            "SlideShare's public API is retired and the website does not expose a documented "
            "replacement API. Tavily results are candidates rather than verified profile members. "
            "Profile HTML can show only part of the uploads; no exhaustive "
            "claim is made."
        ),
        "summary": summary,
        "discovery_providers": [tavily_status],
        "profile_observations": profile_observations,
        "presentations": presentation_results,
        "unmatched_candidates": unmatched,
        "errors": errors,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--profile-snapshot-limit", type=int, default=40)
    parser.add_argument("--url-limit", type=int, default=150)
    parser.add_argument("--delay-seconds", type=float, default=0.15)
    args = parser.parse_args()
    if args.profile_snapshot_limit < 0 or args.url_limit < 1 or args.delay_seconds < 0:
        parser.error("limits and delay must be non-negative; url-limit must be at least 1")
    try:
        report = run_intake(
            profile_snapshot_limit=args.profile_snapshot_limit,
            url_limit=args.url_limit,
            delay_seconds=args.delay_seconds,
            tavily_api_key=os.environ.get("TAVILY_API_KEY"),
        )
    except IntakeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "research-genealogy-archive-candidates.json"
    markdown_path = args.output_dir / "research-genealogy-archive-candidates.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown_report(report), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    if report["errors"]:
        print(f"Completed with {len(report['errors'])} recoverable source errors.", file=sys.stderr)
    if report["summary"]["cdx_queries_succeeded"] == 0:
        print("No CDX queries succeeded; report is incomplete.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

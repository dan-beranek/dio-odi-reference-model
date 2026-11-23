#!/usr/bin/env python3
"""Discover potentially relevant public DIO/ODI evidence across web and scholarly indexes.

This collector is intentionally review-only. Search results are leads, not verified
evidence, and this script never writes to canonical registries or the SCF event feed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from email.utils import parsedate_to_datetime
import os
import re
import sys
import time
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
TAVILY_ENDPOINT = "https://api.tavily.com/search"
OPENALEX_ENDPOINT = "https://api.openalex.org/works"
CROSSREF_ENDPOINT = "https://api.crossref.org/works"
USER_AGENT = "DIO-ODI-SCF-Discovery/0.1 (+https://vocab.danielberanek.cz/)"
MAX_RESPONSE_BYTES = 12_000_000
TRACKING_PARAMS = {"fbclid", "gclid", "mc_cid", "mc_eid", "ref", "source"}
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
ARXIV_RE = re.compile(r"(?:arxiv:)?(\d{4}\.\d{4,5})(?:v\d+)?", re.IGNORECASE)


class DiscoveryError(RuntimeError):
    """Raised when a configured discovery source cannot be read reliably."""


def stable_fingerprint(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def normalise_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", " ", re.sub(r"[^\w]+", " ", decomposed)).strip()


def normalise_url(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    parsed = urlparse(value.strip())
    if parsed.scheme.casefold() not in {"http", "https"} or not parsed.netloc:
        return ""
    host = (parsed.hostname or "").casefold()
    if host.startswith("www."):
        host = host[4:]
    port = parsed.port
    netloc = host if port is None or (parsed.scheme == "https" and port == 443) or (
        parsed.scheme == "http" and port == 80
    ) else f"{host}:{port}"
    query = [
        (key, val) for key, val in parse_qsl(parsed.query, keep_blank_values=True)
        if key.casefold() not in TRACKING_PARAMS
        and not key.casefold().startswith("utm_")
    ]
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((
        parsed.scheme.casefold(), netloc, path, "", urlencode(query, doseq=True), ""
    ))


def extract_dois(*values: Any) -> list[str]:
    found: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        for match in DOI_RE.findall(value):
            found.add(match.rstrip(".,;:)]}>").casefold())
    return sorted(found)


def parse_date(value: Any) -> str | None:
    if isinstance(value, list):
        for item in value:
            parsed = parse_date(item)
            if parsed:
                return parsed
        return None
    if isinstance(value, dict):
        parts = value.get("date-parts")
        if isinstance(parts, list) and parts and isinstance(parts[0], list):
            try:
                year, *rest = parts[0]
                month = rest[0] if len(rest) > 0 else 1
                day = rest[1] if len(rest) > 1 else 1
                return date(int(year), int(month), int(day)).isoformat()
            except (TypeError, ValueError):
                return None
        for key in ("date", "value", "@value"):
            if key in value:
                return parse_date(value[key])
        return None
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = value.strip()
    try:
        return datetime.fromisoformat(candidate.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        try:
            return date.fromisoformat(candidate[:10]).isoformat()
        except ValueError:
            try:
                return parsedate_to_datetime(candidate).date().isoformat()
            except (TypeError, ValueError, OverflowError):
                return None


def fetch_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: int = 35,
) -> Any:
    request_headers = {
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
        **(headers or {}),
    }
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=request_headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise DiscoveryError(f"Response too large for {url}")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        raise DiscoveryError(f"HTTP {exc.code} for {url}: {detail}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise DiscoveryError(f"Request failed for {url}: {exc}") from exc
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DiscoveryError(f"Invalid JSON returned by {url}") from exc


def read_json(path: str) -> dict[str, Any]:
    try:
        value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DiscoveryError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DiscoveryError(f"{path} must contain a JSON object")
    return value


def build_search_queries(
    profile: dict[str, Any], works: dict[str, Any]
) -> list[dict[str, str]]:
    queries: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(query_id: str, query: str, group: str) -> None:
        key = normalise_text(query)
        if key and key not in seen:
            seen.add(key)
            queries.append({"id": query_id, "query": query, "group": group})

    for index, phrase in enumerate(profile.get("identity_phrases", []), start=1):
        if isinstance(phrase, str) and phrase.strip():
            add(f"identity-{index}", f'"{phrase.strip()}"', "identity")

    author = works.get("author", {})
    orcid = author.get("orcid") if isinstance(author, dict) else None
    if isinstance(orcid, str) and orcid.strip():
        add("author-orcid", f'"{orcid.strip()}"', "author-identifier")

    author_name = author.get("name") if isinstance(author, dict) else None
    if isinstance(author_name, str) and author_name.strip():
        add(
            "author-identity",
            f'"{author_name.strip()}" "Digital Identity Optimization"',
            "author-identity",
        )

    for index, anchor in enumerate(profile.get("concept_anchors", []), start=1):
        if isinstance(anchor, str) and anchor.strip():
            add(f"concept-{index}", f'"{anchor.strip()}"', "concept-anchor")

    limit = profile.get("work_title_query_limit", 8)
    if not isinstance(limit, int) or limit < 0:
        raise DiscoveryError("work_title_query_limit must be a non-negative integer")
    eligible = [
        work for work in works.get("works", [])
        if isinstance(work, dict)
        and isinstance(work.get("title"), str)
        and work.get("type") in {
            "dataset", "publication-preprint", "publication-article",
            "web-publication", "research-report",
        }
    ]
    # Existing registry order is canonical; no platform preference is introduced.
    for index, work in enumerate(eligible[:limit], start=1):
        add(
            f"work-title-{index}",
            f'"{work["title"].strip()}"',
            "known-work-title",
        )
    return queries


def existing_evidence_index(feed: dict[str, Any]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
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
            url = normalise_url(source.get("url", ""))
            if url:
                index.setdefault(url, []).append(event["id"])
    return index


def build_known_context(
    works: dict[str, Any],
    registries: list[dict[str, Any]],
    feed: dict[str, Any],
) -> dict[str, Any]:
    title_to_work: dict[str, str] = {}
    doi_to_work: dict[str, str] = {}
    known_urls: set[str] = set()
    known_ids: set[str] = set()

    for work in works.get("works", []):
        if not isinstance(work, dict):
            continue
        work_id = work.get("id")
        title = work.get("title")
        if isinstance(work_id, str) and isinstance(title, str):
            title_to_work[normalise_text(title)] = work_id
        serialised = json.dumps(work, ensure_ascii=False)
        for doi in extract_dois(serialised):
            if isinstance(work_id, str):
                doi_to_work[doi] = work_id
            known_ids.add(doi)
        if isinstance(work.get("arxiv"), dict):
            arxiv_id = work["arxiv"].get("id")
            if isinstance(arxiv_id, str):
                known_ids.add(arxiv_id.casefold())
        known_ids.update(match.casefold() for match in ARXIV_RE.findall(serialised))

    for registry in registries:
        serialised = json.dumps(registry, ensure_ascii=False)
        known_ids.update(extract_dois(serialised))
        for match in re.findall(r"https?://[^\s\"'<>]+", serialised):
            url = normalise_url(match.rstrip(".,;:)"))
            if url:
                known_urls.add(url)

    evidence_index = existing_evidence_index(feed)
    known_urls.update(evidence_index)
    return {
        "title_to_work": title_to_work,
        "doi_to_work": doi_to_work,
        "known_urls": known_urls,
        "known_ids": known_ids,
        "evidence_index": evidence_index,
    }


def resolve_result(
    result: dict[str, Any],
    *,
    provider: str,
    query: dict[str, str],
    context: dict[str, Any],
    identity_phrases: list[str],
    concept_anchors: list[str],
) -> dict[str, Any] | None:
    title = str(result.get("title") or "").strip()
    location = result.get("primary_location") or {}
    url = str(
        result.get("url") or location.get("landing_page_url") or ""
    ).strip()
    if not url:
        doi_value = result.get("doi")
        if isinstance(doi_value, str) and doi_value:
            url = doi_value if doi_value.startswith("http") else f"https://doi.org/{doi_value}"
    clean_url = normalise_url(url)
    if not clean_url:
        return None

    content = str(
        result.get("content") or result.get("description") or result.get("abstract") or ""
    ).strip()
    combined = " ".join((title, content, url, str(result.get("doi") or "")))
    folded = normalise_text(combined)

    dois = extract_dois(combined, result.get("doi"))
    work_ids: set[str] = set()
    for doi in dois:
        work_id = context["doi_to_work"].get(doi)
        if work_id:
            work_ids.add(work_id)

    matched_signals: list[str] = []
    if any(normalise_text(phrase) in folded for phrase in identity_phrases):
        matched_signals.append("core-identity-phrase")
    if any(normalise_text(anchor) in folded for anchor in concept_anchors):
        matched_signals.append("distinctive-concept-anchor")

    title_key = normalise_text(title)
    if title_key and title_key in context["title_to_work"]:
        work_ids.add(context["title_to_work"][title_key])
        matched_signals.append("exact-known-work-title")

    if any(doi in context["known_ids"] for doi in dois):
        matched_signals.append("known-doi")
    if any(orcid in combined for orcid in context.get("orcid_values", [])):
        matched_signals.append("author-orcid")

    if "core-identity-phrase" in matched_signals and "author-orcid" in matched_signals:
        matched_signals.append("author-linked-identity")
    if (
        "distinctive-concept-anchor" in matched_signals
        and ("core-identity-phrase" in matched_signals or "author-orcid" in matched_signals)
    ):
        matched_signals.append("identity-linked-concept")

    # A query is not itself proof of relevance. Author-only and generic acronym hits
    # are excluded unless another identity or work-level signal corroborates them.
    strong = {
        "core-identity-phrase", "exact-known-work-title", "known-doi",
        "author-linked-identity", "identity-linked-concept",
    }
    if not strong.intersection(matched_signals):
        return None

    if "known-doi" in matched_signals or "exact-known-work-title" in matched_signals:
        match_class, relevance = "known-work-or-identifier", 100
    elif "core-identity-phrase" in matched_signals:
        match_class, relevance = "core-identity-phrase", 90
    else:
        match_class, relevance = "identity-linked-concept", 75

    published = (
        result.get("published_date") or result.get("publication_date")
        or parse_date(result.get("published")) or result.get("date")
    )
    published = parse_date(published) if published else None

    evidence_urls = {clean_url}
    for doi in dois:
        evidence_urls.add(normalise_url(f"https://doi.org/{doi}"))
    event_ids = sorted({
        event_id
        for evidence_url in evidence_urls
        for event_id in context["evidence_index"].get(evidence_url, [])
    })
    already_known = any(
        evidence_url in context["known_urls"] for evidence_url in evidence_urls
    ) or any(doi in context["known_ids"] for doi in dois)

    if event_ids:
        reference_status = "already-cited"
    elif already_known:
        reference_status = "already-registered"
    else:
        reference_status = "review-required"

    return {
        "provider": provider,
        "query_id": query["id"],
        "query": query["query"],
        "query_group": query["group"],
        "title": title or "(title unavailable)",
        "url": clean_url,
        "doi_values": dois,
        "published_date": published,
        "snippet": content[:1200],
        "provider_score": result.get("score"),
        "matched_signals": sorted(set(matched_signals)),
        "match_class": match_class,
        "relevance_score": relevance,
        "related_work_ids": sorted(work_ids),
        "reference_status": reference_status,
        "existing_event_ids": event_ids,
        "evidence_urls": sorted(item for item in evidence_urls if item),
    }


def candidate_key(observation: dict[str, Any]) -> str:
    if observation.get("doi_values"):
        return f"doi:{observation['doi_values'][0]}"
    return f"url:{observation['url']}"


def merge_observations(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for observation in observations:
        key = candidate_key(observation)
        current = merged.get(key)
        if current is None:
            current = {
                "candidate_id": f"discovery:{stable_fingerprint(key)[:16]}",
                "candidate_fingerprint": stable_fingerprint(key),
                "kind": "web-discovery-observation",
                "source_url": observation["url"],
                "title": observation["title"],
                "doi_values": observation["doi_values"],
                "published_date": observation["published_date"],
                "snippet": observation["snippet"],
                "provider_score": observation["provider_score"],
                "matched_signals": [],
                "match_class": observation["match_class"],
                "relevance_score": observation["relevance_score"],
                "related_work_ids": [],
                "reference_status": observation["reference_status"],
                "existing_event_ids": [],
                "evidence_urls": [],
                "observed_by": [],
                "queries": [],
                "observations": [],
                "editorial_status": "not-assessed",
                "date_basis_note": (
                    "A discovery provider's publication date is provisional metadata. "
                    "Confirm the primary source and date basis before considering an SCF event."
                ),
            }
            merged[key] = current
        current["observed_by"] = sorted(set(current["observed_by"]) | {observation["provider"]})
        current["matched_signals"] = sorted(
            set(current["matched_signals"]) | set(observation["matched_signals"])
        )
        current["related_work_ids"] = sorted(
            set(current["related_work_ids"]) | set(observation["related_work_ids"])
        )
        current["evidence_urls"] = sorted(
            set(current["evidence_urls"]) | set(observation["evidence_urls"])
        )
        current["existing_event_ids"] = sorted(
            set(current["existing_event_ids"]) | set(observation["existing_event_ids"])
        )
        current["queries"].append({
            "provider": observation["provider"],
            "query_id": observation["query_id"],
            "query": observation["query"],
            "query_group": observation["query_group"],
        })
        current["observations"].append({
            "provider": observation["provider"],
            "url": observation["url"],
            "published_date": observation["published_date"],
            "provider_score": observation["provider_score"],
            "snippet": observation["snippet"],
        })
        if observation["reference_status"] == "already-cited":
            current["reference_status"] = "already-cited"
        elif (
            observation["reference_status"] == "already-registered"
            and current["reference_status"] == "review-required"
        ):
            current["reference_status"] = "already-registered"
        if observation["relevance_score"] > current["relevance_score"]:
            current["relevance_score"] = observation["relevance_score"]
            current["match_class"] = observation["match_class"]
        if not current["published_date"] and observation["published_date"]:
            current["published_date"] = observation["published_date"]
        if len(current["snippet"]) < len(observation["snippet"]):
            current["snippet"] = observation["snippet"]
    for item in merged.values():
        item["queries"] = sorted(
            item["queries"], key=lambda query: (query["provider"], query["query_id"])
        )
        item["observations"] = sorted(
            item["observations"], key=lambda item: (item["provider"], item["url"])
        )
    return sorted(
        merged.values(),
        key=lambda item: (
            item["reference_status"] != "review-required",
            -item["relevance_score"],
            item.get("published_date") or "",
            item["source_url"],
        ),
    )


def search_tavily(
    queries: list[dict[str, str]], api_key: str, max_results: int
) -> tuple[list[tuple[dict[str, Any], dict[str, str]]], dict[str, Any]]:
    observations: list[tuple[dict[str, Any], dict[str, str]]] = []
    errors: list[str] = []
    calls = 0
    for query in queries:
        try:
            payload = fetch_json(
                TAVILY_ENDPOINT,
                method="POST",
                headers={"Authorization": f"Bearer {api_key}"},
                payload={
                    "query": query["query"],
                    "search_depth": "basic",
                    "max_results": max_results,
                    "topic": "general",
                    "include_answer": False,
                    "include_raw_content": False,
                    "include_published_date": True,
                    "include_usage": True,
                    "language": "en",
                },
            )
            calls += 1
            results = payload.get("results", []) if isinstance(payload, dict) else []
            if not isinstance(results, list):
                raise DiscoveryError("Tavily response has no results array")
            observations.extend(
                (item, query) for item in results if isinstance(item, dict)
            )
        except DiscoveryError as exc:
            errors.append(f"{query['id']}: {exc}")
        time.sleep(0.25)
    return observations, {
        "provider": "Tavily Search",
        "enabled": True,
        "queries_attempted": len(queries),
        "requests_succeeded": calls,
        "raw_results": len(observations),
        "errors": errors,
        "complete": not errors and calls == len(queries),
    }


def search_openalex(
    queries: list[dict[str, str]], max_results: int, email: str | None,
    api_key: str | None,
) -> tuple[list[tuple[dict[str, Any], dict[str, str]]], dict[str, Any]]:
    observations: list[tuple[dict[str, Any], dict[str, str]]] = []
    errors: list[str] = []
    selected = [
        query for query in queries
        if query["group"] in {"identity", "concept-anchor", "known-work-title"}
    ][:8]
    for query in selected:
        params = {
            "search": query["query"].replace('"', ""),
            "per-page": str(max_results),
            "select": "id,doi,title,publication_date,authorships,primary_location,ids,type",
        }
        if email:
            params["mailto"] = email
        if api_key:
            params["api_key"] = api_key
        try:
            payload = fetch_json(f"{OPENALEX_ENDPOINT}?{urlencode(params)}")
            items = payload.get("results", []) if isinstance(payload, dict) else []
            if not isinstance(items, list):
                raise DiscoveryError("OpenAlex response has no results array")
            for item in items:
                if not isinstance(item, dict):
                    continue
                authorships = item.get("authorships", [])
                authors = [
                    author.get("author", {}).get("display_name", "")
                    for author in authorships if isinstance(author, dict)
                ]
                location = item.get("primary_location") or {}
                source = location.get("landing_page_url") or item.get("doi") or item.get("id") or ""
                if item.get("doi") and not source.startswith("http"):
                    source = f"https://doi.org/{item['doi']}"
                observations.append(({
                    "title": item.get("title") or "",
                    "url": source,
                    "doi": item.get("doi"),
                    "publication_date": item.get("publication_date"),
                    "description": "Authors: " + "; ".join(filter(None, authors)),
                }, query))
        except DiscoveryError as exc:
            errors.append(f"{query['id']}: {exc}")
    return observations, {
        "provider": "OpenAlex",
        "enabled": True,
        "queries_attempted": len(selected),
        "raw_results": len(observations),
        "errors": errors,
        "complete": not errors,
        "api_key_configured": bool(api_key),
    }


def search_crossref(
    queries: list[dict[str, str]], max_results: int, email: str | None
) -> tuple[list[tuple[dict[str, Any], dict[str, str]]], dict[str, Any]]:
    observations: list[tuple[dict[str, Any], dict[str, str]]] = []
    errors: list[str] = []
    selected = [
        query for query in queries
        if query["group"] in {"identity", "concept-anchor"}
    ][:5]
    for query in selected:
        params = {
            "query.bibliographic": query["query"].replace('"', ""),
            "rows": str(max_results),
            "select": "DOI,title,URL,type,published,published-online,published-print,created,author",
        }
        if email:
            params["mailto"] = email
        try:
            payload = fetch_json(f"{CROSSREF_ENDPOINT}?{urlencode(params)}")
            items = payload.get("message", {}).get("items", []) if isinstance(payload, dict) else []
            if not isinstance(items, list):
                raise DiscoveryError("Crossref response has no items array")
            for item in items:
                if not isinstance(item, dict):
                    continue
                title_value = item.get("title") or []
                title = title_value[0] if title_value else ""
                date_value = (
                    item.get("published-online") or item.get("published-print")
                    or item.get("published") or item.get("created")
                )
                author_values = item.get("author", [])
                authors = [
                    " ".join(filter(None, (person.get("given"), person.get("family"))))
                    for person in author_values if isinstance(person, dict)
                ]
                observations.append(({
                    "title": title,
                    "url": item.get("URL") or (
                        f"https://doi.org/{item['DOI']}" if item.get("DOI") else ""
                    ),
                    "doi": item.get("DOI"),
                    "published": parse_date(date_value),
                    "description": "Authors: " + "; ".join(filter(None, authors)),
                }, query))
        except DiscoveryError as exc:
            errors.append(f"{query['id']}: {exc}")
        time.sleep(1.05)
    return observations, {
        "provider": "Crossref",
        "enabled": True,
        "queries_attempted": len(selected),
        "raw_results": len(observations),
        "errors": errors,
        "complete": not errors,
    }


def build_report(
    profile: dict[str, Any],
    works: dict[str, Any],
    keywords: dict[str, Any],
    distributions: dict[str, Any],
    external_reception: dict[str, Any],
    application_mappings: dict[str, Any],
    feed: dict[str, Any],
    *,
    tavily_api_key: str | None = None,
    openalex_api_key: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    queries = build_search_queries(profile, works)
    if not queries:
        raise DiscoveryError("The discovery query profile produced no queries")

    identity_phrases = profile.get("identity_phrases", [])
    if not isinstance(identity_phrases, list):
        raise DiscoveryError("identity_phrases must be an array")
    chunks = keywords.get("chunks", {})
    canonical_concepts = [
        term
        for chunk in chunks.values()
        if isinstance(chunk, dict)
        for term in chunk.get("terms", [])
        if isinstance(term, str)
    ]
    canonical_set = {normalise_text(term) for term in canonical_concepts}
    concept_anchors = profile.get("concept_anchors", [])
    invalid_anchors = [
        anchor for anchor in concept_anchors
        if normalise_text(anchor) not in canonical_set
    ]
    if invalid_anchors:
        raise DiscoveryError(
            "Concept anchors are not present in canonical keyword grammar: "
            + ", ".join(invalid_anchors)
        )

    author = works.get("author", {}) if isinstance(works.get("author"), dict) else {}
    context = build_known_context(
        works,
        [works, distributions, external_reception, application_mappings],
        feed,
    )
    context["orcid_values"] = [author["orcid"]] if author.get("orcid") else []

    provider_checks: list[dict[str, Any]] = []
    raw_observations: list[tuple[dict[str, Any], dict[str, str], str]] = []

    if tavily_api_key:
        found, check = search_tavily(
            queries, tavily_api_key, int(profile.get("max_results_per_query", 5))
        )
        raw_observations.extend((item, query, "Tavily Search") for item, query in found)
        provider_checks.append(check)
    else:
        provider_checks.append({
            "provider": "Tavily Search",
            "enabled": False,
            "reason": "TAVILY_API_KEY is not configured",
            "complete": None,
        })

    found, check = search_openalex(
        queries, int(profile.get("max_results_per_query", 5)),
        author.get("email"), openalex_api_key,
    )
    raw_observations.extend((item, query, "OpenAlex") for item, query in found)
    provider_checks.append(check)

    found, check = search_crossref(
        queries, int(profile.get("max_results_per_query", 5)), author.get("email")
    )
    raw_observations.extend((item, query, "Crossref") for item, query in found)
    provider_checks.append(check)

    resolved: list[dict[str, Any]] = []
    for item, query, provider in raw_observations:
        candidate = resolve_result(
            item, provider=provider, query=query, context=context,
            identity_phrases=identity_phrases, concept_anchors=concept_anchors,
        )
        if candidate:
            resolved.append(candidate)

    candidates = merge_observations(resolved)
    web_enabled = bool(tavily_api_key)
    errors = [
        {"source": check["provider"], "error": error}
        for check in provider_checks for error in check.get("errors", [])
    ]
    return {
        "report_version": "0.1.0",
        "generated_at": now.isoformat(),
        "query_profile_version": profile.get("profile_version"),
        "query_count": len(queries),
        "queries": queries,
        "coverage": {
            "general_web_search_enabled": web_enabled,
            "scholarly_indexes_enabled": True,
            "coverage_level": "web-and-scholarly" if web_enabled else "scholarly-only",
            "limitation": (
                None if web_enabled else
                "General web search is disabled because TAVILY_API_KEY is not configured. "
                "This run is limited to scholarly metadata indexes and is not a broad web scan."
            ),
        },
        "policy": {
            "review_required": True,
            "automatic_scf_writes": False,
            "automatic_registry_writes": False,
            "search_result_is_primary_evidence": False,
            "author_name_alone_is_sufficient": False,
            "exact_url_and_identifier_matching": True,
            "provider_observations_are_deduplicated": True,
            "source_platforms_are_not_preselected": True,
        },
        "stats": {
            "providers_configured": sum(1 for check in provider_checks if check.get("enabled")),
            "raw_observations": len(raw_observations),
            "relevant_observations": len(resolved),
            "unique_candidates": len(candidates),
            "review_required": sum(
                1 for candidate in candidates
                if candidate["reference_status"] == "review-required"
            ),
            "already_registered": sum(
                1 for candidate in candidates
                if candidate["reference_status"] == "already-registered"
            ),
            "already_cited": sum(
                1 for candidate in candidates
                if candidate["reference_status"] == "already-cited"
            ),
        },
        "provider_checks": provider_checks,
        "candidates": candidates,
        "errors": errors,
        "scan_complete": not errors and all(
            check.get("complete") is not False for check in provider_checks
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    coverage = report["coverage"]
    lines = [
        "# SCF discovery intake",
        "",
        f"Generated: {report['generated_at']}",
        f"Query profile: {report.get('query_profile_version') or 'unknown'}",
        f"Queries generated: **{report['query_count']}**",
        f"Coverage: **{coverage['coverage_level']}**",
        "",
        "> Discovery output is a review queue, not a record of verified reception, citation, endorsement, adoption, or implementation.",
        "",
        f"Raw observations: **{report['stats']['raw_observations']}**  ",
        f"Relevant observations: **{report['stats']['relevant_observations']}**  ",
        f"Unique candidates: **{report['stats']['unique_candidates']}**  ",
        f"Review required: **{report['stats']['review_required']}**  ",
        f"Already registered: **{report['stats']['already_registered']}**  ",
        f"Already cited: **{report['stats']['already_cited']}**",
        "",
    ]
    if coverage.get("limitation"):
        lines.extend([f"**Coverage limitation:** {coverage['limitation']}", ""])
    lines.extend(["## Provider checks", ""])
    for check in report["provider_checks"]:
        lines.append(
            f"- **{check['provider']}** — "
            f"{'enabled' if check.get('enabled') else 'disabled'}; "
            f"queries: {check.get('queries_attempted', 0)}; "
            f"raw observations: {check.get('raw_results', 0)}; "
            f"complete: {check.get('complete')}"
        )
        for error in check.get("errors", []):
            lines.append(f"  - Error: {error}")
    lines.extend(["", "## Query profile used", ""])
    for query in report["queries"]:
        lines.append(f"- {query['id']} ({query['group']}): {query['query']}")
    lines.extend(["", "## Discovery candidates", ""])
    if not report["candidates"]:
        lines.append("No candidates passed the deterministic relevance filters.")
    for item in report["candidates"]:
        lines.extend([
            f"### {item['title']}",
            "",
            f"- Candidate ID: {item['candidate_id']}",
            f"- Match class: **{item['match_class']}** (heuristic relevance {item['relevance_score']}/100)",
            f"- Matched signals: {', '.join(item['matched_signals'])}",
            f"- Reference status: **{item['reference_status']}**",
            f"- Related canonical works: {', '.join(item['related_work_ids']) or 'not resolved'}",
            f"- DOI: {', '.join(item['doi_values']) or 'not identified'}",
            f"- Publication date (provisional): {item.get('published_date') or 'not supplied'}",
            f"- Candidate URL: {item['source_url']}",
            f"- Observed by: {', '.join(item['observed_by'])}",
            f"- Existing SCF events: {', '.join(item['existing_event_ids']) or 'none found by exact URL'}",
            f"- Queries: {', '.join(query['query_id'] for query in item['queries'])}",
            f"- Snippet: {item.get('snippet') or 'not supplied'}",
            "",
        ])
    lines.extend([
        "## Editorial and provenance boundary",
        "",
        "- Search rankings and snippets are discovery signals only; inspect the primary source before assessing relevance.",
        "- A match to an author name or a generic acronym is not sufficient by itself.",
        "- Exact DOI, canonical URL, or title matches are used for deduplication and existing-record lookup; topical similarity is not treated as identity.",
        "- A search result does not establish citation, independent review, endorsement, uptake, implementation, or a material semantic change.",
        "- Publication dates supplied by an index remain provisional until checked against the primary record.",
        "- The collector does not assign SCF event IDs, mutate any registry, change the SCF event feed, increment the feed version, create an archive, or deploy the site.",
        "- The collector does not crawl full pages in this version; it stores short provider snippets and public metadata for human triage.",
        "",
    ])
    if report["errors"]:
        lines.extend(["## Incomplete providers", ""])
        for error in report["errors"]:
            lines.append(f"- **{error['source']}**: {error['error']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="scf-discovery-output")
    args = parser.parse_args()

    try:
        profile = read_json("discovery/query-profile.json")
        works = read_json("metadata/works.json")
        keywords = read_json("metadata/keywords.json")
        distributions = read_json("metadata/distributions.json")
        external_reception = read_json("metadata/external-reception.json")
        application_mappings = read_json("metadata/application-mappings.json")
        feed = read_json("semantic-change-feed/events.json")
        report = build_report(
            profile, works, keywords, distributions, external_reception,
            application_mappings, feed,
            tavily_api_key=os.environ.get("TAVILY_API_KEY"),
            openalex_api_key=os.environ.get("OPENALEX_API_KEY"),
        )
    except DiscoveryError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "scf-discovery-candidates.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "scf-discovery-candidates.md").write_text(
        render_markdown(report), encoding="utf-8"
    )
    if not report["scan_complete"]:
        print("Discovery scan incomplete; inspect provider errors.", file=sys.stderr)
        return 1
    if not report["coverage"]["general_web_search_enabled"]:
        print(
            "Discovery scan completed in scholarly-only mode; "
            "configure TAVILY_API_KEY for general web search.",
            file=sys.stderr,
        )
    print(
        f"Discovery scan complete: {report['stats']['unique_candidates']} "
        "unique review candidates."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

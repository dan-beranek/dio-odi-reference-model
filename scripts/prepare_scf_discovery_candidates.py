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


def work_doi_identifiers(work: dict[str, Any]) -> list[str]:
    """Return only DOI values that identify this work or one of its versions."""
    values: list[str] = []
    for field in (
        "version_doi", "concept_doi", "current_version_doi",
        "reference_model_concept_doi", "preferred_relation_identifier",
    ):
        values.extend(extract_dois(work.get(field)))
    for collection_name in ("versions", "releases"):
        collection = work.get(collection_name, [])
        if isinstance(collection, list):
            for item in collection:
                if isinstance(item, dict):
                    values.extend(extract_dois(item.get("doi")))
    current_release = work.get("current_release")
    if isinstance(current_release, dict):
        values.extend(extract_dois(current_release.get("doi")))
    return list(dict.fromkeys(values))


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

    # Search for references to canonical research identifiers as well as titles.
    # Only the work's own DOI fields and version records are used here; cited DOIs
    # embedded in notes or abstracts are deliberately not treated as its identity.
    identifier_limit = profile.get("identifier_query_limit", 6)
    if not isinstance(identifier_limit, int) or identifier_limit < 0:
        raise DiscoveryError("identifier_query_limit must be a non-negative integer")
    identifier_count = 0
    arxiv_count = 0
    for work in works.get("works", []):
        if not isinstance(work, dict):
            continue
        own_dois = work_doi_identifiers(work)
        for doi in own_dois:
            if identifier_count >= identifier_limit:
                break
            identifier_count += 1
            add(f"work-doi-{identifier_count}", f'"{doi}"', "work-identifier")

        arxiv = work.get("arxiv")
        if isinstance(arxiv, dict) and isinstance(arxiv.get("id"), str):
            arxiv_count += 1
            add(
                f"work-arxiv-{arxiv_count}",
                f'"arXiv:{arxiv["id"]}"',
                "work-identifier",
            )

        if identifier_count >= identifier_limit and arxiv_count:
            break

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
    distributions: dict[str, Any],
    external_reception: dict[str, Any],
    application_mappings: dict[str, Any],
    feed: dict[str, Any],
) -> dict[str, Any]:
    title_to_work: dict[str, str] = {}
    doi_to_work: dict[str, str] = {}
    arxiv_to_work: dict[str, str] = {}
    known_urls: set[str] = set()
    known_ids: set[str] = set()

    url_fields = {
        "url", "canonical_url", "canonical_hub", "repository", "endpoint",
        "health_endpoint", "concept_url", "version_url", "pdf_url", "html_url",
        "site_homepage", "namespace_document", "frontend",
    }

    def add_urls_from_fields(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in url_fields and isinstance(child, str):
                    normalised = normalise_url(child)
                    if normalised:
                        known_urls.add(normalised)
                elif isinstance(child, (dict, list)):
                    add_urls_from_fields(child)
        elif isinstance(value, list):
            for child in value:
                add_urls_from_fields(child)

    for work in works.get("works", []):
        if not isinstance(work, dict):
            continue
        work_id = work.get("id")
        title = work.get("title")
        if isinstance(work_id, str) and isinstance(title, str):
            title_to_work[normalise_text(title)] = work_id
        for doi in work_doi_identifiers(work):
            known_ids.add(doi)
            if isinstance(work_id, str):
                doi_to_work[doi] = work_id
        arxiv = work.get("arxiv")
        if isinstance(arxiv, dict):
            arxiv_id = arxiv.get("id")
            if isinstance(arxiv_id, str):
                normalised_arxiv = arxiv_id.casefold()
                known_ids.add(normalised_arxiv)
                if isinstance(work_id, str):
                    arxiv_to_work[normalised_arxiv] = work_id
        add_urls_from_fields(work)

    # A distribution's explicit identifier belongs to the canonical work
    # named by the registry group. Do not scrape DOI strings from narrative
    # evidence fields: they may describe bibliographic citations, not identity.
    for work_group in distributions.get("works", []):
        if not isinstance(work_group, dict):
            continue
        work_id = work_group.get("work")
        for representation in work_group.get("representations", []):
            if not isinstance(representation, dict):
                continue
            identifier = representation.get("identifier")
            identifier_type = representation.get("identifier_type")
            if identifier_type == "doi":
                for doi in extract_dois(identifier):
                    known_ids.add(doi)
                    if isinstance(work_id, str):
                        doi_to_work[doi] = work_id
            elif identifier_type == "url":
                normalised = normalise_url(identifier)
                if normalised:
                    known_urls.add(normalised)
            add_urls_from_fields(representation)

    # In the External Reception Registry, entry URLs and target-work URLs
    # identify records. cited_sources are references, not record identities.
    for field in ("target_works", "entries"):
        for record in external_reception.get(field, []):
            if not isinstance(record, dict):
                continue
            # Only the record's own landing page is its identity. In particular,
            # do not recurse into cited_sources[].url: those are bibliographic
            # edges to other works, not alternate URLs for this reception record.
            record_url = record.get("url")
            normalised = normalise_url(record_url)
            if normalised:
                known_urls.add(normalised)
                parsed = urlparse(normalised)
                if parsed.hostname in {"doi.org", "dx.doi.org"}:
                    known_ids.update(extract_dois(parsed.path))
            if field == "target_works":
                normalised_homepage = normalise_url(record.get("homepage", ""))
                if normalised_homepage:
                    known_urls.add(normalised_homepage)

    # Only DIO/ODI archived release identifiers count here. External-source
    # DOIs in application mappings remain external citations.
    application_doi_fields = {
        "archived_release_doi", "previous_archived_release_doi",
        "earlier_archived_release_doi", "first_archived_release_doi",
        "introduced_archived_release_doi", "base_mapping_first_archived_release_doi",
    }
    for mapping in application_mappings.get("mappings", []):
        if not isinstance(mapping, dict):
            continue
        for field in application_doi_fields:
            known_ids.update(extract_dois(mapping.get(field)))
        add_urls_from_fields(mapping)

    if isinstance(works.get("hub"), str):
        normalised_hub = normalise_url(works["hub"])
        if normalised_hub:
            known_urls.add(normalised_hub)

    # Zenodo's record landing pages do not expose their DOI in the URL.
    # Add the canonical /records/{numeric-id} URL as an alias for every
    # registered Zenodo DOI so indexed landing pages resolve to the same record.
    for identifier in known_ids:
        match = re.fullmatch(r"10\.5281/zenodo\.(\d+)", identifier)
        if match:
            alias = normalise_url(f"https://zenodo.org/records/{match.group(1)}")
            if alias:
                known_urls.add(alias)

    evidence_index = existing_evidence_index(feed)
    known_urls.update(evidence_index)
    return {
        "title_to_work": title_to_work,
        "doi_to_work": doi_to_work,
        "arxiv_to_work": arxiv_to_work,
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

    # Distinguish the discovered object's own DOI from DOIs merely cited in
    # its title/snippet. A cited DOI links the candidate to a known work, but
    # must never become the candidate's identity or deduplication key.
    primary_dois = set(extract_dois(result.get("doi")))
    parsed_url = urlparse(clean_url)
    if parsed_url.hostname in {"doi.org", "dx.doi.org"}:
        primary_dois.update(extract_dois(parsed_url.path))
    referenced_dois = set(extract_dois(title, content))
    referenced_dois.difference_update(primary_dois)

    primary_arxiv_ids = {
        match.casefold() for match in ARXIV_RE.findall(str(result.get("arxiv_id") or ""))
    }
    if "arxiv.org" in (parsed_url.hostname or ""):
        primary_arxiv_ids.update(match.casefold() for match in ARXIV_RE.findall(parsed_url.path))
    referenced_arxiv_ids = {
        match.casefold() for match in ARXIV_RE.findall(" ".join((title, content)))
    }
    referenced_arxiv_ids.difference_update(primary_arxiv_ids)

    work_ids: set[str] = set()
    for doi in primary_dois | referenced_dois:
        work_id = context["doi_to_work"].get(doi)
        if work_id:
            work_ids.add(work_id)
    for arxiv_id in primary_arxiv_ids | referenced_arxiv_ids:
        work_id = context["arxiv_to_work"].get(arxiv_id)
        if work_id:
            work_ids.add(work_id)

    matched_signals: list[str] = []
    matched_identity_phrases = [
        phrase for phrase in identity_phrases
        if normalise_text(phrase) and normalise_text(phrase) in folded
    ]
    if matched_identity_phrases:
        matched_signals.append("core-identity-phrase")
    if any(
        normalise_text(phrase) != normalise_text("Digital Identity Optimization")
        for phrase in matched_identity_phrases
    ):
        matched_signals.append("distinctive-identity-phrase")
    if any(normalise_text(anchor) in folded for anchor in concept_anchors):
        matched_signals.append("distinctive-concept-anchor")

    title_key = normalise_text(title)
    if title_key and title_key in context["title_to_work"]:
        work_ids.add(context["title_to_work"][title_key])
        matched_signals.append("exact-known-work-title")

    if any(doi in context["known_ids"] for doi in primary_dois):
        matched_signals.append("known-doi")
    if any(doi in context["doi_to_work"] for doi in referenced_dois):
        matched_signals.append("known-doi-reference")
    if any(arxiv_id in context["arxiv_to_work"] for arxiv_id in referenced_arxiv_ids):
        matched_signals.append("known-arxiv-reference")
    if any(arxiv_id in context["arxiv_to_work"] for arxiv_id in primary_arxiv_ids):
        matched_signals.append("known-arxiv-identifier")
    if any(orcid in combined for orcid in context.get("orcid_values", [])):
        matched_signals.append("author-orcid")
    if any(
        normalise_text(author_name) in folded
        for author_name in context.get("author_names", [])
        if normalise_text(author_name)
    ):
        matched_signals.append("author-name")

    if (
        "core-identity-phrase" in matched_signals
        and (
            "author-orcid" in matched_signals
            or "author-name" in matched_signals
        )
    ):
        matched_signals.append("author-linked-identity")
    if (
        "distinctive-concept-anchor" in matched_signals
        and ("core-identity-phrase" in matched_signals or "author-orcid" in matched_signals)
    ):
        matched_signals.append("identity-linked-concept")

    # A query is not itself proof of relevance. Author-only and generic acronym hits
    # are excluded unless another identity or work-level signal corroborates them.
    strong = {
        "distinctive-identity-phrase", "exact-known-work-title", "known-doi",
        "known-doi-reference", "known-arxiv-reference", "known-arxiv-identifier",
        "author-linked-identity", "identity-linked-concept",
    }
    if not strong.intersection(matched_signals):
        return None

    if "known-doi" in matched_signals or "exact-known-work-title" in matched_signals:
        match_class, relevance = "known-work-or-identifier", 100
    elif (
        "known-doi-reference" in matched_signals
        or "known-arxiv-reference" in matched_signals
        or "known-arxiv-identifier" in matched_signals
    ):
        match_class, relevance = "known-work-reference", 95
    elif (
        "distinctive-identity-phrase" in matched_signals
        or "author-linked-identity" in matched_signals
    ):
        match_class, relevance = "identity-linked-identity", 90
    else:
        match_class, relevance = "identity-linked-concept", 75

    published = (
        result.get("published_date") or result.get("publication_date")
        or parse_date(result.get("published")) or result.get("date")
    )
    published = parse_date(published) if published else None

    evidence_urls = {clean_url}
    for doi in primary_dois:
        evidence_urls.add(normalise_url(f"https://doi.org/{doi}"))
    event_ids = sorted({
        event_id
        for evidence_url in evidence_urls
        for event_id in context["evidence_index"].get(evidence_url, [])
    })
    already_known = any(
        evidence_url in context["known_urls"] for evidence_url in evidence_urls
    ) or any(
        doi in context["known_ids"] for doi in primary_dois
    ) or any(
        arxiv_id in context["known_ids"] for arxiv_id in primary_arxiv_ids
    )

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
        "doi_values": sorted(primary_dois),
        "referenced_doi_values": sorted(referenced_dois),
        "referenced_arxiv_ids": sorted(referenced_arxiv_ids),
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
    selected = (
        [query for query in queries if query["group"] == "identity"][:3]
        + [query for query in queries if query["group"] == "concept-anchor"][:2]
        + [query for query in queries if query["group"] == "known-work-title"][:2]
        + [query for query in queries if query["group"] == "work-identifier"][:6]
    )
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
    selected = (
        [query for query in queries if query["group"] == "identity"][:3]
        + [query for query in queries if query["group"] == "concept-anchor"][:2]
        + [query for query in queries if query["group"] == "known-work-title"][:2]
        + [query for query in queries if query["group"] == "work-identifier"][:6]
    )
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
        works, distributions, external_reception, application_mappings, feed
    )
    context["orcid_values"] = [author["orcid"]] if author.get("orcid") else []
    context["author_names"] = [author["name"]] if author.get("name") else []

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
    tavily_check = next(
        check for check in provider_checks if check["provider"] == "Tavily Search"
    )
    web_configured = bool(tavily_api_key)
    web_enabled = web_configured and tavily_check.get("complete") is True
    scholarly_checks = [
        check for check in provider_checks
        if check["provider"] in {"OpenAlex", "Crossref"} and check.get("enabled")
    ]
    scholarly_enabled = bool(scholarly_checks)
    scholarly_complete = any(
        check.get("complete") is True for check in scholarly_checks
    )
    completed_scholarly = [
        check["provider"] for check in scholarly_checks
        if check.get("complete") is True
    ]
    incomplete_providers = [
        check["provider"] for check in provider_checks
        if check.get("enabled") and check.get("complete") is False
    ]
    if web_enabled and scholarly_complete:
        coverage_level = "web-and-scholarly"
    elif web_enabled:
        coverage_level = "general-web-only"
    elif scholarly_complete:
        coverage_level = "scholarly-only"
    else:
        coverage_level = "no-complete-provider"

    if web_configured and not web_enabled:
        coverage_limitation = (
            "Tavily Search was configured but did not complete all queries. "
            "This run has no complete general-web coverage."
        )
    elif not web_configured and not scholarly_complete:
        coverage_limitation = (
            "General web search is disabled and no scholarly metadata provider "
            "completed successfully. This run has no complete search coverage."
        )
    elif not web_configured:
        coverage_limitation = (
            "General web search is disabled because TAVILY_API_KEY is not configured. "
            "This run is limited to scholarly metadata indexes and is not a broad web scan."
        )
    elif not scholarly_complete:
        coverage_limitation = (
            "Tavily completed the general-web scan, but neither scholarly metadata "
            "provider completed successfully."
        )
    elif incomplete_providers:
        coverage_limitation = (
            "The Tavily general-web scan completed and scholarly coverage is available "
            f"through {', '.join(completed_scholarly)}. Supplemental provider gaps remain: "
            f"{', '.join(incomplete_providers)}. See provider checks for details."
        )
    else:
        coverage_limitation = None

    errors = [
        {"source": check["provider"], "error": error}
        for check in provider_checks for error in check.get("errors", [])
    ]
    # When Tavily is configured, its full completion is the acceptance criterion:
    # scholarly providers are supplementary and must report their own gaps without
    # turning a successful general-web scan into a failed workflow. In scholarly-only
    # mode, at least one scholarly index must complete.
    scan_complete = web_enabled if web_configured else scholarly_complete
    scan_status = (
        "complete" if scan_complete and not errors
        else "complete-with-provider-gaps" if scan_complete
        else "incomplete"
    )
    return {
        "report_version": "0.1.0",
        "generated_at": now.isoformat(),
        "query_profile_version": profile.get("profile_version"),
        "query_count": len(queries),
        "queries": queries,
        "coverage": {
            "general_web_search_configured": web_configured,
            "general_web_search_enabled": web_enabled,
            "scholarly_indexes_enabled": scholarly_enabled,
            "scholarly_indexes_complete": scholarly_complete,
            "coverage_level": coverage_level,
            "limitation": coverage_limitation,
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
        "scan_complete": scan_complete,
        "scan_status": scan_status,
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
        f"Run status: **{report.get('scan_status', 'unknown')}**",
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
            f"successful requests: {check.get('requests_succeeded', 'n/a')}; "
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

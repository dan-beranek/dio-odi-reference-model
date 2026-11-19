#!/usr/bin/env python3
"""Generate data-driven site projections from the canonical DIO/ODI JSON registries.

Canonical editorial data stays in JSON. This script regenerates HTML, JSON-LD,
RDF/Turtle, and selected discovery metadata so those representations do not
need to be edited independently.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import unicodedata
import subprocess
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF, RDFS, XSD

ROOT = Path(__file__).resolve().parents[1]
RECEPTION_JSON = "metadata/external-reception.json"
RECEPTION_HTML = "external-reception/index.html"
RECEPTION_TTL = "metadata/external-reception.ttl"
SCF_JSON = "semantic-change-feed/events.json"
SCF_HTML = "semantic-change-feed/index.html"
METADATA_JSON = "metadata.json"
WORKS_JSON = "metadata/works.json"
KEYWORDS_JSON = "metadata/keywords.json"
LLMS_TXT = "llms.txt"
ROOT_README = "README.md"
SCF_README = "semantic-change-feed/README.md"
SITEMAP = "sitemap.xml"
AGENSI_PLANNER_URL = "https://www.agensi.io/r/DANIELBERANEK?to=/skills/agentic-entity-resolution-guardrail-planner"
PLANNER_SOURCE_REPOSITORY = "https://github.com/dan-beranek/agentic-entity-resolution-guardrail-planner"

SCHEMA = Namespace("https://schema.org/")
CITO = Namespace("http://purl.org/spar/cito/")
RECEPTION_URI = "https://vocab.danielberanek.cz/external-reception/"
POLICY_MAPPING_URI = "https://vocab.danielberanek.cz/mappings/commit-boundary-policy/"
PERSON_URI = "https://danielberanek.cz/#person"
LICENSE_URI = "https://creativecommons.org/licenses/by/4.0/"

MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)

DATE_BASIS_LABELS = {
    "publication_date": "publication date",
    "first_archival_inclusion": "first archival inclusion",
    "version_publication_date": "version publication date",
    "archive_publication_date": "archive publication date",
    "hub_changelog_date": "Hub Changelog date",
    "activity_period": "activity period",
    "deployment_date": "deployment date",
    "documentation_date": "documentation date",
}


def read_text(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(f"Required source file is missing: {relative}")
    return path.read_text(encoding="utf-8")


def load_json(relative: str):
    return json.loads(read_text(relative))


def dump_json(document) -> str:
    return json.dumps(document, ensure_ascii=False, indent=2) + "\n"


def esc(value) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def format_date(value: str | None) -> str:
    if not value:
        return ""
    parsed = date.fromisoformat(value[:10])
    return f"{parsed.day} {MONTHS[parsed.month - 1]} {parsed.year}"


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    return slug or "component"


def text_with_links(value: str | None) -> str:
    """Escape plain text while turning literal HTTP(S) URLs into safe links."""
    raw = str(value or "")
    pieces = []
    cursor = 0
    for match in re.finditer(r"https?://[^\s<>]+", raw):
        pieces.append(esc(raw[cursor:match.start()]))
        url = match.group(0)
        suffix = ""
        while url and url[-1] in ".,;:!?)]}":
            suffix = url[-1] + suffix
            url = url[:-1]
        if url:
            safe_url = esc(url)
            pieces.append(
                f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">{safe_url}</a>'
            )
        pieces.append(esc(suffix))
        cursor = match.end()
    pieces.append(esc(raw[cursor:]))
    return "".join(pieces)


def anchor(label: str, url: str) -> str:
    safe_url = esc(url)
    return (
        f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">'
        f'{esc(label)}</a>'
    )


def replace_once(source: str, pattern: str, replacement: str, label: str) -> str:
    callback = replacement if callable(replacement) else lambda _match: replacement
    updated, count = re.subn(pattern, callback, source, count=1, flags=re.S)
    if count != 1:
        raise ValueError(f"Could not locate exactly one generated region: {label}")
    return updated


def replace_line_with_prefix(
    source: str, prefix: str, replacement: str, label: str
) -> str:
    """Replace exactly one complete line without touching later sections."""
    lines = source.splitlines()
    matches = [index for index, line in enumerate(lines) if line.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one line starting with {prefix!r} for {label}; found {len(matches)}"
        )
    lines[matches[0]] = replacement
    return "\n".join(lines) + "\n"


def replace_markdown_section(
    source: str, start_heading: str, end_heading: str, replacement: str, label: str
) -> str:
    """Replace one Markdown section using explicit heading boundaries."""
    if source.count(start_heading) != 1 or source.count(end_heading) != 1:
        raise ValueError(
            f"Expected one {start_heading!r} and one {end_heading!r} boundary for {label}; "
            f"found {source.count(start_heading)} and {source.count(end_heading)}"
        )
    start = source.find(start_heading)
    end = source.find(end_heading, start + len(start_heading))
    if end < 0:
        raise ValueError(f"End boundary {end_heading!r} precedes start for {label}")
    return source[:start] + replacement.rstrip() + "\n\n" + source[end:]


def render_reception_jsonld(registry: dict) -> str:
    works = {item["id"]: item for item in registry.get("target_works", [])}
    has_part = []
    for entry in registry.get("entries", []):
        work_items = []
        for work_id in entry.get("target_work_ids", []):
            work = works.get(work_id)
            if work:
                work_items.append({
                    "@type": "CreativeWork",
                    "@id": work["url"],
                    "name": work["title"],
                })
        item = {
            "@type": "CreativeWork",
            "@id": f'{RECEPTION_URI}#{entry["id"]}',
            "name": entry["title"],
            "url": entry["url"],
            "genre": entry["category"],
            "description": entry["summary"],
            "about": work_items,
        }
        publication_date = entry.get("publication", {}).get("date")
        if publication_date:
            item["datePublished"] = publication_date
        citations = [
            source["url"]
            for source in entry.get("cited_sources", [])
            if source.get("url")
        ]
        if citations:
            item["citation"] = citations
        has_part.append(item)

    graph = [
        {
            "@type": "CollectionPage",
            "@id": RECEPTION_URI,
            "url": RECEPTION_URI,
            "name": registry.get("title", "DIO/ODI External Reception"),
            "description": registry.get("description", ""),
            "inLanguage": "en",
            "isPartOf": {"@id": "https://vocab.danielberanek.cz/#website"},
            "author": {"@id": registry.get("maintainer", {}).get("person_uri", PERSON_URI)},
            "license": LICENSE_URI,
            "hasPart": has_part,
        }
    ]
    return (
        '<script type="application/ld+json">'
        + json.dumps({"@context": "https://schema.org", "@graph": graph},
                     ensure_ascii=False, separators=(",", ":"))
        + "</script>"
    )


def render_reception_card(entry: dict, works: dict[str, dict]) -> str:
    authors = ", ".join(author.get("name", "") for author in entry.get("authors", []) if author.get("name"))
    publication = entry.get("publication", {})
    date_label = publication.get("date") or publication.get("displayed_relative_age") \
        or publication.get("version_scope") or "Date not clearly pinned"
    if publication.get("date"):
        date_label = format_date(publication["date"])
    elif publication.get("displayed_relative_age"):
        date_label = publication["displayed_relative_age"]

    top = (
        '<div class="reception-card-top">'
        f'<span class="tag">{esc(entry.get("platform", ""))}</span>'
        f'<span class="reception-status">{esc(entry.get("review_status", ""))}</span>'
        '</div>'
    )
    meta = (
        '<p class="reception-meta">'
        + " · ".join(part for part in (
            esc(entry.get("platform", "")),
            esc(authors),
            esc(date_label),
        ) if part)
        + "</p>"
    )
    points = entry.get("key_points", [])
    point_list = ""
    if points:
        point_list = "<ul>" + "".join(f"<li>{text_with_links(point)}</li>" for point in points) + "</ul>"

    relations = (
        '<p class="reception-meta"><strong>Relation:</strong> '
        f'{esc(entry.get("relation_to_work", "not-classified"))}'
        ' · <strong>Implementation:</strong> '
        f'{esc(entry.get("implementation_status", "not-claimed"))}</p>'
    )
    citation_status = entry.get("citation_status")
    citation_line = ""
    if citation_status:
        citation_line = (
            '<p class="reception-meta"><strong>Citation status:</strong> '
            f'{esc(citation_status)}</p>'
        )

    target_links = []
    for work_id in entry.get("target_work_ids", []):
        work = works.get(work_id)
        if work:
            target_links.append(anchor(work.get("title", work_id), work["url"]))
    target_line = ""
    if target_links:
        target_line = '<p class="reception-meta"><strong>Related work:</strong> ' + " · ".join(target_links) + "</p>"

    cited = entry.get("cited_sources", [])
    cited_line = ""
    if cited:
        links = [anchor(source.get("title", source["url"]), source["url"])
                 for source in cited if source.get("url")]
        if links:
            cited_line = '<p class="reception-meta">Source links: ' + " · ".join(links) + "</p>"

    evidence = entry.get("evidence_sources", [])
    evidence_line = ""
    if evidence:
        links = [anchor(source.get("title", source["url"]), source["url"])
                 for source in evidence if source.get("url")]
        if links:
            evidence_line = '<p class="reception-meta">Evidence and provenance: ' + " · ".join(links) + "</p>"

    archive_line = ""
    archive = entry.get("archive", {})
    archive_links = []
    if archive.get("direct_view_url"):
        archive_links.append(anchor("Direct archive view", archive["direct_view_url"]))
    if archive.get("snapshot_url"):
        archive_links.append(anchor("Archive snapshot", archive["snapshot_url"]))
    if archive_links:
        archive_line = '<p class="reception-meta">' + " · ".join(archive_links) + "</p>"

    discussion_line = ""
    discussion = entry.get("discussion", {})
    if discussion:
        count = discussion.get("comment_count")
        count_label = "comment count not recorded" if count is None else f'{count} comments'
        capture = discussion.get("capture_scope", "")
        basis = discussion.get("count_basis", "")
        detail = " · ".join(part for part in (basis, capture) if part)
        discussion_line = (
            '<p class="reception-meta"><strong>Discussion:</strong> '
            f'{esc(count_label)}'
            + (f'; {esc(detail)}' if detail else "")
            + "</p>"
        )

    related_line = ""
    related = entry.get("related_entry_ids", [])
    if related:
        related_links = []
        titles = {item["id"]: item["title"] for item in registry_entries_cache}
        for related_id in related:
            title = titles.get(related_id, related_id)
            related_links.append(f'<a href="#{esc(related_id)}">{esc(title)}</a>')
        related_line = '<p class="reception-meta"><strong>Related context:</strong> ' + " · ".join(related_links) + "</p>"

    notes_line = ""
    if entry.get("notes"):
        notes_line = f'<p class="reception-meta">{text_with_links(entry["notes"])}</p>'

    return (
        f'<article class="reception-card" id="{esc(entry["id"])}" data-reception-id="{esc(entry["id"])}">'
        + top
        + f'<h3><a href="{esc(entry["url"])}" target="_blank" rel="noopener noreferrer">{esc(entry["title"])}</a></h3>'
        + meta
        + f'<p>{text_with_links(entry.get("summary", ""))}</p>'
        + point_list
        + relations
        + citation_line
        + target_line
        + cited_line
        + evidence_line
        + discussion_line
        + related_line
        + archive_line
        + notes_line
        + "</article>"
    )


registry_entries_cache: list[dict] = []


def render_reception_html(registry: dict) -> str:
    global registry_entries_cache
    registry_entries_cache = registry.get("entries", [])
    works = {item["id"]: item for item in registry.get("target_works", [])}
    source = read_text(RECEPTION_HTML)

    source = replace_once(
        source,
        r'<script type="application/ld\+json">.*?</script>',
        render_reception_jsonld(registry),
        "External Reception JSON-LD",
    )

    entries = registry.get("entries", [])
    commit_boundary_count = sum(
        "commit-boundary-paper" in entry.get("target_work_ids", []) for entry in entries
    )
    agent_discussion_count = sum(
        entry.get("category") in {"agent-discussion", "adjacent-community-discussion"}
        for entry in entries
    )
    metrics = (
        '<div class="page-hero-metrics">'
        f'<div class="page-hero-stat"><strong>{len(entries)}</strong><span>registry records</span></div>'
        f'<div class="page-hero-stat"><strong>{commit_boundary_count}</strong><span>Commit Boundary records</span></div>'
        f'<div class="page-hero-stat"><strong>{agent_discussion_count}</strong><span>agent / community discussions</span></div>'
        '</div></header>'
    )
    source = replace_once(
        source,
        r'<div class="page-hero-metrics">.*?</div></header>',
        metrics,
        "External Reception hero metrics",
    )

    category_counts = {
        category["id"]: sum(entry.get("category") == category["id"] for entry in entries)
        for category in registry.get("categories", [])
    }
    nav = '<nav class="reception-filter" aria-label="Reception categories">'
    for category in registry.get("categories", []):
        count = category_counts.get(category["id"], 0)
        if count:
            nav += (
                f'<a class="tag" href="#category-{esc(category["id"])}">'
                f'{esc(category["label"])} ({count})</a>\n'
            )
    nav += "</nav>"
    source = replace_once(
        source,
        r'<nav class="reception-filter"[^>]*>.*?</nav>',
        nav,
        "External Reception category navigation",
    )

    sections = []
    for category in registry.get("categories", []):
        category_entries = [
            entry for entry in entries if entry.get("category") == category["id"]
        ]
        if not category_entries:
            continue
        cards = "".join(render_reception_card(entry, works) for entry in category_entries)
        sections.append(
            f'<section class="reception-section" id="category-{esc(category["id"])}">'
            f'<h2>{esc(category["label"])} <span class="tag">{len(category_entries)}</span></h2>'
            f'<p class="reception-intro">{esc(category.get("description", ""))}</p>'
            f'<div class="reception-grid">{cards}</div></section>'
        )
    generated_sections = "\n".join(sections)

    start = source.find('<section class="reception-section"')
    body_end = source.rfind("</body>")
    end = source.rfind("</section>", start, body_end) + len("</section>")
    if start < 0 or end < len("</section>"):
        raise ValueError("Could not locate External Reception generated category sections")
    source = source[:start] + generated_sections + source[end:]
    return source


def render_reception_turtle(registry: dict) -> str:
    graph = Graph()
    graph.bind("cito", CITO)
    graph.bind("dcterms", DCTERMS)
    graph.bind("rdfs", RDFS)
    graph.bind("schema", SCHEMA)
    graph.bind("xsd", XSD)

    page = URIRef(RECEPTION_URI)
    graph.add((page, RDF.type, SCHEMA.CollectionPage))
    graph.add((page, SCHEMA.name, Literal(registry.get("title", "DIO/ODI External Reception"), lang="en")))
    graph.add((page, SCHEMA.url, page))

    works = {item["id"]: item for item in registry.get("target_works", [])}
    mapping = URIRef(POLICY_MAPPING_URI)
    graph.add((mapping, RDFS.seeAlso, page))

    for entry in registry.get("entries", []):
        subject = URIRef(f'{RECEPTION_URI}#{entry["id"]}')
        graph.add((page, SCHEMA.hasPart, subject))
        graph.add((subject, RDF.type, SCHEMA.CreativeWork))
        graph.add((subject, SCHEMA.name, Literal(entry["title"], lang="en")))
        graph.add((subject, SCHEMA.url, URIRef(entry["url"])))
        graph.add((subject, SCHEMA.genre, Literal(entry["category"])))
        graph.add((subject, SCHEMA.description, Literal(entry.get("summary", ""), lang="en")))

        publication_date = entry.get("publication", {}).get("date")
        if publication_date:
            graph.add((subject, SCHEMA.datePublished,
                       Literal(publication_date, datatype=XSD.date)))

        for work_id in entry.get("target_work_ids", []):
            work = works.get(work_id)
            if work and work.get("url"):
                graph.add((subject, SCHEMA.about, URIRef(work["url"])))
            if work_id == "commit-boundary-paper":
                graph.add((mapping, RDFS.seeAlso, subject))

        for citation in entry.get("cited_sources", []):
            if citation.get("url"):
                graph.add((subject, CITO.cites, URIRef(citation["url"])))
        for evidence in entry.get("evidence_sources", []):
            if evidence.get("url"):
                graph.add((subject, DCTERMS.source, URIRef(evidence["url"])))

    return graph.serialize(format="turtle")


def render_scf_event(event: dict) -> str:
    event_id = event.get("id", "")
    event_class = event.get("event_class", "")
    components = [scope.get("component", "") for scope in event.get("scope", [])]
    component_ids = sorted({slugify(value) for value in components if value})
    scope_text = " · ".join(value for value in components if value) or "Not specified"
    event_date = event.get("date", "")
    display_date = format_date(event_date)
    date_basis = DATE_BASIS_LABELS.get(event.get("date_basis", ""), event.get("date_basis", ""))
    summary = text_with_links(event.get("summary", ""))

    html_parts = [
        f'<article class="scf-event" id="{esc(event_id)}" data-event-id="{esc(event_id)}" '
        f'data-event-class="{esc(event_class)}" data-event-date="{esc(event_date)}" '
        f'data-components="{esc(" ".join(component_ids))}">',
        '<div class="event-top"><div>',
        f'<p class="event-id">{esc(event_id)}</p>',
        f'<h2>{esc(event.get("title", ""))}</h2>',
        f'</div><span class="event-class">{esc(event_class)}</span></div>',
        f'<p class="event-summary">{summary}</p>',
        '<div class="event-meta">',
        f'<span><strong>Date</strong> <time datetime="{esc(event_date)}">{esc(display_date)}</time></span>',
        f'<span><strong>Change</strong> {esc(event.get("change_type", ""))}</span>',
        f'<span><strong>Date basis</strong> {esc(date_basis)}</span>',
        '</div>',
        f'<div class="event-scope"><strong>Scope</strong><span>{text_with_links(scope_text)}</span></div>',
        '<div class="before-after">',
        f'<section><h3>Previous state</h3><p>{text_with_links(event.get("before", ""))}</p></section>',
        f'<section><h3>Resulting state</h3><p>{text_with_links(event.get("after", ""))}</p></section>',
        '</div>',
    ]

    invariants = event.get("preserved_invariants", [])
    if invariants:
        html_parts.append(
            '<section class="preserved"><h3>Preserved invariants</h3><ul>'
            + "".join(f"<li>{text_with_links(item)}</li>" for item in invariants)
            + "</ul></section>"
        )

    impact = event.get("impact", {})
    impact_parts = [
        impact.get("level", ""),
        impact.get("compatibility", ""),
    ]
    impact_label = " · ".join(part for part in impact_parts if part)
    impact_notes = impact.get("notes", "")
    if impact_label or impact_notes:
        html_parts.append(
            '<p class="impact"><strong>Impact</strong> '
            + esc(impact_label)
            + ("<br>" + text_with_links(impact_notes) if impact_notes else "")
            + "</p>"
        )

    evidence = event.get("evidence", {})
    sources = evidence.get("sources", [])
    source_list = "".join(
        "<li>"
        + anchor(source.get("label", source.get("url", "")), source["url"])
        + f'<span class="source-role">{esc(source.get("role", ""))}</span></li>'
        for source in sources if source.get("url")
    )
    if evidence or sources:
        status = evidence.get("status", "not-stated")
        html_parts.append(
            '<details class="evidence"><summary>'
            f'Evidence and provenance ({len(sources)} sources · {esc(status)})'
            '</summary>'
            + (f"<ul>{source_list}</ul>" if source_list else "")
            + (f'<p>{text_with_links(evidence.get("temporal_note", ""))}</p>'
               if evidence.get("temporal_note") else "")
            + "</details>"
        )

    lineage = event.get("lineage", {})
    lineage_items = []
    for relation, label in (
        ("related_to", "Related"),
        ("supersedes", "Supersedes"),
        ("corrects", "Corrects"),
    ):
        for target in lineage.get(relation, []):
            lineage_items.append(
                f'<span>{esc(label)}: <a href="#{esc(target)}">{esc(target)}</a></span>'
            )
    if lineage_items:
        html_parts.append('<p class="event-lineage">' + " · ".join(lineage_items) + "</p>")

    html_parts.append("</article>")
    return "".join(html_parts)


def render_scf_html(feed: dict) -> str:
    source = read_text(SCF_HTML)
    events = feed.get("events", [])
    if not events:
        raise ValueError("Semantic Change Feed cannot render an empty event list")

    ordered = sorted(events, key=lambda item: item.get("date", ""))
    first_date = format_date(ordered[0]["date"])
    last_date = format_date(ordered[-1]["date"])
    metrics = (
        '<div class="page-hero-metrics">'
        f'<div class="page-hero-stat"><strong>{esc(first_date)}</strong><span>earliest Changelog milestone</span></div>'
        f'<div class="page-hero-stat"><strong>{esc(last_date)}</strong><span>latest chronology entry</span></div>'
        '</div></header>'
    )
    source = replace_once(
        source,
        r'<div class="page-hero-metrics">.*?</div></header>',
        metrics,
        "SCF hero chronology dates",
    )

    event_classes = sorted({event.get("event_class", "") for event in events if event.get("event_class")})
    class_options = '<option value="">All classes</option>' + "".join(
        f'<option value="{esc(value)}">{esc(value)}</option>' for value in event_classes
    )
    source = replace_once(
        source,
        r'(<label for="scf-class">Change class<select id="scf-class">).*?(</select></label>)',
        lambda_match_placeholder(class_options),
        "SCF class filter options",
    )

    components = {}
    for event in events:
        for scope in event.get("scope", []):
            component = scope.get("component", "")
            if component:
                components[slugify(component)] = component
    component_options = '<option value="">All components</option>' + "".join(
        f'<option value="{esc(component_id)}">{esc(label)}</option>'
        for component_id, label in sorted(components.items(), key=lambda item: item[1].casefold())
    )
    source = replace_once(
        source,
        r'(<label for="scf-component">Affected component<select id="scf-component">).*?(</select></label>)',
        lambda_match_placeholder(component_options),
        "SCF component filter options",
    )

    rendered_events = "".join(
        render_scf_event(event) for event in sorted(events, key=lambda item: item.get("date", ""), reverse=True)
    )
    source = replace_once(
        source,
        r'(<div class="event-list" id="scf-event-list">).*?(</div><p class="empty")',
        lambda_match_placeholder(rendered_events),
        "SCF event cards",
    )

    # The prose remains editorially maintained; only its current coverage date is derived.
    source, count = re.subn(
        r"through \d{1,2} [A-Za-z]+ \d{4}",
        f"through {last_date}",
        source,
        count=1,
    )
    if count != 1:
        raise ValueError("Could not update the SCF frontend coverage date")
    return source


def lambda_match_placeholder(replacement: str):
    """Build a replacement callback that preserves two regex capture groups."""
    def _replace(match):
        return match.group(1) + replacement + match.group(2)
    return _replace


def version_sort_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", version))


def release_doi_url(release: dict) -> str:
    doi = release.get("doi", "")
    return "https://doi.org/" + doi if doi else ""


def archived_release_record(release: dict) -> dict:
    return {
        "version": release["version"],
        "doi": release["doi"],
        "doi_url": release_doi_url(release),
        **({"publication_date": release["publication_date"]} if release.get("publication_date") else {}),
    }


def vocabulary_version() -> str:
    graph = Graph()
    graph.parse(ROOT / "vocabulary/dio-odi-skos.ttl", format="turtle")
    scheme = URIRef("https://vocab.danielberanek.cz/dio-odi/#ReferenceVocabulary")
    version = graph.value(scheme, URIRef("http://www.w3.org/2002/07/owl#versionInfo"))
    if version is None:
        raise ValueError("Canonical SKOS vocabulary is missing owl:versionInfo")
    return str(version)


def render_llms_versions(model: dict, live_vocabulary_version: str) -> str:
    releases = sorted(
        model.get("releases", []),
        key=lambda item: version_sort_key(item["version"]),
        reverse=True,
    )
    current = model["current_release"]
    previous = model.get("previous_archived_release", {})
    lines = [
        "## Versions",
        "",
        f"- Current archived Reference Model release: {current['version']} — {release_doi_url(current)}",
    ]
    if previous.get("version") and previous.get("doi"):
        lines.append(
            f"- Previous archived Reference Model release: {previous['version']} — {release_doi_url(previous)}"
        )
    lines.append(f"- Live Reference Vocabulary: {live_vocabulary_version}")
    if current.get("reference_vocabulary_version"):
        lines.append(
            f"- Vocabulary included in archived v{current['version']}: {current['reference_vocabulary_version']}"
        )
    if previous.get("version"):
        previous_release = next(
            (item for item in releases if item.get("version") == previous["version"]), {}
        )
        if previous_release.get("reference_vocabulary_version"):
            lines.append(
                f"- Vocabulary included in previous archived v{previous['version']}: "
                f"{previous_release['reference_vocabulary_version']}"
            )
    seen_vocabulary_versions = {
        current.get("reference_vocabulary_version"),
        next((item.get("reference_vocabulary_version") for item in releases
              if item.get("version") == previous.get("version")), None),
    }
    for release in releases:
        value = release.get("reference_vocabulary_version")
        if value and value not in seen_vocabulary_versions:
            lines.append(f"- Vocabulary included in archived v{release['version']}: {value}")
            seen_vocabulary_versions.add(value)
    for release in releases:
        if release.get("version") in {current.get("version"), previous.get("version")}:
            continue
        if release.get("doi"):
            lines.append(
                f"- Earlier archived release: v{release['version']} — {release_doi_url(release)}"
            )
    return "\n".join(lines) + "\n"


def render_llms_mcp(mcp: dict) -> str:
    lines = [
        "## Agent-facing MCP distribution",
        "",
        f"- DIO/ODI MCP v{mcp['version']}: {release_doi_url({'doi': mcp['version_doi']})}",
        f"- MCP Concept DOI (all versions): {release_doi_url({'doi': mcp['concept_doi']})}",
        f"- Public Streamable HTTP endpoint: {mcp['endpoint']}",
        f"- Health endpoint: {mcp['health_endpoint']}",
        f"- Source repository: {mcp['repository']}",
        f"- Scope: {mcp['note']}",
        "",
        "## Related Agentic ER planning product",
        "",
        "Agentic Entity Resolution Guardrail Planner is a separate published design-time Agent Skill. It prepares reviewable engineering plans for identity-changing operations; it does not execute mutations, authorize production writes, or deploy a runtime guard.",
        f"- Agensi listing: {AGENSI_PLANNER_URL}",
        f"- Product source repository: {PLANNER_SOURCE_REPOSITORY}",
    ]
    return "\n".join(lines) + "\n"


def render_metadata_projection(
    metadata: dict,
    feed: dict,
    works: dict,
    keywords: dict,
    mappings: dict,
    live_vocabulary_version: str,
) -> dict:
    model = next(item for item in works["works"] if item.get("id") == "reference-model")
    mcp = next(item for item in works["works"] if item.get("id") == "mcp-server")
    taxonomic = next(item for item in works["works"] if item.get("id") == "taxonomic-note")
    current = model["current_release"]
    previous = model.get("previous_archived_release", {})
    history = [
        archived_release_record(release)
        for release in sorted(
            model.get("releases", []),
            key=lambda item: version_sort_key(item["version"]),
            reverse=True,
        )
        if release.get("doi")
    ]

    metadata["title"] = model["title"]
    metadata["site_homepage"] = model["site_homepage"]
    metadata["vocabulary_landing_page"] = model["namespace_document"]
    metadata["version"] = current["version"]
    metadata["status"] = current.get("status", "archived")
    metadata["namespace"] = model["canonical_namespace"]
    metadata["repository"] = model["repository"]
    metadata["license"] = model["license"]
    metadata["taxonomic_note_doi"] = taxonomic["version_doi"]
    metadata["author"] = {
        "name": works["author"]["name"],
        "orcid": works["author"]["orcid"],
        "affiliation": works["author"]["affiliation"],
        "email": works["author"]["email"],
    }
    metadata["reference_model_version"] = current["version"]
    metadata["reference_vocabulary_version"] = model["reference_vocabulary_version"]
    metadata["derived_application_mappings"] = mappings["mappings"]
    metadata["application_mappings_index"] = metadata["site_homepage"].rstrip("/") + "/mappings/"
    metadata["archive_status"] = current.get("status", "archived")
    metadata["previous_archived_release"] = archived_release_record(previous)
    metadata["archived_release_history"] = history
    metadata["current_release"] = {
        "version": current["version"],
        "archive_status": current.get("status", "archived"),
        "doi": current["doi"],
        "doi_url": release_doi_url(current),
        **({"publication_date": current["publication_date"]} if current.get("publication_date") else {}),
    }
    metadata["release_doi"] = current["doi"]
    metadata["release_doi_url"] = release_doi_url(current)
    metadata["current_archived_release"] = archived_release_record(current)
    metadata["current_archived_reference_vocabulary_version"] = current.get("reference_vocabulary_version")
    metadata["live_reference_vocabulary_version"] = live_vocabulary_version

    corpus = metadata.setdefault("corpus_metadata_registry", {})
    corpus.update({
        "guide": "metadata/README.md",
        "works": "metadata/works.json",
        "relations": "metadata/relations.json",
        "references": "metadata/references.json",
        "zenodo_projection": ".zenodo.json",
        "distributions": "metadata/distributions.json",
        "keywords": "metadata/keywords.json",
        "application_mappings": "metadata/application-mappings.json",
        "application_mappings_schema": "metadata/application-mappings.schema.json",
        "keyword_grammar_version": model.get("keyword_grammar_version", ""),
        "keyword_grammar_status": model.get("keyword_profile_status", ""),
    })

    metadata["mcp_server"] = {
        "title": mcp["title"],
        "version": mcp["version"],
        "version_doi": mcp["version_doi"],
        "version_doi_url": release_doi_url({"doi": mcp["version_doi"]}),
        "concept_doi": mcp["concept_doi"],
        "concept_doi_url": release_doi_url({"doi": mcp["concept_doi"]}),
        "repository": mcp["repository"],
        "endpoint": mcp["endpoint"],
        "health_endpoint": mcp["health_endpoint"],
        "access": mcp["access"],
        "license": mcp["license"],
        "embedded_content_license": mcp["embedded_content_license"],
        "relation": mcp["relation"],
        "note": mcp.get("note", ""),
    }

    feed_metadata = metadata.setdefault("semantic_change_feed", {})
    feed_metadata["feed_version"] = feed["feed_version"]
    feed_metadata["schema_version"] = feed["schema_version"]
    feed_metadata["coverage_through"] = feed["events"][-1]["date"]
    feed_metadata.pop("event_count", None)
    archived_snapshot = feed_metadata.setdefault("archived_snapshot", {})
    archived_snapshot.update({
        "reference_model_version": current["version"],
        "reference_model_doi": current["doi"],
        "feed_version": current["semantic_change_feed_version"],
        "schema_version": current["semantic_change_feed_schema_version"],
        "event_count": current["semantic_change_feed_event_count"],
        "coverage_through": current["semantic_change_feed_coverage_through"],
    })
    return metadata


def resolve_keyword_sequence(keywords: dict, profile: dict, profile_id: str) -> list[str]:
    chunk_order = keywords.get("export_policy", {}).get("chunk_order", [])
    source_chunks = keywords.get("chunks", {})
    selections = profile.get("chunks", {})
    resolved: list[str] = []
    seen: set[str] = set()

    for chunk_name in chunk_order:
        if chunk_name not in source_chunks or chunk_name not in selections:
            raise ValueError(f"{profile_id}: missing chunk or selector for {chunk_name}")
        source_terms = source_chunks[chunk_name].get("terms", [])
        selected = selections[chunk_name]
        if selected == "all":
            terms = source_terms
        elif selected == "none":
            terms = []
        elif isinstance(selected, list):
            terms = selected
            if chunk_name != "C2_work_positioning":
                positions = [source_terms.index(term) if term in source_terms else -1 for term in terms]
                if -1 in positions:
                    raise ValueError(f"{profile_id}: unknown term in {chunk_name}")
                if positions != sorted(positions) or len(set(terms)) != len(terms):
                    raise ValueError(f"{profile_id}: {chunk_name} terms must preserve canonical order and be unique")
        else:
            raise ValueError(f"{profile_id}: invalid selector for {chunk_name}")

        for term in terms:
            folded = term.casefold()
            if folded not in seen:
                seen.add(folded)
                resolved.append(term)

    return resolved


def validate_keyword_registry(keywords: dict) -> None:
    c1_name = "C1_reconstruction_environments"
    c1_terms = keywords.get("chunks", {}).get(c1_name, {}).get("terms", [])
    if not c1_terms:
        raise ValueError("C1 reconstruction-environment candidate pool is empty")

    profiles = keywords.get("work_profiles", {})
    for profile_id, profile in profiles.items():
        chunks = profile.get("chunks", {})
        c1 = chunks.get(c1_name)
        if not isinstance(c1, list):
            raise ValueError(f"{profile_id}: C1 must be an explicit ordered selection, not 'all'")
        rationales = profile.get("term_rationales", {})
        if set(rationales) != set(c1):
            raise ValueError(f"{profile_id}: C1 term rationales must match the selected C1 terms exactly")
        calculated = resolve_keyword_sequence(keywords, profile, profile_id)
        if calculated != profile.get("resolved_keywords"):
            raise ValueError(f"{profile_id}: resolved_keywords does not match the ordered chunk projection")

    surface_profiles = keywords.get("surface_profiles", {})
    if not surface_profiles:
        raise ValueError("No derived artefact surface profiles are defined")
    for profile_id, profile in surface_profiles.items():
        chunks = profile.get("chunks", {})
        if chunks.get("C0_identity_invariant") != "all":
            raise ValueError(f"{profile_id}: C0 must always be exported in full")
        c1 = chunks.get(c1_name)
        if not isinstance(c1, list):
            raise ValueError(f"{profile_id}: C1 must be an explicit ordered selection")
        rationales = profile.get("term_rationales", {})
        selected_terms = resolve_keyword_sequence(keywords, profile, profile_id)
        c0_terms = set(keywords["chunks"]["C0_identity_invariant"]["terms"])
        required_rationales = set(selected_terms) - c0_terms
        if set(rationales) != required_rationales:
            missing = sorted(required_rationales - set(rationales))
            extra = sorted(set(rationales) - required_rationales)
            raise ValueError(f"{profile_id}: term_rationales mismatch; missing={missing}; extra={extra}")
        if profile.get("status") != "canonical-approved":
            raise ValueError(f"{profile_id}: surface profile is not canonical-approved")
        if len(selected_terms) != len(set(term.casefold() for term in selected_terms)):
            raise ValueError(f"{profile_id}: duplicate terms in resolved projection")


def render_keyword_exports(
    zenodo: dict,
    citation_text: str,
    keywords: dict,
    model: dict,
    author: dict,
) -> tuple[dict, str]:
    profile_name = model["keyword_profile"]
    profile = keywords["work_profiles"][profile_name]["resolved_keywords"]
    if not keywords.get("export_policy", {}).get("complete_sequence_for_exportable_surfaces"):
        raise ValueError("Keyword registry does not authorize complete-sequence export")

    # A release candidate is the next export target; otherwise use the current archive.
    target = model.get("release_candidate") or model["current_release"]
    version = target["version"]
    doi = target.get("doi")
    family = author["family_names"]
    given = author["given_names"]
    person_orcid = "https://orcid.org/" + author["orcid"]

    zenodo["title"] = model["title"]
    zenodo["version"] = version
    zenodo["upload_type"] = "software" if model.get("type") == "software" else model.get("type")
    zenodo["license"] = model.get("license", "CC-BY-4.0").lower()
    zenodo["creators"] = [{
        "name": f"{family}, {given}",
        "orcid": author["orcid"],
        "affiliation": author.get("affiliation", ""),
    }]
    zenodo["keywords"] = profile

    def replace_cff_scalar(key: str, value: str | None, *, required: bool = True) -> None:
        nonlocal citation_text
        pattern = rf"(?m)^{re.escape(key)}:.*(?:\n|$)"
        if value is None:
            citation_text, count = re.subn(pattern, "", citation_text, count=1)
        else:
            rendered = f"{key}: " + json.dumps(value, ensure_ascii=False) + "\n"
            citation_text, count = re.subn(pattern, lambda _match: rendered, citation_text, count=1)
        if required and count != 1:
            raise ValueError(f"CITATION.cff field could not be updated: {key}")

    replace_cff_scalar("title", model["title"])
    replace_cff_scalar("type", model.get("type", "software"))
    replace_cff_scalar("version", version)
    replace_cff_scalar("doi", doi, required=False)
    replace_cff_scalar("abstract", model["citation_abstract"])
    replace_cff_scalar("repository-code", model["repository"])
    replace_cff_scalar("license", model["license"])

    authors_block = (
        "authors:\n"
        f'  - family-names: {json.dumps(family, ensure_ascii=False)}\n'
        f'    given-names: {json.dumps(given, ensure_ascii=False)}\n'
        f'    orcid: {json.dumps(person_orcid, ensure_ascii=False)}\n'
        f'    affiliation: {json.dumps(author.get("affiliation", ""), ensure_ascii=False)}\n'
    )
    citation_text = replace_once(
        citation_text,
        r"(?m)^authors:\n.*?(?=^[A-Za-z][A-Za-z0-9_-]*:)",
        authors_block,
        "CITATION.cff authors",
    )

    keyword_lines = "keywords:\n" + "".join(
        "  - " + json.dumps(term, ensure_ascii=False) + "\n" for term in profile
    )
    citation_text = replace_once(
        citation_text,
        r"(?m)^keywords:\n(?:  - .*?(?:\n|$))+",
        keyword_lines,
        "CITATION.cff keyword sequence",
    )
    return zenodo, citation_text




def update_discovery_metadata(
    metadata: dict,
    feed: dict,
    works: dict,
    keywords: dict,
    mappings: dict,
    llms_text: str,
    live_vocabulary_version: str,
) -> tuple[dict, str]:
    model = next(item for item in works["works"] if item.get("id") == "reference-model")
    mcp = next(item for item in works["works"] if item.get("id") == "mcp-server")
    metadata = render_metadata_projection(
        metadata, feed, works, keywords, mappings, live_vocabulary_version
    )

    llms_text = replace_markdown_section(
        llms_text,
        "## Versions",
        "## Referenced research works",
        render_llms_versions(model, live_vocabulary_version),
        "llms.txt archived release and vocabulary versions",
    )
    llms_text = replace_markdown_section(
        llms_text,
        "## Agent-facing MCP distribution",
        "## Semantic Change Feed",
        render_llms_mcp(mcp),
        "llms.txt MCP distribution metadata",
    )

    releases_heading = re.search(r"(?m)^## Releases\s*$", llms_text)
    if releases_heading:
        next_heading = re.search(r"(?m)^## Source repository\s*$", llms_text[releases_heading.end():])
        if not next_heading:
            raise ValueError("Could not locate Source repository section after duplicate Releases block")
        remove_end = releases_heading.end() + next_heading.start()
        llms_text = llms_text[:releases_heading.start()] + llms_text[remove_end:]

    crisis = next(item for item in works["works"] if item.get("id") == "crisis-entity-resolution")
    current_version = next(
        (item for item in crisis.get("versions", [])
         if item.get("doi") == crisis.get("current_version_doi")),
        None,
    )
    if current_version:
        crisis_line = (
            f"- {crisis['title']} — current version {current_version['version']}: "
            f"https://doi.org/{current_version['doi']}"
        )
        llms_text = replace_line_with_prefix(
            llms_text,
            "- The Crisis of Entity Resolution in Heterogeneous AI Environments:",
            crisis_line,
            "llms.txt current Crisis of Entity Resolution version",
        )

    archived_snapshot = metadata["semantic_change_feed"]["archived_snapshot"]
    archived_date = format_date(archived_snapshot["coverage_through"])
    archived_label = (
        f"- Archived snapshot in Reference Model v{archived_snapshot['reference_model_version']}: "
        f"feed v{archived_snapshot['feed_version']}, schema v{archived_snapshot['schema_version']}, "
        f"{archived_snapshot['event_count']} events through {archived_date}"
    )
    llms_text = re.sub(
        r"(?m)^- Archived snapshot in Reference Model .*?$",
        lambda _match: archived_label,
        llms_text,
        count=1,
    )

    corpus = metadata["corpus_metadata_registry"]
    profiles = keywords.get("work_profiles", {})
    commit_profile = profiles.get("commit-boundary-paper", {}).get("resolved_keywords", [])
    mcp_profile = profiles.get("mcp-server", {}).get("resolved_keywords", [])
    if commit_profile:
        llms_text = re.sub(
            r"(?m)^  - Work-specific profile: commit-boundary-paper \(.*?\)$",
            f"  - Work-specific profile: commit-boundary-paper ({len(commit_profile)} terms; baseline aligned to Zenodo v1 metadata)",
            llms_text,
            count=1,
        )
    if mcp_profile:
        llms_text = re.sub(
            r"(?m)^  - Work-specific profile: mcp-server \(.*?\)$",
            f"  - Work-specific profile: mcp-server ({len(mcp_profile)} terms; approved in registry v{keywords['registry_version']})",
            llms_text,
            count=1,
        )
    llms_text = replace_line_with_prefix(
        llms_text,
        "  - Keyword registry version:",
        f"  - Keyword registry version: {keywords['registry_version']}",
        "llms.txt canonical keyword registry version",
    )
    llms_text = replace_line_with_prefix(
        llms_text,
        "- Canonical keyword registry:",
        "- Canonical keyword registry: https://vocab.danielberanek.cz/metadata/keywords.json\n"
        "- Page-level metadata manifest: https://vocab.danielberanek.cz/assets/data/resolved-page-metadata.json",
        "llms.txt page-level metadata manifest discovery",
    )
    return metadata, llms_text


def render_root_readme(
    source: str,
    model: dict,
    mcp: dict,
    live_vocabulary_version: str,
) -> str:
    current = model["current_release"]
    previous = model.get("previous_archived_release", {})
    top_lines = [
        f"**Current archived Reference Model release:** v{current['version']} — {release_doi_url(current)}",
    ]
    if previous.get("version") and previous.get("doi"):
        top_lines.append(
            f"**Previous archived Reference Model release:** v{previous['version']} — {release_doi_url(previous)}"
        )
    top_lines.append(f"**Live Reference Vocabulary:** v{live_vocabulary_version}")
    if current.get("reference_vocabulary_version"):
        top_lines.append(
            f"**Vocabulary included in archived v{current['version']}:** "
            f"{current['reference_vocabulary_version']}"
        )
    top_block = "\n".join(top_lines) + "\n\n"
    source = replace_once(
        source,
        r"(?m)(^# DIO/ODI Reference Model\n\n).*?(?=^\*\*Author:\*\*)",
        lambda match: match.group(1) + top_block,
        "Root README release metadata header",
    )

    release_lines = []
    sorted_releases = sorted(
        model.get("releases", []),
        key=lambda item: version_sort_key(item["version"]),
        reverse=True,
    )
    for index, release in enumerate(sorted_releases):
        if not release.get("doi"):
            continue
        label = "Current archived release" if index == 0 else (
            "Previous archived release" if release.get("version") == previous.get("version")
            else "Earlier archived release"
        )
        release_lines.append(
            f"**{label}:** DIO/ODI Reference Model v{release['version']} — {release_doi_url(release)}"
        )
    release_block = "\n\n".join(release_lines) + "\n\n"
    source = replace_once(
        source,
        r"(?m)(## Citation and archival release\n\n).*?(?=^A Reference Model release DOI identifies)",
        lambda match: match.group(1) + release_block,
        "Root README archival release history",
    )

    current_vocab = (
        f"The live Reference Vocabulary is v{live_vocabulary_version}. "
        f"The current archived Reference Model package is v{current['version']} "
        f"({release_doi_url(current)}); its predecessor is v{previous.get('version', '')} "
        f"({release_doi_url(previous)})."
    )
    source = replace_once(
        source,
        r"The live Reference Vocabulary is v.*?its predecessor is v[^ ]+ \(https://doi\.org/[^)]+\)\.",
        current_vocab,
        "Root README current vocabulary/release status",
    )

    mcp_section = (
        "## Agent-facing MCP distribution\n\n"
        f"The Reference Model is also exposed through a separate public, stateless, "
        f"read-only Model Context Protocol server. **DIO/ODI MCP v{mcp['version']}** "
        f"{mcp['note']}\n\n"
        f"- MCP endpoint: {mcp['endpoint']}\n"
        f"- Health endpoint: {mcp['health_endpoint']}\n"
        f"- Source repository: {mcp['repository']}\n"
        f"- Version DOI (v{mcp['version']}): {release_doi_url({'doi': mcp['version_doi']})}\n"
        f"- Concept DOI (all versions): {release_doi_url({'doi': mcp['concept_doi']})}\n\n"
        f"The MCP server is a separate derived software distribution. It does not alter "
        f"the canonical vocabulary or the immutable Reference Model v{current['version']} archive.\n\n"
        "## Related Agentic ER planning product\n\n"
        "Agentic Entity Resolution Guardrail Planner is a separate published design-time Agent Skill. It prepares reviewable engineering plans for identity-changing operations; it does not execute mutations, authorize production writes, or deploy a runtime guard.\n\n"
        f"- Agensi listing: {AGENSI_PLANNER_URL}\n"
        f"- Product source repository: {PLANNER_SOURCE_REPOSITORY}"
    )
    source = replace_once(
        source,
        r"## Agent-facing MCP distribution\n.*?(?=\n## Concept map)",
        mcp_section,
        "Root README MCP distribution metadata",
    )
    return source




def render_metadata_readme(source: str, works: dict) -> str:
    model = next(item for item in works["works"] if item.get("id") == "reference-model")
    mcp = next(item for item in works["works"] if item.get("id") == "mcp-server")
    current = model["current_release"]
    previous = model.get("previous_archived_release", {})

    mcp_paragraph = (
        f"The read-only MCP server is registered as the separate work `mcp-server` in `works.json`. "
        f"Its v{mcp['version']} version DOI is `{mcp['version_doi']}`; its Concept DOI is "
        f"`{mcp['concept_doi']}`. The server's recorded scope is: {mcp['note']} "
        f"Its registered relation is `{mcp['relation']}`. "
        f"Its implementation is licensed under {mcp['license']}; embedded DIO/ODI reference content "
        f"remains {mcp['embedded_content_license']}."
    )
    source = replace_markdown_section(
        source,
        "## DIO/ODI MCP software distribution",
        "## Reference Vocabulary identity and parent Reference Model DOI",
        "## DIO/ODI MCP software distribution\n\n" + mcp_paragraph,
        "Metadata README MCP work identity",
    )

    def scf_snapshot_line(release: dict) -> str:
        details = []
        if release.get("semantic_change_feed_version"):
            details.append(f"SCF v{release['semantic_change_feed_version']}")
        if release.get("semantic_change_feed_schema_version"):
            details.append(f"schema v{release['semantic_change_feed_schema_version']}")
        if release.get("semantic_change_feed_event_count") is not None:
            details.append(f"{release['semantic_change_feed_event_count']} events")
        if release.get("semantic_change_feed_coverage_through"):
            details.append(f"through {format_date(release['semantic_change_feed_coverage_through'])}")
        return ", ".join(details)

    status_note = model.get("reference_vocabulary_status_note", "").strip().rstrip(".")
    if status_note:
        status_note = status_note[0].lower() + status_note[1:]
    live_line = f"The live Reference Vocabulary is v{model['reference_vocabulary_version']}"
    if status_note:
        live_line += f" ({status_note})"
    live_line += "."
    current_line = (
        f"The current archived Reference Model v{current['version']} "
        f"(https://doi.org/{current['doi']}) contains Vocabulary "
        f"v{current['reference_vocabulary_version']} and {scf_snapshot_line(current)}."
    )
    previous_release = next(
        (item for item in model.get("releases", [])
         if item.get("version") == previous.get("version")),
        previous,
    )
    previous_line = ""
    if previous.get("version"):
        previous_line = (
            f"The previous archived Reference Model v{previous['version']} "
            f"(https://doi.org/{previous['doi']}) contains Vocabulary "
            f"v{previous_release.get('reference_vocabulary_version', 'not separately recorded')} "
            f"and {scf_snapshot_line(previous_release)}."
        )
    inclusions = model.get("reference_vocabulary_inclusion_history", [])
    inclusion_items = []
    for item in inclusions:
        inclusion_items.append(
            f"v{item['vocabulary_version']} was first included in archived Reference Model "
            f"v{item['reference_model_release_version']} "
            f"(https://doi.org/{item['reference_model_release_doi']})"
        )
    inclusion_line = (
        "First archival inclusion for each recorded vocabulary state is preserved in "
        "`reference_vocabulary_inclusion_history` in `works.json`: "
        + "; ".join(inclusion_items)
        + "."
    )
    identity_boundary = (
        "These DOI values identify the enclosing Reference Model archives, not separately "
        "archived Vocabulary packages. The Vocabulary has no separate version-specific "
        "Zenodo DOI; use its canonical ConceptScheme URI. The "
        "`reference-vocabulary-v0.2.0` entry in `references.json` provides the corresponding "
        "URI-based citation without assigning the parent model's DOI to the Vocabulary."
    )
    paragraph = " ".join(part for part in (
        live_line, current_line, previous_line, inclusion_line, identity_boundary
    ) if part)
    source = replace_once(
        source,
        r"The live Reference Vocabulary is v.*?parent model's DOI to the Vocabulary\.",
        paragraph,
        "Metadata README vocabulary and archived release status",
    )
    return source


def update_sitemap(sitemap_text: str, changed_paths: set[str], generated_date: str) -> str:
    """Advance sitemap lastmod only where Git history or generated content changed."""
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    try:
        tree = ET.fromstring(sitemap_text)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid sitemap XML: {exc}") from exc

    for url_node in tree.findall(".//sm:url", namespace):
        location = url_node.findtext("sm:loc", namespaces=namespace)
        lastmod_node = url_node.find("sm:lastmod", namespace)
        if not location or lastmod_node is None or not lastmod_node.text:
            continue

        parsed = urlparse(location)
        relative_path = unquote(parsed.path).lstrip("/")
        if not relative_path:
            relative_path = "index.html"
        elif relative_path.endswith("/"):
            relative_path += "index.html"

        source_path = ROOT / relative_path
        if not source_path.is_file():
            continue

        candidate_date = date.fromisoformat(lastmod_node.text)
        if relative_path in changed_paths:
            candidate_date = max(candidate_date, date.fromisoformat(generated_date))
        else:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%cI", "--", relative_path],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                commit_date = datetime.fromisoformat(result.stdout.strip()).astimezone(timezone.utc).date()
                candidate_date = max(candidate_date, commit_date)

        lastmod_node.text = candidate_date.isoformat()

    return ET.tostring(tree, encoding="unicode", xml_declaration=True) + "\n"


def build_outputs() -> dict[str, str]:
    registry = load_json(RECEPTION_JSON)
    feed = load_json(SCF_JSON)
    feed["event_count"] = len(feed.get("events", []))
    works = load_json(WORKS_JSON)
    keywords = load_json(KEYWORDS_JSON)
    validate_keyword_registry(keywords)
    mappings = load_json("metadata/application-mappings.json")
    metadata = load_json(METADATA_JSON)
    llms_text = read_text(LLMS_TXT)
    live_vocab_version = vocabulary_version()
    model = next(item for item in works["works"] if item.get("id") == "reference-model")
    mcp = next(item for item in works["works"] if item.get("id") == "mcp-server")

    outputs = {
        RECEPTION_HTML: render_reception_html(registry),
        RECEPTION_TTL: render_reception_turtle(registry),
        SCF_JSON: dump_json(feed),
        SCF_HTML: render_scf_html(feed),
    }

    metadata, llms_text = update_discovery_metadata(
        metadata, feed, works, keywords, mappings, llms_text, live_vocab_version
    )
    outputs[METADATA_JSON] = dump_json(metadata)
    outputs[LLMS_TXT] = llms_text

    zenodo = load_json(".zenodo.json")
    citation_text = read_text("CITATION.cff")
    zenodo, citation_text = render_keyword_exports(
        zenodo, citation_text, keywords, model, works["author"]
    )
    outputs[".zenodo.json"] = dump_json(zenodo)
    outputs["CITATION.cff"] = citation_text

    root_readme = render_root_readme(
        read_text(ROOT_README), model, mcp, live_vocab_version
    )
    generic_scf_summary = (
        "The [Semantic Change Feed](https://vocab.danielberanek.cz/semantic-change-feed/) "
        "records documented semantic, structural, provenance, mapping, deployment, and "
        "artifact-state changes across the reference system. Its event registry is "
        "append-only and separate from the current component authorities. Archived "
        "Reference Model releases retain the feed and schema versions included in each "
        "immutable package. The live feed advances independently, recording later "
        "SPARQL, archive-reconciliation, MCP, external registry, and Agentic ER product-publication milestones. These "
        "are live maintenance updates only: archived packages remain immutable and no "
        "new Reference Model release is created. SCF is a Reference Model component, "
        "not a separately DOI-identified work."
    )
    root_readme = replace_once(
        root_readme,
        r"The \[Semantic Change Feed\].*?not a separately DOI-identified work\.",
        generic_scf_summary,
        "Root README SCF summary",
    )
    outputs[ROOT_README] = root_readme
    outputs["metadata/README.md"] = render_metadata_readme(
        read_text("metadata/README.md"), works
    )

    scf_readme = read_text(SCF_README)
    scf_readme = re.sub(
        r"(?m)^\*\*Feed version:\*\* .*?$",
        f"**Feed version:** {feed['feed_version']}  ",
        scf_readme,
        count=1,
    )
    scf_readme = re.sub(
        r"(?m)^\*\*Schema version:\*\* .*?$",
        f"**Schema version:** {feed['schema_version']}  ",
        scf_readme,
        count=1,
    )
    scf_readme = re.sub(
        r"(?m)^Version \d+\.\d+\.\d+ is the current live feed and covers:$",
        f"Version {feed['feed_version']} is the current live feed and covers:",
        scf_readme,
        count=1,
    )
    archived = next(item for item in works["works"] if item.get("id") == "reference-model")["current_release"]
    archive_date = format_date(archived["semantic_change_feed_coverage_through"])
    archived_label = (
        f"The archived Reference Model v{archived['version']} "
        f"(https://doi.org/{archived['doi']}) contains SCF v{archived['semantic_change_feed_version']} "
        f"with {archived['semantic_change_feed_event_count']} events and schema "
        f"v{archived['semantic_change_feed_schema_version']} through {archive_date}. The live feed now advances "
        f"independently to v{feed['feed_version']} with schema v{feed['schema_version']}."
    )
    scf_readme = replace_once(
        scf_readme,
        r"The archived Reference Model v.*?The archive-reconciliation records",
        archived_label + " The archive-reconciliation records",
        "SCF README live and archived version summary",
    )
    outputs[SCF_README] = scf_readme

    changed_paths = {
        path for path, content in outputs.items()
        if read_text(path) != content
    }
    today = datetime.now(timezone.utc).date().isoformat()
    sitemap_text = update_sitemap(read_text(SITEMAP), changed_paths, today)
    if read_text(SITEMAP) != sitemap_text:
        outputs[SITEMAP] = sitemap_text
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Fail if generated projections are stale; do not write files.")
    mode.add_argument("--write", action="store_true", help="Write generated projections (the default).")
    args = parser.parse_args()

    try:
        outputs = build_outputs()
        stale = []
        for relative, content in outputs.items():
            path = ROOT / relative
            current = path.read_text(encoding="utf-8") if path.is_file() else None
            if current != content:
                stale.append(relative)
                if not args.check:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content, encoding="utf-8", newline="\n")
        if args.check and stale:
            print("Generated projections are stale:", file=sys.stderr)
            for relative in stale:
                print(f"- {relative}", file=sys.stderr)
            return 1
        if not args.check:
            print("Generated DIO/ODI projections are up to date.")
            if stale:
                print("Updated:")
                for relative in stale:
                    print(f"- {relative}")
        else:
            print("Generated DIO/ODI projections are up to date.")
        return 0
    except Exception as exc:
        print(f"PROJECTION GENERATION FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

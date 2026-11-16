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
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

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
    updated, count = re.subn(pattern, lambda _match: replacement, source, count=1, flags=re.S)
    if count != 1:
        raise ValueError(f"Could not locate exactly one generated region: {label}")
    return updated


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


def update_discovery_metadata(
    metadata: dict,
    feed: dict,
    works: dict,
    keywords: dict,
    llms_text: str,
) -> tuple[dict, str]:
    feed_meta = metadata.setdefault("semantic_change_feed", {})
    feed_meta["feed_version"] = feed["feed_version"]
    feed_meta["schema_version"] = feed["schema_version"]
    feed_meta["coverage_through"] = feed["events"][-1]["date"]
    feed_meta.pop("event_count", None)

    model = next(item for item in works["works"] if item.get("id") == "reference-model")
    archived = model["current_release"]
    archive_date = format_date(archived.get("publication_date"))

    llms_text = re.sub(
        r"(?m)^- Feed version: .*?$",
        "- Feed version: " + feed["feed_version"]
        + "; current live append-only structured history, first published as v0.1.0, "
          "with explicit date basis, preserved invariants, impact, provenance, and lineage",
        llms_text,
        count=1,
    )
    llms_text = re.sub(
        r"(?m)^- Live JSON Schema version: .*?$",
        "- Live JSON Schema version: " + feed["schema_version"],
        llms_text,
        count=1,
    )
    archived_line = (
        f"- Archived snapshot in Reference Model v{archived['version']}: "
        f"feed v{archived['semantic_change_feed_version']}, "
        f"schema v{archived['semantic_change_feed_schema_version']}, "
        f"{archived['semantic_change_feed_event_count']} events through {archive_date}"
    )
    llms_text = re.sub(
        r"(?m)^- Archived snapshot in Reference Model .*?$",
        lambda _match: archived_line,
        llms_text,
        count=1,
    )
    coverage_line = re.search(r"(?m)^- Current coverage: (.*?)$", llms_text)
    if not coverage_line:
        raise ValueError("llms.txt is missing its current coverage line")
    current_coverage = coverage_line.group(1)
    current_coverage = re.sub(
        r"through \d{1,2} [A-Za-z]+ \d{4}$",
        f"through {format_date(feed['events'][-1]['date'])}",
        current_coverage,
    )
    if re.search(r"\b\d+\s+events?\b", current_coverage, re.IGNORECASE):
        raise ValueError("llms.txt current coverage must not repeat the live event count")
    llms_text = (
        llms_text[:coverage_line.start(1)]
        + current_coverage
        + llms_text[coverage_line.end(1):]
    )

    # Keep the keyword registry projection current without maintaining its versions by hand.
    corpus = metadata.get("corpus_metadata_registry", {})
    corpus["keyword_grammar_version"] = keywords.get("grammar_version", corpus.get("keyword_grammar_version", ""))
    mcp_profile = keywords.get("work_profiles", {}).get("mcp-server", {}).get("resolved_keywords", [])
    llms_text = re.sub(
        r"(?m)^  - Keyword registry version: .*?$",
        "  - Keyword registry version: " + keywords["registry_version"],
        llms_text,
        count=1,
    )
    llms_text = re.sub(
        r"(?m)^  - Grammar version: .*?$",
        "  - Grammar version: " + str(corpus.get("keyword_grammar_version", "")),
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
    return metadata, llms_text


def update_sitemap(sitemap_text: str, changed_paths: set[str], generated_date: str) -> str:
    url_by_path = {
        RECEPTION_HTML: "https://vocab.danielberanek.cz/external-reception/",
        RECEPTION_TTL: "https://vocab.danielberanek.cz/metadata/external-reception.ttl",
        SCF_HTML: "https://vocab.danielberanek.cz/semantic-change-feed/",
        METADATA_JSON: "https://vocab.danielberanek.cz/metadata.json",
    }
    for path in changed_paths:
        url = url_by_path.get(path)
        if not url:
            continue
        escaped_url = re.escape(url)
        pattern = (
            r"(<loc>" + escaped_url + r"</loc>\s*<lastmod>)[^<]+(</lastmod>)"
        )
        sitemap_text, count = re.subn(
            pattern,
            lambda match: match.group(1) + generated_date + match.group(2),
            sitemap_text,
            count=1,
        )
        if count != 1:
            raise ValueError(f"Sitemap is missing the changed generated resource: {url}")
    return sitemap_text


def build_outputs() -> dict[str, str]:
    registry = load_json(RECEPTION_JSON)
    feed = load_json(SCF_JSON)
    works = load_json(WORKS_JSON)
    keywords = load_json(KEYWORDS_JSON)
    metadata = load_json(METADATA_JSON)
    llms_text = read_text(LLMS_TXT)

    outputs = {
        RECEPTION_HTML: render_reception_html(registry),
        RECEPTION_TTL: render_reception_turtle(registry),
        SCF_HTML: render_scf_html(feed),
    }

    metadata, llms_text = update_discovery_metadata(metadata, feed, works, keywords, llms_text)
    outputs[METADATA_JSON] = dump_json(metadata)
    outputs[LLMS_TXT] = llms_text

    # Version and schema values are authoritative in events.json; documentation
    # should not need a separate hand edit after a normal feed update.
    root_readme = read_text(ROOT_README)
    generic_scf_summary = (
        "The [Semantic Change Feed](https://vocab.danielberanek.cz/semantic-change-feed/) "
        "records documented semantic, structural, provenance, mapping, deployment, and "
        "artifact-state changes across the reference system. Its event registry is "
        "append-only and separate from the current component authorities. Archived "
        "Reference Model releases retain the feed and schema versions included in each "
        "immutable package. The live feed advances independently, recording later "
        "SPARQL, archive-reconciliation, MCP, and external registry milestones. These "
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
    archived_label = (
        f"The archived Reference Model v{archived['version']} "
        f"(https://doi.org/{archived['doi']}) contains SCF v{archived['semantic_change_feed_version']} "
        f"with {archived['semantic_change_feed_event_count']} events and schema "
        f"v{archived['semantic_change_feed_schema_version']}. The live feed now advances "
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
    if changed_paths:
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

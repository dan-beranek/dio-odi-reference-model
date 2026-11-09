#!/usr/bin/env python3
"""Deterministic integrity checks for the DIO/ODI Reference Model repository.

This validator checks source files and cross-representation constraints. It does
not claim semantic correctness of external application mappings or empirical
validation of the Agentic ER architecture.
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

import yaml
from jsonschema import validate as validate_json_schema
from rdflib import Graph, Namespace, RDF, URIRef
from rdflib.namespace import DCAT, DCTERMS, RDFS, SKOS


ROOT = Path(__file__).resolve().parents[1]
VOCAB_NS = "https://vocab.danielberanek.cz/dio-odi/#"
VOCABULARY_VERSION = "0.2.2"
VOCABULARY_PREFIX = "dio-odi"
ARC_NS = "https://vocab.danielberanek.cz/mappings/agentic-er-architecture/#"
SITE_HOST = "vocab.danielberanek.cz"
ARC = Namespace(ARC_NS)

MAPPING_BASES = {
    "rag-pipeline": {
        "md": "mappings/rag-pipeline-mapping.md",
        "jsonld": "mappings/rag-pipeline-mapping.jsonld",
        "ttl": "mappings/rag-pipeline-mapping.ttl",
        "html": "mappings/rag-pipeline/index.html",
    },
    "hem-dio": {
        "md": "mappings/hem-dio-mapping.md",
        "jsonld": "mappings/hem-dio-mapping.jsonld",
        "ttl": "mappings/hem-dio-mapping.ttl",
        "html": "mappings/hem-dio/index.html",
    },
    "commit-boundary-policy": {
        "md": "mappings/commit-boundary-policy-mapping.md",
        "jsonld": "mappings/commit-boundary-policy-mapping.jsonld",
        "ttl": "mappings/commit-boundary-policy-mapping.ttl",
        "html": "mappings/commit-boundary-policy/index.html",
    },
    "agentic-er": {
        "md": "mappings/agentic-er-commit-boundary-architecture-mapping.md",
        "jsonld": "mappings/agentic-er-commit-boundary-architecture-mapping.jsonld",
        "ttl": "mappings/agentic-er-commit-boundary-architecture-mapping.ttl",
        "html": "mappings/agentic-er-architecture/index.html",
    },
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_text(relative: str) -> str:
    path = ROOT / relative
    require(path.is_file(), f"Required file is missing: {relative}")
    return path.read_text(encoding="utf-8")


def load_json(relative: str):
    try:
        return json.loads(read_text(relative))
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Invalid JSON in {relative}: {exc}") from exc


def parse_turtle(relative: str) -> Graph:
    graph = Graph()
    try:
        graph.parse(ROOT / relative, format="turtle")
    except Exception as exc:
        raise AssertionError(f"Turtle parse failed for {relative}: {exc}") from exc
    require(len(graph) > 0, f"Parsed empty RDF graph: {relative}")
    return graph


def parse_jsonld(relative: str) -> Graph:
    graph = Graph()
    try:
        graph.parse(ROOT / relative, format="json-ld")
    except Exception as exc:
        raise AssertionError(f"JSON-LD parse failed for {relative}: {exc}") from exc
    require(len(graph) > 0, f"Parsed empty JSON-LD graph: {relative}")
    return graph


class HtmlAuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.jsonld_scripts: list[str] = []
        self._inside_jsonld = False
        self._script_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        for key in ("href", "src"):
            value = values.get(key)
            if value:
                self.links.append(value)
        if tag.lower() == "script" and values.get("type", "").lower() == "application/ld+json":
            self._inside_jsonld = True
            self._script_buffer = []

    def handle_startendtag(self, tag: str, attrs) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        if self._inside_jsonld:
            self._script_buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._inside_jsonld:
            self.jsonld_scripts.append("".join(self._script_buffer).strip())
            self._inside_jsonld = False
            self._script_buffer = []


def local_target(source_file: Path, raw_url: str) -> Path | None:
    value = raw_url.strip().strip("<>")
    if not value or value.startswith(("#", "data:", "mailto:", "tel:", "javascript:")):
        return None

    parsed = urlparse(value)
    if parsed.scheme and parsed.scheme not in ("http", "https"):
        return None
    if parsed.netloc and parsed.netloc.lower() != SITE_HOST:
        return None

    path_part = unquote(parsed.path)
    if not path_part:
        path_part = "/"

    if path_part.startswith("/"):
        candidate = (ROOT / path_part.lstrip("/")).resolve()
    else:
        candidate = (source_file.parent / path_part).resolve()

    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return None

    if candidate.is_dir():
        candidate = candidate / "index.html"
    return candidate


def check_local_links() -> int:
    checked = 0
    sources = sorted(
        list(ROOT.rglob("*.html"))
        + list(ROOT.rglob("*.md"))
    )
    markdown_link = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for source in sources:
        content = source.read_text(encoding="utf-8")
        links: list[str] = []
        if source.suffix.lower() == ".html":
            parser = HtmlAuditParser()
            parser.feed(content)
            parser.close()
            links.extend(parser.links)
        else:
            links.extend(match.group(1).split()[0] for match in markdown_link.finditer(content))

        for link in links:
            target = local_target(source, link)
            if target is None:
                continue
            checked += 1
            require(
                target.exists(),
                f"Broken local link in {source.relative_to(ROOT)}: {link} -> {target}",
            )
    return checked


def check_html_and_jsonld() -> tuple[int, int]:
    html_files = sorted(ROOT.rglob("*.html"))
    script_count = 0
    for path in html_files:
        source = path.relative_to(ROOT).as_posix()
        parser = HtmlAuditParser()
        try:
            parser.feed(path.read_text(encoding="utf-8"))
            parser.close()
        except Exception as exc:
            raise AssertionError(f"HTML parser failed for {source}: {exc}") from exc

        for index, payload in enumerate(parser.jsonld_scripts, start=1):
            try:
                document = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise AssertionError(
                    f"Invalid embedded JSON-LD in {source}, script {index}: {exc}"
                ) from exc
            require(
                isinstance(document, (dict, list)),
                f"Embedded JSON-LD must be an object or array: {source}, script {index}",
            )
            require(
                isinstance(document, dict) and "@context" in document,
                f"Embedded JSON-LD is missing @context: {source}, script {index}",
            )
            script_count += 1

    require(script_count > 0, "No embedded JSON-LD scripts were found")
    return len(html_files), script_count


def check_svg_files() -> int:
    files = sorted(ROOT.rglob("*.svg"))
    for path in files:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            raise AssertionError(f"Invalid SVG/XML in {path.relative_to(ROOT)}: {exc}") from exc
        require(
            root.tag.endswith("svg"),
            f"SVG root element is not svg: {path.relative_to(ROOT)}",
        )
    return len(files)


def check_json_inventory() -> int:
    count = 0
    for path in sorted(list(ROOT.rglob("*.json")) + list(ROOT.rglob("*.jsonld"))):
        if path.is_file():
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise AssertionError(f"Invalid JSON/JSON-LD in {path.relative_to(ROOT)}: {exc}") from exc
            count += 1
    return count


def check_vocabularies() -> dict[str, int]:
    ttl = parse_turtle("vocabulary/dio-odi-skos.ttl")
    jsonld = parse_jsonld("vocabulary/dio-odi.jsonld")
    dcat = parse_turtle("vocabulary/dio-odi-dcat.ttl")

    scheme = URIRef(VOCAB_NS + "ReferenceVocabulary")
    vocabulary_ttl_source = read_text("vocabulary/dio-odi-skos.ttl")
    vocabulary_jsonld_document = load_json("vocabulary/dio-odi.jsonld")
    jsonld_context = vocabulary_jsonld_document.get("@context", {})
    require(
        f'vann:preferredNamespacePrefix "{VOCABULARY_PREFIX}"' in vocabulary_ttl_source,
        "The canonical Turtle vocabulary must declare the preferred namespace prefix dio-odi",
    )
    require(
        isinstance(jsonld_context, dict)
        and jsonld_context.get(VOCABULARY_PREFIX) == VOCAB_NS
        and "dio" not in jsonld_context,
        "The canonical JSON-LD context must map dio-odi to the canonical namespace and must not retain dio",
    )
    version_info_uri = URIRef("http://www.w3.org/2002/07/owl#versionInfo")
    require(
        str(ttl.value(scheme, version_info_uri)) == VOCABULARY_VERSION,
        f"Canonical Reference Vocabulary version should be {VOCABULARY_VERSION}",
    )
    prefix_sources = (
        "vocabulary/dio-odi-skos.ttl",
        "vocabulary/dio-odi.jsonld",
        "vocabulary/dio-odi-dcat.ttl",
        "dio-odi/index.html",
        "mappings/agentic-er-commit-boundary-architecture-mapping.ttl",
        "mappings/commit-boundary-policy-mapping.ttl",
        "mappings/hem-dio-mapping.ttl",
        "mappings/rag-pipeline-mapping.ttl",
        "examples/queries.sparql",
    )
    for relative in prefix_sources:
        source = read_text(relative)
        require(
            "dio:" not in source and "dio-odi" in source,
            f"Legacy or missing namespace prefix in {relative}; expected dio-odi",
        )
    concepts = set(ttl.subjects(RDF.type, SKOS.Concept))
    schemes = set(ttl.subjects(RDF.type, SKOS.ConceptScheme))
    require(len(schemes) == 1 and scheme in schemes, "SKOS graph must define exactly the canonical ConceptScheme")
    require(len(concepts) == 40, f"Expected 40 SKOS concepts, found {len(concepts)}")
    require(all(str(uri).startswith(VOCAB_NS) for uri in concepts), "A SKOS concept URI is outside the canonical namespace")
    require(all((uri, SKOS.inScheme, scheme) in ttl for uri in concepts), "Every SKOS concept must belong to the canonical ConceptScheme")
    require(all((uri, SKOS.prefLabel, None) in ttl for uri in concepts), "A SKOS concept is missing skos:prefLabel")
    require((scheme, DCTERMS.isPartOf, URIRef("https://doi.org/10.5281/zenodo.23272897")) in ttl,
            "ConceptScheme must identify the parent Reference Model through dcterms:isPartOf")
    require((scheme, URIRef("http://www.w3.org/2002/07/owl#versionInfo"), None) in ttl,
            "ConceptScheme is missing owl:versionInfo")
    require(
        len(set(dcat.subjects(RDF.type, DCAT.Dataset))) == 1,
        "DCAT graph must contain exactly one Dataset",
    )
    distributions = set(dcat.subjects(RDF.type, DCAT.Distribution))
    require(len(distributions) == 2, f"Expected two DCAT distributions, found {len(distributions)}")
    require(
        (URIRef("https://vocab.danielberanek.cz/dio-odi/#dataset"), DCTERMS.identifier, scheme) in dcat,
        "DCAT Dataset identifier must be the canonical ConceptScheme URI",
    )
    require(ttl.isomorphic(jsonld), "SKOS Turtle and Vocabulary JSON-LD graphs are not isomorphic")

    return {
        "skos_concepts": len(concepts),
        "concept_schemes": len(schemes),
        "dcat_datasets": 1,
        "dcat_distributions": len(distributions),
        "vocabulary_triples": len(ttl),
    }


def check_mapping_graphs() -> dict[str, int]:
    totals: dict[str, int] = {}
    ttl_graphs: dict[str, Graph] = {}
    jsonld_graphs: dict[str, Graph] = {}
    for key, files in MAPPING_BASES.items():
        md = read_text(files["md"])
        json_doc = load_json(files["jsonld"])
        ttl_graph = parse_turtle(files["ttl"])
        jsonld_graph = parse_jsonld(files["jsonld"])
        require("@context" in json_doc, f"{key} JSON-LD has no @context")
        require("@type" in json_doc or "@graph" in json_doc, f"{key} JSON-LD has no top-level type or graph")
        require(len(ttl_graph) > 0, f"{key} Turtle graph is empty")
        require(
            "canonical DIO/ODI Reference Vocabulary" in md
            or "canonical vocabulary" in md.lower(),
            f"{key} Markdown should retain the boundary from the canonical vocabulary",
        )
        ttl_graphs[key] = ttl_graph
        jsonld_graphs[key] = jsonld_graph
        totals[f"{key}_ttl_triples"] = len(ttl_graph)
        totals[f"{key}_jsonld_triples"] = len(jsonld_graph)

    agentic = jsonld_graphs["agentic-er"]
    agentic_ttl = ttl_graphs["agentic-er"]
    # The full graphs intentionally retain representation-specific descriptive metadata
    # (for example, Turtle rdfs:label/rdfs:comment and JSON-LD dataset context).
    # Parity is therefore enforced over the 206 qualified relation records and 120
    # local architecture-concept identifiers below, not over every descriptive triple.
    rels = set(agentic.subjects(RDF.type, ARC.RelationAssertion))
    statements = set(agentic.subjects(RDF.type, RDF.Statement))
    ttl_rels = set(agentic_ttl.subjects(RDF.type, ARC.RelationAssertion))
    ttl_statements = set(agentic_ttl.subjects(RDF.type, RDF.Statement))
    require(len(rels) == 206, f"Agentic ER mapping must contain 206 qualified relation assertions, found {len(rels)}")
    require(rels == statements, "Agentic ER relation assertions and RDF Statements are not the same set")
    require(ttl_rels == rels and ttl_statements == ttl_rels,
            "Agentic ER Turtle and JSON-LD relation assertion identifiers differ")

    relation_fields = (
        RDF.subject, RDF.predicate, RDF.object, ARC.epistemicStatus,
        ARC.sourceSection, ARC.interpretationNote, DCTERMS.source,
    )
    relation_differences = []
    for assertion in sorted(rels, key=str):
        for predicate in relation_fields:
            ttl_values = set(agentic_ttl.objects(assertion, predicate))
            jsonld_values = set(agentic.objects(assertion, predicate))
            if ttl_values != jsonld_values:
                relation_differences.append({
                    "assertion": str(assertion).rsplit("/", 1)[-1],
                    "predicate": str(predicate),
                    "turtle": sorted(map(str, ttl_values)),
                    "jsonld": sorted(map(str, jsonld_values)),
                })
    require(
        not relation_differences,
        "Agentic ER relation fields differ between Turtle and JSON-LD: "
        + json.dumps(relation_differences[:10], ensure_ascii=False),
    )

    mapping_root = URIRef(ARC_NS + "Mapping")
    provenance_source = URIRef(ARC_NS + "source/constraining_the_commit_boundary_v55")
    typed_local_nodes = {
        subject
        for subject in agentic.subjects(RDF.type, None)
        if isinstance(subject, URIRef) and str(subject).startswith(ARC_NS)
    }
    concept_nodes = typed_local_nodes - rels - {mapping_root, provenance_source}
    ttl_typed_local_nodes = {
        subject
        for subject in agentic_ttl.subjects(RDF.type, None)
        if isinstance(subject, URIRef) and str(subject).startswith(ARC_NS)
    }
    # Turtle also declares local RDF classes and properties that are schema terms,
    # not architecture-concept instances. Exclude those declarations before comparing
    # the complete concept identifier sets in both serializations.
    ttl_schema_nodes = (
        set(agentic_ttl.subjects(RDF.type, RDFS.Class))
        | set(agentic_ttl.subjects(RDF.type, RDF.Property))
    )
    ttl_concept_nodes = ttl_typed_local_nodes - ttl_rels - {mapping_root, provenance_source} - ttl_schema_nodes
    require(len(concept_nodes) == 120, f"Agentic ER mapping must contain 120 local architecture concepts, found {len(concept_nodes)}")
    missing_in_turtle = concept_nodes - ttl_concept_nodes
    extra_in_turtle = ttl_concept_nodes - concept_nodes
    require(
        not missing_in_turtle and not extra_in_turtle,
        "Agentic ER concept identifiers differ between Turtle and JSON-LD: "
        + json.dumps({
            "missing_in_turtle": sorted(str(node) for node in missing_in_turtle),
            "extra_in_turtle": sorted(str(node) for node in extra_in_turtle),
        }, ensure_ascii=False),
    )

    required_statuses = {
        "specified",
        "assumed",
        "illustrative",
        "proposed evaluation",
        "future research",
        "canonical reference",
    }
    statuses = {
        str(agentic.value(subject, URIRef("http://schema.org/name")) or agentic.value(subject, URIRef("https://schema.org/name")))
        for subject in agentic.subjects(RDF.type, ARC.EpistemicStatus)
    }
    require(statuses == required_statuses, f"Unexpected Agentic ER epistemic-status set: {sorted(statuses)}")

    for assertion in rels:
        for predicate in (RDF.subject, RDF.predicate, RDF.object):
            require(
                len(list(agentic.objects(assertion, predicate))) == 1,
                f"Qualified Agentic ER relation must have one {predicate} value: {assertion}",
            )
        require(
            len(list(agentic.objects(assertion, ARC.epistemicStatus))) == 1,
            f"Qualified Agentic ER relation is missing a single epistemic status: {assertion}",
        )
        require(
            len(list(agentic.objects(assertion, DCTERMS.source))) == 1,
            f"Qualified Agentic ER relation is missing a single provenance source: {assertion}",
        )

    totals["agentic_er_concepts"] = len(concept_nodes)
    totals["agentic_er_relations"] = len(rels)
    totals["agentic_er_triples"] = len(agentic)
    return totals


def check_metadata() -> dict[str, int | str]:
    zenodo = load_json(".zenodo.json")
    works = load_json("metadata/works.json")
    keywords = load_json("metadata/keywords.json")
    distributions = load_json("metadata/distributions.json")
    references = load_json("metadata/references.json")
    relations = load_json("metadata/relations.json")
    external = load_json("metadata/external-concept-mappings.json")
    external_schema = load_json("metadata/external-concept-mappings.schema.json")
    validate_json_schema(instance=external, schema=external_schema)

    citation = yaml.safe_load(read_text("CITATION.cff"))
    require(zenodo.get("version") == citation.get("version"), ".zenodo.json and CITATION.cff versions do not match")
    require(zenodo.get("license") == "cc-by-4.0", "Zenodo projection must preserve CC BY 4.0")
    require(citation.get("license") == "CC-BY-4.0", "CITATION.cff must preserve CC BY 4.0")

    model = next((item for item in works["works"] if item.get("id") == "reference-model"), None)
    require(model is not None, "Reference Model work entry is missing")
    require(model.get("reference_vocabulary_uri") == VOCAB_NS + "ReferenceVocabulary",
            "Reference Vocabulary ConceptScheme URI is not canonical")
    inclusion_history = model.get("reference_vocabulary_inclusion_history", [])
    require(
        not any(key in model for key in (
            "reference_vocabulary_publication_date",
            "reference_vocabulary_initial_archived_version",
            "reference_vocabulary_initial_archived_version_doi",
            "reference_vocabulary_initial_archived_version_doi_url",
        )),
        "Reference Vocabulary archive metadata still uses ambiguous standalone-publication fields",
    )
    expected_inclusions = {
        "0.1.0": ("0.1.0", "10.5281/zenodo.23272898"),
        "0.2.0": ("0.2.0", "10.5281/zenodo.23282752"),
    }
    require(len(inclusion_history) == 2, "Reference Vocabulary inclusion history must contain the first two archived states")
    model_releases = {
        release.get("version"): release
        for work in works["works"] if work.get("id") == "reference-model"
        for release in work.get("releases", [])
    }
    for entry in inclusion_history:
        vocabulary_version = entry.get("vocabulary_version")
        expected = expected_inclusions.get(vocabulary_version)
        require(expected is not None, f"Unexpected archived Reference Vocabulary version in inclusion history: {vocabulary_version}")
        release_version, release_doi = expected
        require(
            entry.get("reference_model_release_version") == release_version
            and entry.get("reference_model_release_doi") == release_doi,
            f"Reference Vocabulary {vocabulary_version} must point to its enclosing Reference Model {release_version} archive",
        )
        release = model_releases.get(release_version)
        require(release is not None and release.get("doi") == release_doi,
                f"Reference Vocabulary inclusion DOI does not resolve to Reference Model release {release_version}")

    vocabulary_reference = next(
        (item for item in references.get("references", [])
         if item.get("id") == "reference-vocabulary-v0.2.0"),
        None,
    )
    require(vocabulary_reference is not None, "Canonical Reference Vocabulary citation is missing from references.json")
    require(
        vocabulary_reference.get("canonical_uri") == VOCAB_NS + "ReferenceVocabulary"
        and vocabulary_reference.get("version") == "0.2.0"
        and vocabulary_reference.get("included_in_reference_model_version") == "0.5.0",
        "Reference Vocabulary citation does not identify the canonical URI and archived parent-model context",
    )
    require(
        "doi" not in vocabulary_reference
        and "10.5281/zenodo.23272897" not in json.dumps(vocabulary_reference, ensure_ascii=False),
        "Reference Model Concept DOI must not be assigned to the Reference Vocabulary",
    )
    require(model.get("reference_model_concept_doi") == "10.5281/zenodo.23272897",
            "Reference Model Concept DOI has changed unexpectedly")
    require(model.get("reference_vocabulary_version") == VOCABULARY_VERSION,
            f"Live Reference Vocabulary version should be {VOCABULARY_VERSION}")
    require(model.get("current_release", {}).get("version") == zenodo.get("version")
            or model.get("release_candidate", {}).get("version") == zenodo.get("version"),
            "Zenodo projection version must match either current archive or explicit release candidate")
    
    profile = keywords["work_profiles"]["reference-model"]["resolved_keywords"]
    paper_profile = keywords["work_profiles"]["commit-boundary-paper"]["resolved_keywords"]
    require(len(profile) == 67, f"Expected 67 Reference Model keywords, found {len(profile)}")
    require(len(paper_profile) == 34, f"Expected 34 commit-boundary paper keywords, found {len(paper_profile)}")
    require(zenodo.get("keywords") == profile, ".zenodo.json keywords differ from the canonical Reference Model profile")
    require(citation.get("keywords") == profile, "CITATION.cff keywords differ from the canonical Reference Model profile")

    cff_doi = citation.get("doi")
    current_doi = model.get("current_release", {}).get("doi")
    if zenodo.get("version") == model.get("current_release", {}).get("version"):
        require(cff_doi == current_doi, "CITATION.cff DOI differs from the current archived release DOI")

    arxiv = next((item for item in works["works"] if item.get("id") == "commit-boundary-paper"), None)
    require(arxiv is not None and arxiv.get("arxiv", {}).get("current_version") == "v2",
            "Commit-Boundary paper registry must identify arXiv v2 as current")
    distribution = next(
        (item for work in distributions["works"] if work.get("work") == "commit-boundary-paper"
         for item in work.get("representations", []) if item.get("platform") == "arXiv"),
        None,
    )
    require(distribution is not None and distribution.get("canonical_relation") == "isNewVersionOf",
            "arXiv v2 distribution relation must remain isNewVersionOf")
    require(distribution.get("applies_to_version_doi") == "10.5281/zenodo.23580733",
            "arXiv v2 relation must remain scoped to Zenodo version 1")

    return {
        "keyword_registry": keywords["registry_version"],
        "reference_model_keywords": len(profile),
        "commit_boundary_keywords": len(paper_profile),
        "works_registry": works["registry_version"],
        "references_registry": references.get("registry_version", "n/a"),
        "relations_registry": relations.get("registry_version", "n/a"),
        "distributions_registry": distributions["registry_version"],
    }


def check_semantic_change_feed() -> dict[str, int | str]:
    feed = load_json("semantic-change-feed/events.json")
    schema = load_json("semantic-change-feed/schema.json")
    validate_json_schema(instance=feed, schema=schema)
    events = feed.get("events", [])
    ids = [event.get("id") for event in events]
    require(len(ids) == len(set(ids)), "Semantic Change Feed event IDs must be unique")
    require(feed.get("event_count") == len(events), "Semantic Change Feed event_count does not match events array")
    dates = [event.get("date") for event in events]
    require(dates == sorted(dates), "Semantic Change Feed events must be stored in chronological order")
    known_ids = set(ids)
    for event in events:
        for relation in ("related_to", "supersedes", "corrects"):
            unknown = set(event.get("lineage", {}).get(relation, [])) - known_ids
            require(not unknown, f"{event['id']} has unresolved {relation} references: {sorted(unknown)}")
        require(event.get("evidence", {}).get("sources"), f"{event['id']} has no evidence sources")
        temporal_note = event.get("evidence", {}).get("temporal_note", "")
        if "transcribed from the author-maintained DIO/ODI Hub Changelog" in temporal_note:
            require(event.get("date_basis") == "hub_changelog_date",
                    f"{event['id']} attributes a non-Changelog date to the Hub Changelog")
    page = read_text("semantic-change-feed/index.html")
    page_ids = set(re.findall(r'data-event-id="(SCF-[^"]+)"', page))
    require(page_ids == known_ids, "Semantic Change Feed HTML event inventory differs from events.json")
    for path in sorted(ROOT.rglob("*.html")):
        source = path.read_text(encoding="utf-8")
        if '<nav class="site-nav"' in source:
            require('href="/semantic-change-feed/"' in source,
                    f"Global navigation is missing Semantic Change Feed link: {path.relative_to(ROOT)}")
    require('aria-current="page"' in page and 'href="/semantic-change-feed/"' in page,
            "Semantic Change Feed page must mark its navigation item as current")
    return {"scf_feed_version": feed["feed_version"], "scf_events": len(events),
            "scf_event_classes": len({event["event_class"] for event in events})}

def check_site_homepage() -> int:
    source = read_text("index.html")
    require('<link rel="canonical" href="https://vocab.danielberanek.cz/">' in source,
            "Homepage canonical must identify the site root")
    require('<meta name="robots" content="index,follow' in source,
            "Homepage must be indexable")
    require('http-equiv="refresh"' not in source.lower(),
            "Homepage must not redirect to the vocabulary page")
    for link in ('href="/dio-odi/"', 'href="/mappings/"',
                 'href="/metadata/"', 'href="/semantic-change-feed/"', 'href="https://danielberanek.cz/manifest-dio/"'):
        require(link in source, f"Homepage is missing navigation target: {link}")
    return 1


def check_sitemap() -> int:
    path = ROOT / "sitemap.xml"
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise AssertionError(f"Invalid sitemap.xml: {exc}") from exc
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = {
        node.findtext("sm:loc", namespaces=namespace): node.findtext("sm:lastmod", namespaces=namespace)
        for node in tree.findall(".//sm:url", namespace)
    }
    required = [
        "https://vocab.danielberanek.cz/",
        "https://vocab.danielberanek.cz/dio-odi/",
        "https://vocab.danielberanek.cz/mappings/",
        "https://vocab.danielberanek.cz/metadata/",
        "https://vocab.danielberanek.cz/semantic-change-feed/",
        "https://vocab.danielberanek.cz/semantic-change-feed/events.json",
        "https://vocab.danielberanek.cz/semantic-change-feed/schema.json",
        "https://vocab.danielberanek.cz/mappings/rag-pipeline/",
        "https://vocab.danielberanek.cz/mappings/hem-dio/",
        "https://vocab.danielberanek.cz/mappings/commit-boundary-policy/",
        "https://vocab.danielberanek.cz/mappings/agentic-er-architecture/",
    ]
    missing = [url for url in required if url not in urls]
    require(not missing, f"Sitemap is missing required pages: {missing}")
    return len(urls)


def main() -> int:
    try:
        counts = {
            "json_files": check_json_inventory(),
        }
        html_count, jsonld_count = check_html_and_jsonld()
        counts["html_pages"] = html_count
        counts["homepage"] = check_site_homepage()
        counts["embedded_jsonld_scripts"] = jsonld_count
        counts["svg_files"] = check_svg_files()
        counts["sitemap_urls"] = check_sitemap()
        counts["local_links_checked"] = check_local_links()
        counts.update(check_vocabularies())
        counts.update(check_mapping_graphs())
        counts.update(check_metadata())
        counts.update(check_semantic_change_feed())
    except Exception as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        return 1

    print("DIO/ODI Reference Model validation passed.")
    for key, value in counts.items():
        print(f"- {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

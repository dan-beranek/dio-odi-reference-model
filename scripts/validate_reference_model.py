#!/usr/bin/env python3
"""Deterministic integrity checks for the DIO/ODI Reference Model repository.

This validator checks source files and cross-representation constraints. It does
not claim semantic correctness of external application mappings or empirical
validation of the Agentic ER architecture.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

import yaml
from jsonschema import validate as validate_json_schema
from rdflib import Graph, Namespace, RDF, URIRef
from rdflib.namespace import DCAT, DCTERMS, RDFS, SKOS


ROOT = Path(__file__).resolve().parents[1]
VOCAB_NS = "https://vocab.danielberanek.cz/dio-odi/#"
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
    vocabulary_version = str(ttl.value(scheme, version_info_uri) or "")
    require(bool(vocabulary_version), "Canonical Reference Vocabulary is missing owl:versionInfo")
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
    require(bool(concepts), "SKOS graph must contain at least one concept")
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
    media_types = {
        str(media_type)
        for distribution in distributions
        for media_type in dcat.objects(distribution, DCAT.mediaType)
    }
    required_media_types = {
        "https://www.iana.org/assignments/media-types/text/turtle",
        "https://www.iana.org/assignments/media-types/application/ld+json",
    }
    require(required_media_types <= media_types,
            "DCAT must expose both Turtle and JSON-LD distributions")
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
        "vocabulary_version": vocabulary_version,
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
    # Parity is therefore enforced over the complete qualified-relation and
    # local architecture-concept identifier sets, not over every descriptive triple.
    rels = set(agentic.subjects(RDF.type, ARC.RelationAssertion))
    statements = set(agentic.subjects(RDF.type, RDF.Statement))
    ttl_rels = set(agentic_ttl.subjects(RDF.type, ARC.RelationAssertion))
    ttl_statements = set(agentic_ttl.subjects(RDF.type, RDF.Statement))
    require(bool(rels), "Agentic ER mapping must contain qualified relation assertions")
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
    require(bool(concept_nodes), "Agentic ER mapping must contain local architecture concepts")
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


def mcp_version_doi(works: dict) -> str | None:
    item = next((work for work in works.get("works", []) if work.get("id") == "mcp-server"), {})
    return item.get("version_doi")


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
    application_mappings = load_json("metadata/application-mappings.json")
    application_mappings_schema = load_json("metadata/application-mappings.schema.json")
    validate_json_schema(instance=application_mappings, schema=application_mappings_schema)
    research_genealogy = load_json("metadata/research-genealogy.json")
    research_genealogy_schema = load_json("metadata/research-genealogy.schema.json")
    validate_json_schema(instance=research_genealogy, schema=research_genealogy_schema)
    metadata_projection = load_json("metadata.json")

    citation = yaml.safe_load(read_text("CITATION.cff"))
    require(zenodo.get("version") == citation.get("version"), ".zenodo.json and CITATION.cff versions do not match")
    require(zenodo.get("license") == "cc-by-4.0", "Zenodo projection must preserve CC BY 4.0")
    require(citation.get("license") == "CC-BY-4.0", "CITATION.cff must preserve CC BY 4.0")

    model = next((item for item in works["works"] if item.get("id") == "reference-model"), None)
    require(model is not None, "Reference Model work entry is missing")
    release_target = model.get("release_candidate") or model.get("current_release")
    author = works.get("author", {})
    expected_creator = {
        "name": f"{author.get('family_names')}, {author.get('given_names')}",
        "orcid": author.get("orcid"),
        "affiliation": author.get("affiliation"),
    }
    require(zenodo.get("title") == model.get("title"), "Zenodo title differs from canonical Reference Model title")
    require(zenodo.get("version") == release_target.get("version"),
            "Zenodo version differs from the canonical release target")
    require(zenodo.get("upload_type") == model.get("type") == "software",
            "Zenodo upload type must match the canonical Reference Model type")
    require(zenodo.get("creators") == [expected_creator],
            "Zenodo creators differ from the canonical works author")
    require(citation.get("title") == model.get("title")
            and citation.get("type") == model.get("type")
            and citation.get("version") == release_target.get("version")
            and citation.get("abstract") == model.get("citation_abstract")
            and citation.get("repository-code") == model.get("repository"),
            "CITATION.cff identity fields differ from canonical works metadata")
    expected_doi = release_target.get("doi")
    require(citation.get("doi") == expected_doi,
            "CITATION.cff DOI differs from the canonical release target")
    require(citation.get("authors") == [{
        "family-names": author.get("family_names"),
        "given-names": author.get("given_names"),
        "orcid": f"https://orcid.org/{author.get('orcid')}",
        "affiliation": author.get("affiliation"),
    }], "CITATION.cff authors differ from the canonical works author")

    require(model is not None, "Reference Model work entry is missing")
    release_records = model.get("releases", [])
    release_versions = [item.get("version") for item in release_records]
    release_dois = [item.get("doi") for item in release_records if item.get("doi")]
    require(
        all(release_versions)
        and len(release_versions) == len(set(release_versions))
        and len(release_dois) == len(set(release_dois)),
        "Reference Model release history must have unique, non-empty version identifiers and DOIs",
    )
    releases_by_version = {item["version"]: item for item in release_records}
    current_release = model.get("current_release", {})
    previous_release = model.get("previous_archived_release", {})
    require(
        releases_by_version.get(current_release.get("version"), {}).get("doi") == current_release.get("doi")
        and releases_by_version.get(previous_release.get("version"), {}).get("doi") == previous_release.get("doi"),
        "Current and previous archived releases must resolve to the matching canonical release records",
    )
    projected_history = metadata_projection.get("archived_release_history", [])
    projected_versions = [item.get("version") for item in projected_history]
    expected_versions = sorted(
        (version for version, release in releases_by_version.items() if release.get("doi")),
        key=lambda value: tuple(int(part) for part in re.findall(r"\d+", value)),
        reverse=True,
    )
    require(
        projected_versions == expected_versions
        and all(
            entry.get("doi") == releases_by_version[entry["version"]].get("doi")
            for entry in projected_history
        ),
        "metadata.json archived release history must be derived and sorted from the canonical works registry",
    )
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
    model_releases = {
        release.get("version"): release
        for release in model.get("releases", [])
    }
    inclusion_versions = [entry.get("vocabulary_version") for entry in inclusion_history]
    require(
        all(inclusion_versions)
        and len(inclusion_versions) == len(set(inclusion_versions)),
        "Reference Vocabulary inclusion history must use unique, non-empty version identifiers",
    )
    for entry in inclusion_history:
        vocabulary_version = entry.get("vocabulary_version")
        release_version = entry.get("reference_model_release_version")
        release_doi = entry.get("reference_model_release_doi")
        release = model_releases.get(release_version)
        require(release is not None and release.get("doi") == release_doi,
                f"Reference Vocabulary {vocabulary_version} inclusion must point to a matching archived Reference Model release")

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
    vocabulary_graph = parse_turtle("vocabulary/dio-odi-skos.ttl")
    vocabulary_version = str(
        vocabulary_graph.value(
            URIRef(VOCAB_NS + "ReferenceVocabulary"),
            URIRef("http://www.w3.org/2002/07/owl#versionInfo"),
        ) or ""
    )
    require(bool(vocabulary_version), "Canonical Reference Vocabulary has no declared version")
    require(model.get("reference_vocabulary_version") == vocabulary_version,
            "Works registry Reference Vocabulary version differs from the canonical SKOS source")
    require(model.get("current_release", {}).get("version") == zenodo.get("version")
            or model.get("release_candidate", {}).get("version") == zenodo.get("version"),
            "Zenodo projection version must match either current archive or explicit release candidate")
    
    profile = keywords["work_profiles"]["reference-model"]["resolved_keywords"]
    paper_profile = keywords["work_profiles"]["commit-boundary-paper"]["resolved_keywords"]
    require(zenodo.get("keywords") == profile, ".zenodo.json keywords differ from the canonical Reference Model profile")
    require(citation.get("keywords") == profile, "CITATION.cff keywords differ from the canonical Reference Model profile")
    require(
        metadata_projection.get("derived_application_mappings") == application_mappings.get("mappings"),
        "metadata.json Application Mappings projection differs from the canonical Application Mappings registry",
    )
    current_release = model.get("current_release", {})
    require(
        metadata_projection.get("current_release", {}).get("version") == current_release.get("version")
        and metadata_projection.get("current_release", {}).get("doi") == current_release.get("doi"),
        "metadata.json current release projection differs from the canonical works registry",
    )
    require(
        metadata_projection.get("mcp_server", {}).get("version_doi") == mcp_version_doi(works),
        "metadata.json MCP distribution projection differs from the canonical works registry",
    )
    require(
        metadata_projection.get("author", {}).get("email") == works["author"].get("email")
        and metadata_projection.get("taxonomic_note_doi")
        == next(item for item in works["works"] if item.get("id") == "taxonomic-note").get("version_doi")
        and metadata_projection.get("reference_vocabulary_version") == model.get("reference_vocabulary_version")
        and metadata_projection.get("live_reference_vocabulary_version") == vocabulary_version,
        "metadata.json identity and author projections differ from canonical registries",
    )
    require(
        metadata_projection.get("corpus_metadata_registry", {}).get("application_mappings")
        == "metadata/application-mappings.json",
        "metadata.json does not identify the canonical Application Mappings registry",
    )
    require(
        metadata_projection.get("corpus_metadata_registry", {}).get("research_genealogy")
        == "metadata/research-genealogy.json"
        and metadata_projection.get("corpus_metadata_registry", {}).get("research_genealogy_schema")
        == "metadata/research-genealogy.schema.json"
        and metadata_projection.get("corpus_metadata_registry", {}).get("research_genealogy_guide")
        == "docs/research-genealogy.md",
        "metadata.json does not identify the canonical Research Genealogy resources",
    )

    cff_doi = citation.get("doi")
    current_doi = model.get("current_release", {}).get("doi")
    if zenodo.get("version") == model.get("current_release", {}).get("version"):
        require(cff_doi == current_doi, "CITATION.cff DOI differs from the current archived release DOI")

    arxiv = next((item for item in works["works"] if item.get("id") == "commit-boundary-paper"), None)
    require(arxiv is not None and arxiv.get("arxiv", {}).get("current_version"),
            "Commit-Boundary paper registry must identify its current arXiv version")
    distribution = next(
        (item for work in distributions["works"] if work.get("work") == "commit-boundary-paper"
         for item in work.get("representations", []) if item.get("platform") == "arXiv"),
        None,
    )
    require(
        distribution is not None
        and distribution.get("version") == arxiv["arxiv"]["current_version"]
        and distribution.get("version_url") == arxiv["arxiv"]["version_url"],
        "arXiv distribution must match the current version recorded in works.json",
    )
    require(
        distribution.get("canonical_relation") == "isNewVersionOf"
        and distribution.get("applies_to_version_doi") == arxiv.get("version_doi"),
        "arXiv version relation must remain scoped to the canonical Zenodo source version",
    )

    research_objects = research_genealogy.get("research_objects", [])
    research_processes = research_genealogy.get("research_processes", [])
    genealogy_milestones = research_genealogy.get("milestones", [])
    genealogy_collections = research_genealogy.get("source_collections", [])
    genealogy_artefacts = research_genealogy.get("artefacts", [])
    genealogy_leads = research_genealogy.get("inventory_leads", [])
    genealogy_relations = research_genealogy.get("relations", [])

    object_ids = [item.get("id") for item in research_objects]
    process_ids = [item.get("id") for item in research_processes]
    milestone_ids = [item.get("id") for item in genealogy_milestones]
    collection_ids = [item.get("id") for item in genealogy_collections]
    artefact_ids = [item.get("id") for item in genealogy_artefacts]
    require(
        all(object_ids) and len(object_ids) == len(set(object_ids))
        and all(process_ids) and len(process_ids) == len(set(process_ids))
        and all(milestone_ids) and len(milestone_ids) == len(set(milestone_ids))
        and all(collection_ids) and len(collection_ids) == len(set(collection_ids))
        and all(artefact_ids) and len(artefact_ids) == len(set(artefact_ids)),
        "Research Genealogy object, process, milestone, collection, and artefact identifiers must be unique and non-empty",
    )

    concept_ids = {
        outcome.get("id")
        for process in research_processes
        for outcome in process.get("concept_outcomes", [])
        if outcome.get("id")
    }
    work_ids = {item.get("id") for item in works.get("works", []) if item.get("id")}
    genealogy_entity_ids = (
        set(object_ids) | set(process_ids) | set(milestone_ids)
        | set(collection_ids) | set(artefact_ids) | concept_ids | work_ids
    )
    for process in research_processes:
        require(
            set(process.get("research_object_ids", [])) <= set(object_ids),
            f"Research process has an unresolved research object: {process.get('id')}",
        )
        outcomes = {item.get("id"): item for item in process.get("concept_outcomes", [])}
        require(
            outcomes.get("DIO", {}).get("articulated_on") == "2026-05-21"
            and outcomes.get("ODI", {}).get("articulated_on") == "2026-06-22",
            "DIO and ODI concept outcomes must retain their changelog articulation dates",
        )
        for outcome in process.get("concept_outcomes", []):
            require(outcome.get("uri") in {
                VOCAB_NS + "DIO", VOCAB_NS + "ODI"
            }, f"Research Genealogy concept URI is outside the canonical namespace: {outcome.get('id')}")

    milestone_dates = [item.get("date") for item in genealogy_milestones]
    require(
        milestone_dates == sorted(milestone_dates),
        "Research Genealogy milestones must be in chronological order",
    )
    for milestone in genealogy_milestones:
        require(
            set(milestone.get("research_object_ids", [])) <= set(object_ids)
            and set(milestone.get("process_ids", [])) <= set(process_ids)
            and set(milestone.get("concept_ids", [])) <= concept_ids,
            f"Research Genealogy milestone has an unresolved reference: {milestone.get('id')}",
        )

    for artefact in genealogy_artefacts:
        require(
            artefact.get("source_collection_id") in set(collection_ids),
            f"Research Genealogy artefact has an unresolved source collection: {artefact.get('id')}",
        )
        require(
            set(artefact.get("research_object_ids", [])) <= set(object_ids)
            and set(artefact.get("process_ids", [])) <= set(process_ids)
            and set(artefact.get("related_work_ids", [])) <= work_ids,
            f"Research Genealogy artefact has an unresolved research or work relation: {artefact.get('id')}",
        )
    for lead in genealogy_leads:
        require(
            lead.get("source_collection_id") in set(collection_ids),
            f"Research Genealogy inventory lead has an unresolved source collection: {lead.get('title')}",
        )
    for relation in genealogy_relations:
        require(
            relation.get("subject_id") in genealogy_entity_ids
            and relation.get("object_id") in genealogy_entity_ids,
            f"Research Genealogy relation has an unresolved endpoint: {relation.get('subject_id')} -> {relation.get('object_id')}",
        )

    professional_ethnography = next(
        (item for item in research_objects if item.get("id") == "professional-ethnography"),
        None,
    )
    slideshare_collection = next(
        (item for item in genealogy_collections if item.get("id") == "slideshare-danielberanek"),
        None,
    )
    semiotic_artefact = next(
        (item for item in genealogy_artefacts
         if item.get("id") == "slideshare-semiotic-discursive-deconstruction"),
        None,
    )
    crisis_presentation = next(
        (item for item in genealogy_artefacts
         if item.get("id") == "slideshare-crisis-entity-resolution-presentation"),
        None,
    )
    require(
        professional_ethnography is not None
        and professional_ethnography.get("uri") == "https://danielberanek.cz/od-pultu-az-k-seo-a-copy-s-ostrymi-hroty-profesni-bio/"
        and slideshare_collection is not None
        and slideshare_collection.get("url") == "https://www.slideshare.net/danielberanek",
        "Research Genealogy must preserve the canonical professional-ethnography object and SlideShare source collection",
    )
    require(
        semiotic_artefact is not None
        and "DIO" in semiotic_artefact.get("research_role", "")
        and crisis_presentation is not None
        and crisis_presentation.get("related_work_ids") == ["crisis-entity-resolution"],
        "Research Genealogy must distinguish an exploratory reading from a presentation of a registered research work",
    )

    genealogy_page = read_text("metadata/index.html")
    require(
        "/metadata/research-genealogy.json" in genealogy_page
        and "/metadata/research-genealogy.schema.json" in genealogy_page
        and "/docs/research-genealogy.md" in genealogy_page,
        "Corpus Metadata frontend is missing the Research Genealogy registry links",
    )
    genealogy_discovery = read_text("llms.txt")
    require(
        "- Research Genealogy Registry: https://vocab.danielberanek.cz/metadata/research-genealogy.json" in genealogy_discovery
        and "## Research Genealogy" in genealogy_discovery,
        "llms.txt is missing the Research Genealogy discovery entry",
    )

    return {
        "keyword_registry": keywords["registry_version"],
        "reference_model_keywords": len(profile),
        "commit_boundary_keywords": len(paper_profile),
        "works_registry": works["registry_version"],
        "references_registry": references.get("registry_version", "n/a"),
        "relations_registry": relations.get("registry_version", "n/a"),
        "distributions_registry": distributions["registry_version"],
        "application_mappings_registry": application_mappings["registry_version"],
        "research_genealogy_objects": len(research_objects),
        "research_genealogy_processes": len(research_processes),
        "research_genealogy_milestones": len(genealogy_milestones),
        "research_genealogy_artefacts": len(genealogy_artefacts),
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
    required_reconciliations = {
        "SCF-2026-046": ("deployment_date", "2026-11-09"),
        "SCF-2026-047": ("documentation_date", "2026-11-10"),
        "SCF-2026-048": ("documentation_date", "2026-11-10"),
        "SCF-2026-049": ("deployment_date", "2026-11-11"),
        "SCF-2026-050": ("documentation_date", "2026-11-11"),
        "SCF-2026-051": ("documentation_date", "2026-11-14"),
        "SCF-2026-055": ("publication_date", "2026-11-19"),
    }
    events_by_id = {event["id"]: event for event in events}
    for event_id, expected in required_reconciliations.items():
        require(event_id in events_by_id, f"Semantic Change Feed is missing required maintenance event {event_id}")
        require((events_by_id[event_id]["date_basis"], events_by_id[event_id]["date"]) == expected,
                f"{event_id} has an incorrect temporal basis or date")
    archive_events = {"0.8.0": "SCF-2026-047", "0.9.0": "SCF-2026-048"}
    works = load_json("metadata/works.json")
    model = next((item for item in works["works"] if item.get("id") == "reference-model"), None)
    require(model is not None, "Reference Model work entry is missing while reconciling SCF archive milestones")
    release_by_version = {item["version"]: item for item in model.get("releases", [])}
    for version, event_id in archive_events.items():
        release = release_by_version.get(version)
        event = events_by_id[event_id]
        require(release is not None, f"Reference Model release {version} is missing from works.json")
        expected_doi = release["doi"]
        require(any(scope.get("uri") == f"https://doi.org/{expected_doi}" for scope in event.get("scope", [])),
                f"{event_id} does not identify archived Reference Model {version}")
        require(any(source.get("url") == f"https://doi.org/{expected_doi}" for source in event.get("evidence", {}).get("sources", [])),
                f"{event_id} does not cite its corresponding archival record")
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
    require('id="scf-count" class="count" role="status" aria-live="polite">All records</span>' in page,
            "Semantic Change Feed frontend must use a neutral initial counter and calculate filtered counts dynamically")
    require(not re.search(r'<div class="page-hero-stat"><strong>\d+</strong><span>live documented records', page),
            "Semantic Change Feed frontend must not contain a manually maintained live record count")
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

def check_llms_txt() -> int:
    source = read_text("llms.txt")
    metadata = load_json("metadata.json")
    keywords = load_json("metadata/keywords.json")
    feed = load_json("semantic-change-feed/events.json")
    registry = metadata["corpus_metadata_registry"]
    current_release = metadata["current_archived_release"]
    previous_release = metadata["previous_archived_release"]

    required_lines = (
        f"- Current archived Reference Model release: {current_release['version']} — {current_release['doi_url']}",
        f"- Previous archived Reference Model release: {previous_release['version']} — {previous_release['doi_url']}",
        f"- Live Reference Vocabulary: {metadata['live_reference_vocabulary_version']}",
        f"- Vocabulary included in archived v{current_release['version']}: {metadata['current_archived_reference_vocabulary_version']}",
        f"- Feed version: {feed['feed_version']};",
        "- Application Mappings metadata registry: https://vocab.danielberanek.cz/metadata/application-mappings.json",
        "- Application Mappings metadata schema: https://vocab.danielberanek.cz/metadata/application-mappings.schema.json",
        f"  - Keyword registry version: {keywords['registry_version']}",
        f"  - Grammar version: {registry['keyword_grammar_version']}",
    )
    for expected in required_lines:
        require(expected in source, f"llms.txt is out of sync with canonical metadata: missing {expected!r}")

    coverage_date = date.fromisoformat(feed["events"][-1]["date"])
    coverage_label = f"{coverage_date.day} {coverage_date.strftime('%B %Y')}"
    coverage_line = next(
        (line for line in source.splitlines() if line.startswith("- Current coverage:")),
        "",
    )
    require(bool(coverage_line), "llms.txt is missing its current coverage description")
    require(not re.search(r"\b\d+\s+events?\b", coverage_line, re.IGNORECASE),
            "llms.txt must not duplicate the live SCF event count")
    require(
        f"through {coverage_label}" in coverage_line,
        f"llms.txt coverage date is stale; expected the latest event date {coverage_label}",
    )

    scf_metadata = metadata["semantic_change_feed"]
    require("event_count" not in scf_metadata,
            "metadata.json must not duplicate the live SCF event_count; derive it from events.json")
    require(
        scf_metadata["feed_version"] == feed["feed_version"]
        and scf_metadata["schema_version"] == feed["schema_version"]
        and scf_metadata["coverage_through"] == feed["events"][-1]["date"],
        "metadata.json and Semantic Change Feed events.json are inconsistent",
    )
    works = load_json("metadata/works.json")
    model = next((item for item in works["works"] if item.get("id") == "reference-model"), None)
    archived = scf_metadata.get("archived_snapshot", {})
    release = model.get("current_release", {}) if model else {}
    require(
        archived.get("reference_model_version") == release.get("version")
        and archived.get("reference_model_doi") == release.get("doi")
        and archived.get("feed_version") == release.get("semantic_change_feed_version")
        and archived.get("schema_version") == release.get("semantic_change_feed_schema_version")
        and archived.get("event_count") == release.get("semantic_change_feed_event_count"),
        "Live SCF metadata does not preserve the exact archived snapshot recorded in works.json",
    )
    archive_coverage = date.fromisoformat(archived.get("coverage_through"))
    archive_coverage_label = f"{archive_coverage.day} {archive_coverage.strftime('%B %Y')}"
    archive_label = (f"- Archived snapshot in Reference Model v{archived.get('reference_model_version')}: "
                     f"feed v{archived.get('feed_version')}, schema v{archived.get('schema_version')}, "
                     f"{archived.get('event_count')} events through {archive_coverage_label}")
    require(archive_label in source, "llms.txt is missing the archived SCF snapshot boundary")
    return len(required_lines) + 2



def check_external_reception() -> dict[str, int]:
    registry = load_json("metadata/external-reception.json")
    schema = load_json("metadata/external-reception.schema.json")
    validate_json_schema(instance=registry, schema=schema)
    entries = registry.get("entries", [])
    ids = [entry.get("id") for entry in entries]
    require(len(ids) == len(set(ids)), "External Reception entry IDs must be unique")
    known_works = {item.get("id") for item in registry.get("target_works", [])}
    known_entries = set(ids)
    for entry in entries:
        require(set(entry.get("target_work_ids", [])) <= known_works,
                f"External Reception entry has an unknown target work: {entry.get('id')}")
        require(set(entry.get("related_entry_ids", [])) <= known_entries,
                f"External Reception entry has an unresolved related entry: {entry.get('id')}")
        require(bool(entry.get("provenance", {}).get("basis")),
                f"External Reception entry is missing provenance: {entry.get('id')}")
        if entry.get("implementation_status") == "proposal-only":
            require("propos" in entry.get("summary", "").lower(),
                    f"Proposal-only entry must state proposal status: {entry.get('id')}")
    bioregistry = next((e for e in entries if e.get("id") == "bioregistry-dio-odi-prefix"), None)
    require(bioregistry is not None and bioregistry.get("category") == "registry-interoperability"
            and bioregistry.get("target_work_ids") == ["reference-vocabulary"],
            "BioRegistry prefix record must remain in the registry/interoperability category and target the Reference Vocabulary")
    semantic_farm = next((e for e in entries if e.get("id") == "semantic-farm-dio-odi-prefix"), None)
    require(semantic_farm is not None and semantic_farm.get("category") == "registry-interoperability"
            and semantic_farm.get("target_work_ids") == ["reference-vocabulary"],
            "Semantic Farm record must remain a distinct registry/resolver integration targeting the Reference Vocabulary")
    bartoc = next((e for e in entries if e.get("id") == "bartoc-dio-odi-vocabulary"), None)
    require(bartoc is not None and bartoc.get("category") == "registry-interoperability"
            and bartoc.get("content_kind") == "external-kos-catalogue-record"
            and bartoc.get("relation_to_work") == "catalogued-as-knowledge-organization-system"
            and bartoc.get("target_work_ids") == ["reference-vocabulary"],
            "BARTOC must remain a KOS catalogue record targeting the Reference Vocabulary, not a prefix/resolver registration")
    require(set(bartoc.get("related_entry_ids", [])) == {"bioregistry-dio-odi-prefix", "semantic-farm-dio-odi-prefix"},
            "BARTOC must retain explicit links to the distinct BioRegistry and Semantic Farm integrations")
    wren = next((e for e in entries if e.get("id") == "wren-castillo-entity-resolution-heterogeneous-sources"), None)
    require(wren is not None and wren.get("target_work_ids") == ["crisis-entity-resolution"],
            "Wren-Castillo must remain linked to Crisis of Entity Resolution")
    neo = next((e for e in entries if e.get("id") == "moltbook-neo-konsi-permission-escalation"), None)
    require(neo is not None and neo.get("citation_status") == "no-commit-boundary-citation-observed",
            "Adjacent neo_konsi thread must not be represented as a Commit Boundary citation")
    unghost = next((e for e in entries if e.get("id") == "unghost-agentic-er-loop-guardrail"), None)
    require(unghost is not None and "v1" in unghost.get("publication", {}).get("version_scope", ""),
            "unGhost entry must retain the arXiv v1 source boundary")
    page = read_text("external-reception/index.html")
    page_ids = set(re.findall(r'data-reception-id="([^"]+)"', page))
    require(page_ids == set(ids), "External Reception frontend inventory differs from registry JSON")
    ttl = read_text("metadata/external-reception.ttl")
    require("cito:cites" in ttl and "moltbook-neo-konsi-permission-escalation" in ttl
            and "bioregistry-dio-odi-prefix" in ttl,
            "External Reception RDF projection is missing citation and adjacent-discussion distinctions")
    require("rdfs:seeAlso <https://vocab.danielberanek.cz/external-reception/>" in ttl,
            "Commit-Boundary mapping must link to External Reception")
    for path in sorted(ROOT.rglob("*.html")):
        source = path.read_text(encoding="utf-8")
        if '<nav class="site-nav"' in source:
            require('href="/external-reception/"' in source,
                    f"Global navigation is missing External Reception link: {path.relative_to(ROOT)}")
    return {"external_reception_entries": len(entries), "external_reception_categories": len(registry.get("categories", []))}


def check_site_homepage() -> int:
    source = read_text("index.html")
    require('<link rel="canonical" href="https://vocab.danielberanek.cz/">' in source,
            "Homepage canonical must identify the site root")
    require('<meta name="robots" content="index,follow' in source,
            "Homepage must be indexable")
    require('http-equiv="refresh"' not in source.lower(),
            "Homepage must not redirect to the vocabulary page")
    for link in ('href="/dio-odi/"', 'href="/mappings/"',
                 'href="/metadata/"', 'href="/external-reception/"', 'href="/semantic-change-feed/"', 'href="https://danielberanek.cz/manifest-dio/"'):
        require(link in source, f"Homepage is missing navigation target: {link}")
    return 1


def check_sitemap() -> int:
    path = ROOT / "sitemap.xml"
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise AssertionError(f"Invalid sitemap.xml: {exc}") from exc
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    nodes = tree.findall(".//sm:url", namespace)
    locations = [node.findtext("sm:loc", namespaces=namespace) for node in nodes]
    require(all(locations), "Every sitemap URL entry must contain a loc value")
    require(len(locations) == len(set(locations)), "Sitemap contains duplicate URL entries")
    urls = {
        node.findtext("sm:loc", namespaces=namespace): node.findtext("sm:lastmod", namespaces=namespace)
        for node in nodes
    }
    required = [
        "https://vocab.danielberanek.cz/",
        "https://vocab.danielberanek.cz/dio-odi/",
        "https://vocab.danielberanek.cz/mappings/",
        "https://vocab.danielberanek.cz/metadata/",
        "https://vocab.danielberanek.cz/external-reception/",
        "https://vocab.danielberanek.cz/metadata/external-reception.json",
        "https://vocab.danielberanek.cz/metadata/external-reception.schema.json",
        "https://vocab.danielberanek.cz/metadata/external-reception.ttl",
        "https://vocab.danielberanek.cz/metadata/application-mappings.json",
        "https://vocab.danielberanek.cz/metadata/application-mappings.schema.json",
        "https://vocab.danielberanek.cz/metadata/research-genealogy.json",
        "https://vocab.danielberanek.cz/metadata/research-genealogy.schema.json",
        "https://vocab.danielberanek.cz/docs/research-genealogy.md",
        "https://vocab.danielberanek.cz/semantic-change-feed/",
        "https://vocab.danielberanek.cz/semantic-change-feed/events.json",
        "https://vocab.danielberanek.cz/semantic-change-feed/schema.json",
        "https://vocab.danielberanek.cz/mappings/rag-pipeline/",
        "https://vocab.danielberanek.cz/mappings/hem-dio/",
        "https://vocab.danielberanek.cz/mappings/commit-boundary-policy/",
        "https://vocab.danielberanek.cz/mappings/agentic-er-architecture/",
        "https://vocab.danielberanek.cz/examples/queries.rq",
    ]
    missing = [url for url in required if url not in urls]
    require(not missing, f"Sitemap is missing required pages: {missing}")
    require("https://vocab.danielberanek.cz/examples/queries.sparql" not in urls, "Legacy .sparql endpoint must not be listed in the sitemap; use the canonical .rq endpoint")

    for url, lastmod in urls.items():
        parsed = urlparse(url)
        require(
            parsed.scheme == "https" and parsed.netloc.lower() == SITE_HOST,
            f"Sitemap URL must use the canonical HTTPS host: {url}",
        )
        require(bool(lastmod), f"Sitemap entry is missing lastmod: {url}")
        try:
            sitemap_date = date.fromisoformat(lastmod)
        except ValueError as exc:
            raise AssertionError(f"Sitemap lastmod must be ISO 8601 date: {url} -> {lastmod!r}") from exc

        relative_path = unquote(parsed.path).lstrip("/")
        if not relative_path:
            relative_path = "index.html"
        elif relative_path.endswith("/"):
            relative_path += "index.html"

        target = (ROOT / relative_path).resolve()
        try:
            target.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise AssertionError(f"Sitemap URL escapes the repository root: {url}") from exc
        require(target.is_file(), f"Sitemap URL has no corresponding repository file: {url} -> {relative_path}")

        result = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", relative_path],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        require(
            result.returncode == 0 and bool(result.stdout.strip()),
            f"Could not determine the latest Git modification date for sitemap URL: {url}",
        )
        latest_commit_timestamp = datetime.fromisoformat(result.stdout.strip())
        latest_commit_date = latest_commit_timestamp.astimezone(timezone.utc).date()
        require(
            sitemap_date >= latest_commit_date,
            f"Sitemap lastmod is stale for {url}: {lastmod} is earlier than "
            f"the latest source change {latest_commit_date.isoformat()}",
        )

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
        counts.update(check_external_reception())
        counts.update(check_semantic_change_feed())
        counts["llms_metadata_checks"] = check_llms_txt()
    except Exception as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        return 1

    print("DIO/ODI Reference Model validation passed.")
    for key, value in counts.items():
        print(f"- {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

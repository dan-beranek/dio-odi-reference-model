# DIO/ODI Reference Model v0.9.0

## Release scope

This release archives the metadata-only namespace-prefix alignment of the live DIO/ODI Reference Vocabulary and the corresponding Semantic Change Feed update. It does not change the conceptual content of the vocabulary or the semantics of the derived Application Mappings.

## Reference Vocabulary v0.2.2

- Changes the preferred compact namespace prefix from `dio` to `dio-odi` to disambiguate it from the existing Bioregistry use of `dio`.
- Synchronizes the prefix across canonical Turtle/SKOS, JSON-LD, the embedded HTML JSON-LD graph, all four derived Application Mapping Turtle serializations, and example SPARQL queries.
- Preserves the canonical namespace URI `https://vocab.danielberanek.cz/dio-odi/#`, the ConceptScheme URI, and all 40 concept URIs.
- Preserves all concept labels, definitions, notes, hierarchy, provenance, and semantic relations.
- This is a metadata and serialization update only; it does not introduce a new concept-model version.

## Semantic Change Feed v0.1.1

- Appends event **SCF-2026-045** documenting the Vocabulary v0.2.2 prefix alignment.
- Increases the feed inventory from 44 to **45 documented events**.
- Extends the source-supported chronology through 9 November 2026.
- Preserves the append-only event model, existing event identifiers, temporal distinctions, and lineage.

The SCF JSON Schema remains v0.2.0. The feed remains an integrated provenance component of the Reference Model, not a separately published work or a Git commit log.

## Preserved components and boundaries

- The RAG, HEM × DIO, Commit-Boundary × Policy-as-Code, and Agentic ER application mappings remain derived and non-normative; their analytical semantics are unchanged.
- The Reference Model remains SKOS-first and is not presented as a completed formal OWL ontology.
- No implementation or empirical-validation claim is added.
- Earlier Reference Model releases remain immutable. Reference Model v0.8.0 remains the previous archived snapshot containing Vocabulary v0.2.1 and SCF v0.1.0.

## Validation

The repository validator checks the canonical Turtle and JSON-LD graph isomorphism, the 40-concept inventory, mapping graph integrity, embedded JSON-LD, metadata consistency, SCF schema conformance, event chronology and lineage, HTML/feed inventory parity, local links, sitemap, and site structure. The public-endpoint workflow separately checks deployed resources and MIME types on `main`.

## Version scope

- Reference Model: **v0.9.0**
- Reference Vocabulary: **v0.2.2**
- Semantic Change Feed: **v0.1.1** (45 records)
- Semantic Change Feed schema: **v0.2.0**
- Previous archived Reference Model release: **v0.8.0** — https://doi.org/10.5281/zenodo.24056601

The version-specific DOI for v0.9.0 is assigned by Zenodo after the GitHub release is published and archived.

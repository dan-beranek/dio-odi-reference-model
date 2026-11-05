# DIO/ODI Reference Model v0.6.0 — release candidate

**Status:** prepared for GitHub Release and Zenodo archiving. The archived v0.5.0 record remains the latest published release until v0.6.0 is archived.

## Scope

This release candidate archives the accumulated repository state since v0.5.0, not only the new Agentic ER mapping. The current main branch is 98 commits ahead of the v0.5.0 tag and includes updates to existing RAG, HEM, and Commit-Boundary × Policy-as-Code mappings; corpus metadata registries; vocabulary serializations and reference metadata; web frontends, indexes, and machine-readable discovery files.

## New architecture mapping

Agentic ER Commit-Boundary Architecture Mapping **v0.3.0** is aligned to production manuscript v55 (4 November 2026), prepared for arXiv v2.

- 120 local architecture concepts.
- 206 qualified relation assertions, each with source-section provenance, an interpretation note, and an epistemic status.
- Markdown, JSON-LD, and Turtle/RDF source representations.
- HTML frontend and SVG architecture overview.
- Explicit action classes: READ, STAGE_LOCAL, REVERSIBLE_WRITE, and IRREVERSIBLE_WRITE.
- Action-specific version binding and staging-isolation state; atomic version comparison and provisional shadow staging.
- Separate mutation-independent evidence-admission and mutation-specific claim-conflict checks.
- Versioned quarantine disposition, fresh admission before release, and restrictions on who may change authorization-eligibility metadata.

The mapping reuses canonical DIO/ODI identifiers and defines paper-specific constructs in its own namespace. It does not modify Reference Vocabulary v0.2.0 and does not claim implementation, formal proof, or empirical validation.

## Versioning

- Reference Model package: **0.6.0**.
- Agentic ER Architecture Mapping: **0.3.0**.
- Canonical Reference Vocabulary: **0.2.0** (unchanged).
- Previous archived Reference Model release: **0.5.0**, DOI <https://doi.org/10.5281/zenodo.23643845>.

The v0.6.0 version-specific DOI is intentionally not prepopulated. Zenodo assigns it after the GitHub Release is archived. Once the record is public, synchronize the minted DOI in the live metadata, README, and CITATION.cff; do not rewrite the immutable archived snapshot.

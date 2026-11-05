# DIO/ODI Reference Vocabulary v0.2.1

**Release date:** 2026-11-05  
**Release type:** Metadata-only maintenance update  
**Previous vocabulary version:** v0.2.0  
**Vocabulary concept DOI (all versions):** https://doi.org/10.5281/zenodo.23272897

## Scope

Version 0.2.1 synchronizes and enriches the vocabulary-level metadata across the canonical Turtle/SKOS serialization, standalone JSON-LD serialization, and the embedded JSON-LD graph on the public vocabulary page.

## Changes

- Replaces the literal creator name with the canonical person URI `https://danielberanek.cz/#person`.
- Describes that person as `schema:Person` and `dcterms:Agent`, with the ORCID URI `https://orcid.org/0009-0004-0050-0264` expressed using `schema:sameAs`.
- Adds Dublin Core metadata for title, license, issue date, modification date, and language.
- Adds VANN preferred namespace prefix and namespace URI metadata.
- Adds a FOAF page link to the public vocabulary documentation.
- Synchronizes the version metadata and author graph across both machine-readable serializations and the embedded HTML graph.

## Preservation statement

This is a metadata-only update. It does not add, remove, rename, redefine, or re-relate any SKOS concepts. All concept URIs, labels, definitions, notes, hierarchy, and provenance statements are preserved from v0.2.0. In particular, the historical status of `Entity Resolution Anomaly` is unchanged.

The archived Reference Model v0.6.0 remains an immutable snapshot containing Reference Vocabulary v0.2.0. This live vocabulary update does not rewrite that archive.

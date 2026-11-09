# DIO/ODI Reference Vocabulary v0.2.2

**Release date:** 2026-11-09  
**Release type:** Metadata-only maintenance update  
**Previous vocabulary version:** v0.2.1  
**Parent DIO/ODI Reference Model Concept DOI:** https://doi.org/10.5281/zenodo.23272897

## Scope

Version 0.2.2 aligns the preferred compact namespace prefix with the unambiguous Bioregistry candidate `dio-odi`. The change is confined to namespace-prefix metadata and compact-prefix aliases in serializations and examples. It does not alter the namespace URI or any concept identifier.

## Changes

- Changes `vann:preferredNamespacePrefix` from `dio` to `dio-odi`.
- Uses `dio-odi:` consistently as the local Turtle prefix in the canonical vocabulary and all four derived Application Mapping Turtle serializations.
- Updates the JSON-LD context and compact identifiers in the canonical Vocabulary JSON-LD and the embedded SKOS JSON-LD graph on the public vocabulary page.
- Updates the example SPARQL queries to use `PREFIX dio-odi:`.
- Synchronizes the vocabulary version and modification metadata across the canonical Turtle, JSON-LD, DCAT, and embedded HTML representations.

## Preservation statement

This is a metadata- and serialization-only update. The canonical namespace URI remains:

`https://vocab.danielberanek.cz/dio-odi/#`

The canonical ConceptScheme URI and all 40 concept URIs remain unchanged. Labels, definitions, notes, hierarchy, provenance, and the semantics of all derived Application Mappings are preserved. Only the compact prefix used to abbreviate the existing IRIs changes.

The archived Reference Model v0.8.0 remains an immutable snapshot containing Reference Vocabulary v0.2.1. This live vocabulary update does not rewrite that archive; v0.2.2 can be included in a subsequent Reference Model archive.

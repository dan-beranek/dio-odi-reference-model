# DIO/ODI Reference Model v0.8.0

## Release scope

This release adds the **DIO/ODI Semantic Change Feed (SCF)** as an integrated provenance component of the Reference Model. It is not a separate publication and does not receive an independent DOI.

- **Semantic Change Feed:** v0.1.0
- **SCF JSON Schema:** v0.2.0
- **Event inventory:** 44 documented records, covering the dated DIO/ODI Hub Changelog entries from 25 March through 25 October 2026 and subsequent source-supported milestones through 7 November 2026.
- **Representations:** machine-readable JSON event registry, JSON Schema, human-readable HTML frontend, and technical README.
- **Governance:** append-only event identifiers; explicit temporal basis; source-linked evidence; lineage-based corrections and replacements.
- **Boundary:** SCF is not a Git commit log and does not replace the Hub Changelog, canonical Reference Vocabulary, Application Mappings, or Corpus Metadata Registry.

## Carried-forward components

- **Reference Vocabulary v0.2.1** remains unchanged; its concept inventory and semantic relations are not modified by this release.
- Existing RAG, HEM, Commit-Boundary × Policy-as-Code, and Agentic ER application mappings are carried forward without claiming implementation or empirical validation.
- Existing persistent concept identifiers and namespace are preserved.

## Validation

The repository validator checks the feed against its JSON Schema, event ID uniqueness, chronological order, lineage references, HTML/feed inventory parity, navigation, and sitemap presence. The public-endpoint workflow checks deployed resources and MIME types.

## Version scope

- Reference Model: **v0.8.0**
- Reference Vocabulary: **v0.2.1** (unchanged)
- Semantic Change Feed: **v0.1.0**
- Semantic Change Feed schema: **v0.2.0**
- Previous archived Reference Model release: **v0.7.0** — https://doi.org/10.5281/zenodo.24020300

The version-specific DOI for this release is https://doi.org/10.5281/zenodo.24056601.

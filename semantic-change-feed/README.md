# DIO/ODI Semantic Change Feed

**Feed version:** 0.1.0  
**Schema version:** 0.1.0  
**Status:** Initial curated historical register  
**Maintainer:** Daniel Beránek  
**License:** CC BY 4.0

## Purpose

The Semantic Change Feed (SCF) is a versioned, append-only register of changes that materially affect the meaning, structure, provenance, application, or reconstructability of the DIO/ODI reference system. It is not a Git commit log: a file change is not automatically a semantic event, and Git diffs are not authoritative evidence of conceptual intent.

## Public resources

- Human-readable frontend: https://vocab.danielberanek.cz/semantic-change-feed/
- Canonical event feed: https://vocab.danielberanek.cz/semantic-change-feed/events.json
- JSON Schema: https://vocab.danielberanek.cz/semantic-change-feed/schema.json
- Source repository: https://github.com/dan-beranek/dio-odi-reference-model/tree/main/semantic-change-feed

## Architectural boundary

- **Reference Vocabulary** remains authoritative for current canonical concept identifiers, labels, definitions, and SKOS relations.
- **Application Mappings** remain derived, non-normative analytical projections.
- **Corpus Metadata Registry** remains authoritative for publication identities, versions, references, distributions, and inter-work relations.
- **Reference Model releases** remain immutable versioned research-software snapshots.
- **Changelog and release notes** remain concise release-oriented summaries.

The SCF links these resources through explicit events and lineage. It does not redefine them.

## Record model

Each event has a stable identifier (SCF-YYYY-NNN) and records its temporal basis, classification, operation, scope, previous and resulting state, preserved invariants, impact, evidence, and lineage.

Event classes: Conceptual, Relational, Theoretical, Structural, Provenance, Mapping, Artifact, Distribution.

Operations: introduced, refined, reclassified, extended, synchronized, archived, corrected, deprecated.

A record's date is not assumed to be the exact edit timestamp. The `date_basis` field specifies whether it is a publication date, first archival inclusion, version publication date, or archive publication date. The `evidence.status` field distinguishes documented claims from reconstructed or partially documented history.

## Append-only and correction policy

Published identifiers are stable. New events are appended; historical events are not silently deleted or rewritten. A correction is a new event linked through `lineage.corrects`; a replacement is linked through `lineage.supersedes`.

## Initial historical coverage

Version 0.1.0 captures seven selected events from 8 October to 6 November 2026. This bootstrap is selective, not exhaustive; earlier events may be added only where dates, scope, and source evidence can be stated without conjecture.

## Validation

The repository validator checks the feed against `schema.json`, unique IDs, chronological order, HTML/feed inventory parity, lineage references, shared navigation, and sitemap presence. The public-endpoint workflow checks deployment and MIME types.

## License

The files are licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

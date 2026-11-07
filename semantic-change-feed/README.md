# DIO/ODI Semantic Change Feed

**Feed version:** 0.1.0  
**Schema version:** 0.2.0  
**Status:** Full Hub Changelog coverage plus subsequent release history  
**Maintainer:** Daniel Beránek  
**License:** CC BY 4.0

## Purpose

The Semantic Change Feed (SCF) is a curated, append-only record of documented events that materially affect the DIO/ODI conceptual system, publications, vocabulary, application mappings, provenance, distributions, and versioned reference artifacts.

It is not a Git commit log. Repository diffs are not authoritative evidence of conceptual intent, and dates in the feed must not be read as source-control timestamps unless explicitly stated.

## Coverage

Version 0.1.0 contains **43 event records** and covers:

- Every dated entry in the DIO/ODI Hub Changelog from **25 March through 25 October 2026**.
- Subsequent documented vocabulary, mapping, publication, provenance, and Reference Model archive milestones through **6 November 2026**.
- Publication of the public **DIO to DIO** portfolio of ten author-led, model-specific reconstruction analyses.
- Compound Changelog bullets split into separate records where they describe distinct conceptual, publication, distribution, mapping, or archival events.

This is complete coverage of the dated Hub Changelog entries, not a claim that every repository commit or every undated intermediate artifact has its own event.

## Public resources

- Human-readable frontend: https://vocab.danielberanek.cz/semantic-change-feed/
- Canonical event feed: https://vocab.danielberanek.cz/semantic-change-feed/events.json
- JSON Schema: https://vocab.danielberanek.cz/semantic-change-feed/schema.json
- Primary historical source: https://danielberanek.cz/manifest-dio/
- Source repository: https://github.com/dan-beranek/dio-odi-reference-model/tree/main/semantic-change-feed

## Architectural boundary

- **Reference Vocabulary** remains authoritative for current canonical concept identifiers, labels, definitions, and SKOS relations.
- **Application Mappings** remain derived, non-normative analytical projections.
- **Corpus Metadata Registry** remains authoritative for publication identities, versions, references, distributions, and inter-work relations.
- **Reference Model releases** remain immutable versioned research-software snapshots.
- **The Hub Changelog** remains the author-maintained public chronology; SCF provides a structured, machine-readable event model and source-linked event granularity.

The SCF does not replace or redefine any of these sources.

The DIO to DIO portfolio is included as a documented research-and-distribution milestone, not as an authority for historical claims. Its model-specific analyses retain different observation boundaries and interpretations; they may guide discovery of potentially relevant evidence, but factual claims entering the SCF must be checked against primary publications, release records, registries, or archives.

## Record model

Each event has a stable identifier (SCF-YYYY-NNN) and records classification, operation, scope, previous and resulting state, preserved invariants, impact, evidence, and lineage.

Event classes: Conceptual, Relational, Theoretical, Structural, Provenance, Mapping, Artifact, Distribution, ResearchProcess.

Operations: introduced, refined, reclassified, extended, synchronized, archived, corrected, deprecated, published, documented, distributed.

### Temporal discipline

The `date_basis` field distinguishes:

- `hub_changelog_date` — date stated in the author-maintained Hub Changelog.
- `activity_period` — bounded period stated by the Changelog; `date_range_start` and `date_range_end` preserve the interval.
- `publication_date` — date of a publication.
- `first_archival_inclusion` — first archived package state containing a component change.
- `version_publication_date` — publication date of a versioned component.
- `archive_publication_date` — publication date of an immutable Reference Model archive.

A date from the Hub Changelog is not silently converted into an exact edit or commit timestamp.

## Append-only and correction policy

Published identifiers are stable. New events are appended; historical events are not silently deleted or rewritten. A correction is a new event linked through `lineage.corrects`; a replacement is linked through `lineage.supersedes`. Related events are linked only where their relationship is source-supported.

## Validation

The repository validator checks JSON Schema conformance, event ID uniqueness, chronological order, lineage references, HTML/feed inventory parity, shared navigation, and sitemap presence. The public-endpoint workflow checks deployment and MIME types on `main`.

## License

The files are licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

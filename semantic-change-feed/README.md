# DIO/ODI Semantic Change Feed

**Feed version:** 0.1.3  
**Schema version:** 0.2.1  
**Status:** Live append-only maintenance after archived Reference Model v0.9.0; no new Reference Model release  
**Maintainer:** Daniel Beránek  
**License:** CC BY 4.0

## Purpose

The Semantic Change Feed (SCF) is a curated, append-only record of documented events that materially affect the DIO/ODI conceptual system, publications, vocabulary, application mappings, provenance, distributions, and versioned reference artifacts.

It is not a Git commit log. Repository diffs are not authoritative evidence of conceptual intent, and dates in the feed must not be read as source-control timestamps unless explicitly stated.

## Coverage

Version 0.1.3 contains **49 event records** and covers:

- Every dated entry in the DIO/ODI Hub Changelog from **25 March through 25 October 2026**.
- Subsequent documented vocabulary, mapping, publication, provenance, and deployment milestones through **9 November 2026**, plus two previously omitted archive milestones reconciled into the live chronology on **10 November 2026**.
- Initial publication of the public **DIO to DIO** portfolio with ten author-led, model-specific reconstruction analyses, followed by a separate event recording the addition of the eleventh report (Claude Sonnet 5.5) on 7 November 2026.
- Compound Changelog bullets split into separate records where they describe distinct conceptual, publication, distribution, mapping, or archival events.
- The live Reference Vocabulary v0.2.2 metadata-only prefix-alignment update on 9 November 2026.
- The canonical SPARQL query endpoint at `examples/queries.rq`, publicly deployed on 9 November 2026 with `application/sparql-query`; the former `.sparql` path remains a legacy compatibility copy.
- The public read-only DIO/ODI MCP service deployment and 31/31 production smoke validation on 11 November 2026, recorded as SCF-2026-049.
- Explicit chronology entries for archived Reference Model v0.8.0 and v0.9.0. These entries were added to the live feed on 10 November 2026 while preserving the releases' actual publication dates and immutable component snapshots.

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

The archived Reference Model v0.9.0 (https://doi.org/10.5281/zenodo.24085589) contains SCF v0.1.1 with 45 events and schema v0.2.0. The live feed now advances independently to v0.1.3 with 49 events and schema v0.2.1. The archive-reconciliation records, SPARQL endpoint record, and MCP integration-service deployment record are live maintenance only: neither v0.8.0 nor v0.9.0 is rewritten, and no new Reference Model archive or DOI is created.

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
- `deployment_date` — date of a successful public deployment of a technical artifact; it is not assumed to be the source commit or merge date.
- `documentation_date` — date on which a previously completed, source-verified historical milestone was first added to the live feed. Its original event date must be stated separately in the temporal note and evidence.

A date from the Hub Changelog is not silently converted into an exact edit or commit timestamp. A `documentation_date` preserves append-only chronology when a historical event is reconciled after its original date; it must never replace or obscure the underlying publication or archive date.

## Append-only and correction policy

Published identifiers are stable. New events are appended; historical events are not silently deleted or rewritten. A correction is a new event linked through `lineage.corrects`; a replacement is linked through `lineage.supersedes`. Related events are linked only where their relationship is source-supported.

## Validation

The repository validator checks JSON Schema conformance, event ID uniqueness, chronological order, lineage references, archive-snapshot reconciliation, HTML/feed inventory parity, shared navigation, and sitemap presence. The public-endpoint workflow checks deployment and MIME types on `main`.

## License

The files are licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

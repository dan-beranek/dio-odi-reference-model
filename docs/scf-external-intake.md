# SCF external evidence intake

The external intake workflow prepares review-only observations from selected public registries and publication interfaces. It complements, but does not replace, the source-registry and GitHub operational intake workflows.

## Monitored sources

### BioRegistry and Semantic Farm

The scanner checks the dio-odi prefix through both public API surfaces:

- BioRegistry: https://bioregistry.io/api/registry/dio-odi?format=json
- Semantic Farm: https://semantic.farm/api/registry/dio-odi?format=json

Semantic Farm exposes the same upstream Bioregistry record through a second interface. The two responses are compared for consistency, but are not counted as independent registrations or independent confirmations.

The scanner also inspects the upstream Bioregistry data file src/bioregistry/data/bioregistry.json through GitHub commit history from the review date recorded in the canonical External Reception Registry. Only diffs that touch the exact dio-odi record are candidates. The upstream commit timestamp is evidence of a data change, not automatically the public registry refresh date.

### BARTOC

The scanner retrieves the BARTOC JSKOS record for the DIO/ODI Reference Vocabulary through its public data API:

- Record: https://bartoc.org/en/node/21188
- JSKOS data: https://bartoc.org/api/data?uri=http%3A%2F%2Fbartoc.org%2Fen%2Fnode%2F21188

It checks the record's modified timestamp (or the HTTP Last-Modified header) against the last reviewed date in metadata/external-reception.json. A newer timestamp triggers review; it does not establish that the changed fields are material to the SCF.

### FAIRsharing

The DIO/ODI Reference Vocabulary has a public FAIRsharing record at https://fairsharing.org/9470, documented in SCF-2026-061. This record is currently handled through manual source review and is not queried by the automated intake workflow.

### arXiv

The scanner checks the Atom API record for arXiv 2610.37407 and compares the current version and update timestamp with the canonical state in metadata/works.json. A new version or a timestamp newer than the recorded version is surfaced for review.

### Hashnode and DEV.to

The scanner reads the Hashnode publication RSS feed, the public DEV.to articles API for the danielberanek account, and the Medium profile RSS feed at https://seo-spec-copy-daniel-beranek.medium.com/feed. It filters or maps the known DIO/ODI and Agentic Entity Resolution representations, then groups them by the canonical work URL.

Hashnode remains the canonical publication for “The Match Is Easy, the Merge Is Not”. DEV.to and Medium are secondary representations of that same work and are attached to the Hashnode canonical URL. The Medium mirror is matched by its known article URL; it is not treated as a separate publication work. LinkedIn is not scraped: the existing LinkedIn architectural overview is a separate work, and no suitable public API is configured for this read-only monitor.

## Deliberate exclusions

- The workflow does not treat BioRegistry and Semantic Farm as two independent registry integrations.
- Registry entries are compared with canonical resource identities and existing SCF citations before candidate changes are prepared.
- It does not scrape LinkedIn or infer a publication date from an inaccessible profile.
- TIB terminology services are not included yet; they require a stable, directly addressable public record identifier and a source interface that can be checked reliably.
- The workflow does not modify metadata/external-reception.json, metadata/works.json, metadata/distributions.json, or semantic-change-feed/events.json.

## Output and schedule

The scheduled workflow runs daily at 06:47 UTC. A manual run can use a publication lookback between 1 and 720 hours; the default is 168 hours (seven days).

Each run creates:

- scf-external-candidates.json — structured observations, source fingerprints, canonical URLs, timestamps, current feed matches, and source-check results.
- scf-external-candidates.md — a human-readable review queue.

The files are uploaded as a GitHub Actions artifact for 30 days, and the Markdown report is added to the Actions workflow summary. Source errors make scan_complete false and fail the workflow rather than presenting a partial scan as complete.

## Editorial boundary

A changed registry payload, a newer record-modified timestamp, an upstream commit, a new arXiv version, or a newly observed article is a candidate signal only. The scanner does not allocate SCF event IDs, classify semantic change, assign impact or lineage, infer a definitive event date, write the feed, increment its version, create an archive, or deploy the site.

Any SCF inclusion remains an editorial decision grounded in the primary record, its actual before/after state, temporal basis, scope, impact, preserved invariants, and lineage. Exact evidence URL matching helps identify existing event citations; it is not a complete semantic duplicate detector.

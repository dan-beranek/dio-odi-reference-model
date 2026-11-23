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

### arXiv

The scanner checks the Atom API record for arXiv 2610.37407 and compares the current version and update timestamp with the canonical state in metadata/works.json. A new version or a timestamp newer than the recorded version is surfaced for review.

### Hashnode and DEV.to

The scanner reads the Hashnode publication RSS feed and the public DEV.to articles API for the danielberanek account. It filters for relevant DIO/ODI and Agentic Entity Resolution content, then groups syndicated representations by canonical URL.

Hashnode is the canonical publication source for “The Match Is Easy, the Merge Is Not”; DEV.to is a secondary representation. The two are not counted as separate works. LinkedIn is not scraped: the existing LinkedIn architectural overview is a separate work, and no suitable public API is configured for this read-only monitor.

## Deliberate exclusions

- The workflow does not treat BioRegistry and Semantic Farm as two independent registry integrations.
- It does not infer scholarly citation, independent review, endorsement, adoption, or implementation from a registry listing.
- It does not scrape LinkedIn or infer a publication date from an inaccessible profile.
- TIB terminology services and FAIRsharing are not included yet. They require stable, directly addressable public record identifiers and a source interface that can be checked reliably; a submitted URL or an unconfirmed record is not enough.
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

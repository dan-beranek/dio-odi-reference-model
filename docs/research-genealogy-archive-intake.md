# Research Genealogy — SlideShare / Wayback archive intake

## Purpose

The archive intake creates a review-only inventory of Wayback Machine captures for the SlideShare source collection recorded in metadata/research-genealogy.json.

It reads three types of evidence:

1. SlideShare presentation URLs already recorded in the canonical Research Genealogy registry.
2. Presentation links exposed in the current public SlideShare profile HTML.
3. Presentation links exposed in inspected archived HTML snapshots of that profile.

It then queries the Internet Archive CDX index for each discovered presentation URL and writes a JSON report plus a Markdown summary as a GitHub Actions artifact.

## What it does not do

- It does not edit metadata/research-genealogy.json.
- It does not infer original publication dates, upload dates, or creation dates from archive timestamps.
- It does not merge records merely because titles or topics are similar.
- It does not treat multiple captures, redirects, host aliases, or duplicate digests as separate research outputs.
- It does not claim an exhaustive inventory of all SlideShare uploads.

SlideShare's public API has been retired and Scribd states that there is no replacement API. The intake therefore uses only the publicly rendered profile HTML and the documented Internet Archive CDX interface. Profile HTML may expose only a subset of uploads in a given response; historic profile captures may also be incomplete. The report explicitly marks its inventory as partial.

## Run manually

Repository → Actions → **Research Genealogy archive intake** → Run workflow.

Inputs:

| Input | Default | Purpose |
|---|---:|---|
| profile_snapshot_limit | 40 | Maximum number of archived profile snapshots fetched for link extraction |
| url_limit | 150 | Safety limit for distinct presentation URLs queried |
| delay_seconds | 0.15 | Delay between requests to the public CDX service |

The workflow also runs weekly and on pull requests that modify the scanner, its tests, or its supporting metadata and documentation.

## Output

The workflow artifact contains:

- research-genealogy-archive-candidates.json — complete query report, profile observations, each URL's registry match, CDX capture timestamps, status codes, MIME types, digests, lengths, and Wayback replay URLs.
- research-genealogy-archive-candidates.md — concise review summary, coverage assessment, source observations, and outstanding errors.

Artifacts are retained for 30 days. The workflow also writes the Markdown report to the Actions run summary.

## Curation procedure

For every unmatched candidate:

1. Open the public presentation page and verify the uploader/profile attribution.
2. Inspect the CDX replay and confirm that the original URL matches the page, not merely a redirect or a similarly named item.
3. Compare the presentation's content with existing research works and artefacts.
4. Classify the result as a distinct output, an alternative manifestation of an existing output, or unresolved.
5. Only after those checks, add a matching artefact or archive observation to the canonical registry in a separate reviewed change.

CDX timestamps document archive capture observations. They can establish that a particular URL representation was captured at or before a given time; they do not by themselves establish when the work was created or uploaded.

## Technical references

- Internet Archive Wayback CDX Server documentation: https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/README.md
- SlideShare API retirement notice: https://support.scribd.com/hc/en-us/articles/53231623793684-Slideshare-API-errors-the-public-API-has-been-retired
- SlideShare profile help: https://support.scribd.com/hc/en-us/articles/360055257592-Your-Slideshare-profile

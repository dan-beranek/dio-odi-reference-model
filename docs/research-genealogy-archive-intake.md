# Research Genealogy — SlideShare / Wayback archive intake

## Purpose

The archive intake creates a review-only inventory of Wayback Machine captures for the SlideShare source collection recorded in metadata/research-genealogy.json.

It reads four types of evidence:

1. Primary SlideShare artefact URLs and nested SlideShare publication-manifestation URLs already recorded in the canonical Research Genealogy registry.
2. Presentation links exposed in the current public SlideShare profile HTML or its rendered DOM after ordinary browser navigation and scrolling.
3. Presentation links exposed in inspected archived HTML snapshots of that profile.
4. Direct presentation URLs returned by Tavily's indexed-web search, filtered to SlideShare presentation paths and retained as discovery leads.

It then queries the Internet Archive CDX index for each discovered presentation URL and writes a JSON report plus a Markdown summary as a GitHub Actions artifact.

## What it does not do

- It does not edit metadata/research-genealogy.json.
- It does not infer original publication dates, upload dates, or creation dates from archive timestamps.
- It does not merge records merely because titles or topics are similar.
- It does not treat multiple captures, redirects, host aliases, or duplicate digests as separate research outputs.
- It does not claim an exhaustive inventory of all SlideShare uploads.

SlideShare's public API has been retired and Scribd states that there is no replacement API. The intake therefore uses the public profile HTML, a headless Chromium session that renders the publicly accessible presentation tab and scrolls its visible content, optional Tavily indexed-web search for direct presentation URLs, and the documented Internet Archive CDX interface. Profile HTML may expose only a subset of uploads in a given response; historic profile captures may also be incomplete. Tavily may only return pages currently present in its search index, and a search result is not proof of authorship, uploader attribution, publication date, or identity with an existing output. The report explicitly marks its inventory as partial.

## Run manually

Repository → Actions → **Research Genealogy archive intake** → Run workflow.

Inputs:

| Input | Default | Purpose |
|---|---:|---|
| profile_snapshot_limit | 40 | Maximum number of archived profile snapshots fetched for link extraction |
| url_limit | 150 | Safety limit for distinct presentation URLs queried |
| delay_seconds | 0.15 | Delay between requests to the public CDX service |

The optional repository Actions secret `TAVILY_API_KEY` enables four basic indexed-web queries only when the workflow is started manually with **Enable Tavily indexed-web discovery** turned on. Scheduled and pull-request runs do not consume Tavily API credits. Without that manual opt-in, the report explicitly marks Tavily as disabled and continues with profile and archive sources only. If Tavily returns HTTP 432 because the plan usage limit has been reached, the scanner stops after the first blocked request and records the plan-limit state.

The workflow also runs weekly and on pull requests that modify the scanner, its tests, or its supporting metadata and documentation.

## Output

The workflow installs Playwright/Chromium for the public-profile rendering step. If the rendered page still exposes no presentation links, the report marks that discovery state explicitly; a successful CDX query of previously known URLs must not be mistaken for a complete profile inventory.

The workflow queries both primary SlideShare artefacts and nested SlideShare representations (for example, language editions and condensed presentation manifestations). Its summary keeps the counts for underlying artefacts and nested representations separate.

The workflow artifact contains:

- research-genealogy-archive-candidates.json — complete query report, profile observations, each URL's discovery source, parent artefact or nested representation match, candidate labels/snippets where available, CDX capture timestamps, status codes, MIME types, digests, lengths, and Wayback replay URLs. Provider status records whether Tavily was enabled and how many requests and direct SlideShare candidates it returned.
- research-genealogy-archive-candidates.md — concise review summary, separate primary-artefact and nested-representation counts, coverage assessment, source observations, and outstanding errors.

Artifacts are retained for 30 days. The workflow also writes the Markdown report to the Actions run summary.

## Curation procedure

For every unmatched candidate:

1. Open the public presentation page and verify the uploader/profile attribution, especially for URLs found only through indexed-web search.
2. Inspect the CDX replay and confirm that the original URL matches the page, not merely a redirect or a similarly named item.
3. Compare the presentation's content with existing research works and artefacts.
4. Classify the result as a distinct output, an alternative manifestation of an existing output, or unresolved.
5. Only after those checks, add a matching artefact or archive observation to the canonical registry in a separate reviewed change. Do not treat a Tavily snippet or candidate URL as sufficient evidence for an artifact record.

CDX timestamps document archive capture observations. They can establish that a particular URL representation was captured at or before a given time; they do not by themselves establish when the work was created or uploaded.

## Technical references

- Internet Archive Wayback CDX Server documentation: https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/README.md
- SlideShare API retirement notice: https://support.scribd.com/hc/en-us/articles/53231623793684-Slideshare-API-errors-the-public-API-has-been-retired
- SlideShare profile help: https://support.scribd.com/hc/en-us/articles/360055257592-Your-Slideshare-profile


## Discovery-state interpretation

- `profile-links-extracted` — at least one current-profile presentation URL was extracted and the profile count was visible.
- `profile-links-extracted-count-not-observed` — presentation URLs were extracted, but the profile's displayed total was not readable.
- `profile-count-visible-but-links-not-extracted` — the page exposed its total, but no presentation links were extracted; this is an explicit discovery failure, not a zero-item inventory.
- `no-profile-links-or-count-extracted` — neither a displayed total nor presentation links were captured; only registry-known URLs and archive observations can be reported.

When the profile total is unavailable, the report displays the count-to-link difference as `not measurable`, not zero.

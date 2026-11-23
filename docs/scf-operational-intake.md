# SCF operational evidence intake

The operational intake workflow reads public GitHub metadata from six DIO/ODI project repositories:

- dan-beranek/dio-odi-reference-model — successful GitHub Pages deployment workflow.
- dan-beranek/dio-odi-mcp — successful Cloudflare Worker deployment workflow.
- dan-beranek-apps/agentic-entity-resolution-guardrail-planner — successful Planner frontend deployment workflow.
- dan-beranek/dio-odi-autorsky-koncept — successful bilingual site deployment workflow.
- dan-beranek/dio-to-dio — successful DIO to DIO site deployment workflow.
- dan-beranek-apps/dan-beranek-apps.github.io — successful Apps directory Pages deployment workflow.

The scanner also checks published, non-draft, non-prerelease GitHub Releases in those repositories.

## Output

A scheduled or manually triggered run creates:

- scf-operational-candidates.json — structured observations, source URLs, commit SHAs, timestamps, and reference status.
- scf-operational-candidates.md — a human-readable review queue.

The default lookback is 48 hours. The workflow runs daily and can be manually run with a different lookback (1–720 hours). Reports are uploaded as GitHub Actions artifacts and retained for 30 days.

## Matching against the canonical feed

The scanner extracts exact evidence URLs already cited by events in semantic-change-feed/events.json. Observations whose GitHub URL is already present are marked already-cited and include the matching SCF event IDs. New URLs are marked review-required; this is a queue for review, not a claim that the SCF is incomplete.

## Deliberate boundary

Only exact allow-listed deployment workflow names are considered. CI and validation-only workflows are not treated as deployments. Failed, cancelled, in-progress, draft, prerelease, and unpublished records are ignored.

A successful deployment workflow is operational evidence, but workflow completion time is only a candidate date and is not automatically accepted as the public deployment date. A GitHub Release publication timestamp is retained as source metadata, but the release still requires an editorial decision about whether and how it should be represented in the SCF.

The workflow uses read-only repository permissions and reads public GitHub API endpoints. It does not write to other repositories, allocate SCF event IDs, modify events.json, increment the feed version, create Reference Model archives, or deploy the SCF website. API errors are reported and fail the run so a partial scan is not silently presented as complete.

# SCF discovery-first evidence intake

The discovery intake is a broad, query-led discovery layer. It complements the three existing read-only intake workflows; it does not replace their more precise checks of known registries, project deployments, releases, or configured public records.

## Discovery model

The engine starts from the canonical DIO/ODI identity and works outward. It does not maintain a preferred list of publication platforms or a fixed list of external registries.

The query profile in discovery/query-profile.json currently supplies:

- the canonical identity phrases Digital Identity Optimization, Ontology of Digital Identity, and DIO/ODI;
- the author's ORCID and a name query coupled to the full identity phrase;
- distinctive concept anchors validated against the canonical keyword grammar in metadata/keywords.json;
- exact titles and the works' own version/concept DOI and arXiv identifiers drawn from the canonical works registry in metadata/works.json.

The profile can be extended when the identity vocabulary changes. Work-title queries are derived from the work registry rather than duplicated as another manually maintained publication inventory. A small number of distinctive concept anchors are selected deliberately; the engine does not send every generic keyword to a search provider.

## Search providers

The collector uses adapters rather than a platform allowlist:

- **Tavily Search** provides general indexed-web discovery. Configure the repository Actions secret TAVILY_API_KEY to enable it. Without that secret, the workflow still checks scholarly metadata indexes but labels the run scholarly-only; it must not be described as a broad web scan.
- **OpenAlex** searches scholarly works and author/work metadata. Basic queries are available without a key; an optional OPENALEX_API_KEY Actions secret can be supplied for the account's larger daily budget.
- **Crossref** searches registered scholarly metadata through the public Works API. The collector uses the public author contact in metadata/works.json as its polite-pool mailto parameter.

The initial implementation deliberately uses public metadata and short search-result snippets. It does not crawl full pages, scrape social-network interfaces, or infer platform support. When discovery identifies a useful source with a stable record, feed, API, or change history, that source can later be added to a targeted monitor where appropriate.

The workflow runs daily at 07:17 UTC and can also be started manually. Search queries are not limited to a publication-date window: a page newly indexed today may describe an older event, and a current search result is not reliable evidence of when the underlying event occurred.

## Provider failure isolation

Each provider is evaluated independently and its query count, returned observations, completion state, and errors remain visible in the report.

When Tavily is configured, a fully completed Tavily scan is the workflow's acceptance criterion. An unavailable supplemental scholarly provider (for example, OpenAlex returning HTTP 429) is reported as a provider gap but does not mark the completed general-web scan as failed. The coverage label distinguishes web-and-scholarly from general-web-only when neither scholarly index completes.

When Tavily is not configured, the run remains scholarly-only and requires at least one scholarly metadata provider to complete. If no enabled provider completes, the workflow fails rather than presenting an empty or partial run as a successful scan.

## Candidate resolution

Results are normalised and deduplicated by the discovered object's own DOI when available, otherwise by URL. A DOI or arXiv identifier merely cited in a result is retained as a reference to a related canonical work; it is never substituted for the discovered page's own identity. The collector retains provider and query provenance so that two search services returning the same work appear as one candidate with multiple observations.

Deterministic relevance signals include distinctive DIO/ODI phrases, exact canonical work titles, known DOI/arXiv identifiers, and distinctive keyword anchors corroborated by identity context. The broader phrase Digital Identity Optimization alone is treated as ambiguous: it must be corroborated by the author name/ORCID or a distinctive concept. An author identifier alone, an author name alone, or a generic acronym match is insufficient.

Each candidate is compared against the canonical work and distribution metadata and the exact evidence URLs already present in the SCF. The resulting statuses are:

- already-cited — an exact evidence URL is already cited by one or more SCF events;
- already-registered — the URL or DOI is present in the current metadata registries but not found as an exact SCF evidence URL;
- review-required — the result is not matched to an existing canonical record.

These are matching outcomes, not semantic judgments. A result may still be a duplicate, an incidental mention, a syndicated copy, a low-quality index page, an AI-generated summary, or an unrelated use of similar terminology. Exact matching does not establish semantic equivalence.

## Output and operational boundary

Each run creates:

- scf-discovery-candidates.json — structured candidate records, snippets, URLs, identifiers, dates, relevance signals, query provenance, provider observations, and current reference status;
- scf-discovery-candidates.md — a human-readable triage report containing query and provider coverage.

Reports are uploaded as GitHub Actions artifacts for 30 days and the Markdown report is added to the workflow summary. An API error from an enabled provider is reported as an incomplete scan; missing Tavily credentials are not silently passed off as general-web coverage.

Zenodo record landing pages are matched to registered Zenodo DOIs through their numeric record IDs. This prevents already registered archived versions from reappearing as new review candidates merely because a search provider returned the `zenodo.org/records/{id}` URL instead of the DOI URL.

The collector is review-only. It does not assign SCF event IDs, classify semantic change, decide whether an event is material, establish a definitive event date, update the External Reception Registry or any other canonical registry, modify semantic-change-feed/events.json, increment the feed version, create an archive, open issues, or deploy the site. All discovered items remain candidates for editorial assessment against primary evidence.

The workflow reads the canonical registries but does not make any changes to them. No search provider is treated as an authority for DIO/ODI identity or for the truth of a candidate's claims.

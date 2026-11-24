# Research Genealogy — content and provenance reconciliation protocol

## Purpose

This protocol governs the transition from a locator inventory to a content-grounded Research Genealogy. It separates the identity of an underlying research output from the platform pages, files, shared conversations, deployed applications, and archive captures through which that output is exposed or preserved.

The goal is not to maximize the number of records. It is to preserve the correct identity, lineage, and temporal status of each output without merging distinct works or counting alternate manifestations as separate research.

## Record layers

The curation process works with five layers:

1. **Research object** — a source or subject examined during a research process, such as the professional ethnography or the author's professional digital identity as an E-E-A-T assessment subject.
2. **Underlying output** — a substantive analysis, report, synthesis, interpretation, presentation authored as a distinct work, or other result of a research activity.
3. **Publication manifestation** — a specific publication surface or format: shared AI conversation, hosted page, Canvas artifact, deployed web application, PDF, SlideShare deck, or another public representation of an underlying output.
4. **Archive observation** — a timestamped capture of a publication manifestation, including its archive service, original target URL, timestamp basis, digest, HTTP status, and MIME type where available.
5. **Discovery lead** — a locator, reference, or indirect mention whose exact relationship to an underlying output has not been established.

A single underlying output may have multiple manifestations and many archive observations. A single publication manifestation may also contain more than one underlying output, such as a report collection or a meta-analysis that names multiple source reports. Record structure must preserve that cardinality rather than flattening everything into one list of URLs.

## Evidence hierarchy

Use the strongest available evidence for each assertion:

| Level | Evidence | What it can establish |
|---|---|---|
| A | Directly readable output content or a captured document with inspectable text | Content identity, internal structure, version differences, exact textual overlap, source references |
| B | Original publication page with title, author/uploader, description, model attribution, file type, slide/page count, or explicit source links | Publication identity, attribution as displayed, declared model/source set, format, stated relationships |
| C | Author-maintained source text, changelog, or explicit author statement about a relationship | Research context, source/derivation relationships, authorial intent, temporal context |
| D | Archive record with original URL, timestamp, status, MIME type, and digest | Existence of a captured representation at a given time; exact target and capture identity |
| E | Search index snippet, directory listing, title similarity, model name, URL slug, or thematic proximity | Discovery lead only; not enough by itself to merge outputs |

Evidence levels are claim-specific. A search result may discover a URL but cannot prove two pages contain the same output. A capture timestamp may establish that a page existed by that date but does not establish the work's upload date or creation date. A matching uploader name does not prove that the current host-page operator created the underlying content.

## Relationship decision model

Use these decisions when reconciling two or more records:

### Same underlying output — alternate manifestation

Apply only where the content is demonstrably the same or near-identical in its substantive structure and wording, with no material difference in analysis, source set, or conclusion. Strong indicators include matching section sequence, distinctive paragraphs, source lists, figures, and conclusions.

Record the platform-specific page as a nested representation item of the underlying output record. Do not count it as an additional output. Preserve the page URL, platform, displayed title, representation type, evidence basis, and any archive captures.

### Same output — revised or adapted manifestation

Use where a page or deck is recognizably derived from an existing output but changes its wording, structure, source set, analysis, or conclusions. Preserve the relationship as a derivative/revised representation where the current schema can express it; otherwise keep separate artefact records and an explicit relation. Do not describe a substantive revision as an identical copy.

### Distinct underlying output

Use where the page or document contains a distinct analysis, a separately produced synthesis, a different model-specific assessment, or a work with its own research question, structure, and conclusions. Shared subject matter, prompt family, source set, model vendor, or publication date do not make outputs identical.

### Archive duplicate or alternate archive host

Two archive locators are not automatically two observations. Normalize the original target URL, archive service, timestamp, and short capture identifier. Host aliases such as archive.is and archive.ph may expose the same Archive.today capture identifier; preserve alternate URL forms only when useful for access, and do not count them as independent captures. Different timestamps from the same service remain separate capture observations, but still do not create new research outputs.

### Unresolved relationship

Use when direct content is inaccessible or evidence is indirect, contradictory, or incomplete. Retain each known locator and record what would resolve the ambiguity. Do not use an implied relationship merely to make the graph look connected.

## Temporal discipline

Keep these dates distinct:

- **creation/completion date** — only where directly evidenced;
- **publication date** — the date the platform or publisher identifies for the work;
- **last-modified date** — a platform or page metadata value, with its field meaning preserved;
- **first-known-online-by** — a bounded claim supported by an archive or other dated observation;
- **archive-capture time** — the timestamp of a specific archived representation;
- **registry-documentation date** — when a previously completed historical relationship is added to the canonical registry.

Wayback timestamps are UTC. Megalodon timestamps encoded in Japanese local time must retain the original source value and timezone and then be normalized to UTC. The timestamp embedded in a SlideShare numeric item identifier is not a publication timestamp. Do not infer an upload date from numeric IDs, search crawl dates, profile ordering, or a latest-update byline.

## Reconciliation work packages

### WP1 — SlideShare inventory completeness

**Question:** Which public SlideShare items are associated with the author, and which are already represented in the canonical registry?

Tasks:
1. Extract presentation URLs from current profile HTML and the rendered public presentation tab.
2. Extract links from a representative set of archived profile snapshots, prioritizing snapshots with older or materially different profile states.
3. Compare extracted URLs against the known registry URLs after canonical URL normalization.
4. Search the profile's public, indexed presentation surface for items not exposed in the current DOM. Treat search results as leads until the original page is opened.
5. Verify each candidate's title, uploader, format, slide count, description, and direct page URL.
6. Assign a curation state: registered, newly confirmed, non-research/professional context, duplicate URL/alias, or unresolved.
7. Preserve source-collection count and discovery coverage as separate metrics; a profile's total item count is not the count of DIO/ODI research outputs.

**Deliverable:** A reviewed SlideShare URL inventory with canonical URL, title, displayed uploader, file type/page count where available, current registry match, discovery sources, and archive-query status.

**Status:** The author supplied 49 unique SlideShare URLs from the profile on 24 November 2026. All 49 locators have been triaged against the registry and classified as an existing artefact, a new artefact, a nested manifestation, an unresolved lead, or an out-of-scope profile item. Direct content review remains incomplete for a subset of URLs, so inventory completeness must not be confused with content-level identity review.

**Priority:** Continue content and provenance review of unresolved and candidate items; the initial URL-discovery step is complete for the supplied profile export.

### WP2 — E-E-A-T first-order report reconciliation

**Question:** How many distinct first-order E-E-A-T assessments exist, and which platform URLs represent each output?

Tasks:
1. Verify the direct SlideShare pages and exact model/version labels.
2. Compare each report with any candidate shared conversation, hosted page, or deployed web artifact already registered.
3. Use source lists, section sequence, distinctive passages, and conclusions to test identity.
4. Keep model-version differences explicit, especially Gemini 2.5 Pro Preview versus Gemini 3.1 Pro Preview.
5. Keep the Seznam Asistent report as a discovery lead until its original page and uploader attribution are verified.
6. Record each proven alternate manifestation under its underlying output; retain materially revised versions separately.

**Deliverable:** A model-by-model report map with separate columns for underlying output ID, SlideShare manifestation, any shared conversation or web manifestation, version label, comparison evidence, and decision status.

**Priority:** High. This is the densest known multi-platform cluster and the most likely place to overcount the same output or conflate different model versions.

### WP3 — Meta-analysis identity and cross-format reconciliation

**Question:** Which meta-analyses are independently generated, and which pages are alternate manifestations of one synthesis?

Tasks:
1. Compare the six directly reviewed SlideShare meta-analyses attributed to Gemini 3 Deep Research, Gemini 3.1 Pro Preview, Kimi, Claude, ChatGPT, and Mistral AI as separate works.
2. Compare each with corresponding Manus, Kimi, Macaly, Lovable, Netlify, Perplexity, ChatGPT, Gemini, Grok, or other web/shared artifacts.
3. Match exact section sequences, source-report enumerations, unique paragraphs, and conclusions.
4. Record source-set differences as substantive evidence. Do not silently unify the Claude/Macaly Gemini 2.5 reference with the Gemini 3.1 reference in Kimi/ChatGPT.
5. Preserve the distinction between first-order E-E-A-T reports and second-order meta-analyses.

**Deliverable:** A meta-analysis lineage map showing source reports, six directly reviewed independent SlideShare synthesis output IDs, the Manus PDF/web candidate manifestation relationship, and remaining unresolved relationships.

**Priority:** High. The Manus PDF is provisionally nested under the Manus-hosted meta-analysis web output; direct content equivalence remains to be checked.

### WP4 — Cross-platform AI output reconciliation outside E-E-A-T

**Question:** Which Kimi, DeepSeek, Qwen, Perplexity, ChatGPT, Mistral, Gemini, Grok, Claude, and Seznam Asistent locators represent distinct outputs or alternate manifestations?

Tasks:
1. Attempt direct access to each public share, deployed page, or application.
2. Where direct access is unavailable, inspect author-supplied archive captures and record whether their contents are readable, partial, or blocked.
3. Compare accessible text, titles, source lists, prompt/response sequence, page structure, and output-specific phrases.
4. Preserve model/version attribution only as the original page states it.
5. Keep unreviewed locators as separate records or leads; do not infer their subject from the platform or slug alone.
6. Reconcile the known Mistral target-ID mismatch separately: the supplied Browseo snapshot targets 4e8ae9f8-8862-4225-a6a8-0e6948651d91, not the registered dfd88fe5-ba35-4b9a-97c8-2d2f016e7a51 chat.

**Deliverable:** A platform-by-platform identity matrix with access state, original locator, archive evidence, content fingerprint or comparison notes, model attribution, and relationship decision.

**Priority:** Medium–high after WPs 2–3.

### WP5 — Earlier academic, professional, and technical SlideShare materials

**Question:** Which older SlideShare items are relevant preceding context, distinct research objects, or simply professional distribution artifacts?

Tasks:
1. Review older profile items such as the comparative AI-tools presentation, the Rearticulation of Ideology and Hegemony work, the OpenLiteSpeed study, positive-psychology analysis, the power-situation model, and the Internet-promotion project.
2. Compare them with existing canonical articles, publication pages, or research outputs.
3. Register a presentation as a separate manifestation where it is derived from an existing work; create a distinct research object only where the underlying material warrants one.
4. Do not automatically attach every historical SlideShare item to DIO/ODI merely because it appears in the same profile collection.

**Deliverable:** A contextual-material map separating pre-DIO professional context, academic publications, technical experiments, and unrelated distribution artifacts.

**Priority:** Medium.

### WP6 — Archive provenance reconciliation

**Question:** Which public representations have time-stamped captures, and which captures are duplicates or unmatched?

Tasks:
1. Run the read-only CDX intake for every confirmed SlideShare presentation URL.
2. Inspect CDX original, timestamp, statuscode, mimetype, and digest.
3. Compare digest duplicates, redirects, canonical URL changes, and language subdomains before attaching captures.
4. Inspect selected captures of disappearing or content-mutated pages.
5. Preserve original archive locators and source timezone semantics.
6. Keep CDX capture times separate from creation, upload, publication, and last-modified dates.
7. Retain unresolved captures as inventory leads.

**Deliverable:** A per-manifestation archive history with UTC capture time, source timestamp basis, original target, content digest, archive replay URL, review status, and duplicate group.

**Priority:** Run iteratively alongside WPs 1–5; finalize after URL inventory stabilizes.

### WP7 — Registry update and validation

**Question:** Can each relationship be represented without weakening identity boundaries or chronology?

Tasks:
1. Update the canonical Research Genealogy JSON only after WP-specific decisions are documented.
2. Keep underlying outputs separate from nested representations and archive captures.
3. Add explicit relations for source, derivation, thematic membership, and alternative manifestation only where evidenced.
4. Ensure every object, process, artifact, representation, cluster, and relation endpoint is stable and uniquely identified.
5. Preserve unresolved leads with an explicit resolution criterion.
6. Update this guide and frontend metadata/projections from the canonical JSON source.
7. Run JSON Schema, reference-integrity, chronology, and reproducible projection validation.

**Deliverable:** A validated registry release candidate and generated frontend consistent with its canonical source.

## Suggested execution order

| Phase | Work packages | Exit condition |
|---|---|---|
| A — Inventory | WP1 + initial WP6 | All 49 profile-export URLs are classified as existing, new, nested, unresolved, or out of scope; content review can continue separately |
| B — High-value identity | WP2 + WP3 | The nine-report SEO-pillar series, additional model-specific assessments, and six independently attributed SlideShare meta-analyses have stable identities; Manus PDF/web equivalence remains marked as a candidate |
| C — Platform reconciliation | WP4 | Accessible AI shares and deployed outputs have evidence-based relationships or explicit unresolved status |
| D — Historical context | WP5 | Older materials are separated into relevant context and unrelated collection items |
| E — Archive completion | WP6 | Every confirmed manifestation has its archive-query state and inspected captures where available |
| F — Canonical consolidation | WP7 | Registry and frontend projections validate without unresolved references |

Phases may overlap where a new archive capture helps identify a manifestation, but canonical relation and identity decisions should remain traceable to the underlying WP evidence.

## Current state on 24 November 2026

- Research Genealogy registry v0.2.0 began with 29 artefact records. PR #106 now proposes registry v0.3.0 with 56 underlying artefact records, 17 inventory leads, and an expanded profile inventory.
- The author supplied 49 unique SlideShare URLs from the public profile. All 49 have been triaged and classified; the 49-item profile count is not treated as a count of DIO/ODI research outputs. The current registry contains 33 primary SlideShare artefact records and five nested SlideShare manifestations.
- The original nine first-order E-E-A-T reports assessing the SEO pillar page remain a distinct series. Additional separately registered analyses include a Copilot Research assessment of the copywriting pillar page, a Mistral analysis of the broader professional ethnography, a Qwen Beyond E-E-A-T analysis, and a Gemini 3.1 Pro Preview semiotic/structured-data reading.
- Six independently attributed SlideShare E-E-A-T meta-analysis decks have been directly reviewed: Gemini 3 Deep Research, Gemini 3.1 Pro Preview, Kimi, Claude, ChatGPT, and Mistral AI. The Manus-labelled PDF is preserved as a candidate manifestation under the Manus-hosted web meta-analysis; content identity remains unverified.
- The Claude meta-analysis remains one underlying synthesis with three publication manifestations: SlideShare, Macaly, and Lovable. The Qwen Beyond Buzzwords and Kimi Structural Isomorphisms works each have a Czech original and an explicitly linked English reader's edition. These language-specific publications are nested manifestations, not additional underlying outputs.
- The 2011 ideology/hegemony thesis remains a distinct contextual academic research object. Its 86-slide SlideShare copy and seven-slide summary deck are now recorded as thesis distribution/presentation manifestations. The 2009 positive-psychology thesis and the supplied SlideShare material with a different title remain separate until their exact identity is verified.
- Historical and professional inventory leads include Model mocenské situace, the positive-psychology materials, and the OpenLiteSpeed technical study/article relationship. The Seznam Asistent strategy presentation is registered as contextual professional AI-industry analysis. The Přesahy 005 festival campaign, Top1Taxi brochure, stem-cell brochure, and Nero 2015 manual are classified as out of scope for the DIO/ODI research artefact count.
- The profile inventory does not imply that every URL is a DIO/ODI research output. The canonical registry retains a curated research subset, while preserving unresolved leads and out-of-scope distinctions.
- The SCF Knowledge Panel event is maintained separately from the Research Genealogy registry.
- The read-only SlideShare/Wayback intake workflow is validated in PR #105. Its CDX-only pass queried archive observations for the registered SlideShare URLs; no new profile URLs were extracted from the rendered public profile, which is why the author-provided 49-URL export became the inventory basis.

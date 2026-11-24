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

**Priority:** High. The current registry is a curated subset; the profile reported 49 Slideshow items when checked on 24 November 2026, while the initial registry contained only a small SlideShare sample.

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
1. Compare the Gemini 3 Deep Research, Kimi, Claude, and ChatGPT meta-analysis contents as separate works.
2. Compare each with corresponding Manus, Kimi, Macaly, Lovable, Netlify, Perplexity, ChatGPT, Gemini, Grok, or other web/shared artifacts.
3. Match exact section sequences, source-report enumerations, unique paragraphs, and conclusions.
4. Record source-set differences as substantive evidence. Do not silently unify the Claude/Macaly Gemini 2.5 reference with the Gemini 3.1 reference in Kimi/ChatGPT.
5. Preserve the distinction between first-order E-E-A-T reports and second-order meta-analyses.

**Deliverable:** A meta-analysis lineage map showing source reports, independent synthesis output IDs, alternate manifestations, and unresolved relationships.

**Priority:** High.

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
| A — Inventory | WP1 + initial WP6 | All currently discoverable profile URLs are matched or explicitly unresolved |
| B — High-value identity | WP2 + WP3 | E-E-A-T reports and four meta-analyses have stable identities and manifestations |
| C — Platform reconciliation | WP4 | Accessible AI shares and deployed outputs have evidence-based relationships or explicit unresolved status |
| D — Historical context | WP5 | Older materials are separated into relevant context and unrelated collection items |
| E — Archive completion | WP6 | Every confirmed manifestation has its archive-query state and inspected captures where available |
| F — Canonical consolidation | WP7 | Registry and frontend projections validate without unresolved references |

Phases may overlap where a new archive capture helps identify a manifestation, but canonical relation and identity decisions should remain traceable to the underlying WP evidence.

## Current state on 24 November 2026

- Research Genealogy registry v0.2.0 began with 29 artefact records; PR #106 proposes v0.3.0 with 46 artefact records, a documented model-specific E-E-A-T report series, a separate Gemini Deep Research transdisciplinary E-E-A-T/semantic analysis, a versioned Claude semiotic E-E-A-T analysis, and separate DeepSeek and Qwen interpretations of the professional ethnography.
- The initial SlideShare inventory is curated, not exhaustive. The English profile view displayed 49 Slideshow items on 24 November 2026. Four older academic/project cards and one technical-study relationship are now preserved as inventory leads where direct locators or provenance are incomplete.
- The SCF Knowledge Panel event is maintained separately from the Research Genealogy registry.
- A read-only SlideShare/Wayback intake prototype is under validation in PR #105. Its first CDX-only pass retrieved archive observations for five known SlideShare URLs but did not extract new URLs from server-side HTML or archived profile snapshots. A rendered Chromium discovery pass has been added; its live result must be reviewed before the intake is described as effective at profile-wide discovery.
- Two university records are now represented as separate historical academic research objects: the 2009 positive-psychology thesis and the 2011 ideology/hegemony thesis. Their corresponding SlideShare profile cards remain candidate associations, not confirmed identical outputs. They are not asserted as direct origins of DIO/ODI.
- Model-specific outputs on the professional ethnography now include the DeepSeek text-only E-E-A-T/semiotic analysis and the Qwen interdisciplinary DIO synthesis; their shared subject does not imply equivalence to the Claude reports.
- A Claude E-E-A-T/semiotic analysis of the professional ethnography exists in two directly reviewed SlideShare versions: a nine-slide first edition and a ten-slide v2 that explicitly adds structured data, external references, and DIO-priority evidence. The registry links v2 to v1 as a revision rather than treating them as unrelated analyses or as alternate copies.
- Direct content reconciliation has confirmed at least one alternate representation: the Macaly page and Claude SlideShare PDF are manifestations of the same meta-analysis. Their platform/uploader attribution is not treated as identical merely from that content match.
- The source-set discrepancy between Gemini 2.5 Pro Preview and Gemini 3.1 Pro Preview remains an explicit inventory lead.
- Seznam Asistent's first-order SlideShare report is mentioned by meta-analyses but its own page remains unreviewed.
- The SlideShare profile lists older items on power relations, positive psychology, ideology/hegemony, and a festival-promotion project; these remain discovery leads until direct pages and relationships are checked. The OpenLiteSpeed deck and article have both been identified, but their relation and temporal direction remain unresolved.

## Editorial safeguards

- Do not inflate the number of outputs by counting every platform URL or archive capture as a new work.
- Do not reduce distinct model-specific analyses or meta-analyses to one work because they share a topic.
- Do not infer author/uploader attribution from hosting alone.
- Do not infer creation/publication dates from archive timestamps, profile order, numeric IDs, or search crawl dates.
- Do not label an output as an alternative manifestation until content comparison supports the relationship.
- When evidence is incomplete, preserve the uncertainty as a first-class record state rather than making a best-guess merge.

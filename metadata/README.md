# DIO/ODI metadata registry

This directory is the operational metadata source of truth for the DIO/ODI publication corpus and the DIO/ODI Reference Model.

It is deliberately separate from the canonical DIO/ODI Reference Vocabulary. Updating these files does not modify vocabulary definitions, hierarchy, or concept provenance.

## Files

- `works.json` — identities and publication metadata of DIO/ODI works, Reference Model releases, and the separate DIO/ODI MCP software distribution.
- `relations.json` — directed inter-work relation graph. Only relations with `approved_for_zenodo: true` should be projected automatically into Zenodo metadata.
- `references.json` — canonical bibliographic strings for internal and external references.
- `distributions.json` — external distribution, identical, variant, and supplementary representations of each canonical work, preserving the exact relation type.
- `keywords.json` — canonical C0–C6 keyword grammar, publication profiles, derived product and public-page surface profiles for the Planner, author concept site, Reference Model, DIO to DIO analyses, open-source application, taxonomy map, terminology case study, and MCP landing page, plus non-export aliases.
- `application-mappings.json` — canonical descriptive metadata, source paths, and release provenance for derived Application Mappings.
- `application-mappings.schema.json` — JSON Schema 2020-12 validation contract for Application Mappings metadata.
- root `.zenodo.json` — Zenodo-specific projection for future GitHub → Zenodo Reference Model releases.

## Workflow

1. Maintain canonical work identities, DOI/version information, relations, distribution representations, keyword profiles, and Application Mappings metadata in their JSON registries.
2. The projection generator refreshes the shared identity and keyword fields in `.zenodo.json` and `CITATION.cff`. Review the release-specific description, related identifiers, and references separately; those remain editorial and relation-governed metadata.
3. Zenodo GitHub archiving reads `.zenodo.json` for new releases.
4. Existing historical Zenodo records are not retroactively changed by these files; they require metadata synchronization through Zenodo's editor, API, or browser automation.
5. Zenodo assigns the version-specific DOI only after the GitHub Release is archived. Add the minted DOI and archived snapshot details once to `metadata/works.json`; the generator then synchronizes the derived metadata, citation, documentation, and site projections. Never rewrite an immutable archived snapshot.

## DIO/ODI MCP software distribution

The read-only MCP server is registered as the separate work `mcp-server` in `works.json`. Its v0.1.1 version DOI is `10.5281/zenodo.24123229`; its Concept DOI is `10.5281/zenodo.24123228`. The server's recorded scope is: Public, stateless, read-only MCP distribution exposing a bounded snapshot of the DIO/ODI Reference Model and selected derived Agentic ER and Policy-as-Code mappings. It is not an MVDIO Supervisor or authorization service and does not execute application-side authorization or mutate application state. Its registered relation is `derived-read-only-distribution`. Its implementation is licensed under MIT; embedded DIO/ODI reference content remains CC-BY-4.0.

## Reference Vocabulary identity and parent Reference Model DOI

The canonical DIO/ODI Reference Vocabulary is identified by its own SKOS ConceptScheme URI:

`https://vocab.danielberanek.cz/dio-odi/#ReferenceVocabulary`

The Zenodo Concept DOI `10.5281/zenodo.23272897` identifies the **DIO/ODI Reference Model**, not the Reference Vocabulary as an independently archived object. The vocabulary is a component of that broader Reference Model. Therefore:

- use the vocabulary URI as the identifier of the SKOS ConceptScheme;
- represent its relation to the parent Reference Model with `dcterms:isPartOf` (or the equivalent Schema.org relationship);
- never label the Reference Model Concept DOI as a vocabulary-specific DOI;
- distinguish the live vocabulary version from the vocabulary state included in a particular archived Reference Model release.

The live Reference Vocabulary is v0.2.2 (a metadata-only namespace-prefix alignment to v0.2.1; the concept model is unchanged). The current archived Reference Model v0.9.0 (https://doi.org/10.5281/zenodo.24085589) contains Vocabulary v0.2.2 and SCF v0.1.1, schema v0.2.0, 45 events, through 9 November 2026. The previous archived Reference Model v0.8.0 (https://doi.org/10.5281/zenodo.24056601) contains Vocabulary v0.2.1 and SCF v0.1.0, schema v0.2.0, 44 events, through 8 November 2026. First archival inclusion for each recorded vocabulary state is preserved in `reference_vocabulary_inclusion_history` in `works.json`: v0.1.0 was first included in archived Reference Model v0.1.0 (https://doi.org/10.5281/zenodo.23272898); v0.2.0 was first included in archived Reference Model v0.2.0 (https://doi.org/10.5281/zenodo.23282752); v0.2.1 was first included in archived Reference Model v0.7.0 (https://doi.org/10.5281/zenodo.24020300); v0.2.2 was first included in archived Reference Model v0.9.0 (https://doi.org/10.5281/zenodo.24085589). These DOI values identify the enclosing Reference Model archives, not separately archived Vocabulary packages. The Vocabulary has no separate version-specific Zenodo DOI; use its canonical ConceptScheme URI. The `reference-vocabulary-v0.2.0` entry in `references.json` provides the corresponding URI-based citation without assigning the parent model's DOI to the Vocabulary.

## Relation discipline

The graph is intentionally conservative. A relation should not be strengthened merely to make the graph denser.

In particular, the candidate relation between the archived Reference Model package and the namespace URI `https://vocab.danielberanek.cz/dio-odi/#` is currently marked for semantic review rather than exported automatically as `isIdenticalTo`.


## Distribution representations

External copies and distribution layers are part of the metadata graph but are not automatically treated as identical to the canonical work.

For each canonical work, audit ResearchGate, Figshare, SSRN, Kaggle, Hugging Face, institutional repositories, and other known distribution layers where applicable. Preserve the precise relation actually justified by the record:

- `isIdenticalTo` for genuinely identical objects;
- `isSupplementedBy` where the external representation supplements the canonical record;
- other supported relation types where more accurate.

Do not collapse all distribution channels into a generic equivalence relation.


### Verification rule for existing Related Works

Existing Zenodo relations are observations of previously entered metadata, not automatically canonical truth.

Before approving a distribution relation:

1. compare the actual files/content, not only titles and landing pages;
2. determine whether the external object is the exact same research output, a modified/variant form, a distinct version, or a genuine supplement;
3. use `IsIdenticalTo` only for the exact same research output stored in two locations;
4. use `IsSupplementedBy` only when the external resource genuinely supplements the canonical resource;
5. keep the relation unapproved if the distinction cannot be established safely.

A prior relation already present on Zenodo may therefore be corrected during metadata normalization.


### MVDIO distribution check (2026-11-14)

The canonical MVDIO record (Zenodo DOI `10.5281/zenodo.23226205`) was checked against its live Related Works display on 14 November 2026. It currently lists all three author-confirmed identical distribution copies as **Is identical to**:

- ResearchGate: `10.13140/RG.2.2.10967.43682`
- Figshare: `10.6084/m9.figshare.34231965`
- SSRN: `10.2139/ssrn.7582778`

The Zenodo record page reports that it was last modified on 8 November 2026. The current observed relation and the author-confirmed canonical relation therefore agree for all three representations: `isIdenticalTo`.

The registry previously carried an outdated observation for this record (ResearchGate and Figshare as `isSupplementedBy`, and SSRN not listed). That observation is superseded by the current Zenodo record and must not be treated as the present state.



### Version-scoped distribution relations

Distribution relations may legitimately change between versions of the same canonical work.

When a later Zenodo version differs from an external distribution copy, do not automatically inherit an earlier `isIdenticalTo` relation. Record the relation against the specific version for which it is valid and preserve the earlier relation as historical provenance where appropriate.

Current-version relation semantics take precedence for projection to the current Zenodo record; historical relation semantics must not be retroactively overwritten.


## Keyword discipline

`keywords.json` defines a canonical **ordered metadata grammar**, not an unordered bag of tags.

The fixed chunk order is:

`C0 Identity invariant → C1 Reconstruction environments → C2 Work positioning → C3 Reconstruction mechanics → C4 K6 → C5 Reconstruction failures and robustness → C6 Machine-readable representation`

Rules:

1. **C0 is invariant.** It is always exported in full and first for every approved DIO/ODI work or derived artefact profile.
2. **C1 is a global candidate pool, not a mandatory four-term bundle.** Each object explicitly selects only the reconstruction environments it substantively addresses: artificial intelligence, search engines, knowledge graphs, and/or human observers. The literal selector `all` is not permitted for C1; an explicit ordered array is required, including an empty array where no environment can be established.
3. C2 is work- or artefact-specific.
4. C3, C5, and C6 are master-ordered chunks: profiles may activate only a relevant subset, while preserving the canonical relative order.
5. C4 (K6) is all-or-nothing and is exported only as the complete ordered sequence: K6 Semantic Connectome, Entity, Representation, Interpretation, Trust, Relationship, Reconstruction.
6. Flattened keyword arrays preserve chunk order and term order. Aliases support reconstruction and variant recognition but are not exported by default.
7. Keyword assignment must not retroactively project concepts into an object that it does not substantively carry. A citation, incidental mention, shared author, or generic word overlap is not sufficient evidence for a keyword.
8. Every selected C1 term carries an explicit object-level rationale. Derived artefact profiles additionally provide a rationale for every selected non-C0 term. The projection generator validates these rationales and checks that every selected term belongs to its canonical chunk.
9. `work_profiles` retain the canonical publication profiles. `surface_profiles` define derived public artefacts, including product pages and demonstrations, without misrepresenting them as separate DIO/ODI publications.
10. Public frontend pages may use one profile per semantic page object. Localized mirrors of the same page may share a profile when their scope is equivalent; language differences do not create a new conceptual object. Each page generator resolves the profile from the canonical registry and records the exact registry version and profile identifier in its generated metadata.
11. The Reference Model repository uses ten page-level profiles for its public portal, canonical vocabulary, External Reception frontend, Application Mappings index and four mapping pages, Corpus Metadata Registry frontend, and Semantic Change Feed frontend. The separate DIO to DIO portfolio uses twelve more profiles: one homepage and eleven model-specific report pages. These are derived web surfaces, not new publication works and not canonical vocabulary concepts.
12. The Reference Model page generator adds `meta keywords` and a separate JSON-LD keyword property node linked to the existing primary page entity by its `@id`. This preserves existing multi-entity JSON-LD graphs and does not overwrite independent Dataset or CreativeWork entities embedded on the same page. The generated `assets/data/resolved-page-metadata.json` records the profile selectors, rationale coverage, resolved terms, entity identifier and SHA-256 of the exact registry source.
13. Exportable metadata surfaces use the complete resolved sequence for the specific profile whenever the target format supports it. Do not maintain manually curated, shorter parallel lists. The sequence is generated from the profile's chunk selectors and the canonical chunk definitions.

The C1 terms remain global to DIO's reconstruction model. Selective export does not narrow the DIO definition; it prevents an individual paper, product, demonstration, or other artefact from being described as covering environments that are not relevant to that object.


## Description discipline

Zenodo Description is treated as a semantic identity surface, not as a repository tagline.

For canonical DIO/ODI records, descriptions should follow a stable high-level order where supported by the work:

1. **Identity and scope** — what the work is and how it positions DIO/ODI.
2. **Corpus position and genealogy** — which earlier/later DIO/ODI works it develops, refines, references, or operationalizes.
3. **Core conceptual content** — the main mechanisms, models, dimensions, or analytical distinctions carried by the work.
4. **Failure / robustness structure** — Reconstruction Failure Modes, Semantic Vulnerability, Semantic Robustness, Identity Collapse, or related concepts where genuinely present.
5. **Application / external mappings** — only where the work maps DIO/ODI into an external domain.
6. **Metadata, distribution, and relation layer** — where relevant, explain versioning, provenance, distribution identity, typed relations, and machine-readable metadata.
7. **Epistemic boundary and use** — state what the work does not claim, preserve distinctions from stronger formalizations, and identify its intended interpretive/reuse role.

The grammar constrains sequence and function, not wording. A work must not acquire concepts merely to fill a description block. Later descriptions may be structurally consistent while remaining faithful to the historical scope of each publication.


## Resource type discipline

Use the actual publication state of each work and do not strengthen it through metadata.

- Manifest v1: `dataset`
- DIO Conceptual Framework: `publication-preprint`
- Crisis of Entity Resolution: `publication-preprint`
- MVDIO: `publication-preprint`
- Taxonomic Note: `publication-preprint`
- DIO/ODI Reference Model: `software`
- Externally published HEM source: `publication-article`

A Zenodo-hosted research manuscript is not a journal article merely because Zenodo exposes an article-like publication category. Canonical metadata must preserve the distinction between a preprint and peer-reviewed journal publication.


## Archival continuity and correction

DIO/ODI metadata maintenance does not silently rewrite history in order to produce an artificially clean record.

When a metadata error or weaker historical representation is identified:

1. the archived historical state remains identifiable as the state that actually existed;
2. the canonical current representation is corrected transparently;
3. the correction must not imply that the earlier metadata state never existed;
4. version, provenance, and relation information should preserve continuity between historical and corrected representations;
5. a metadata correction alone does not justify creating a new research-object version unless the underlying files or substantive object have changed.

This applies the DIO principle of identity-preserving change to the DIO/ODI corpus itself: continuity is maintained through explicit transformation and provenance, not by erasing earlier states.


## Commit-Boundary preprint version relationship

The DIO/ODI corpus registry records the arXiv v2 representation of *Constraining the Commit Boundary* as `isNewVersionOf` the specific Zenodo v1 record `10.5281/zenodo.23580733`. The author confirmed on 7 November 2026 that the Zenodo v1 record now carries two complementary relations: **Is identical to** the matching v1 representation, and **Is previous version of** arXiv v2 (`10.48550/arXiv.2610.37407`, the arXiv concept DOI; current version v2). The first relation records identity of the v1 representations; the second records version succession from v1 to v2.

The record's **Cites** relation to `10.48550/arXiv.2607.27435` identifies the separate paper *AgenticER: the next frontier in Entity Resolution* by Papadakis et al. It is a bibliographic citation, not an identifier for this preprint, and must not be conflated with the two version relations. The distribution registry records the Zenodo change as author-confirmed; it was not independently re-fetched during this update.


## External Reception Registry

The External Reception Registry is a separate, manually curated record of material and registry entries maintained outside the DIO/ODI corpus that discuss, interpret, extend, summarize, index, or otherwise represent specific DIO/ODI research works and canonical reference artifacts.

Files:
- `external-reception.json` — structured records for external reception, source provenance, target-work relationships, review status, citation evidence, and archive references.
- `external-reception.schema.json` — JSON Schema 2020-12 validation contract.
- `external-reception.ttl` — RDF projection for discovery and typed relations.
- `/external-reception/` — human-readable frontend.

The registry distinguishes independent technical analyses, conceptual uptake, agent-account-authored posts and discussions, adjacent community discussion without a direct paper citation, AI-generated or localized summaries, research-discovery/indexing profiles, registry and knowledge-organization catalogue integrations, and limited editorial summaries.

Each entry is linked to the specific research work or canonical reference artifact it concerns. The BioRegistry and Semantic Farm records document distinct prefix/resolver integrations for the Reference Vocabulary; the BARTOC record catalogues it as a Terminology knowledge-organization system (KOS), without adding a namespace prefix or implying a separate Vocabulary DOI. None of these catalogue or registry entries is treated as an independent scholarly assessment. The Wren-Castillo article is linked to *The Crisis of Entity Resolution in Heterogeneous AI Environments*, not to *Constraining the Commit Boundary*.

CiTO `cito:cites` assertions are emitted only where an explicit citation or source link to the relevant work is documented. Topical relationships or discovery profiles are not automatically treated as citations. The RDF projection uses `rdfs:seeAlso` for navigational links from the Commit-Boundary Policy-as-Code mapping.

Moltbook entries preserve the original post and Megalodon archive URLs, including the direct-view `/ref/` form. Platform verification badges do not establish autonomous authorship. Discussion counts are source-displayed totals; where only an excerpt was supplied, the record states that capture is partial.

Implementation status is conservative. A technical proposal is not an implementation; an independently authored validator or illustrative code is not automatically an implementation of the source paper; an AI summary or paper index is not an independent review. The unGhost record is explicitly scoped to a limited summary of the arXiv v1 source.

The registry does not modify the canonical DIO/ODI Reference Vocabulary or the Semantic Change Feed.

## Generated projections and maintenance

Canonical JSON sources are the editable layer. External Reception HTML, embedded JSON-LD, and RDF/Turtle are generated from `metadata/external-reception.json`. The Semantic Change Feed frontend is generated from `semantic-change-feed/events.json`. Application Mappings index metadata is maintained in `metadata/application-mappings.json`; the mapping's substantive Markdown, JSON-LD, Turtle, and visualization content remains in its own source files.

The generator also projects release and author metadata from `metadata/works.json`, keyword sequences from `metadata/keywords.json`, and mapping summaries from the Application Mappings registry into `metadata.json`, the root README, `llms.txt`, `CITATION.cff`, selected `.zenodo.json` fields, the SCF technical README, this guide's release summaries, and sitemap dates. Do not hand-edit generated copies. Change the canonical source and let the generator rebuild the projections.

GitHub Actions runs the generator during validation. After changes reach `main`, it commits regenerated projections automatically. A local rebuild, when needed, is:

```bash
python scripts/generate_projections.py --write
python scripts/generate_projections.py --check
```

The `--check` mode is read-only and exits with an error if any generated projection is stale. Generated files remain committed to the repository so the public static site and machine-readable endpoints do not depend on a runtime rendering service.

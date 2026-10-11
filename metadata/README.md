# DIO/ODI metadata registry

This directory is the operational metadata source of truth for the DIO/ODI publication corpus and the DIO/ODI Reference Model.

It is deliberately separate from the canonical DIO/ODI Reference Vocabulary. Updating these files does not modify vocabulary definitions, hierarchy, or concept provenance.

## Files

- `works.json` — identities and publication metadata of DIO/ODI works and Reference Model releases.
- `relations.json` — directed inter-work relation graph. Only relations with `approved_for_zenodo: true` should be projected automatically into Zenodo metadata.
- `references.json` — canonical bibliographic strings for internal and external references.
- `distributions.json` — external distribution, identical, variant, and supplementary representations of each canonical work, preserving the exact relation type.
- `keywords.json` — canonical invariant keyword core, work-specific keyword profiles, and non-export aliases.
- root `.zenodo.json` — Zenodo-specific projection for future GitHub → Zenodo Reference Model releases.

## Workflow

1. Maintain work identities, DOI/version information, relations, distribution representations, keywords, and citations here.
2. Before a new Reference Model release, ensure `.zenodo.json` reflects the approved subset of this registry.
3. Zenodo GitHub archiving reads `.zenodo.json` for new releases.
4. Existing historical Zenodo records are not retroactively changed by these files; they require a one-time metadata synchronization through Zenodo's editor, API, or browser automation.

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


## Keyword discipline

`keywords.json` defines a canonical **ordered metadata grammar**, not an unordered bag of tags.

The fixed chunk order is:

`C0 Identity invariant → C1 Reconstruction environments → C2 Work positioning → C3 Reconstruction mechanics → C4 K6 → C5 Reconstruction failures and robustness → C6 Machine-readable representation`

Rules:

1. C0 is always first and identical across the DIO/ODI corpus.
2. C1 is always second and identifies the main reconstruction environments: artificial intelligence, search engines, knowledge graphs, and human observers.
3. C2 is work-specific.
4. C3, C5, and C6 are master-ordered chunks: works may activate only a subset, but selected terms retain the same relative order.
5. C4 (K6) is all-or-nothing and always exported as the complete sequence: K6 Semantic Connectome, Entity, Representation, Interpretation, Trust, Relationship, Reconstruction.
6. Flattened keyword arrays preserve chunk order and term order.
7. Aliases support reconstruction and variant recognition but are not exported by default.
8. Keyword assignment must not retroactively project concepts into a work that the work does not substantively carry.

This creates lexical and structural consistency across records while preserving the conceptual scope of each work.


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

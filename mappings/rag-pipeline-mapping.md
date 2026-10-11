# Application Mapping: DIO Reconstruction Failure Modes × RAG Pipeline

**Status:** Derived application layer introduced in DIO/ODI Reference Model v0.2.0 and included in v0.3.1  
**Current release:** DIO/ODI Reference Model v0.3.1 — Zenodo DOI pending  
**Previous archived release containing this mapping:** DIO/ODI Reference Model v0.3.0 — https://doi.org/10.5281/zenodo.23289615  
**Relation to the reference vocabulary:** This mapping is not part of the canonical DIO/ODI Reference Vocabulary. It applies vocabulary concepts to an external technical domain and does not modify their definitions or relations.  
**Scope:** Derived mapping; not a normative redefinition of DIO, ODI, RAG, or the Reconstruction Failure Mode taxonomy.  
**JSON-LD:** https://vocab.danielberanek.cz/mappings/rag-pipeline-mapping.jsonld  
**Turtle RDF:** https://vocab.danielberanek.cz/mappings/rag-pipeline-mapping.ttl

## Purpose

This document projects the current DIO Reconstruction Failure Mode taxonomy onto a generic retrieval-augmented generation (RAG) pipeline. Its purpose is diagnostic: to show where RAG processing conditions can contribute to, expose, or amplify failures of digital-identity reconstruction.

The mapping is deliberately **non-deterministic**. A DIO failure mode is defined by the resulting reconstruction, not by the technical stage at which an upstream error occurs. The same failure mode may arise from different pipeline loci, and one pipeline defect may contribute to several failure modes.

A typical RAG pipeline is represented here at a deliberately generic level:

1. source/corpus formation;
2. segmentation and indexing;
3. query interpretation and entity linking;
4. retrieval;
5. reranking and context assembly;
6. generation and synthesis;
7. output validation and citation.

These stages are analytical conveniences, not a claim that all RAG systems implement the same architecture.

## Mapping table

| DIO failure mode | Typical RAG locus/loci | Possible pipeline mechanism | Observable symptom | Hypothetical incident | DIO interpretation |
| --- | --- | --- | --- | --- | --- |
| [Entity Substitution](https://vocab.danielberanek.cz/dio-odi/#EntitySubstitution) | Query interpretation; entity linking; retrieval; synthesis | The query or evidence is anchored to a distinct but confusable referent, such as a namesake, similarly named organization, or adjacent product. | The answer is coherent but describes the wrong entity. | A query about one Daniel Beránek retrieves and synthesizes evidence belonging to another person with the same name. | The intended referent is reconstructed as another distinct referent. |
| [Merge Failure](https://vocab.danielberanek.cz/dio-odi/#MergeFailure) | Indexing/entity linking; retrieval; context assembly; synthesis | Representations belonging to distinct referents are pooled under one working identity. | The answer combines attributes that cannot all belong to the same entity. | Two companies with similar names contribute documents to one generated company profile. | Distinct referents are reconstructed as a single referential identity. |
| [Split Failure](https://vocab.danielberanek.cz/dio-odi/#SplitFailure) | Indexing/entity linking; retrieval; synthesis | Aliases, historical names, domains, identifiers, or legitimate transformations of one entity are treated as unrelated identity clusters. | One continuous entity appears as two or more independent entities. | A company before and after a rebrand is described as two unrelated organizations. | Referential unity of one continuous entity is lost. |
| [Entity Omission](https://vocab.danielberanek.cz/dio-odi/#EntityOmission) | Post-retrieval context use; generation; synthesis | Sufficient representational grounds are available to the effective observer, but the model fails to produce the relevant entity reconstruction. | Relevant evidence is present in the usable context, yet the entity is absent from the answer. | Retrieved passages explicitly establish an organization and its role, but the generated answer omits that organization entirely. | No relevant reconstruction is produced despite sufficient grounds being available within the observation domain. Mere non-retrieval, non-indexing, or unavailability is outside this failure mode. |
| [Semantic Fragmentation](https://vocab.danielberanek.cz/dio-odi/#SemanticFragmentation) | Context assembly; synthesis | Compatible representations of the same referent are treated as disconnected semantic fragments, or incompatible fragments are juxtaposed without identity-preserving integration. | The entity is correctly identified, but its reconstructed identity is internally incoherent or disjointed. | The answer correctly refers to one researcher but presents professional, publication, and organizational representations as unrelated fragments that fail to form a coherent identity. | Referential unity remains, while identity-preserving semantic coherence is lost. |
| [Temporal Discontinuity](https://vocab.danielberanek.cz/dio-odi/#TemporalDiscontinuity) | Indexing/version handling; retrieval; context assembly; synthesis | Representations from legitimate successive states are not connected as transformations of the same referent. | The system fails to preserve identity continuity across change. | A renamed project is reconstructed as having disappeared and been replaced by a different project rather than as one continuing entity. | Referential continuity across legitimate transformation is not preserved. |
| [Temporal Misalignment](https://vocab.danielberanek.cz/dio-odi/#TemporalMisalignment) | Retrieval; reranking; context assembly; synthesis | Older but authoritative or highly ranked representations dominate over the state relevant to the query time. | The correct entity is returned with an outdated or otherwise temporally inappropriate state. | A RAG answer identifies the correct company but reports its previous CEO as the current CEO. | The referent is correct; the reconstructed state is temporally inappropriate to the observation situation. |
| [Contextual Displacement](https://vocab.danielberanek.cz/dio-odi/#ContextualDisplacement) | Query interpretation; reranking; context assembly; synthesis | A legitimate but contextually secondary aspect of the entity dominates evidence that is more relevant to the current task. | The answer is factually supportable yet answers with the wrong aspect of the entity. | A query about a person's current research role returns a detailed but accurate reconstruction of an older professional role because that representation dominates retrieval and synthesis. | A true reconstruction is contextually inadequate because another legitimate identity aspect displaces the one relevant to the observation context. |

## Pipeline view

The table can also be read in the opposite direction:

- **Source formation and indexing** can create conditions for later Merge, Split, Temporal Discontinuity, or Temporal Misalignment, but upstream heterogeneity is not itself a DIO failure mode.
- **Query interpretation and entity linking** are especially relevant to Entity Substitution, Merge Failure, Split Failure, and Contextual Displacement.
- **Retrieval and reranking** can alter which representational state becomes available for reconstruction, particularly in substitution, merge, temporal, and contextual cases.
- **Context assembly** can preserve or destroy useful separation among referents, time states, and semantic aspects before generation begins.
- **Generation and synthesis** are where many failures become directly observable as reconstructions, even when their causes are upstream.
- **Validation and citation** may detect a failure without being the stage that produced it.

This distinction matters because DIO does not reduce reconstruction failure to retrieval quality. A technically successful retrieval can still lead to a referentially, semantically, temporally, or contextually defective reconstruction.

## Hypothetical incident patterns

### 1. Same-name substitution

A user asks for the publications of Person A. Retrieval returns a mixture of evidence for Person A and a namesake, Person B. Reranking favors Person B's stronger publication profile, and generation produces a coherent bibliography for B.

**RAG diagnosis:** entity-linking/retrieval contamination.  
**DIO diagnosis:** Entity Substitution.

### 2. Cross-entity profile fusion

Documents for Organization A and Organization B share abbreviations and overlapping terminology. The retrieval set contains both, and synthesis creates one profile containing A's founding date and B's leadership.

**RAG diagnosis:** entity separation failed across indexing, retrieval, or context assembly.  
**DIO diagnosis:** Merge Failure.

### 3. Rebrand treated as a new entity

A project changes its name, domain, and visual identity while preserving organizational and referential continuity. Indexed representations under the old and new names are retrieved into separate clusters and generated as two unrelated projects.

**RAG diagnosis:** version/entity linking failed to connect legitimate transformation.  
**DIO diagnosis:** Split Failure and potentially Temporal Discontinuity as overlapping diagnostic modes.

### 4. Available evidence, omitted entity

The retrieved context explicitly contains multiple passages establishing Entity X as a participant in an event. The generated answer discusses the event but omits X entirely.

**RAG diagnosis:** generation/context utilization failure.  
**DIO diagnosis:** Entity Omission.

If the relevant evidence was never indexed or retrieved, the current DIO definition does **not** classify the case as Entity Omission.

### 5. Correct entity, fragmented identity

The context contains compatible representations of one entity across a personal site, publication record, organization profile, and structured metadata. Generation mentions all of them but fails to integrate them into one coherent reconstruction.

**RAG diagnosis:** synthesis failed to integrate distributed evidence.  
**DIO diagnosis:** Semantic Fragmentation.

This is distinct from Split Failure: the answer may still recognize that all facts refer to the same entity.

### 6. Stale reconstruction

A current-state query retrieves both old and new authoritative documents. Older material has stronger retrieval or ranking signals and dominates the context window.

**RAG diagnosis:** temporal retrieval/reranking imbalance.  
**DIO diagnosis:** Temporal Misalignment.

### 7. True but contextually wrong

The user asks about an entity in a specific present-day professional context. Retrieval surfaces a highly authoritative historical representation, and the answer accurately describes it while neglecting the context requested.

**RAG diagnosis:** query-context or reranking mismatch.  
**DIO diagnosis:** Contextual Displacement.

## Related concepts outside the failure-mode taxonomy

[Semantic Vulnerability](https://vocab.danielberanek.cz/dio-odi/#SemanticVulnerability) is not a realized Reconstruction Failure Mode. In a RAG setting it can be used as a robustness-oriented lens: how susceptible is a reconstruction to disproportionate change when retrieval conditions, source availability, ranking, or context composition are perturbed?

[Reconstruction Capture](https://vocab.danielberanek.cz/dio-odi/#ReconstructionCapture) is especially relevant to RAG because a small subset of retrieved representations can disproportionately dominate the generated reconstruction. The current vocabulary records it as related to Semantic Vulnerability but does not formalize a stronger relation.

[Identity Collapse](https://vocab.danielberanek.cz/dio-odi/#IdentityCollapse) remains a phenomenon-level concept outside the current failure-mode hierarchy. This mapping does not assert that any RAG failure mode causes, constitutes, exhausts, or is required for Identity Collapse.

## Interpretation boundary

This mapping should not be read as:

- redefining DIO as a RAG framework;
- claiming that every RAG error is a DIO failure;
- claiming a one-to-one relation between pipeline stages and Reconstruction Failure Modes;
- treating retrieval failure, hallucination, factual error, or source-quality problems as automatic synonyms for DIO concepts;
- asserting causal relations not established in the DIO/ODI corpus.

Its narrower claim is that the DIO Reconstruction Failure Mode taxonomy provides a useful diagnostic layer for describing **how an entity's identity is reconstructed incorrectly or inadequately** in systems where retrieval and generation jointly shape the observable reconstruction.

## Source basis

This mapping is derived from the current DIO/ODI Reference Model and its source corpus, especially:

- Beránek, D. (2026). *Minimum Viable Digital Identity Optimization (DIO): From Adversarial Reduction to the Semantic Field Dynamics of Digital Identity*. https://doi.org/10.5281/zenodo.23226205
- Beránek, D. (2026). *From Entity Resolution Anomalies to Reconstruction Failure Modes: A Taxonomic Note Following Minimum Viable DIO*. https://doi.org/10.5281/zenodo.23269323

The RAG stages and incidents in this document are generic analytical examples, not claims of empirical validation.

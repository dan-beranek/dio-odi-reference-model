# Application Mapping: DIO Reconstruction Failure Modes × RAG Pipeline

**Status:** Base mapping introduced and archived in DIO/ODI Reference Model v0.2.0, retained in archived v0.3.x releases. Iterative/hypothesis-conditioned evidence-acquisition extension added on 25 October 2026, first included in archived v0.4.0, and carried forward in v0.5.0.  
**Current archived release:** DIO/ODI Reference Model v0.5.0 — https://doi.org/10.5281/zenodo.23643845  
**Previous archived release containing this mapping:** DIO/ODI Reference Model v0.3.1 — https://doi.org/10.5281/zenodo.23290683  
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

## Development context and temporal lineage

This page now contains the original RAG-to-DIO mapping and a later analytical extension. Their temporal and conceptual relationship is part of the artifact's provenance.

- **10 October 2026 — Base RAG × DIO mapping.** The original mapping was published as a diagnostic projection from DIO Reconstruction Failure Modes to generic RAG pipeline loci, mechanisms, and observable symptoms. The base mapping is included in archived DIO/ODI Reference Model v0.3.2.
- **22 October 2026 — Commit-boundary research.** In [*Constraining the Commit Boundary: A DIO/ODI-Informed Authorization Guardrail for Agentic Entity Resolution*](https://zenodo.org/records/23580733), the analysis distinguishes evidence available for exploratory reasoning from evidence eligible to authorize a persistent identity-changing mutation. It explicitly leaves broader dependency-aware control of hypothesis-conditioned evidence acquisition and feedback as a separate research direction.
- **25 October 2026 — Live analytical extension.** The section below extends the earlier RAG mapping to examine that upstream evidentiary process: how a working hypothesis can influence subsequent query selection, evidence exposure, and hypothesis updates. This extension is motivated by the boundary made explicit in the later paper; it is not claimed to be contained in, implemented by, or empirically validated by that paper.

The relationship is developmental, not a claim of deterministic causality: the RAG mapping supplies the earlier process-to-reconstruction diagnostic layer; the commit-boundary paper isolates a downstream authorization boundary and explicitly does not solve the upstream feedback problem; this live extension examines that previously separated question in relation to the existing RAG mapping. The extension was added to the live source tree on 25 October 2026; it was not included in the archived v0.3.2 package, was first included in archived v0.4.0, and is carried forward in archived v0.5.0. The live canonical DIO/ODI Reference Vocabulary is now v0.2.0; this mapping remains outside it.

## Iterative and Hypothesis-Conditioned Evidence Acquisition

The existing RAG mapping locates possible reconstruction pressures across pipeline stages. It does not explicitly model dependencies that span successive retrieval and reasoning steps. In agentic retrieval, a working hypothesis at step (t) may influence the next query, tool call, source choice, or selection of candidate evidence. The returned and selected material then informs a subsequent hypothesis, which in turn shapes later search:

**working hypothesis → next retrieval action → exposed/selected evidence → updated hypothesis → subsequent retrieval action**

This is a process-level extension across existing RAG loci, not a new canonical DIO/ODI concept or an additional stage that every RAG architecture must implement.

| Analytical condition | What it adds beyond the existing RAG matrix | Possible DIO relevance | Interpretation limit |
| --- | --- | --- | --- |
| **Hypothesis-conditioned query selection** | The current working hypothesis influences which follow-up questions, tools, or source paths are explored. | Changes in evidence exposure may interact with existing failure modes such as Entity Substitution, Merge Failure, or Contextual Displacement, depending on the resulting reconstruction. | Hypothesis-conditioned search is normal in agentic systems; it is not itself proof of bias or failure. |
| **Path-dependent evidence acquisition** | Later evidence and explored alternatives depend partly on earlier retrieval results and intermediate interpretations. | An early referential or contextual error may remain unchallenged or be amplified if later steps inherit its assumptions; other steps may also correct it. | Dependence across steps does not establish that the evidence is false or that the final reconstruction is defective. |
| **Evidence-lineage dependence** | Several retrieved documents, summaries, or agent outputs may inherit a shared source or earlier claim, so their number does not establish independent evidentiary support. | This matters when judging whether apparently convergent representations provide distinct support for a reconstruction or claim. It may be relevant to Merge Failure or Entity Substitution only when a defective reconstruction is actually produced. | Shared provenance is not inherently defective. Independence must not be inferred from document counts, citations, or agent counts alone. |
| **Cross-agent hypothesis propagation** | In a multi-agent configuration, one agent's hypothesis, partial match, or summary may condition another agent's retrieval and interpretation. | Apparent agreement may reflect a shared premise rather than independent examination; possible reconstruction consequences remain outcome-dependent. | This is a multi-agent special case, not a definition of agentic retrieval. Multiple agents can also provide genuinely complementary evidence. |

These are local analytical labels for this extension, not a new taxonomy of DIO/ODI failure modes. Their relations to existing DIO/ODI concepts are conditional and non-deterministic. The relevant DIO failure mode remains defined by the resulting reconstruction, not by the mere existence of an iterative search process.

### Relation to the commit boundary

The distinction from [*Constraining the Commit Boundary*](https://zenodo.org/records/23580733) is complementary:

- **This extension** examines how a hypothesis may shape the evidentiary path before a final identity-changing decision.
- **The commit-boundary paper** specifies conditions under which the proposed persistent mutation may be authorized.
- **Neither artifact claims that the other problem is solved by its own contribution.** A commit guardrail can constrain a write under its declared evidence contract; this extension does not claim to correct the upstream acquisition process, and it does not propose a complete control or recovery mechanism.

A high confidence score or agreement among several agents is therefore not, by itself, evidence that the supporting retrieval paths were independent. Conversely, evidence dependence alone does not prove that a hypothesis is wrong. The mapping identifies a question to inspect, not a universal verdict on agentic retrieval.

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
- Beránek, D. (2026, 22 October). *Constraining the Commit Boundary: A DIO/ODI-Informed Authorization Guardrail for Agentic Entity Resolution*. Zenodo, record 23580733: https://zenodo.org/records/23580733. This later work distinguishes commit-time authorization from the broader hypothesis-conditioned evidence-acquisition and feedback problem examined in the live extension.

The first two works ground the original DIO diagnostic mapping. *Constraining the Commit Boundary* is a later developmental reference; its inclusion does not imply that it implements or empirically validates this mapping extension.

The RAG stages and incidents in this document are generic analytical examples, not claims of empirical validation.

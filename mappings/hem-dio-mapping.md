# Application Mapping: HEM Heterogeneity Taxonomy × DIO Reconstruction Consequences

**Status:** Derived application layer under active development after DIO/ODI Reference Model v0.2.0  
**Relation to the reference vocabulary:** This mapping is not part of the canonical DIO/ODI Reference Vocabulary. It applies vocabulary concepts to an external analytical framework and does not modify their definitions, hierarchy, or relations.  
**Scope:** Diagnostic mapping between heterogeneity conditions identified in Heterogeneous Entity Matching (HEM) and possible DIO reconstruction consequences. It is not a claim of taxonomic equivalence or deterministic causality.

## Context and rationale

Heterogeneous Entity Matching (HEM) provides a systematic taxonomy of heterogeneity affecting entity matching across diverse data environments. Moslemi et al. distinguish between **representation heterogeneity**—Multimodality, Format Heterogeneity, and Structural (Schema) Heterogeneity—and **semantic heterogeneity**—Terminology & Language, Contextual Variability, Granularity & Resolution, Temporal Variability, and Data Quality.

The HEM taxonomy is valuable here because it characterizes heterogeneity as a first-class condition of the entity-matching problem. Its categories provide an external analytical axis for asking how variations in the form, organization, meaning, context, temporal state, resolution, or quality of representations may affect the subsequent reconstruction of entity identity.

The two frameworks operate at different analytical levels:

> **HEM heterogeneity types describe properties or mismatches in input representations and datasets; DIO Reconstruction Failure Modes describe failures or inadequacies of the resulting identity reconstruction.**

The relationship is therefore neither equivalence nor a one-to-one translation between taxonomies.

This mapping asks a narrower question: **under what conditions could particular forms of heterogeneity identified by HEM contribute to, amplify, or increase susceptibility to reconstruction consequences described by DIO?**

Relations are consequently expressed as *may contribute to*, *may increase the risk of*, or *may increase Semantic Vulnerability*. They should not be interpreted as deterministic causal claims.

## HEM taxonomy used in this mapping

### Representation heterogeneity

1. **Multimodality**
2. **Format Heterogeneity**
3. **Structural (Schema) Heterogeneity**

### Semantic heterogeneity

4. **Terminology & Language**
5. **Contextual Variability**
6. **Granularity & Resolution**
7. **Temporal Variability**
8. **Data Quality**

These labels follow the taxonomy presented by Moslemi et al. The DIO-side concepts in the table below are drawn from the DIO/ODI Reference Vocabulary v0.1.0.

## Mapping table

| HEM heterogeneity type | DIO reconstruction consequence | Relation | Interpretation |
| --- | --- | --- | --- |
| **Multimodality** | [Semantic Fragmentation](https://vocab.danielberanek.cz/dio-odi/#SemanticFragmentation); [Split Failure](https://vocab.danielberanek.cz/dio-odi/#SplitFailure); [Semantic Vulnerability](https://vocab.danielberanek.cz/dio-odi/#SemanticVulnerability) | may contribute to / may increase | Representations of one referent distributed across modalities may be integrated unevenly or treated as disconnected evidence. Multimodality itself is not a DIO failure; the relevant DIO question is whether referential unity or semantic coherence survives cross-modal reconstruction. |
| **Format Heterogeneity** | [Semantic Vulnerability](https://vocab.danielberanek.cz/dio-odi/#SemanticVulnerability); secondarily Merge/Split failures | may increase / may contribute to | Syntactic incompatibility can reduce the usable overlap among otherwise compatible representations. Where parsing, normalization, or alignment is incomplete, reconstruction becomes more sensitive to which formats remain legible to the observer. |
| **Structural (Schema) Heterogeneity** | [Merge Failure](https://vocab.danielberanek.cz/dio-odi/#MergeFailure); [Split Failure](https://vocab.danielberanek.cz/dio-odi/#SplitFailure); [Semantic Fragmentation](https://vocab.danielberanek.cz/dio-odi/#SemanticFragmentation) | may contribute to | Misaligned attributes, hierarchies, or schemas can obscure identity-preserving correspondences or produce false correspondences, affecting referential separation and semantic integration. |
| **Terminology & Language** | [Entity Substitution](https://vocab.danielberanek.cz/dio-odi/#EntitySubstitution); [Split Failure](https://vocab.danielberanek.cz/dio-odi/#SplitFailure); [Semantic Fragmentation](https://vocab.danielberanek.cz/dio-odi/#SemanticFragmentation) | may contribute to / may increase risk of | Aliases, synonyms, multilingual labels, and domain-specific terminology can weaken or distort the connection among representations of the same referent or increase confusion among distinct referents. |
| **Contextual Variability** | [Contextual Displacement](https://vocab.danielberanek.cz/dio-odi/#ContextualDisplacement); [Entity Substitution](https://vocab.danielberanek.cz/dio-odi/#EntitySubstitution) | may contribute to | Meaning that changes with context can cause a legitimate but secondary aspect of an entity to dominate reconstruction, or can support a wrong referential interpretation where contextual disambiguation fails. |
| **Granularity & Resolution** | [Semantic Fragmentation](https://vocab.danielberanek.cz/dio-odi/#SemanticFragmentation); [Contextual Displacement](https://vocab.danielberanek.cz/dio-odi/#ContextualDisplacement); [Semantic Vulnerability](https://vocab.danielberanek.cz/dio-odi/#SemanticVulnerability) | may contribute to / may increase | Representations at different levels of detail can remain referentially compatible while resisting coherent integration. A coarse or overly specific representation can also displace the level of identity relevant to the observation context. |
| **Temporal Variability** | [Temporal Misalignment](https://vocab.danielberanek.cz/dio-odi/#TemporalMisalignment); [Temporal Discontinuity](https://vocab.danielberanek.cz/dio-odi/#TemporalDiscontinuity) | may contribute to | Time-sensitive differences can yield a reconstruction with the correct referent but the wrong temporal state, or can break perceived continuity across legitimate transformation. |
| **Data Quality** | [Semantic Vulnerability](https://vocab.danielberanek.cz/dio-odi/#SemanticVulnerability); potentially multiple Reconstruction Failure Modes | may increase / may contribute to | Missing, noisy, inconsistent, or outdated values can make reconstruction disproportionately sensitive to the remaining evidence. No single DIO failure follows automatically: the realized consequence depends on the observation domain and reconstruction mechanism. |

## Analytical bridge

The mapping can be summarized as a three-level distinction:

1. **HEM heterogeneity condition** — a property or mismatch in available representations or datasets;
2. **reconstruction pressure** — the way that condition alters legibility, alignment, evidence balance, or robustness for an observer;
3. **DIO reconstruction consequence** — a realized failure mode, contextual/temporal inadequacy, or increased Semantic Vulnerability.

This distinction prevents upstream data heterogeneity from being mislabeled as a downstream reconstruction failure.

### Semantic Vulnerability as a bridge concept

[Semantic Vulnerability](https://vocab.danielberanek.cz/dio-odi/#SemanticVulnerability) is especially useful in this mapping because heterogeneity need not produce an observable Reconstruction Failure Mode. Instead, it may make the reconstruction more susceptible to disproportionate change under perturbations in representation availability, interpretation, ranking, or context.

This gives the two frameworks a useful non-equivalent relation:

**HEM describes heterogeneous conditions; Semantic Vulnerability expresses susceptibility under those conditions; Reconstruction Failure Modes describe particular realized failures of reconstruction.**

This is a diagnostic interpretation, not an assertion that Semantic Vulnerability is caused by every HEM category.

## Interpretation boundary

This mapping should not be read as:

- claiming that HEM and DIO use equivalent taxonomies;
- redefining HEM heterogeneity types as DIO concepts;
- claiming that heterogeneity necessarily produces a reconstruction failure;
- claiming a one-to-one relation between any HEM type and any DIO failure mode;
- treating an entity-matching model error as automatically identical to a DIO Reconstruction Failure Mode;
- asserting causal relations not established empirically.

The mapping is an analytical projection: it uses HEM as an externally developed taxonomy of heterogeneous input conditions and DIO as a vocabulary for describing possible consequences for identity reconstruction.

## Source basis

### HEM source

Moslemi, M. H., Mousavi, A., Behkamal, B., & Milani, M. (2026). *Heterogeneity in entity matching: A survey and experimental analysis*. **Data & Knowledge Engineering, 164**, 102575.  
https://doi.org/10.1016/j.datak.2026.102575

The HEM taxonomy and its category labels are attributed to this source. The HEM paper distinguishes representation and semantic heterogeneity and presents eight second-level categories used in this mapping.

### DIO/ODI sources

- Beránek, D. (2026). *Minimum Viable Digital Identity Optimization (DIO): From Adversarial Reduction to the Semantic Field Dynamics of Digital Identity*. https://doi.org/10.5281/zenodo.23226205
- Beránek, D. (2026). *From Entity Resolution Anomalies to Reconstruction Failure Modes: A Taxonomic Note Following Minimum Viable DIO*. https://doi.org/10.5281/zenodo.23269323
- DIO/ODI Reference Vocabulary v0.1.0: https://vocab.danielberanek.cz/dio-odi/

## Provenance note

The **HEM taxonomy is external source material**. The relations proposed in the mapping table are a DIO-side analytical interpretation authored for this Application Mapping. They are not claims made by Moslemi et al., and they do not modify the canonical DIO/ODI Reference Vocabulary.

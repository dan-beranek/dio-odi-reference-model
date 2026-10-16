# DIO/ODI terminology — v0.1.1 (working revision)

This file is the human-readable companion to `dio-odi-skos.ttl`.

## Discipline and models

| Concept | Current role |
|---|---|
| Digital Identity Optimization (DIO) | Applied discipline |
| Ontology of Digital Identity (ODI) | Theoretical meta-layer |
| Minimum Viable DIO (MVDIO) | Coarse-grained minimum analytical model |
| K6 Semantic Connectome | Finer-grained candidate model of the same dynamic object |
| Semantic Field | Model label for the shared configuration of mutually conditioned dimensions |

## K6 dimensions

Entity · Representation · Interpretation · Trust · Relationship · Reconstruction

The vocabulary does **not** model these as a sequential pipeline.

## MVDIO core

- Referential Continuity
- Distributed Digital Representational State
- Observer
- Observation Domain
- Reconstruction Mechanism
- DIO Problem
- DIO Intervention
- Identity-Preserving Constraint
- Essential Vector
- Identity-Preserving Variation

## Current Reconstruction Failure Mode hierarchy

- Referential Reconstruction Failures
  - Entity Substitution
  - Merge Failure
  - Split Failure
  - Entity Omission
- Semantic Coherence Failures
  - Semantic Fragmentation
- Temporal Reconstruction Failures
  - Temporal Discontinuity
  - Temporal Misalignment
- Contextual Adequacy Failures
  - Contextual Displacement

The hierarchy is non-exclusive and multi-level.

## Deliberately outside the failure hierarchy

### Identity Collapse

Retained as a phenomenon-level concept in the sense established in *The Crisis of Entity Resolution in Heterogeneous AI Environments*. v0.1 does not assert a causal, constitutive, exhaustive, or necessary relationship between Identity Collapse and individual Reconstruction Failure Modes.

### Semantic Vulnerability

A robustness-related property, not a realized Reconstruction Failure Mode.

Direct conceptual counterpart: **Semantic Robustness**.

### Reconstruction Capture

Present in MVDIO and retained as a related concept. v0.1 deliberately does not strengthen its relation to Semantic Vulnerability beyond `skos:related`.

## Historical vocabulary

**Entity Resolution Anomaly** is retained only as a historical grouping label. The current hierarchy should not be reconstructed by treating it as the parent class of Identity Collapse, Semantic Fragmentation, Temporal Discontinuity, and Semantic Vulnerability.


## External reference terminology

These established terms are included for contextual reference. They are not defined as DIO-specific constructs and are not part of the Reconstruction Failure Mode hierarchy.

| Concept | Definition | Source |
|---|---|---|
| Knowledge Graph (KG) | Graph-structured representation of knowledge in which nodes represent entities or concepts and edges represent semantic relationships. | [Schneider et al. (2022)](https://doi.org/10.18653/v1/2022.aacl-main.46) |
| Entity Linking | Associates entity mentions in text with corresponding entities or unambiguous identifiers in a knowledge base or knowledge graph. Do not conflate with Entity Resolution. | [Rosales-Méndez et al. (2019)](https://doi.org/10.18653/v1/D19-1066) |

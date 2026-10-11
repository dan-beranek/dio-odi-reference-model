# Application mappings

Application Mappings are **derived application layers** within the DIO/ODI Reference Model. They project the canonical DIO/ODI Reference Vocabulary onto external technical or analytical domains while remaining explicitly outside the vocabulary itself.

**Reference Vocabulary = what DIO/ODI concepts mean.**  
**Application Mapping = how those concepts can be analytically applied to an external domain.**

Public index: https://vocab.danielberanek.cz/mappings/

## Available

### Application Mapping: DIO Reconstruction Failure Modes × RAG Pipeline

- Frontend: https://vocab.danielberanek.cz/mappings/rag-pipeline/
- Source: [rag-pipeline-mapping.md](rag-pipeline-mapping.md)
- JSON-LD: [rag-pipeline-mapping.jsonld](rag-pipeline-mapping.jsonld) — introduced in Reference Model v0.3.1
- Turtle RDF: [rag-pipeline-mapping.ttl](rag-pipeline-mapping.ttl) — introduced in Reference Model v0.3.1 with qualified mapping assertions
- Introduced in: DIO/ODI Reference Model v0.2.0
- Included in: DIO/ODI Reference Model v0.3.1 — DOI pending
- Archived release: https://doi.org/10.5281/zenodo.23282752

Maps current DIO Reconstruction Failure Modes to generic retrieval-augmented generation pipeline loci, mechanisms, observable symptoms, and hypothetical incidents.

### Application Mapping: HEM Heterogeneity Taxonomy × DIO Reconstruction Consequences

- Frontend: https://vocab.danielberanek.cz/mappings/hem-dio/
- Source: [hem-dio-mapping.md](hem-dio-mapping.md)
- JSON-LD: [hem-dio-mapping.jsonld](hem-dio-mapping.jsonld)
- Turtle RDF: [hem-dio-mapping.ttl](hem-dio-mapping.ttl) — post-v0.3.0 live representation with qualified mapping assertions
- Conceptual bridge: [hem-dio/bridge.svg](hem-dio/bridge.svg)
- External HEM source: https://doi.org/10.1016/j.datak.2026.102575
- Introduced in: DIO/ODI Reference Model v0.3.0
- Included in: DIO/ODI Reference Model v0.3.1 — DOI pending

Uses the Heterogeneous Entity Matching taxonomy of Moslemi et al. as an external analytical axis. HEM categories characterize heterogeneous input conditions; DIO concepts characterize possible consequences for identity reconstruction. The mapping is many-to-many and diagnostic, not taxonomic equivalence.

## Boundary

Nothing in this directory automatically becomes part of the canonical DIO/ODI Reference Vocabulary. New mappings may apply existing concepts, cite external frameworks, and propose explicitly labeled analytical relations, but they must not silently modify canonical definitions, hierarchy, or provenance.

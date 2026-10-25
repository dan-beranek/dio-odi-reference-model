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
- Introduced and initially archived in: DIO/ODI Reference Model v0.2.0 — https://doi.org/10.5281/zenodo.23282752
- Retained in subsequent archived v0.3.x releases, including v0.3.1 and v0.3.2
- Iterative/hypothesis-conditioned extension added: 2026-10-25; first included in archived Reference Model v0.4.0 — https://doi.org/10.5281/zenodo.23632619
- Carried forward in current archived Reference Model v0.5.0 — https://doi.org/10.5281/zenodo.23643845
- Development link: *Constraining the Commit Boundary* (published 2026-10-22) — https://zenodo.org/records/23580733

Maps current DIO Reconstruction Failure Modes to generic retrieval-augmented generation pipeline loci, mechanisms, observable symptoms, and hypothetical incidents. A live extension added on 2026-10-25 examines iterative and hypothesis-conditioned evidence acquisition in relation to the upstream research boundary identified in [Constraining the Commit Boundary](https://zenodo.org/records/23580733). The base mapping was introduced and archived in v0.2.0 and retained in subsequent v0.3.x releases; the iterative/hypothesis-conditioned extension was first included in archived v0.4.0 and is carried forward in archived v0.5.0.

### Application Mapping: HEM Heterogeneity Taxonomy × DIO Reconstruction Consequences

- Frontend: https://vocab.danielberanek.cz/mappings/hem-dio/
- Source: [hem-dio-mapping.md](hem-dio-mapping.md)
- JSON-LD: [hem-dio-mapping.jsonld](hem-dio-mapping.jsonld)
- Turtle RDF: [hem-dio-mapping.ttl](hem-dio-mapping.ttl) — introduced in Reference Model v0.3.1 with qualified mapping assertions
- Conceptual bridge: [hem-dio/bridge.svg](hem-dio/bridge.svg)
- External HEM source: https://doi.org/10.1016/j.datak.2026.102575
- Introduced in: DIO/ODI Reference Model v0.3.0
- Included in: DIO/ODI Reference Model v0.3.2 — https://doi.org/10.5281/zenodo.23300703
- Carried forward in archived Reference Model v0.4.0 — https://doi.org/10.5281/zenodo.23632619
- Carried forward in current archived Reference Model v0.5.0 — https://doi.org/10.5281/zenodo.23643845

Uses the Heterogeneous Entity Matching taxonomy of Moslemi et al. as an external analytical axis. HEM categories characterize heterogeneous input conditions; DIO concepts characterize possible consequences for identity reconstruction. The mapping is many-to-many and diagnostic, not taxonomic equivalence.

### Application Mapping: DIO/ODI Commit-Boundary Contract × Policy-as-Code Authorization

- Frontend: https://vocab.danielberanek.cz/mappings/commit-boundary-policy/
- Source: [commit-boundary-policy-mapping.md](commit-boundary-policy-mapping.md)
- JSON-LD: [commit-boundary-policy-mapping.jsonld](commit-boundary-policy-mapping.jsonld)
- Turtle RDF: [commit-boundary-policy-mapping.ttl](commit-boundary-policy-mapping.ttl)
- DIO/ODI source: https://zenodo.org/records/23580733
- External technical references: OPA documentation (https://www.openpolicyagent.org/docs); Cedar authorization guide (https://docs.cedarpolicy.com/auth/authorization.html)
- Added to live source tree: 2026-10-25
- Archival status: first included in archived Reference Model v0.4.0 — https://doi.org/10.5281/zenodo.23632619; carried forward in v0.5.0 — https://doi.org/10.5281/zenodo.23643845

Maps commit-boundary authorization obligations to relevant Policy-as-Code capabilities and the additional policy-modeling, trusted-evidence, enforcement, freshness, and transactional mechanisms needed for an integration. OPA/Rego and Cedar are reference points only; the mapping does not claim either engine natively implements the commit-boundary contract.

## Boundary

Nothing in this directory automatically becomes part of the canonical DIO/ODI Reference Vocabulary. New mappings may apply existing concepts, cite external frameworks, and propose explicitly labeled analytical relations, but they must not silently modify canonical definitions, hierarchy, or provenance.

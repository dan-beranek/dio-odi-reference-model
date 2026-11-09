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
- Carried forward in archived Reference Model v0.5.0 — https://doi.org/10.5281/zenodo.23643845 and v0.6.0 — https://doi.org/10.5281/zenodo.23966487
- First included in archived Reference Model v0.7.0; carried forward in v0.8.0 and current archived v0.9.0 — https://doi.org/10.5281/zenodo.24085589
- Development link: *Constraining the Commit Boundary* (published 2026-10-22) — https://zenodo.org/records/23580733

Maps current DIO Reconstruction Failure Modes to generic retrieval-augmented generation pipeline loci, mechanisms, observable symptoms, and hypothetical incidents. A live extension added on 2026-10-25 examines iterative and hypothesis-conditioned evidence acquisition in relation to the upstream research boundary identified in [Constraining the Commit Boundary](https://zenodo.org/records/23580733). The base mapping was introduced and archived in v0.2.0 and retained in subsequent v0.3.x releases; the iterative/hypothesis-conditioned extension was first included in archived v0.4.0 and is carried forward in archived v0.5.0, v0.6.0, and v0.7.0.

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
- Carried forward in archived Reference Model v0.5.0 — https://doi.org/10.5281/zenodo.23643845 and v0.6.0 — https://doi.org/10.5281/zenodo.23966487
- First included in archived Reference Model v0.7.0; carried forward in v0.8.0 and current archived v0.9.0 — https://doi.org/10.5281/zenodo.24085589

Uses the Heterogeneous Entity Matching taxonomy of Moslemi et al. as an external analytical axis. HEM categories characterize heterogeneous input conditions; DIO concepts characterize possible consequences for identity reconstruction. The mapping is many-to-many and diagnostic, not taxonomic equivalence.

### Application Mapping: DIO/ODI Commit-Boundary Contract × Policy-as-Code Authorization

- Frontend: https://vocab.danielberanek.cz/mappings/commit-boundary-policy/
- Source: [commit-boundary-policy-mapping.md](commit-boundary-policy-mapping.md)
- JSON-LD: [commit-boundary-policy-mapping.jsonld](commit-boundary-policy-mapping.jsonld)
- Turtle RDF: [commit-boundary-policy-mapping.ttl](commit-boundary-policy-mapping.ttl)
- DIO/ODI source: https://zenodo.org/records/23580733
- External technical references: OPA documentation (https://www.openpolicyagent.org/docs); Cedar authorization guide (https://docs.cedarpolicy.com/auth/authorization.html)
- Added to live source tree: 2026-10-25
- Archival status: first included in archived Reference Model v0.4.0 — https://doi.org/10.5281/zenodo.23632619; carried forward in archived v0.5.0, v0.6.0, v0.7.0, and v0.8.0; included in current archived v0.9.0 — https://doi.org/10.5281/zenodo.24085589

Maps commit-boundary authorization obligations to relevant Policy-as-Code capabilities and the additional policy-modeling, trusted-evidence, enforcement, freshness, and transactional mechanisms needed for an integration. OPA/Rego and Cedar are reference points only; the mapping does not claim either engine natively implements the commit-boundary contract.


### Application Mapping: DIO/ODI-Informed Agentic ER Commit-Boundary Architecture

- Frontend: https://vocab.danielberanek.cz/mappings/agentic-er-architecture/
- Source: [agentic-er-commit-boundary-architecture-mapping.md](agentic-er-commit-boundary-architecture-mapping.md)
- JSON-LD: [agentic-er-commit-boundary-architecture-mapping.jsonld](agentic-er-commit-boundary-architecture-mapping.jsonld) — 120 local architecture concepts and 206 qualified relation assertions
- Turtle RDF: [agentic-er-commit-boundary-architecture-mapping.ttl](agentic-er-commit-boundary-architecture-mapping.ttl)
- Architecture diagram: [agentic-er-architecture/architecture.svg](agentic-er-architecture/architecture.svg)
- Public source paper: arXiv:2610.37407 v2 — https://arxiv.org/abs/2610.37407v2; stable Concept URL: https://arxiv.org/abs/2610.37407; earlier Zenodo version 1 record: https://zenodo.org/records/23580733
- Section-level alignment: production manuscript `Constraining_the_Commit_Boundary_v55_production.md`, dated 2026-11-04; retained as the provenance source for section anchors in public arXiv v2
- Canonical Reference Vocabulary identity: https://vocab.danielberanek.cz/dio-odi/#ReferenceVocabulary
- Vocabulary state at mapping v0.3.1 publication: v0.2.1; the v0.9.0 archive carries Vocabulary v0.2.2, a metadata-only prefix alignment with the same concept model
- First archived in: DIO/ODI Reference Model v0.7.0 — https://doi.org/10.5281/zenodo.24020300; carried forward in v0.8.0 and current v0.9.0 — https://doi.org/10.5281/zenodo.24085589
- Previous archived snapshot: Reference Model v0.6.0 contains the earlier mapping v0.3.0 and Vocabulary v0.2.0 — https://doi.org/10.5281/zenodo.23966487
- Added to live source tree: 2026-11-04; mapping v0.3.1 reflects the 2026-11-06 provenance synchronization to public arXiv v2 and was first included in archived Reference Model v0.7.0, then carried forward in v0.8.0 and v0.9.0; version 0.3.0 remains archived in Reference Model v0.6.0

Together, the arXiv paper and this mapping form a coordinated research artefact: the paper specifies the proposed architecture, while the mapping formalizes its internal conceptual and functional relations. The Markdown source and its JSON-LD and Turtle/RDF serializations expose that same relational model for human inspection and machine processing. The mapping covers selected diagnostics, domain-governed constraint binding, mutation-specific required propositions, claim-specific evidence eligibility, two-phase authorization, the conditional commit invariant, assumptions, and prospective evaluation design. It is complementary to the Commit-Boundary × Policy-as-Code mapping, which projects selected contract obligations into OPA/Rego and Cedar. This mapping is a non-normative derived layer, does not modify canonical vocabulary, and claims neither implementation nor empirical validation.

## Boundary

Nothing in this directory automatically becomes part of the canonical DIO/ODI Reference Vocabulary. New mappings may apply existing concepts, cite external frameworks, and propose explicitly labeled analytical relations, but they must not silently modify canonical definitions, hierarchy, or provenance.

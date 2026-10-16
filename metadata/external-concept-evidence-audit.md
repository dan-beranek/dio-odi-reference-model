# Semantic audit of external concept evidence

Date: 2026-10-16  
Scope: the 90 evidence records in `metadata/external-concept-mappings.json`, covering 39 DIO/ODI concepts and 17 distinct Wikipedia pages.

## Purpose and limits

This is a semantic-usefulness review, not a SKOS mapping approval. A first cleanup pass has since been applied to the evidence registry: three redundant name-resolution records and one duplicate record-linkage record were removed, and several weak notes were made more precise. Evidence may be retained because it offers a direct technical neighbor, a bounded methodological/structural analogy, or an explicit contrast. A source does not become a mapping target merely because it is useful evidence. No `skos:exactMatch` or `owl:sameAs` is implied.

The review is based on the recorded source notes and the high-level page checks. It is not a line-by-line validation of every note against a cited passage. Where the relationship is only analogical, the notes must preserve that boundary.

## Decision categories

- **A — Retain: direct adjacent technical context.** The source addresses a narrower mechanism or problem that overlaps a specific part of the DIO/ODI concept.
- **B — Retain: bounded analogy or contrast.** Useful for theoretical orientation or for delimiting scope, but not evidence of equivalence.
- **C — Retain selectively / consolidate.** Potentially useful, but duplicated, indirect, or low-yield relative to other evidence for the same concept.
- **D — Remove only if the note cannot be made specific.** Generic topical proximity without a clear explanatory contribution. No source should be removed merely because it is distant if the relation is clearly explained.

## Concept-by-concept recommendations

| DIO/ODI concept | Assessment | Recommendation |
|---|---|---|
| DIO | A | Keep Digital identity as broad context; keep Record linkage and Entity linking as narrower neighboring technical fields. Explicitly avoid implying either defines DIO. |
| ODI | A/B | Keep Ontology (information science), Linked data, and Ontology alignment. Keep Ontology components and UMBEL as structural/mapping-architecture analogies, not theoretical precedents for ODI itself. |
| MVDIO | B/C | Ontology components and UMBEL are distant architecture analogies. Ontology alignment is the clearest methodological analogy. Consider whether all three add distinct value; do not describe any as validation of the minimum model. |
| Semantic Field | B/C | Meaning (semiotics) is the strongest conceptual context. Ontology domain-of-discourse and Linked data are distant analogies; retain only with the current explicit non-equivalence caveats. |
| K6 Semantic Connectome | B/C | Ontology components is a generic structural analogy; UMBEL and Ontology alignment are indirect. Retain as architectural context only if the notes explicitly state that they do not validate K6's six dimensions. |
| Entity dimension | B | Digital identity is broad context, not a definition. One evidence record is sufficient unless a more specific source is identified. |
| Representation dimension | A/B | Keep Digital identity and Linked data as concrete representation context; Signified and signifier is a theoretical contrast between form and interpreted concept. Preserve the distinction between representation and identity. |
| Interpretation dimension | A/B | Keep Name resolution as a narrow computational example and Sign (semiotics) as theoretical context. State clearly that neither exhausts DIO's interpretation dimension. |
| Trust dimension | B | Keep Trust (social science) only as an explicit contrast. Preserve the non-anthropomorphic, task-sensitive DIO framing; do not map the concepts. |
| Relationship dimension | A/B | Keep FOAF and Linked data as machine-readable relational examples; Sign (semiotics) is a theoretical analogy. Avoid equating formal relations, semiotic relations, and the DIO dimension. |
| Reconstruction dimension | A/C | Record linkage, name resolution, and Entity linking are relevant narrow mechanisms. Consolidate the two name-resolution records if they do not serve distinct evidentiary purposes. |
| Referential continuity | B | Personal identity is a philosophical analogy; Signified and signifier is a more distant contrast. Keep only with explicit scope limits; neither is a direct definition of temporal referential continuity. |
| Distributed representational state | A | Linked data is the strongest technical context; Digital identity and JSON-LD add broader context and a serialization example. Do not equate a serialization format with the distributed state. |
| Observer | B/C | Sign (semiotics) is a bounded theoretical parallel. Name resolution is a weak processing-context connection; retain only if it illustrates an explicitly defined machine observer rather than merely a software process. |
| Observation domain | B/C | Ontology's domain of discourse is a distant analogy. Keep if the distinction between a modeling domain and DIO's observation domain is made explicit. |
| Reconstruction mechanism | A/C | Record linkage is a concrete neighboring mechanism. JSON-LD concerns representation infrastructure rather than reconstruction itself; retain as a boundary case only if that contrast is useful. The two Record linkage records are partly redundant and can likely be consolidated. |
| DIO problem | C | Name resolution provides a narrow example of a referential problem. Keep if the intended problem class is specified; otherwise this is generic topical context. |
| DIO intervention | C | Record linkage and Linked data describe possible technical intervention contexts, but the connection is indirect. Keep only if the note explains what changes in the evidence available to an observer. |
| Identity-preserving constraint | B | Personal identity, Linked data identifiers, and Ontology alignment offer distinct philosophical, technical, and methodological perspectives. Keep as analogies, not as a jointly established criterion. |
| Essential vector | B/C | Personal identity is the clearest distant analogy; Linked data identifiers are a narrow technical example; Meaning (semiotics) is contextual. Avoid suggesting that stable identifiers define the essential vector. Consider consolidating if the three perspectives do not each do distinct work. |
| Identity-preserving variation | B | Personal identity and Signified and signifier are conceptual analogies for persistence amid change. Keep with the caveat that neither establishes DIO's criteria for identity preservation. |
| Reconstruction failure mode | A/C | Name resolution and Record linkage provide narrow failure examples. Keep both if they illustrate distinct failure mechanisms; otherwise consolidate redundant general context. |
| Referential reconstruction failure | A | Record linkage errors and wrong-referent name resolution are relevant neighboring failure examples. The name-resolution evidence is the more specific example; do not treat either as the whole DIO failure concept. |
| Entity substitution | A | Name resolution and Entity linking are the clearest neighboring examples of assignment to a wrong referent/entity. Keep both if the NLP-level distinction is useful. |
| Merge failure | A | Record linkage is directly adjacent to incorrect linkage of distinct entities. Keep as technical context; any SKOS mapping still requires separate target-scope review. |
| Split failure | A | Record linkage is directly adjacent to failure to link records of the same entity. Keep as technical context; retain the distinction between record-level matching and reconstructed identity. |
| Entity omission | A/C | Entity linking is the stronger technical neighbor for missed or unlinked mentions; Name resolution is broader and less specific. Consider retaining only Entity linking unless the name-resolution source adds a distinct example. |
| Semantic coherence failure | B/C | Ontology alignment is the strongest methodological neighbor; Ontology components and UMBEL provide structural/interoperability context. Linked data is mostly a contrast. Keep only where each source adds a distinct explanatory role. |
| Semantic fragmentation | B/C | Ontology alignment and Linked data offer useful contrasts around interlinking/aligning descriptions; UMBEL and Ontology components are more distant. Consolidate if the same structural point is repeated. |
| Temporal reconstruction failure | B | Personal identity provides philosophical context for persistence through time. Keep as analogy, not evidence of the DIO failure mode itself. |
| Temporal discontinuity | B | Personal identity is a useful but distant temporal analogy. Keep only with the explicit distinction that DIO concerns reconstruction across digital traces. |
| Temporal misalignment | C | Digital identity is broad context but the current note does not yet establish a specific temporal-mismatch mechanism. Strengthen the note against a relevant passage or remove this evidence record. |
| Contextual adequacy failure | A/C | Name resolution and Entity linking are relevant context-sensitive tasks. The two Name resolution records are near-duplicates; consolidate unless each is tied to a different passage or point. |
| Contextual displacement | A/C | Name resolution and Entity linking illustrate context-dependent referent selection. Consolidate duplicate Name resolution records and distinguish displacement from ordinary ambiguity. |
| Identity collapse | C | Digital identity alone is a weak contrast unless the note names the specific distinction between general digital identity and DIO's identity-collapse phenomenon. Strengthen or remove this evidence record. |
| Semantic vulnerability | B | Robustness (computer science) is a useful conceptual counterpart/contrast. Keep as a bounded relationship; do not imply the article defines semantic vulnerability. |
| Semantic robustness | A/B/C | Robustness (computer science) is the strongest neighboring concept. Linked data is an infrastructure boundary case and may be redundant unless it illustrates why explicit links do not guarantee robust reconstruction. |
| Reconstruction capture | C | Record linkage and JSON-LD are both indirect. Retain only if the notes explain the specific mechanism by which a selected dataset/matching procedure or context layer constrains downstream reconstruction; otherwise consider removing both. |
| Entity resolution anomaly | A | Record linkage and Entity linking are the strongest adjacent technical contexts; Name resolution adds a narrower NLP perspective. Linked data is useful as a contrast because linking resources is not the same operation as resolving whether records refer to one entity. |

## Cross-cutting cleanup recommendations

1. **Consolidate repeated evidence.** Name resolution appears multiple times for Reconstruction, Contextual adequacy failure, and Contextual displacement. Duplicate source URLs are not inherently wrong, but each record should support a distinct proposition or passage.
2. **Separate evidence from mappings.** The current evidence registry may retain all four categories above. SKOS mappings should be reviewed independently against the external concept's actual scope and relation direction.
3. **Keep explicit contrastive evidence.** Trust (social science), Signified and signifier, Personal identity, and Robustness (computer science) can be useful even when distant, provided the notes state what the comparison illuminates and where it breaks.
4. **Do not treat a Wikipedia topic as proof.** The presence of an article supports source availability and topical context; it does not establish that the DIO concept is recognized externally or that the proposed relationship is semantically valid.
5. **No mapping approvals follow from this audit.** Candidate and rejected mapping statuses remain unchanged pending independent review of the Wikidata/DBpedia target pages, scope, and SKOS relation direction.

## Recommended next sequence

1. **Completed first pass:** consolidated four redundant evidence records and clarified notes for contextual adequacy/displacement, temporal misalignment, identity collapse, observer, reconstruction capture, essential vector, semantic coherence, and semantic fragmentation.
2. Review the remaining distant evidence selectively; preserve it when it contributes a clearly articulated contrast or analogy, rather than deleting it merely for being indirect.
3. Review each existing Wikidata/DBpedia mapping candidate against the actual target definition and the intended SKOS relation.
4. Only then consider generating a derived mapped Turtle file from the canonical vocabulary plus approved mappings.

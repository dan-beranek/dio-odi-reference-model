# External concept mapping audit — first candidate review

Date: 2026-10-16  
Scope: current candidate mappings in `metadata/external-concept-mappings.json`. This is a semantic review of target scope and relation choice, not an approval to publish mappings in derived Turtle.

## Decision rule

A candidate is not approved merely because its target is topically adjacent. `skos:broadMatch` requires the external target to be broader than the DIO/ODI concept; `skos:relatedMatch` is appropriate only for a meaningful, bounded associative relation. Wikipedia/DBpedia pages derived from the same article are not independent corroboration. No `skos:exactMatch` or `owl:sameAs` is proposed.

## Candidate assessment

| DIO/ODI concept | Target | Assessment | Recommendation |
|---|---|---|---|
| Entity Resolution Anomaly | Wikidata Q1266546 — record linkage | The item defines record linkage as matching records/entities across datasets and lists entity resolution as an alias. That establishes a clear neighboring technical field, but the DIO concept is an anomaly/failure category, not the matching process itself. | Retain as **candidate** `skos:relatedMatch`, with explicit scope limitation. Strongest current candidate, but not an automatic approval. |
| Entity Resolution Anomaly | DBpedia Record linkage | Topically adjacent to the Wikidata item and likely based on the same Wikipedia topic; not independent evidence. The current `skos:broadMatch` direction is not justified: record linkage is not demonstrably a broader concept of an anomaly. | Do not approve as `broadMatch`. Consider removing or revising to a clearly bounded `relatedMatch` only after validating the DBpedia resource and provenance. |
| Merge Failure | Wikidata Q18207010 — false positives and false negatives | The item concerns test/classification/reporting errors. DIO Merge Failure means distinct referents are reconstructed as one identity. The shared idea of an erroneous result is too generic to establish a useful concept mapping. | Reject as a mapping candidate; retain the item only as contextual evidence if the note explains the contrast. |
| Split Failure | Wikidata Q18207010 — false positives and false negatives | False negatives/positives do not describe one referentially continuous entity being reconstructed as multiple identities. The analogy is too weak for a stable vocabulary mapping. | Reject as a mapping candidate; contextual evidence only if useful to explain the distinction. |
| Merge Failure | DBpedia False positives and false negatives | Same scope problem as the Wikidata target; DBpedia may derive from the corresponding Wikipedia article and is not independent corroboration. The `broadMatch` direction is not supported. | Do not approve; remove or reclassify as contextual evidence. |
| Split Failure | DBpedia False positives and false negatives | Same scope problem as above; false-positive/false-negative classification errors are not the DIO referential split phenomenon. | Do not approve; remove or reclassify as contextual evidence. |
| Referential Continuity | Wikidata Q254474 — identity | The item defines identity as the relation each thing bears to itself. DIO Referential Continuity concerns a referent remaining analytically continuous through legitimate change over time. The concepts are philosophically adjacent but have different extensions. | Keep as **candidate** `skos:relatedMatch` only if the contrast is documented; otherwise reject. Do not use `broadMatch`. |
| Referential Continuity | DBpedia Identity (philosophy) | Philosophical identity is relevant background, but the proposed broader-than relation is not established and the scope differs from temporal continuity under change. | Do not approve as `broadMatch`; contextual evidence is safer than mapping. |
| Trust Dimension | Wikidata Q659974 — trust | The item describes reliance on another party's honesty and classifies trust under emotion/belief/psychological terminology. DIO's Trust dimension is explicitly context- and task-sensitive and need not imply human psychology. | **Reject** as a mapping candidate; use only as contrastive evidence if needed. |
| Trust Dimension | DBpedia Trust (social science) | Social-science trust is relevant to the ordinary meaning but risks importing interpersonal/anthropomorphic assumptions into the DIO dimension. Its proposed `broadMatch` direction is not established. | Do not approve. Prefer contextual/contrastive evidence over a SKOS mapping. |
| Semantic Robustness | Wikidata Q403605 — robustness | Wikidata defines robustness as the ability of an object, system, or property to resist perturbations. DIO Semantic Robustness specifically concerns identity reconstruction under perturbations of the representational environment, so the Wikidata concept plausibly has broader scope. | Retain as **candidate** `skos:broadMatch`; the direction is plausible, but author review is still needed before approval. |
| Semantic Robustness | DBpedia Robustness (computer science) | A potentially relevant neighboring concept, but the resource has not been validated sufficiently here to determine its precise scope or whether it is broader than the DIO concept. | Keep **candidate** only; verify the DBpedia resource and compare definitions before deciding. |

## Verified source observations

- Wikidata Q1266546 identifies **record linkage** as matching records/entities across datasets and lists “entity resolution” among its aliases: https://www.wikidata.org/wiki/Q1266546
- Wikidata Q18207010 describes **false positives and false negatives** as test/reporting errors and relates them to Type I/II errors and binary classification: https://www.wikidata.org/wiki/Q18207010
- Wikidata Q254474 defines philosophical **identity** as the relation each thing bears to itself: https://www.wikidata.org/wiki/Q254474
- Wikidata Q659974 describes **trust** as reliance on another party's honesty and includes psychological/emotional classifications: https://www.wikidata.org/wiki/Q659974
- Wikidata Q403605 defines **robustness** as the ability of an object, system, or property to resist perturbations: https://www.wikidata.org/wiki/Q403605

## Outcome

No candidate is promoted to `approved` in this audit. There are now two comparatively defensible provisional candidates: `EntityResolutionAnomaly skos:relatedMatch Q1266546`, because record linkage is a directly evidenced neighboring technical process; and `SemanticRobustness skos:broadMatch Q403605`, because general robustness plausibly has broader scope than robustness of identity reconstruction under representational perturbations. Both remain candidates until the vocabulary author confirms that the relation is useful for intended machine-readable interoperability.

The Merge Failure and Split Failure links to false positives/false negatives should not be treated as mappings: their commonality is generic error language, not a sufficiently specific conceptual relation. The trust and philosophical-identity candidates are better handled as contextual/contrastive evidence unless a more precisely scoped external concept is found.

DBpedia targets were not promoted: direct page retrieval was not reliable in this pass, and in any event a DBpedia URI derived from the same Wikipedia topic should not be counted as independent corroboration.

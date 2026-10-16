# DIO/ODI External Concept Mappings

## Purpose
This registry records candidate and reviewed semantic mappings from the canonical DIO/ODI Reference Vocabulary to external structured knowledge bases, and separately records external conceptual evidence. It does not redefine DIO/ODI concepts or alter the canonical vocabulary.

## Current state
- Registry version: 0.1.0
- State: audit in progress; initial semantic checks completed for a subset of candidates
- Source vocabulary: `vocabulary/dio-odi-skos.ttl`
- Source blob at inventory time: `f7c33af7a9977b40c787daf5ab0328c1590b1ffe`
- Vocabulary version: 0.1.0
- Concepts inventoried: 39
- Initial DBpedia candidates retained: 6 (unverified)
- Additional Wikidata candidates added after checking item descriptions: 4
- Rejected candidate mappings recorded: 1
- Approved mappings: 0
- Wikipedia evidence records added: 42 across 39 DIO/ODI concepts

The audit is partial. Wikipedia evidence has now been recorded at concept level for every inventoried concept with a relevant, identifiable article found in this pass. These are contextual references, not approved mappings. Some articles are deliberately distant analogues or contrastive cases; each note states the limited semantic value and the boundary of the comparison.

## Distinguish mapping targets from evidence sources
- **Wikidata:** a structured mapping target, but only after checking the item's label, description, statements, and scope.
- **DBpedia:** a structured RDF mapping target, only after confirming URI resolution and semantic scope.
- **Wikipedia:** normally a conceptual evidence source, not a mapping target. Its article can establish terminology, neighboring usage, examples, contrasts, or a relevant research context without asserting equivalence.
- **Primary literature and DIO/ODI source works:** evidence for interpreting the external article and the canonical concept.

Wikipedia articles are allowed to be semantically distant when the relationship is useful and explicitly qualified. “Related context” is not automatically a SKOS mapping. Record-linkage, personal-identity, ontology, and name-resolution articles, for example, illuminate different edges of the conceptual neighborhood but do not define DIO/ODI concepts.

Wikipedia and DBpedia must not be treated as independent corroboration where a DBpedia resource derives from the corresponding Wikipedia article.

## Allowed SKOS mapping properties
- `skos:closeMatch`
- `skos:broadMatch`
- `skos:narrowMatch`
- `skos:relatedMatch`

The direction matters. `dio:Concept skos:broadMatch external:Concept` says the external concept is broader than the DIO/ODI concept. `skos:narrowMatch` expresses the inverse direction.

Do not routinely use `skos:exactMatch` and do not use `owl:sameAs` for these concept mappings. Similar labels or topical adjacency are not sufficient evidence for any mapping relation.

## Evidence model
Each concept can carry an `evidence` array independently of its `mappings`. An evidence record contains:
- `uri`: the source article or document;
- `role`: why it is relevant (e.g. `adjacent-concept`, `contrastive-context`, `temporal-context`);
- `checkedOn`: date checked;
- `note`: the specific semantic connection and its limitation.

A concept-level evidence record does not imply a target mapping, does not change mapping status, and must not be projected into mapped Turtle as a SKOS relation. Evidence should be added when it improves conceptual interpretation, including for distant analogies and counterexamples. Do not manufacture a connection just to fill every concept's evidence list.

## Review states
- `not-reviewed`: concept inventory exists, external candidates have not yet been audited.
- `in-review`: one or more candidate mappings require verification.
- `reviewed-no-match`: a review was performed and no defensible external match was found.
- `reviewed-with-candidates`: research found candidates but none has been approved yet.
- `approved-mappings`: at least one mapping is approved.

Individual mappings use `candidate`, `approved`, or `rejected`. URI verification and semantic review are recorded separately. A documented no-match is a valid result, not a failed audit.

## Publication rule
Only mappings with mapping-level status `approved` may be projected into a derived Turtle distribution. Candidates, rejected mappings, evidence, rationale, and no-match decisions remain in this registry. The mapped Turtle file should be generated from the canonical vocabulary plus this registry; it must not become an independently maintained source of truth.

## Provenance and definition links
The canonical vocabulary currently uses `dcterms:source` on its concepts. The checked repository version contains no `rdfs:isDefinedBy` statements. Before changing this, compare the deployed namespace representation with the canonical file and decide separately how concept definitions, source publications, and archived Reference Model packages should be linked. A release DOI is not automatically the definition source for every concept.

## Initial candidates
The initial six DBpedia candidates are retained as unverified suggestions only:
1. Entity Resolution Anomaly → `http://dbpedia.org/resource/Record_linkage`
2. Merge Failure → `http://dbpedia.org/resource/False_positives_and_false_negatives`
3. Split Failure → `http://dbpedia.org/resource/False_positives_and_false_negatives`
4. Semantic Robustness → `http://dbpedia.org/resource/Robustness_(computer_science)`
5. Referential Continuity → `http://dbpedia.org/resource/Identity_(philosophy)`
6. Trust (K6 dimension) → `http://dbpedia.org/resource/Trust_(social_science)`

These are not endorsements. Merge Failure and Split Failure should be assessed separately even though the same external resource was proposed for both.

## Initial evidence-based findings (2026-10-16)
- **Record linkage — Wikidata Q1266546:** its description concerns joining records/entities across datasets and lists entity resolution as an alias. This is adjacent to the historical DIO term *Entity Resolution Anomaly*, but it does not define the anomaly itself. A tentative `skos:relatedMatch` candidate is recorded, not approved. [Wikidata item](https://www.wikidata.org/wiki/Q1266546)
- **False positives and false negatives — Wikidata Q18207010:** the item concerns data-reporting errors and is placed under type I/type II errors and binary classification. It is not equivalent to DIO Merge Failure or Split Failure. Separate weak `skos:relatedMatch` candidates are recorded for review, not approved. [Wikidata item](https://www.wikidata.org/wiki/Q18207010)
- **Identity — Wikidata Q254474:** the item describes the relation each thing bears to itself alone. This is not the same as DIO Referential Continuity across legitimate change. A tentative `skos:relatedMatch` candidate is recorded, not approved. [Wikidata item](https://www.wikidata.org/wiki/Q254474)
- **Trust — Wikidata Q659974:** the item frames trust as a feeling/certainty and classifies it in terms of emotion and belief. This is a poor fit for the DIO K6 dimension, which explicitly need not imply human psychology. This candidate has been rejected. [Wikidata item](https://www.wikidata.org/wiki/Q659974)

The Wikipedia evidence URLs and their roles are listed per concept in the JSON registry. This is an initial curated evidence pass, not a claim that all potentially relevant Wikipedia pages or language editions have been exhausted.

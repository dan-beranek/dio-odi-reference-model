# DIO/ODI External Concept Mappings

## Purpose
This registry records candidate and reviewed semantic mappings from the canonical DIO/ODI Reference Vocabulary to external structured knowledge bases. It does not redefine DIO/ODI concepts or alter the canonical vocabulary.

## Current state
- Registry version: 0.1.0
- State: initial inventory; audit incomplete
- Source vocabulary: `vocabulary/dio-odi-skos.ttl`
- Source blob at inventory time: `f7c33af7a9977b40c787daf5ab0328c1590b1ffe`
- Vocabulary version: 0.1.0
- Concepts inventoried: 39
- Candidate mappings seeded for review: 6
- Approved mappings: 0

The six initial candidates were suggested in a prior analysis. Their target URIs and semantic relations are unverified. They must not be consumed as approved mappings.

## Source systems
- **Wikidata:** map to a specific item URI (QID) only after checking the item's label, description, statements, and semantic scope.
- **DBpedia:** map to a specific resource URI only after confirming that the URI resolves and the resource's scope fits the DIO/ODI concept.
- **Wikipedia:** use as supporting evidence and contextual reading, not automatically as a third equivalent structured mapping layer.

## Allowed SKOS mapping properties
- `skos:closeMatch`
- `skos:broadMatch`
- `skos:narrowMatch`
- `skos:relatedMatch`

The direction matters. `dio:Concept skos:broadMatch external:Concept` says the external concept is broader than the DIO/ODI concept. `skos:narrowMatch` expresses the inverse direction.

Do not routinely use `skos:exactMatch` and do not use `owl:sameAs` for these concept mappings. Similar labels or topical adjacency are not sufficient evidence for any mapping relation.

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

## Audit workflow
1. Re-read the current canonical Turtle and verify its blob SHA before each material update.
2. Audit every concept, not only the initial six candidates.
3. Search Wikidata and DBpedia separately; record exact target identifiers and evidence consulted.
4. Check scope, hierarchy, and relation direction before approval.
5. Record rejected and no-match outcomes as well as approvals.
6. Validate the registry against the JSON Schema.
7. Generate a mapped Turtle distribution only after the audit has produced approved mappings.
8. Preserve the canonical vocabulary unchanged unless a separately justified vocabulary change is required.

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
| Referential Continuity | Wikidata Q141646085 — GFO Persistant | The item’s scope note explicitly addresses identity over time: entities may have different properties at different times and nevertheless be the same. This is a closer theoretical neighbor, though it comes from General Formal Ontology and is not identical to DIO’s operational referential criterion. | Retain as **candidate** `skos:relatedMatch`; this is a stronger theoretical candidate than identity-as-self-relation, but still needs author review. |
| Referential Continuity | DBpedia Identity (philosophy) | Philosophical identity is relevant background, but the proposed broader-than relation is not established and the scope differs from temporal continuity under change. | Do not approve as `broadMatch`; contextual evidence is safer than mapping. |
| Trust Dimension | Wikidata Q659974 — trust | The item describes reliance on another party's honesty and classifies trust under emotion/belief/psychological terminology. DIO's Trust dimension is explicitly context- and task-sensitive and need not imply human psychology. | **Reject** as a mapping candidate; use only as contrastive evidence if needed. |
| Trust Dimension | DBpedia Trust (social science) | Social-science trust is relevant to the ordinary meaning but risks importing interpersonal/anthropomorphic assumptions into the DIO dimension. Its proposed `broadMatch` direction is not established. | Do not approve. Prefer contextual/contrastive evidence over a SKOS mapping. |
| Semantic Robustness | Wikidata Q403605 — robustness | Wikidata defines robustness as the ability of an object, system, or property to resist perturbations. DIO Semantic Robustness specifically concerns identity reconstruction under perturbations of the representational environment, so the Wikidata concept plausibly has broader scope. | Retain as **candidate** `skos:broadMatch`; the direction is plausible, but author review is still needed before approval. |
| Reconstruction Dimension | Wikidata Q17012245 — entity linking | Wikidata defines entity linking as assigning a unique identity to entities mentioned in text. This is a bounded text-to-entity task within DIO reconstruction, which also covers distributed representations, temporal continuity, context, and multiple observer mechanisms. | Retain as **candidate** `skos:narrowMatch`; useful as a narrow technical subtask, not an equivalent to reconstruction as a whole. |
| Semantic Robustness | DBpedia Robustness (computer science) | A potentially relevant neighboring concept, but the resource has not been validated sufficiently here to determine its precise scope or whether it is broader than the DIO concept. | Keep **candidate** only; verify the DBpedia resource and compare definitions before deciding. |

## Verified source observations

- Wikidata Q1266546 identifies **record linkage** as matching records/entities across datasets and lists “entity resolution” among its aliases: https://www.wikidata.org/wiki/Q1266546
- Wikidata Q18207010 describes **false positives and false negatives** as test/reporting errors and relates them to Type I/II errors and binary classification: https://www.wikidata.org/wiki/Q18207010
- Wikidata Q254474 defines philosophical **identity** as the relation each thing bears to itself: https://www.wikidata.org/wiki/Q254474
- Wikidata Q141646085 describes GFO **Persistant** as a formal-ontology notion used to account for identity over time despite changes in properties: https://www.wikidata.org/wiki/Q141646085
- Wikidata Q659974 describes **trust** as reliance on another party's honesty and includes psychological/emotional classifications: https://www.wikidata.org/wiki/Q659974
- Wikidata Q403605 defines **robustness** as the ability of an object, system, or property to resist perturbations: https://www.wikidata.org/wiki/Q403605
- Wikidata Q17012245 defines **entity linking** as assigning a unique identity to entities mentioned in text: https://www.wikidata.org/wiki/Q17012245

## Outcome

No candidate is promoted to `approved` in this audit. There are now three comparatively defensible provisional candidates: `EntityResolutionAnomaly skos:relatedMatch Q1266546`, because record linkage is a directly evidenced neighboring technical process; `SemanticRobustness skos:broadMatch Q403605`, because general robustness plausibly has broader scope than robustness of identity reconstruction under representational perturbations; and `ReferentialContinuity skos:relatedMatch Q141646085`, because GFO Persistant explicitly addresses identity over time despite changing properties. All remain candidates until the vocabulary author confirms that the relations are useful for intended machine-readable interoperability.

The Merge Failure and Split Failure links to false positives/false negatives should not be treated as mappings: their commonality is generic error language, not a sufficiently specific conceptual relation. The trust and philosophical-identity candidates are better handled as contextual/contrastive evidence unless a more precisely scoped external concept is found.

DBpedia targets were not promoted: direct page retrieval was not reliable in this pass, and in any event a DBpedia URI derived from the same Wikipedia topic should not be counted as independent corroboration.


## Follow-up audit — Entity Substitution, Entity Omission, Temporal Misalignment, Semantic Fragmentation (2026-10-16)

### Entity Substitution
No new mapping candidate. Entity linking (Wikidata Q17012245) is a neighboring task that assigns mentions to entities, not the substitution failure itself. Wikidata's own conflation guidance describes one record/entity representing multiple distinct things; that is closer to Merge Failure than to Entity Substitution. Sources: https://www.wikidata.org/wiki/Q17012245 ; https://www.wikidata.org/wiki/Help:Conflation

### Entity Omission
No mapping candidate. Research on knowledge-graph inconsistencies describes missing nodes and missing statements as graph incompleteness, while the Wikipedia article on link analysis discusses missing data and links. These are useful contextual evidence but do not establish a stable external concept with the same scope as omission of an intended referent during identity reconstruction. Sources: https://academ.us/article/2607.25959/ ; https://en.wikipedia.org/wiki/Link_analysis

### Temporal Misalignment
No mapping candidate. Wikidata's data-synchronization concept describes a process for maintaining consistency across data stores, not the failure state of temporal misalignment. Dynamic time warping is a domain-specific sequence-alignment method that can address temporal misalignment, not an equivalent concept. Wikidata ontology modeling provides context for temporal extents and identity persistence. Sources: https://www.wikidata.org/wiki/Q1172333 ; https://en.wikipedia.org/wiki/Dynamic_time_warping ; https://www.wikidata.org/wiki/Wikidata:WikiProject_Ontology/Ontology_Course/Modeling_time

### Semantic Fragmentation
No mapping candidate. Wikidata Q1132459 describes fragmentation of memory/storage allocation, a lexical false friend rather than semantic fragmentation. Wikipedia's memory-fragmentation article offers a distant structural analogy involving loss of integration/coherence, but belongs to a psychological/clinical domain and must not be treated as a mapping. Sources: https://www.wikidata.org/wiki/Q1132459 ; https://en.wikipedia.org/wiki/Fragmentation_of_memory

### Decision
This pass adds contextual evidence, not SKOS mappings. That is intentional: the sources support neighboring tasks, failure contexts, or analogies, but not a sufficiently well-defined mapping relation. Candidate count remains unchanged; the four concepts remain under review pending author-level decision on whether contextual evidence alone is enough to mark each concept reviewed.


## Follow-up audit — Temporal Discontinuity, Semantic Vulnerability, Identity Collapse, Contextual Displacement, Semantic Coherence Failure, Reconstruction Capture (2026-10-16)

### Temporal Discontinuity
No mapping candidate. Wikidata ontology modeling discusses temporal extent, interval relations, and entities persisting through time; the Stanford Encyclopedia of Philosophy's identity-over-time entry gives theoretical context for persistence through change. Neither denotes the specific DIO failure mode. Sources: https://www.wikidata.org/wiki/Wikidata:WikiProject_Ontology/Ontology_Course/Modeling_time ; https://seop.illc.uva.nl/entries///identity-time/

### Semantic Vulnerability
No mapping candidate. Wikidata Q631425 defines computer vulnerability as a security weakness that can reduce information assurance. This is adjacent but domain-specific; it may import attacker/security assumptions absent from DIO's concept. Source: https://www.wikidata.org/wiki/Q631425

### Identity Collapse
No mapping candidate. Wikidata Q3354876 is a psychological identity-crisis concept, while Q844569 describes social identity as qualities and expressions characterizing people or groups. These are lexical/disciplinary false friends, not DIO's reconstruction failure mode. Sources: https://www.wikidata.org/wiki/Q3354876 ; https://www.wikidata.org/wiki/Q844569

### Contextual Displacement
No mapping candidate. Wikidata Q47555586 identifies research on context drift/shift in human memory. It is a distant analogy for context-dependent interpretation, not an external concept for DIO contextual displacement. Source: https://www.wikidata.org/wiki/Q47555586

### Semantic Coherence Failure
No mapping candidate. Linguistic coherence is relevant background for connected meaning in discourse, but it does not capture DIO's specific failure of identity reconstruction. Source: https://en.wikipedia.org/wiki/Coherence_(linguistics)

### Reconstruction Capture
No mapping candidate. Information retrieval is an upstream technical context for how observers access representations, not a stable concept equivalent to reconstruction capture. Source: https://en.wikipedia.org/wiki/Information_retrieval

### Decision
As in the prior pass, these links are recorded as contextual/contrastive evidence only. Lexical overlap and neighboring mechanisms do not justify a SKOS mapping relation.


## Follow-up audit — Observer, Observation Domain, Relationship, Identity-Preserving Constraint, Essential Vector, Contextual Adequacy Failure, DIO Intervention (2026-10-16)

### Observer
The Industrial Ontology Foundry defines an Observer as an agent with an observer role, and its ObserverRole definition explicitly includes people, groups, and engineered systems that perceive an entity and distinguish it from others. This is the strongest formal-ontology neighbor in this pass. However, DIO's Observer also includes the mechanism through which the observer processes representations; the IFO class does not explicitly capture that composite. Keep as contextual evidence; no mapping candidate yet. Sources: https://spec.industrialontologies.org/portal/release/202603/productservicesystem/Observer.html ; https://spec.industrialontologies.org/portal/release/202603/productservicesystem/ObserverRole.html

### Observation Domain
TERN/SOSA models observation with temporal, spatial, procedural, and feature-of-interest context. This provides useful modeling patterns, but DIO Observation Domain is a bounded set of situations against which an optimization is evaluated, not an observation event or sensor context. Wikidata's Observation item likewise describes an activity, not the domain boundary. Sources: https://linkeddata.tern.org.au/information-models/tern-ontology/conceptual-information-model ; https://www.wikidata.org/wiki/Q193181

### Relationship Dimension
PROV-O can represent provenance relations among entities, activities, and agents. These relations may help describe historical traces surrounding representations, but do not equate to DIO's persistent, historically sedimented observer–entity relationship. Source: https://www.w3.org/TR/prov-o/

### Identity-Preserving Constraint
GFO Persistant is a theoretical neighbor because it concerns identity over time despite changing properties; OWL-Time can represent temporal extents and relations. Neither denotes the DIO constraints whose preservation licenses legitimate variation while maintaining referential continuity. Sources: https://www.wikidata.org/wiki/Q141646085 ; https://www.w3.org/TR/owl-time/

### Essential Vector
No mapping candidate. Entity linking resolves mentions to entities but does not define a minimal core of identity-preserving constraints. SKOS itself is a vocabulary model, not a theory of identity essence. Sources: https://www.wikidata.org/wiki/Q17012245 ; https://www.w3.org/TR/skos-reference/

### Contextual Adequacy Failure
Pragmatics provides broad theoretical context for how context affects interpretation, while ontology alignment addresses correspondences between concepts. Neither is a specific external concept for inadequate identity reconstruction within a defined observation domain. Sources: https://en.wikipedia.org/wiki/Pragmatics ; https://www.wikidata.org/wiki/Q1224764

### DIO Intervention
PROV-O can describe activities and provenance, while ontology alignment is one possible technique for changing or reconciling representations. Neither is equivalent to the DIO concept of an intentional, systematic change to the distributed representational state or relations among representations. Sources: https://www.w3.org/TR/prov-o/ ; https://www.wikidata.org/wiki/Q1224764

### Decision
This pass adds contextual evidence but no SKOS mappings. The Industrial Ontology Foundry's Observer/ObserverRole deserves a focused author review later because it is a formally defined, machine-readable neighboring concept; even there, a mapping should not be added unless the scope and direction are defensible.


## Follow-up audit — Representation, Interpretation, Distributed State, Reconstruction Mechanism, DIO Problem, Semantic Coherence Failure (2026-10-16)

### Representation Dimension
PROV-O describes provenance among entities, activities, and agents; JSON-LD provides a linked-data expression mechanism. Both are useful infrastructure contexts, but neither is equivalent to the full DIO analytical dimension of representation. Sources: https://www.w3.org/TR/prov-o/ ; https://www.w3.org/TR/json-ld11/

### Interpretation Dimension
The semiotic interpretant is a useful theoretical neighbor for meaning generated through sign interpretation. Wikidata's observation concept describes information acquisition rather than interpretation. Neither captures the full DIO dimension across heterogeneous human and machine observers. Sources: https://en.wikipedia.org/wiki/Interpretant ; https://www.wikidata.org/wiki/Q193181

### Distributed Representational State
PROV-O can encode provenance and JSON-LD can express linked representations, but the DIO concept includes a wider observable state: content, attributes, metadata, identifiers, provenance, availability, and relations among representations. No mapping candidate. Sources: https://www.w3.org/TR/prov-o/ ; https://www.w3.org/TR/json-ld11/

### Reconstruction Mechanism
SOSA models sensors, observations, procedures, and features of interest; entity linking is a specific mention-to-entity task. These are concrete neighboring mechanisms, not a general equivalent for the range of mechanisms by which observers reconstruct digital identity. Sources: https://www.w3.org/TR/sosa/ ; https://www.wikidata.org/wiki/Q17012245

### DIO Problem
Ontology alignment can identify correspondences between vocabularies, while SHACL validates RDF graphs against declared constraints. These techniques can reveal specific mismatches or structural defects, but neither captures DIO Problem's broader evaluation of reconstruction, continuity, or robustness relative to a legitimate objective and observation domain. Sources: https://www.wikidata.org/wiki/Q1224764 ; https://www.w3.org/TR/shacl/

### Semantic Coherence Failure
SHACL graph conformance is not semantic identity coherence; linguistic coherence concerns connectedness of discourse rather than the specific failure of identity reconstruction. These sources are useful contrasts, not mapping targets. Sources: https://www.w3.org/TR/shacl/ ; https://en.wikipedia.org/wiki/Coherence_(linguistics)

### Decision
No mappings added in this pass. The external sources are useful as formal modeling infrastructure, theoretical neighbors, or contrastive examples, but do not justify SKOS relations at the current level of scope precision.

## Observer: human recipient vs. cross-system observer (2026-10-16)

The canonical DIO concept deliberately defines **Observer** as “a human or machine observer together with the mechanism through which it reads or processes representations.” It must remain broader than a human audience: the DIO observer can be a person, AI system, search engine, knowledge-graph-mediated process, or legacy technology, depending on the observation domain and the reconstruction mechanism.

Communication theory offers a useful adjacent vocabulary for the human-facing case:
- **Receiver** — Wikidata Q1339255 describes the receiving end of a communication channel in information theory. This is a process role, not a human-only class and not the DIO composite concept. [Wikidata](https://www.wikidata.org/wiki/Q1339255)
- **Target audience** — Wikidata Q2604680 defines the intended or ideal recipient of a message or artistic expression, usually a group of humans. Useful when intentional address matters; it excludes unintended observers and non-human systems. [Wikidata](https://www.wikidata.org/wiki/Q2604680)
- **Audience** — Wikidata Q211198 describes a group of people encountering a show or work. Useful for the public/reception side, but too group- and media-oriented to cover an individual observer or the DIO superordinate concept. [Wikidata](https://www.wikidata.org/wiki/Q211198)
- **SMCR receiver** — Berlo's source–message–channel–receiver model distinguishes source, message, channel, and receiver, with the receiver decoding a message. It is a strong theoretical neighbor for message reception, but not a direct DIO mapping. [Wikipedia](https://en.wikipedia.org/wiki/Source%E2%80%93message%E2%80%93channel%E2%80%93receiver_model_of_communication)
- **Audience reception** — reception theory emphasizes active interpretation and divergent readings. Relevant to human interpretation, but bounded by its media/audience frame. [Wikipedia](https://en.wikipedia.org/wiki/Audience_reception)
- **Lasswell's “to whom”** — identifies the recipient/audience dimension of communication, again as a communication-role framework rather than an equivalent to DIO Observer. [Wikipedia](https://en.wikipedia.org/wiki/Lasswell%27s_model_of_communication)

### Design implication

Do **not** map DIO Observer to audience, target audience, or receiver as if these were equivalent. The useful next question is whether the canonical vocabulary needs a distinct subordinate concept such as **Human Observer**, **Human Recipient**, or **Human Interpreter**. These names are not interchangeable:
- **Human Observer** is broad and fits a person observing/reconstructing an entity, whether or not a message was intentionally addressed to them.
- **Human Recipient** is best when the relevant role is receiving a message or representation.
- **Human Interpreter** foregrounds meaning-making and interpretation, but risks narrowing the concept to semiotic/interpretive activity.
- **Audience** implies a communicative or media setting and often a group; it is likely too narrow as the general human counterpart.

This would be a **vocabulary-design decision**, not an external mapping approval. If added, the new concept should be explicitly narrower than Observer in the DIO hierarchy and retain the general concept's human/machine/technology neutrality. No new canonical concept or SKOS mapping is created by this evidence pass.

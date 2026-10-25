# Application Mapping: DIO/ODI Commit-Boundary Contract × Policy-as-Code Authorization

**Status:** derived application mapping first included in archived Reference Model v0.4.0 and carried forward in v0.5.0; it remains outside the canonical vocabulary  
**Reference Model:** current archived release v0.5.0 — https://doi.org/10.5281/zenodo.23643845  
**Live Reference Vocabulary:** v0.2.0; this mapping does not modify its definitions or relations  
**Frontend:** https://vocab.danielberanek.cz/mappings/commit-boundary-policy/  
**JSON-LD:** https://vocab.danielberanek.cz/mappings/commit-boundary-policy-mapping.jsonld  
**Turtle RDF:** https://vocab.danielberanek.cz/mappings/commit-boundary-policy-mapping.ttl  
**License:** CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/

## Purpose

This mapping examines how the authorization obligations described in *Constraining the Commit Boundary: A DIO/ODI-Informed Authorization Guardrail for Agentic Entity Resolution* can be represented, evaluated, enforced, and audited in a Policy-as-Code architecture. Open Policy Agent (OPA/Rego) and Cedar are used as documented technical reference points, not as endorsed or validated implementations.

The mapping's central distinction is:

**Evidence usable for reasoning is not automatically evidence eligible to authorize a persistent identity mutation.**

A high-confidence identity hypothesis, a policy decision, and a committed graph change are different things. A policy engine can evaluate the request and conditions that an application provides; it does not thereby establish the truth of the identity hypothesis, authenticate every evidence source, discover all material conflicts, or make a later graph write atomic.

## Scope and analytical direction

The mapping proceeds from a DIO/ODI-informed commit-boundary obligation to the mechanisms and limits of a Policy-as-Code authorization architecture:

**Contract obligation → policy representation/evaluation → enforcement and residual integration requirement.**

It does not map DIO/ODI terms to supposed synonyms in OPA or Cedar. It does not claim that either policy engine implements the MVDIO Supervisor Layer, the complete commit-boundary contract, or the semantics of the DIO/ODI Reference Vocabulary out of the box.

The following labels qualify the mapping relations:

- **Relevant mechanism:** the external system documents a capability that can support part of an obligation.
- **Requires policy modeling:** the capability must be expressed in application-defined data, rules, or policy conventions.
- **Requires integration:** conformance depends on an application, evidence service, transaction layer, or protected write path outside the policy decision alone.
- **Not established by the decision:** the engine's authorization result does not itself prove the associated semantic or operational property.

These labels describe this mapping's analysis. They are not native OPA or Cedar result types.

## Mapping table

| DIO/ODI-informed obligation | Policy-as-Code correspondence | OPA / Rego | Cedar | Residual requirement and relation |
| --- | --- | --- | --- | --- |
| **1. Bind authorization to a specific proposed mutation.** | Represent the requested operation, target, actor or service, and permitted operational scope explicitly. | OPA accepts arbitrary structured input and evaluates it against Rego policies. | Cedar models an authorization request through principal, action, resource, and context (PARC). | **Relevant mechanism; requires policy modeling.** The application must define which identity-changing operations and target resources are protected. Neither input shape supplies DIO/ODI semantics by itself. |
| **2. Require support for each proposition that the mutation depends on.** | Carry the required claims and claim-specific evidence references into the decision process. | Rego can inspect structured evidence metadata and return a structured decision. | Claims and evidence metadata can be represented in entity attributes or request context where the application schema permits. | **Requires policy modeling and integration.** Neither engine automatically establishes the provenance, authenticity, scope, or relevance of supplied evidence. The agent must not be allowed to self-certify that its own evidence is authorized. |
| **3. Evaluate identity-preserving constraints over the proposed result.** | Express applicable constraints as predicates over the proposed operation, its claims, and the relevant candidate state. | Rego can evaluate predicates over supplied input and policy data. | Cedar conditions can evaluate attributes of the principal, resource, and request context. | **Requires policy modeling and integration.** The constraint set and candidate-state representation remain domain-configured. A policy decision cannot validate facts or graph state that were not reliably supplied to it. |
| **4. Preserve the difference between a violation and insufficient or unresolved evidence.** | Retain distinct states such as PASS, BREACH, and UNKNOWN_EVIDENCE rather than collapsing all outcomes into a confidence score. | OPA can return an application-defined structured result; the policy and its calling code must define the semantics of each state. | Cedar returns Allow or Deny with diagnostics, including policy evaluation errors. That interface is not the same as the DIO/ODI multi-state contract. | **Requires explicit modeling and an adapter/integration layer.** A policy denial is not necessarily evidence of a semantic breach; a missing or erroneous evaluation must not silently become authorization. |
| **5. Bind the decision to the relevant observation context and temporal validity.** | Include the observation time, evidence validity intervals, relevant context, and any domain-specific temporal constraints. | These values can be supplied in structured input and inspected in Rego. | Context and entity attributes can carry values used in policy conditions. | **Requires policy modeling.** Neither engine independently determines which temporal interpretation of an identity is correct. The upstream evidence process must provide meaningful time and context data. |
| **6. Ensure that the policy used for authorization is the policy applicable at commitment.** | Record and check the policy version or revision used for the decision. | OPA decision logs can record the bundle revision associated with an evaluation. Bundle distribution is eventually consistent by design. | The integrating application should record an identifier or version for the exact policy set used; this mapping does not assume a built-in commit-time policy-version lock. | **Requires integration.** The commit path must reject or re-evaluate a decision if the applicable policy version has changed under the declared contract. An audit record of an earlier revision is not a freshness guarantee. |
| **7. Ensure that the underlying graph state is still the state that was authorized.** | Bind the decision to a candidate graph snapshot or expected state version. | The application can pass a version as input, but OPA does not make the graph store's later transaction atomic. | A state version can be represented in request context or resource data, but Cedar does not lock the graph store at authorization time. | **Requires integration outside the policy engine.** Re-check the expected state at the protected write boundary, using a transaction or compare-and-swap/version check. |
| **8. Ensure that authorization actually controls the persistent write.** | Separate decision-making from enforcement and make the protected write conditional on a valid decision for the same operation. | OPA explicitly separates policy decision-making from policy enforcement; the caller or enforcement component must enforce the returned result. | Cedar's authorizer returns a decision to the calling application, which must enforce it. | **Requires integration.** Every effect-capable path to the protected graph must enforce the contract. A correct upstream decision is insufficient if an alternate write path can bypass it. |
| **9. Preserve an auditable link between evidence, policy decision, versions, and mutation.** | Record claim identifiers, evidence/provenance references, requested operation, relevant versions, decision, and commit outcome. | Decision logs can record the query input, result, decision ID, and bundle metadata; sensitive fields require deliberate masking or omission. | Authorization responses provide the decision and diagnostics, but application-level evidence and commit records must be joined by the integrating system. | **Relevant mechanism; requires integration.** Neither engine alone provides the complete end-to-end evidence-to-commit provenance record described by the mapping. |
| **10. Handle unknown, timeout, unavailable-engine, and evaluation-error states safely.** | Specify deferral or fail-closed behavior and prevent an absent decision from authorizing a write. | The calling system must distinguish a valid structured policy result from an undefined result, transport failure, or evaluation error. | Cedar exposes policy evaluation diagnostics; the application must define how errors affect the protected operation. | **Requires integration.** UNKNOWN, timeout, or unavailable authorization must not be interpreted as PASS. The protected write path needs a defined safe behavior for each non-success state. |
| **11. Avoid treating authorization as proof of identity truth.** | Interpret Allow/PASS only against the exact encoded policy and supplied data; keep semantic truth and authorization status distinct. | An OPA result states the outcome of the queried policy under its input and policy/data state. | Cedar's Allow means a permit policy matched without an applicable forbid decision under Cedar's algorithm. | **Not established by the decision.** Neither Allow nor PASS proves that the reconstructed identity is objectively correct. The strength of the conclusion is bounded by the evidence, model, policy, and assumptions supplied to the system. |

## Minimal request shape (illustrative)

A Policy-as-Code integration needs a stable contract for the inputs used in the authorization decision. A schematic request may carry:

    {
      "operation": {
        "kind": "identity_merge",
        "target": "candidate-graph-mutation",
        "scope": "declared-operational-scope"
      },
      "required_claims": [
        {
          "proposition": "same_legal_entity",
          "evidence_refs": ["evidence-record-1", "evidence-record-2"],
          "evidence_state": "application-defined-state"
        }
      ],
      "candidate_state": {
        "expected_graph_version": "version-id"
      },
      "authorization_context": {
        "observed_at": "timestamp",
        "policy_revision": "revision-id"
      }
    }

This is a conceptual interface example, not an OPA or Cedar native schema and not executable policy code. The fields and their meanings would need to be defined by the application. In particular, an agent-supplied string such as PASS or an evidence reference is not proof on its own: the authorization path must rely on trusted validation outputs, controlled provenance, and a binding to the candidate operation and state.

## Worked interpretation: a high-confidence merge proposal

Suppose an agent proposes merging two supplier records and assigns its identity hypothesis a confidence of 0.97. The score may help prioritize review or guide exploratory reasoning. It is not, by itself, authorization to alter the persistent graph.

A DIO/ODI-informed Policy-as-Code integration would instead ask whether the proposed operation is within scope; whether every required proposition has eligible, claim-specific support; whether material conflicts remain unresolved; whether the declared identity-preserving constraints pass; and whether the policy and graph versions remain valid at the protected commit boundary.

If a required claim lacks eligible support, the appropriate outcome may be deferral or UNKNOWN rather than a low-confidence estimate converted into a permit. If the graph version changes after authorization, the earlier decision must not automatically authorize the stale mutation. If all encoded conditions pass, the resulting Allow still means only that the configured authorization contract passed against the supplied inputs; it does not independently prove the real-world identity relation.

## What the mapping establishes—and what it does not

### It establishes

- A practical analytical bridge from the published DIO/ODI commit-boundary obligations to Policy-as-Code mechanisms.
- A separation between policy decision, enforcement, evidence validation, and atomic graph commitment.
- A set of explicit integration gaps that remain even when a policy engine is available.
- A basis for comparing implementations without conflating semantic authorization with ordinary access-control decisions.

### It does not establish

- That OPA, Cedar, or any other engine natively implements the MVDIO Supervisor Layer.
- That either engine validates the truth or provenance of evidence merely because it receives structured input.
- That a policy decision protects against stale state, concurrent mutation, or bypass unless the integration enforces those conditions.
- That DIO/ODI-informed policies outperform an equally informed generic policy design. This is an empirical question, not a result of the mapping.
- That the integration has been implemented, benchmarked, or independently evaluated.
- A new canonical DIO/ODI concept, failure mode, or hierarchy relation.

## Interpretation boundary

This is a **derived, non-normative application mapping**. It does not redefine the DIO/ODI Reference Vocabulary, OPA, Rego, or Cedar. OPA and Cedar are distinct systems with different request and decision models; the mapping identifies relevant capabilities and gaps rather than treating their constructs as interchangeable.

The mapping is about authorization of a proposed persistent identity mutation. It does not model the full hypothesis-conditioned evidence-acquisition loop, downstream mutation propagation, dependency-aware cascade mitigation, or post-commit identity recovery. Those are separate problems and are not implied to be solved by adding a policy engine.

## Source basis

### DIO/ODI source

Beránek, D. (2026). *Constraining the Commit Boundary: A DIO/ODI-Informed Authorization Guardrail for Agentic Entity Resolution*. Zenodo record 23580733.  
https://zenodo.org/records/23580733

The paper specifies the commit-boundary authorization obligations mapped here. This mapping is a derived application layer; it is not part of that paper's experimental validation and does not add performance results.

### External technical sources

- Open Policy Agent. *Open Policy Agent documentation* — policy evaluation over structured input and separation of decision-making from enforcement. https://www.openpolicyagent.org/docs
- Open Policy Agent. *Decision Logs* — decision inputs, outputs, decision identifiers, and bundle revision metadata. https://www.openpolicyagent.org/docs/management-decision-logs
- Open Policy Agent. *Bundles* — policy/data distribution and update behavior, including eventual consistency. https://www.openpolicyagent.org/docs/management-bundles
- Cedar Policy Language Reference Guide. *How Cedar authorization works* — request structure, Allow/Deny decisions, evaluation rules, and diagnostics. https://docs.cedarpolicy.com/auth/authorization.html
- Cedar Policy Language Reference Guide. *Basic policy construction in Cedar* — policy scope and conditions. https://docs.cedarpolicy.com/policies/syntax-policy.html

The external sources document the capabilities described. The DIO/ODI obligations-to-mechanism relations and residual requirements are the analytical interpretation made in this mapping; they are not claims made by the OPA or Cedar documentation.

## Source and machine-readable metadata

- [Markdown source](https://vocab.danielberanek.cz/mappings/commit-boundary-policy-mapping.md)
- [JSON-LD representation](https://vocab.danielberanek.cz/mappings/commit-boundary-policy-mapping.jsonld)
- [Turtle RDF — qualified mapping assertions](https://vocab.danielberanek.cz/mappings/commit-boundary-policy-mapping.ttl)
- [Application Mappings index](https://vocab.danielberanek.cz/mappings/)
- [Reference Model source repository](https://github.com/dan-beranek/dio-odi-reference-model)

Author: **Daniel Beránek** · ORCID 0009-0004-0050-0264 · License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

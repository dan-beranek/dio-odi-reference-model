import unittest
from unittest.mock import patch

from scripts import prepare_scf_discovery_candidates as discovery


class DiscoveryIntakeTests(unittest.TestCase):
    def setUp(self):
        self.profile = {
            "profile_version": "0.1.0",
            "identity_phrases": [
                "Digital Identity Optimization",
                "Ontology of Digital Identity",
                "DIO/ODI",
            ],
            "concept_anchors": [
                "K6 Semantic Connectome",
                "Reconstruction Failure Modes",
            ],
            "work_title_query_limit": 2,
            "max_results_per_query": 5,
        }
        self.works = {
            "author": {
                "name": "Daniel Beránek",
                "orcid": "0009-0004-0050-0264",
                "email": "public@example.invalid",
            },
            "works": [
                {
                    "id": "paper-a",
                    "title": "Digital Identity Optimization: A Test Framework",
                    "type": "publication-preprint",
                    "version_doi": "10.5281/zenodo.1234567",
                    "note": "Related background: 10.9999/external-reference.",
                },
                {
                    "id": "paper-b",
                    "title": "A Separate Identity Paper",
                    "type": "publication-preprint",
                },
            ],
        }
        self.keywords = {
            "chunks": {
                "C0": {
                    "terms": [
                        "Digital Identity Optimization",
                        "Ontology of Digital Identity",
                        "DIO",
                        "ODI",
                    ]
                },
                "C4": {"terms": ["K6 Semantic Connectome"]},
                "C5": {"terms": ["Reconstruction Failure Modes"]},
            }
        }
        self.context = {
            "title_to_work": {
                discovery.normalise_text(self.works["works"][0]["title"]): "paper-a"
            },
            "doi_to_work": {"10.5281/zenodo.1234567": "paper-a"},
            "known_urls": set(),
            "known_ids": {"10.5281/zenodo.1234567"},
            "arxiv_to_work": {"2610.37407": "paper-a"},
            "evidence_index": {},
            "orcid_values": ["0009-0004-0050-0264"],
            "author_names": ["Daniel Beránek"],
            "author_name": "Daniel Beránek",
            "author_orcid": "0009-0004-0050-0264",
            "author_handles": {"daniel-beranek", "danielberanek", "dan-beranek"},
            "own_domains": {"danielberanek.cz"},
            "owned_url_prefixes": {"https://github.com/dan-beranek"},
            "work_id_to_title": {"paper-a": "Digital Identity Optimization: A Test Framework"},
        }

    def test_known_context_maps_only_structured_distribution_identifiers(self):
        works = {
            "works": [
                {
                    "id": "paper-a",
                    "title": "Paper A",
                    "version_doi": "10.5281/zenodo.1111111",
                    "note": "Cites 10.9999/external-reference.",
                }
            ],
            "hub": "https://danielberanek.cz/manifest-dio/",
        }
        distributions = {
            "works": [
                {
                    "work": "paper-a",
                    "representations": [
                        {
                            "identifier_type": "doi",
                            "identifier": "10.5281/zenodo.7654321",
                            "evidence": "Relation page cites 10.9998/other-source.",
                        },
                        {
                            "identifier_type": "url",
                            "identifier": "https://example.org/paper-a-mirror",
                        },
                    ]
                }
            ]
        }
        reception = {
            "target_works": [
                {
                    "id": "paper-a",
                    "url": "https://doi.org/10.5281/zenodo.1111111",
                }
            ],
            "entries": [
                {
                    "id": "external-commentary",
                    "url": "https://example.org/commentary",
                    "cited_sources": [
                        {
                            "title": "Paper A",
                            "url": "https://doi.org/10.5281/zenodo.1111111",
                        },
                        {
                            "title": "Unrelated source",
                            "url": "https://doi.org/10.9997/cited-only",
                        },
                    ],
                }
            ],
        }
        mappings = {
            "mappings": [
                {
                    "title": "Mapping A",
                    "archived_release_doi": "10.5281/zenodo.2222222",
                    "external_source_doi": "10.1016/j.external.2026.123456",
                    "note": "Mentions 10.9996/narrative-only.",
                }
            ]
        }
        context = discovery.build_known_context(
            works, distributions, reception, mappings, {"events": []}
        )
        self.assertEqual(
            context["doi_to_work"]["10.5281/zenodo.7654321"], "paper-a"
        )
        self.assertIn("10.5281/zenodo.7654321", context["known_ids"])
        self.assertIn("10.5281/zenodo.1111111", context["known_ids"])
        self.assertIn("10.5281/zenodo.2222222", context["known_ids"])
        self.assertNotIn("10.9999/external-reference", context["known_ids"])
        self.assertNotIn("10.9998/other-source", context["known_ids"])
        self.assertNotIn("10.9996/narrative-only", context["known_ids"])
        self.assertNotIn("10.1016/j.external.2026.123456", context["known_ids"])
        self.assertIn(
            "https://example.org/commentary", context["known_urls"]
        )
        self.assertIn(
            "https://example.org/paper-a-mirror", context["known_urls"]
        )
        self.assertNotIn(
            "https://doi.org/10.9997/cited-only", context["known_urls"]
        )

    def test_known_zenodo_record_url_is_already_registered(self):
        works = {
            "works": [
                {
                    "id": "reference-model",
                    "title": "DIO/ODI Reference Model",
                    "version_doi": "10.5281/zenodo.24085589",
                    "versions": [
                        {"version": "0.8.0", "doi": "10.5281/zenodo.24056601"},
                    ],
                }
            ]
        }
        context = discovery.build_known_context(
            works, {}, {}, {}, {"events": []}
        )
        self.assertIn(
            "https://zenodo.org/records/24085589", context["known_urls"]
        )
        self.assertIn(
            "https://zenodo.org/records/24056601", context["known_urls"]
        )
        result = discovery.resolve_result(
            {
                "title": "DIO/ODI Reference Model",
                "url": "https://zenodo.org/records/24085589",
                "content": "Digital Identity Optimization and Ontology of Digital Identity.",
            },
            provider="Tavily Search",
            query={
                "id": "identity-3",
                "query": '"DIO/ODI"',
                "group": "identity",
            },
            context={
                **context,
                "orcid_values": [],
                "author_names": [],
            },
            identity_phrases=self.profile["identity_phrases"],
            concept_anchors=self.profile["concept_anchors"],
        )
        self.assertEqual(result["reference_status"], "already-registered")

    def test_platform_landing_urls_infer_their_own_persistent_identifiers(self):
        cases = [
            ("https://zenodo.org/records/24085589", "10.5281/zenodo.24085589", None),
            ("https://figshare.com/articles/preprint/a_paper/34751127", "10.6084/m9.figshare.34751127", None),
            ("https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7659038", "10.2139/ssrn.7659038", None),
            ("https://papers.ssrn.com/sol3/Delivery.cfm/7582778.pdf?abstractid=7582778&mirid=1", "10.2139/ssrn.7582778", None),
            ("https://arxiv.org/html/2610.37407v2", "10.48550/arxiv.2610.37407", "2610.37407"),
            ("https://arxiv.org/audio/2610.37407", "10.48550/arxiv.2610.37407", "2610.37407"),
        ]
        for url, expected_doi, expected_arxiv in cases:
            with self.subTest(url=url):
                dois, arxiv_ids = discovery.identifiers_from_url(url)
                self.assertEqual(dois, [expected_doi])
                self.assertEqual(arxiv_ids, [expected_arxiv] if expected_arxiv else [])

    def test_ssrn_doi_and_abstract_page_deduplicate(self):
        shared = {
            "title": "Digital Identity Optimization: A Test Framework",
            "content": "Digital Identity Optimization and DIO/ODI.",
        }
        from_landing = discovery.resolve_result(
            dict(shared, url="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7654321"),
            provider="Tavily Search",
            query={"id": "identity-1", "query": '"Digital Identity Optimization"', "group": "identity"},
            context=self.context,
            identity_phrases=self.profile["identity_phrases"],
            concept_anchors=self.profile["concept_anchors"],
        )
        from_doi = discovery.resolve_result(
            dict(shared, url="https://doi.org/10.2139/ssrn.7654321", doi="10.2139/ssrn.7654321"),
            provider="Crossref",
            query={"id": "identity-1", "query": '"Digital Identity Optimization"', "group": "identity"},
            context=self.context,
            identity_phrases=self.profile["identity_phrases"],
            concept_anchors=self.profile["concept_anchors"],
        )
        self.assertEqual(discovery.candidate_key(from_landing), discovery.candidate_key(from_doi))
        self.assertEqual(discovery.candidate_key(from_landing), "doi:10.2139/ssrn.7654321")

    def test_near_identical_title_links_to_canonical_work(self):
        context = dict(self.context)
        context["title_to_work"] = {
            "from entity resolution anomalies to reconstruction failure modes a taxonomic note following minimum viable dio": "taxonomic-note"
        }
        result = discovery.resolve_result(
            {
                "title": "From Entity Resolution Anomalies to Reconstruction Failure Modes: A Taxonomic Note Following Minimum Viable Digital Identity Optimization (DIO)",
                "url": "https://doi.org/10.2139/ssrn.7590979",
                "doi": "10.2139/ssrn.7590979",
                "description": "Authors: Daniel Beránek",
            },
            provider="OpenAlex",
            query={"id": "identity-3", "query": '"DIO/ODI"', "group": "identity"},
            context=context,
            identity_phrases=self.profile["identity_phrases"],
            concept_anchors=self.profile["concept_anchors"],
        )
        self.assertIn("taxonomic-note", result["related_work_ids"])
        self.assertIn("similar-known-work-title", result["matched_signals"])
        self.assertEqual(result["authorship_status"], "author-listed")

    def test_structured_author_list_classifies_own_research_output(self):
        result = discovery.resolve_result(
            {
                "title": "Digital Identity Optimization: A Test Framework",
                "url": "https://doi.org/10.9999/new-output",
                "doi": "10.9999/new-output",
                "description": "Authors: Daniel Beránek",
            },
            provider="OpenAlex",
            query={"id": "work-title-1", "query": '"Digital Identity Optimization"', "group": "known-work-title"},
            context=self.context,
            identity_phrases=self.profile["identity_phrases"],
            concept_anchors=self.profile["concept_anchors"],
        )
        candidate = discovery.merge_observations([result])[0]
        classification = discovery.classify_candidate(candidate, self.context)
        self.assertEqual(candidate["authorship_status"], "author-listed")
        self.assertEqual(classification["category"], "author-corpus")
        self.assertEqual(classification["confidence"], "high")

    def test_other_authors_and_known_work_reference_classifies_as_external_reception(self):
        result = discovery.resolve_result(
            {
                "title": "Independent analysis of DIO/ODI",
                "url": "https://example.org/independent-analysis",
                "content": "Authors: External Researcher; cites 10.5281/zenodo.1234567.",
            },
            provider="OpenAlex",
            query={"id": "identity-3", "query": '"DIO/ODI"', "group": "identity"},
            context=self.context,
            identity_phrases=self.profile["identity_phrases"],
            concept_anchors=self.profile["concept_anchors"],
        )
        candidate = discovery.merge_observations([result])[0]
        classification = discovery.classify_candidate(candidate, self.context)
        self.assertEqual(candidate["authorship_status"], "other-authors-listed")
        self.assertEqual(classification["category"], "independent-external-reception")
        self.assertEqual(classification["confidence"], "high")

    def test_author_profiles_and_platform_handles_are_not_external_reception(self):
        context = dict(self.context)
        profile = discovery.detect_source_ownership(
            "https://bioregistry.io/contributor/0009-0004-0050-0264", context
        )
        github_pages = discovery.detect_source_ownership(
            "https://dan-beranek.github.io/dio-odi-autorsky-koncept/en", context
        )
        github = discovery.detect_source_ownership(
            "https://github.com/dan-beranek", context
        )
        huggingface = discovery.detect_source_ownership(
            "https://huggingface.co/datasets/danielberanek/manifest", context
        )
        self.assertEqual(profile["subclass"], "author-profile")
        self.assertEqual(github["subclass"], "author-profile-or-repository")
        self.assertEqual(github_pages["subclass"], "author-maintained-web-presence")
        self.assertEqual(huggingface["subclass"], "author-associated-distribution")
        researchgate = discovery.detect_source_ownership(
            "https://researchgate.net/profile/Daniel-Beranek", context
        )
        linkedin = discovery.detect_source_ownership(
            "https://linkedin.com/posts/seo-specialista-copywriter-daniel-beranek_digitalidentityoptimization-activity-7516523106669355008-tTtE",
            context,
        )
        self.assertEqual(researchgate["subclass"], "author-profile")
        self.assertEqual(linkedin["subclass"], "author-associated-social-content")

    def test_external_registry_record_is_classified_as_a_review_lead(self):
        candidate = {
            "source_url": "https://registry.example.org/entries/dio-odi",
            "title": "DIO/ODI registry entry",
            "snippet": "A controlled vocabulary record.",
            "authorship_status": "not-provided",
            "doi_values": [],
            "primary_arxiv_ids": [],
            "related_work_ids": [],
            "matched_signals": ["distinctive-identity-phrase"],
        }
        classification = discovery.classify_candidate(candidate, self.context)
        self.assertEqual(classification["category"], "external-registry-or-application")
        self.assertEqual(classification["subcategory"], "registry-record-lead")

    def test_work_clusters_keep_distinct_platform_identifiers(self):
        candidates = [
            {"candidate_id": "a", "related_work_ids": ["paper-a"], "doi_values": ["10.2139/ssrn.1"], "primary_arxiv_ids": []},
            {"candidate_id": "b", "related_work_ids": ["paper-a"], "doi_values": ["10.6084/m9.figshare.1"], "primary_arxiv_ids": []},
        ]
        groups = discovery.build_work_groups(candidates, self.context)
        self.assertEqual(groups[0]["candidate_count"], 2)
        self.assertEqual(
            groups[0]["identifiers"],
            ["10.2139/ssrn.1", "10.6084/m9.figshare.1"],
        )

    def test_work_notes_do_not_become_canonical_doi_identifiers(self):
        work = {
            "id": "paper-a",
            "title": "Paper A",
            "note": "Bibliographic reference: 10.9999/external-reference",
        }
        self.assertEqual(discovery.work_doi_identifiers(work), [])

    def test_normalise_url_removes_tracking_and_fragment(self):
        self.assertEqual(
            discovery.normalise_url(
                "HTTPS://WWW.Example.com/Article/?utm_source=x&v=2#section"
            ),
            "https://example.com/Article?v=2",
        )

    def test_query_profile_has_no_platform_allowlist(self):
        queries = discovery.build_search_queries(self.profile, self.works)
        self.assertEqual(queries[0]["query"], '"Digital Identity Optimization"')
        self.assertTrue(any(item["id"] == "author-orcid" for item in queries))
        self.assertTrue(any(item["id"] == "work-doi-1" for item in queries))
        self.assertFalse(any("10.9999/external-reference" in item["query"] for item in queries))
        self.assertEqual(
            [item["group"] for item in queries].count("known-work-title"), 2
        )
        self.profile["relationship_queries"] = [
            {"id": "external-registry", "query": '"DIO/ODI" registry vocabulary terminology'},
            {"id": "external-reception", "query": '"DIO/ODI" citation independent review'},
        ]
        expanded = discovery.build_search_queries(self.profile, self.works)
        self.assertTrue(any(item["id"] == "external-registry" and item["group"] == "external-relationship" for item in expanded))
        self.assertTrue(any(item["id"] == "external-reception" and item["group"] == "external-relationship" for item in expanded))


    def test_author_identifier_without_identity_or_work_signal_is_not_enough(self):
        result = discovery.resolve_result(
            {
                "title": "Daniel Beranek profile",
                "url": "https://example.org/profile",
                "content": "ORCID 0009-0004-0050-0264",
            },
            provider="Tavily Search",
            query={
                "id": "author-orcid",
                "query": '"0009-0004-0050-0264"',
                "group": "author-identifier",
            },
            context=self.context,
            identity_phrases=self.profile["identity_phrases"],
            concept_anchors=self.profile["concept_anchors"],
        )
        self.assertIsNone(result)

    def test_ambiguous_core_phrase_without_identity_context_is_filtered(self):
        result = discovery.resolve_result(
            {
                "title": "Technology Management for Digital Identity Optimization",
                "url": "https://example.org/college-professors",
                "content": "Digital identity optimisation for college professors.",
            },
            provider="OpenAlex",
            query={
                "id": "identity-1",
                "query": '"Digital Identity Optimization"',
                "group": "identity",
            },
            context=self.context,
            identity_phrases=self.profile["identity_phrases"],
            concept_anchors=self.profile["concept_anchors"],
        )
        self.assertIsNone(result)

    def test_core_phrase_with_author_identity_is_a_candidate(self):
        result = discovery.resolve_result(
            {
                "title": "Notes on Digital Identity Optimization",
                "url": "https://example.org/author-note",
                "content": "Daniel Beránek discusses Digital Identity Optimization.",
            },
            provider="Tavily Search",
            query={
                "id": "author-identity",
                "query": '"Daniel Beránek" "Digital Identity Optimization"',
                "group": "author-identity",
            },
            context=self.context,
            identity_phrases=self.profile["identity_phrases"],
            concept_anchors=self.profile["concept_anchors"],
        )
        self.assertIsNotNone(result)
        self.assertIn("author-linked-identity", result["matched_signals"])

    def test_concept_anchor_requires_identity_context(self):
        result = discovery.resolve_result(
            {
                "title": "K6 Semantic Connectome overview",
                "url": "https://example.org/k6",
                "content": "A description of the K6 Semantic Connectome.",
            },
            provider="Tavily Search",
            query={
                "id": "concept-1",
                "query": '"K6 Semantic Connectome"',
                "group": "concept-anchor",
            },
            context=self.context,
            identity_phrases=self.profile["identity_phrases"],
            concept_anchors=self.profile["concept_anchors"],
        )
        self.assertIsNone(result)

    def test_concept_anchor_with_core_identity_is_a_candidate(self):
        result = discovery.resolve_result(
            {
                "title": "DIO/ODI and the K6 Semantic Connectome",
                "url": "https://example.org/k6-dio",
                "content": "Digital Identity Optimization and the K6 Semantic Connectome.",
            },
            provider="Tavily Search",
            query={
                "id": "concept-1",
                "query": '"K6 Semantic Connectome"',
                "group": "concept-anchor",
            },
            context=self.context,
            identity_phrases=self.profile["identity_phrases"],
            concept_anchors=self.profile["concept_anchors"],
        )
        self.assertIsNotNone(result)
        self.assertIn("identity-linked-concept", result["matched_signals"])

    def test_exact_work_doi_maps_to_registered_record(self):
        result = discovery.resolve_result(
            {
                "title": "Digital Identity Optimization: A Test Framework",
                "url": "https://doi.org/10.5281/zenodo.1234567",
                "doi": "10.5281/zenodo.1234567",
                "publication_date": "2026-11-20",
            },
            provider="OpenAlex",
            query={
                "id": "work-title-1",
                "query": '"Digital Identity Optimization: A Test Framework"',
                "group": "known-work-title",
            },
            context=self.context,
            identity_phrases=self.profile["identity_phrases"],
            concept_anchors=self.profile["concept_anchors"],
        )
        self.assertEqual(result["reference_status"], "already-registered")
        self.assertEqual(result["related_work_ids"], ["paper-a"])

    def test_cited_doi_links_candidate_without_becoming_its_identity(self):
        result = discovery.resolve_result(
            {
                "title": "An independent analysis of a related method",
                "url": "https://example.org/independent-analysis",
                "content": (
                    "This analysis discusses DIO/ODI and cites "
                    "10.5281/zenodo.1234567."
                ),
            },
            provider="Tavily Search",
            query={
                "id": "identity-1",
                "query": '"Digital Identity Optimization"',
                "group": "identity",
            },
            context=self.context,
            identity_phrases=self.profile["identity_phrases"],
            concept_anchors=self.profile["concept_anchors"],
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["doi_values"], [])
        self.assertEqual(result["referenced_doi_values"], ["10.5281/zenodo.1234567"])
        self.assertEqual(result["related_work_ids"], ["paper-a"])
        self.assertIn("known-doi-reference", result["matched_signals"])
        self.assertEqual(result["reference_status"], "review-required")
        self.assertEqual(
            discovery.candidate_key(result),
            "url:https://example.org/independent-analysis",
        )

    def test_known_arxiv_reference_links_to_registered_work(self):
        result = discovery.resolve_result(
            {
                "title": "Independent commentary on an authorization design",
                "url": "https://example.org/commentary",
                "content": "See arXiv:2610.37407v2 for the related work.",
            },
            provider="Tavily Search",
            query={
                "id": "identity-1",
                "query": '"Digital Identity Optimization"',
                "group": "identity",
            },
            context=self.context,
            identity_phrases=self.profile["identity_phrases"],
            concept_anchors=self.profile["concept_anchors"],
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["doi_values"], [])
        self.assertEqual(result["referenced_arxiv_ids"], ["2610.37407"])
        self.assertEqual(result["related_work_ids"], ["paper-a"])
        self.assertIn("known-arxiv-reference", result["matched_signals"])

    def test_exact_existing_evidence_maps_to_event_id(self):
        context = dict(self.context)
        context["evidence_index"] = {
            "https://doi.org/10.5281/zenodo.1234567": ["SCF-2026-001"]
        }
        result = discovery.resolve_result(
            {
                "title": "Digital Identity Optimization: A Test Framework",
                "url": "https://doi.org/10.5281/zenodo.1234567",
                "doi": "10.5281/zenodo.1234567",
            },
            provider="Crossref",
            query={
                "id": "identity-1",
                "query": '"Digital Identity Optimization"',
                "group": "identity",
            },
            context=context,
            identity_phrases=self.profile["identity_phrases"],
            concept_anchors=self.profile["concept_anchors"],
        )
        self.assertEqual(result["reference_status"], "already-cited")
        self.assertEqual(result["existing_event_ids"], ["SCF-2026-001"])

    def test_same_doi_from_multiple_providers_is_one_candidate(self):
        base = {
            "url": "https://doi.org/10.5281/zenodo.7654321",
            "doi_values": ["10.5281/zenodo.7654321"],
            "title": "Digital Identity Optimization external analysis",
            "published_date": "2026-11-20",
            "snippet": "Digital Identity Optimization and DIO/ODI.",
            "provider_score": 0.8,
            "matched_signals": ["core-identity-phrase"],
            "match_class": "core-identity-phrase",
            "relevance_score": 90,
            "related_work_ids": [],
            "reference_status": "review-required",
            "existing_event_ids": [],
            "evidence_urls": ["https://doi.org/10.5281/zenodo.7654321"],
        }
        observations = [
            dict(base, provider="OpenAlex", query_id="identity-1",
                 query='"Digital Identity Optimization"', query_group="identity"),
            dict(base, provider="Crossref", query_id="identity-1",
                 query='"Digital Identity Optimization"', query_group="identity"),
        ]
        candidates = discovery.merge_observations(observations)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(set(candidates[0]["observed_by"]), {"OpenAlex", "Crossref"})

    def test_tavily_failure_does_not_claim_general_web_coverage(self):
        with patch.object(
            discovery, "search_tavily",
            return_value=([], {
                "provider": "Tavily Search", "enabled": True,
                "queries_attempted": 3, "requests_succeeded": 2,
                "raw_results": 0, "errors": ["identity-3: timeout"],
                "complete": False,
            }),
        ), patch.object(
            discovery, "search_openalex",
            return_value=([], {
                "provider": "OpenAlex", "enabled": True, "queries_attempted": 1,
                "raw_results": 0, "errors": [], "complete": True,
            }),
        ), patch.object(
            discovery, "search_crossref",
            return_value=([], {
                "provider": "Crossref", "enabled": True, "queries_attempted": 1,
                "raw_results": 0, "errors": [], "complete": True,
            }),
        ):
            report = discovery.build_report(
                self.profile, self.works, self.keywords, {}, {}, {}, {"events": []},
                tavily_api_key="configured-test-key",
            )
        self.assertFalse(report["scan_complete"])
        self.assertTrue(report["coverage"]["general_web_search_configured"])
        self.assertFalse(report["coverage"]["general_web_search_enabled"])
        self.assertEqual(report["coverage"]["coverage_level"], "scholarly-only")
        self.assertIn("did not complete all queries", report["coverage"]["limitation"])

    def test_openalex_failure_does_not_fail_complete_tavily_scan(self):
        observation = (
            {
                "title": "An independently indexed DIO/ODI note",
                "url": "https://example.org/dio-odi-note",
                "content": "Digital Identity Optimization and Ontology of Digital Identity.",
                "published_date": "2026-11-22",
                "score": 0.9,
            },
            {
                "id": "identity-1",
                "query": '"Digital Identity Optimization"',
                "group": "identity",
            },
        )
        with patch.object(
            discovery, "search_tavily",
            return_value=([observation], {
                "provider": "Tavily Search", "enabled": True,
                "queries_attempted": 24, "requests_succeeded": 24,
                "raw_results": 1, "errors": [], "complete": True,
            }),
        ), patch.object(
            discovery, "search_openalex",
            return_value=([], {
                "provider": "OpenAlex", "enabled": True, "queries_attempted": 13,
                "raw_results": 0, "errors": ["HTTP 429"], "complete": False,
            }),
        ), patch.object(
            discovery, "search_crossref",
            return_value=([], {
                "provider": "Crossref", "enabled": True, "queries_attempted": 13,
                "raw_results": 0, "errors": [], "complete": True,
            }),
        ):
            report = discovery.build_report(
                self.profile, self.works, self.keywords, {}, {}, {}, {"events": []},
                tavily_api_key="configured-test-key",
            )
        self.assertTrue(report["scan_complete"])
        self.assertEqual(report["scan_status"], "complete-with-provider-gaps")
        self.assertTrue(report["coverage"]["general_web_search_enabled"])
        self.assertTrue(report["coverage"]["scholarly_indexes_complete"])
        self.assertEqual(report["coverage"]["coverage_level"], "web-and-scholarly")
        self.assertEqual(report["errors"][0]["source"], "OpenAlex")
        self.assertIn("OpenAlex", report["coverage"]["limitation"])

    def test_build_report_marks_unconfigured_general_search_as_limited(self):
        observation = (
            {
                "title": "Digital Identity Optimization external analysis",
                "url": "https://example.org/dio-analysis",
                "content": "Daniel Beránek discusses Digital Identity Optimization in a new paper.",
                "published_date": "2026-11-22",
                "score": 0.91,
            },
            {
                "id": "identity-1",
                "query": '"Digital Identity Optimization"',
                "group": "identity",
            },
        )
        with patch.object(
            discovery, "search_openalex",
            return_value=([observation], {
                "provider": "OpenAlex", "enabled": True, "queries_attempted": 1,
                "raw_results": 1, "errors": [], "complete": True,
            }),
        ), patch.object(
            discovery, "search_crossref",
            return_value=([], {
                "provider": "Crossref", "enabled": True, "queries_attempted": 1,
                "raw_results": 0, "errors": [], "complete": True,
            }),
        ):
            report = discovery.build_report(
                self.profile, self.works, self.keywords, {}, {}, {}, {"events": []},
                now=__import__("datetime").datetime(
                    2026, 11, 23, tzinfo=__import__("datetime").timezone.utc
                ),
            )
        self.assertTrue(report["scan_complete"])
        self.assertEqual(report["coverage"]["coverage_level"], "scholarly-only")
        self.assertEqual(report["stats"]["unique_candidates"], 1)
        self.assertIn("not a broad web scan", report["coverage"]["limitation"])


if __name__ == "__main__":
    unittest.main()

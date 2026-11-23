import unittest

from scripts.prepare_scf_review_candidates import compare_records, extract_records


class ScfReviewCandidateTests(unittest.TestCase):
    def test_works_registry_records_are_keyed_by_work_id(self):
        document = {
            "registry_version": "1.0",
            "works": [
                {"id": "paper-a", "title": "Paper A", "publication_date": "2026-01-01"}
            ],
        }
        records = extract_records("metadata/works.json", document)
        self.assertEqual(records["paper-a"]["title"], "Paper A")
        self.assertIn("__registry_metadata__", records)

    def test_distribution_representations_are_flattened(self):
        document = {
            "registry_version": "1.0",
            "works": [
                {
                    "work": "paper-a",
                    "audit_status": "reviewed",
                    "representations": [
                        {"id": "distribution:paper-a:hashnode", "platform": "Hashnode"}
                    ],
                }
            ],
        }
        records = extract_records("metadata/distributions.json", document)
        self.assertIn("work:paper-a", records)
        self.assertEqual(
            records["distribution:paper-a:hashnode"]["platform"], "Hashnode"
        )

    def test_external_reception_entries_are_keyed_by_id(self):
        document = {"entries": [{"id": "registry-entry", "title": "Entry"}]}
        records = extract_records("metadata/external-reception.json", document)
        self.assertEqual(records["registry-entry"]["title"], "Entry")

    def test_application_mapping_uses_frontend_identity(self):
        document = {
            "mappings": [
                {"frontend": "https://example.test/mapping/", "title": "Mapping"}
            ]
        }
        records = extract_records("metadata/application-mappings.json", document)
        self.assertEqual(
            records["https://example.test/mapping/"]["title"], "Mapping"
        )

    def test_discovery_entries_use_urn_identifier(self):
        document = {
            "source_version": "0.1.0",
            "entries": [
                {"identifier": "urn:example:feed", "displayName": "Feed"}
            ],
        }
        records = extract_records("discovery/catalog-source.json", document)
        self.assertEqual(records["urn:example:feed"]["displayName"], "Feed")

    def test_added_and_modified_records_are_review_only(self):
        before = {"paper-a": {"id": "paper-a", "title": "Old"}}
        after = {
            "paper-a": {"id": "paper-a", "title": "New"},
            "paper-b": {"id": "paper-b", "title": "Added"},
        }
        candidates = compare_records("metadata/works.json", before, after)
        self.assertEqual(
            [item["change_kind"] for item in candidates],
            ["modified", "added"],
        )
        self.assertTrue(
            all(item["before"] is not None or item["after"] is not None
                for item in candidates)
        )
        self.assertNotIn("event_class", candidates[0])
        self.assertNotIn("date_basis", candidates[0])

    def test_removed_record_is_detected(self):
        candidates = compare_records(
            "metadata/works.json",
            {"paper-a": {"id": "paper-a", "title": "Paper A"}},
            {},
        )
        self.assertEqual(candidates[0]["change_kind"], "removed")
        self.assertIsNone(candidates[0]["after"])

    def test_no_candidate_for_unchanged_record(self):
        record = {"id": "paper-a", "title": "Paper A"}
        self.assertEqual(
            compare_records(
                "metadata/works.json", {"paper-a": record}, {"paper-a": record}
            ),
            [],
        )

    def test_registry_metadata_changes_are_visible(self):
        before = extract_records(
            "metadata/works.json", {"registry_version": "1.0", "works": []}
        )
        after = extract_records(
            "metadata/works.json", {"registry_version": "1.1", "works": []}
        )
        self.assertEqual(
            compare_records("metadata/works.json", before, after)[0]["source_record_id"],
            "__registry_metadata__",
        )


if __name__ == "__main__":
    unittest.main()

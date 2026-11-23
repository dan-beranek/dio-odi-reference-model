from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

sys.path.insert(0, "scripts")
import prepare_scf_external_candidates as scf


BIO_RECORD = {
    "prefix": "dio-odi",
    "name": "Digital Identity Optimization and Ontology of Digital Identity Reference Vocabulary",
    "description": "DIO/ODI Reference Vocabulary.",
    "pattern": "^[A-Z][A-Za-z0-9]*$",
    "uri_format": "https://vocab.danielberanek.cz/dio-odi/#$1",
    "homepage": "https://vocab.danielberanek.cz/dio-odi",
    "repository": "https://github.com/dan-beranek/dio-odi-reference-model",
    "license": "CC-BY-4.0",
    "deprecated": False,
}


def registry_fixture():
    return {
        "entries": [
            {
                "id": "bioregistry-dio-odi-prefix",
                "url": "https://bioregistry.io/registry/dio-odi",
                "provenance": {"review_date": "2026-11-15"},
            },
            {
                "id": "bartoc-dio-odi-vocabulary",
                "url": "https://bartoc.org/en/node/21188",
                "provenance": {"review_date": "2026-11-20"},
            },
        ]
    }


def works_fixture():
    return {
        "works": [
            {
                "id": "commit-boundary-paper",
                "arxiv": {
                    "current_version": "v2",
                    "version_history_timestamp_utc": "2026-11-05T00:52:52Z",
                },
            }
        ]
    }


class FakeGitHub:
    def __init__(self, commits=None, details=None):
        self.commits = commits or []
        self.details = details or {}

    def get_json(self, path, params=None):
        if path.endswith("/commits"):
            return self.commits
        sha = path.rsplit("/", 1)[-1]
        return self.details[sha]


class TestExternalCandidateHelpers(unittest.TestCase):
    def test_parse_timestamp_supports_iso_and_rfc2822(self):
        self.assertEqual(
            scf.parse_timestamp("2026-11-22T12:00:00Z"),
            datetime(2026, 11, 22, 12, tzinfo=timezone.utc),
        )
        self.assertEqual(
            scf.parse_timestamp("Sun, 22 Nov 2026 12:00:00 GMT"),
            datetime(2026, 11, 22, 12, tzinfo=timezone.utc),
        )

    def test_exact_evidence_matching_distinguishes_updated_source(self):
        index = {"https://example.org/record": ["SCF-2026-055"]}
        status, ids = scf.reference_status(["https://example.org/record/"], index)
        self.assertEqual(status, "already-cited")
        self.assertEqual(ids, ["SCF-2026-055"])
        status, ids = scf.reference_status(
            ["https://example.org/record"], index, changed=True
        )
        self.assertEqual(status, "previously-cited-source-updated")
        self.assertEqual(ids, ["SCF-2026-055"])

    def test_bartoc_modified_timestamp_supports_jskos_and_http_header(self):
        stamp = scf.extract_modified_timestamp(
            {"modified": ["2026-11-21T10:15:00Z"]}, {}
        )
        self.assertEqual(stamp.date().isoformat(), "2026-11-21")
        header_stamp = scf.extract_modified_timestamp({}, {
            "last-modified": "Sat, 21 Nov 2026 10:15:00 GMT"
        })
        self.assertEqual(header_stamp.date().isoformat(), "2026-11-21")

    def test_bartoc_missing_modified_timestamp_is_not_silently_accepted(self):
        with self.assertRaises(scf.ScanError):
            scf.extract_modified_timestamp({"prefLabel": {"en": "DIO/ODI"}}, {})

    def test_hashnode_rss_parses_rss_items(self):
        xml = """<?xml version="1.0"?>
        <rss version="2.0"><channel><item>
          <title>The Match Is Easy, the Merge Is Not</title>
          <link>https://dio-odi.hashnode.dev/the-match-is-easy-the-merge-is-not</link>
          <pubDate>Sun, 22 Nov 2026 12:00:00 GMT</pubDate>
        </item></channel></rss>"""
        items = scf.parse_hashnode_rss(xml)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["observed_on"], "Hashnode RSS")
        self.assertEqual(items[0]["canonical_url"], "https://dio-odi.hashnode.dev/the-match-is-easy-the-merge-is-not")

    def test_hashnode_rss_parses_atom_entries(self):
        xml = """<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom"><entry>
          <title>New DIO/ODI analysis</title>
          <link rel="alternate" href="https://dio-odi.hashnode.dev/new-analysis"/>
          <published>2026-11-22T12:00:00Z</published>
        </entry></feed>"""
        items = scf.parse_hashnode_rss(xml)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["canonical_url"], "https://dio-odi.hashnode.dev/new-analysis")


    def test_medium_rss_maps_known_mirror_to_hashnode_canonical(self):
        xml = """<?xml version="1.0"?>
        <rss version="2.0"><channel><item>
          <title>The Match Is Easy, the Merge Is Not</title>
          <link>https://seo-spec-copy-daniel-beranek.medium.com/the-match-is-easy-the-merge-is-not-28eaba24a2d6?source=rss</link>
          <pubDate>Mon, 23 Nov 2026 09:00:00 GMT</pubDate>
        </item></channel></rss>"""
        items = scf.parse_medium_rss(xml)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["canonical_url"], scf.MEDIUM_CANONICAL_URL)
        self.assertEqual(items[0]["observed_on"], "Medium RSS")
        self.assertIn(scf.MEDIUM_ARTICLE_URL, items[0]["representation_urls"])


    def test_devto_filters_to_dio_odi_canonical_content(self):
        items = scf.parse_devto_articles([
            {
                "title": "The Match Is Easy, the Merge Is Not",
                "url": "https://dev.to/danielberanek/the-match-is-easy-the-merge-is-not-khb",
                "canonical_url": "https://dio-odi.hashnode.dev/the-match-is-easy-the-merge-is-not",
                "published_at": "2026-11-22T12:00:00Z",
                "tag_list": ["agentic", "entityresolution"],
            },
            {
                "title": "Unrelated personal post",
                "url": "https://dev.to/danielberanek/unrelated",
                "canonical_url": "https://dev.to/danielberanek/unrelated",
                "published_at": "2026-11-22T12:00:00Z",
                "tag_list": ["life"],
            },
        ])
        self.assertEqual(len(items), 1)
        self.assertEqual(
            items[0]["canonical_url"],
            "https://dio-odi.hashnode.dev/the-match-is-easy-the-merge-is-not",
        )

    def test_bioregistry_mirror_parity_and_unrelated_commit(self):
        with patch.object(
            scf, "fetch_json",
            side_effect=[(BIO_RECORD, {}), (BIO_RECORD, {})],
        ), patch.object(
            scf, "fetch_bioregistry_record",
            side_effect=[BIO_RECORD, BIO_RECORD],
        ):
            candidates, status = scf.scan_bioregistry(
                registry_fixture(), {}, FakeGitHub(
                    commits=[{"sha": "abc123"}],
                    details={
                        "abc123": {
                            "parents": [{"sha": "parent123"}],
                            "files": [{
                                "filename": scf.BIOREGISTRY_PATH,
                                "patch": '+  "other-prefix": {',
                            }]
                        }
                    },
                ),
            )
        self.assertEqual(candidates, [])
        self.assertTrue(status["surfaces_match"])
        self.assertEqual(status["relevant_prefix_commits"], 0)

    def test_bioregistry_prefix_change_is_a_candidate(self):
        event_index = {
            "https://bioregistry.io/registry/dio-odi": ["SCF-2026-051"]
        }
        before = dict(BIO_RECORD)
        after = dict(BIO_RECORD, description="Updated DIO/ODI description")
        with patch.object(
            scf, "fetch_json",
            side_effect=[(BIO_RECORD, {}), (BIO_RECORD, {})],
        ), patch.object(
            scf, "fetch_bioregistry_record",
            side_effect=[before, after],
        ):
            candidates, _ = scf.scan_bioregistry(
                registry_fixture(), event_index, FakeGitHub(
                    commits=[{"sha": "def456"}],
                    details={
                        "def456": {
                            "parents": [{"sha": "parent456"}],
                            "commit": {
                                "author": {"date": "2026-11-21T10:00:00Z"},
                                "committer": {"date": "2026-11-21T10:00:00Z"},
                            },
                            "files": [{
                                "filename": scf.BIOREGISTRY_PATH,
                                "patch": '@@ -1,3 +1,3 @@',
                            }]
                        }
                    },
                ),
            )
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["reference_status"], "previously-cited-source-updated")
        self.assertEqual(candidates[0]["existing_event_ids"], ["SCF-2026-051"])
        self.assertEqual(candidates[0]["before_record"]["description"], BIO_RECORD["description"])
        self.assertEqual(candidates[0]["after_record"]["description"], "Updated DIO/ODI description")

    def test_bartoc_update_after_review_baseline_becomes_candidate(self):
        with patch.object(
            scf, "fetch_json",
            return_value=({"modified": ["2026-11-21T10:15:00Z"]}, {}),
        ):
            candidates, status = scf.scan_bartoc(
                registry_fixture(),
                {"https://bartoc.org/en/node/21188": ["SCF-2026-055"]},
            )
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["reference_status"], "previously-cited-source-updated")
        self.assertTrue(status["newer_than_review_baseline"])

    def test_bartoc_unchanged_record_produces_no_candidate(self):
        with patch.object(
            scf, "fetch_json",
            return_value=({"modified": ["2026-11-19T10:15:00Z"]}, {}),
        ):
            candidates, status = scf.scan_bartoc(registry_fixture(), {})
        self.assertEqual(candidates, [])
        self.assertFalse(status["newer_than_review_baseline"])

    def test_bartoc_api_single_record_array_is_supported(self):
        with patch.object(
            scf, "fetch_json",
            return_value=([{"modified": ["2026-11-19T10:15:00Z"]}], {}),
        ):
            candidates, status = scf.scan_bartoc(registry_fixture(), {})
        self.assertEqual(candidates, [])
        self.assertTrue(status["record_retrieved"])

    def test_publication_feeds_merge_canonical_and_syndicated_copy(self):
        rss = """<?xml version="1.0"?>
        <rss version="2.0"><channel><item>
          <title>The Match Is Easy, the Merge Is Not</title>
          <link>https://dio-odi.hashnode.dev/the-match-is-easy-the-merge-is-not</link>
          <pubDate>Sun, 22 Nov 2026 12:00:00 GMT</pubDate>
        </item></channel></rss>"""
        medium_rss = """<?xml version="1.0"?>
        <rss version="2.0"><channel><item>
          <title>The Match Is Easy, the Merge Is Not</title>
          <link>https://seo-spec-copy-daniel-beranek.medium.com/the-match-is-easy-the-merge-is-not-28eaba24a2d6</link>
          <pubDate>Mon, 23 Nov 2026 09:00:00 GMT</pubDate>
        </item></channel></rss>"""
        devto = [{
            "title": "The Match Is Easy, the Merge Is Not",
            "url": "https://dev.to/danielberanek/the-match-is-easy-the-merge-is-not-khb",
            "canonical_url": "https://dio-odi.hashnode.dev/the-match-is-easy-the-merge-is-not",
            "published_at": "2026-11-22T12:00:00Z",
            "tag_list": ["agentic"],
        }]
        with patch.object(scf, "fetch_text", side_effect=[rss, medium_rss]), patch.object(
            scf, "fetch_json", return_value=(devto, {})
        ):
            candidates, stats, errors = scf.scan_publications(
                {
                    "https://dio-odi.hashnode.dev/the-match-is-easy-the-merge-is-not": ["SCF-2026-058"],
                    "https://dev.to/danielberanek/the-match-is-easy-the-merge-is-not-khb": ["SCF-2026-058"],
                },
                datetime(2026, 11, 21, tzinfo=timezone.utc),
            )
        self.assertEqual(errors, [])
        self.assertEqual(len(candidates), 1)
        self.assertEqual(set(candidates[0]["observed_on"]), {"Hashnode RSS", "DEV.to API", "Medium RSS"})
        self.assertIn(scf.MEDIUM_ARTICLE_URL, candidates[0]["representation_urls"])
        self.assertEqual(candidates[0]["source_url"], scf.MEDIUM_CANONICAL_URL)
        self.assertEqual(candidates[0]["reference_status"], "already-cited")
        self.assertEqual(candidates[0]["existing_event_ids"], ["SCF-2026-058"])
        self.assertEqual(stats["devto_articles_inspected"], 1)
        self.assertEqual(stats["medium_items_inspected"], 1)

    def test_arxiv_newer_version_is_a_candidate(self):
        xml = """<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <id>http://arxiv.org/abs/2610.37407v3</id>
            <updated>2026-11-21T10:00:00Z</updated>
          </entry>
        </feed>"""
        with patch.object(scf, "fetch_text", return_value=xml):
            candidates, status = scf.scan_arxiv(works_fixture(), {})
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["live_version"], "v3")
        self.assertEqual(status["expected_version"], "v2")


if __name__ == "__main__":
    unittest.main()

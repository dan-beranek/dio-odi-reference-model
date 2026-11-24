from __future__ import annotations

import sys
import unittest

sys.path.insert(0, "scripts")
import prepare_research_genealogy_archive_intake as intake


class TestResearchGenealogyArchiveIntake(unittest.TestCase):
    def test_normalized_url_removes_www_scheme_and_trailing_slash(self):
        self.assertEqual(
            intake.normalized_url("http://www.slideshare.net/slideshow/example/12345/"),
            "https://slideshare.net/slideshow/example/12345",
        )

    def test_normalized_url_keeps_query_parameters(self):
        self.assertEqual(
            intake.normalized_url("https://www.slideshare.net/danielberanek?tab=presentations"),
            "https://slideshare.net/danielberanek?tab=presentations",
        )

    def test_is_slideshare_url_accepts_presentation_path_and_subdomain(self):
        self.assertTrue(intake.is_slideshare_url(
            "https://de.slideshare.net/slideshow/example/12345"
        ))
        self.assertFalse(intake.is_slideshare_url(
            "https://www.slideshare.net/danielberanek"
        ))
        self.assertFalse(intake.is_slideshare_url(
            "https://example.com/slideshow/example/12345"
        ))

    def test_extract_profile_presentation_links_and_ignore_other_links(self):
        html = """
        <html><body>
          <h1>SEO specialista a copywriter Daniel Beránek</h1>
          <p>49 Slideshow</p>
          <a href="/slideshow/ai-tools-review/276986914">
            <img alt="AIs: zhola subjektivně a děsně útržkovitě">
          </a>
          <a href="https://de.slideshare.net/slideshow/example-title/287729434">Read</a>
          <a href="https://www.slideshare.net/danielberanek">Profile</a>
          <a href="https://scribd.com/document/123">Scribd</a>
        </body></html>
        """
        links = intake.extract_slideshow_links(
            html, "https://www.slideshare.net/danielberanek"
        )
        self.assertEqual(len(links), 2)
        self.assertEqual(
            {link["url"] for link in links},
            {
                "https://www.slideshare.net/slideshow/ai-tools-review/276986914",
                "https://de.slideshare.net/slideshow/example-title/287729434",
            },
        )
        self.assertEqual(intake.profile_count(html), 49)

    def test_extract_profile_links_from_absolute_urls_embedded_in_html(self):
        html = (
            '<script>const u = "https://www.slideshare.net/slideshow/'
            'some-deck/999888";</script>'
        )
        links = intake.extract_slideshow_links(html, "https://example.org/")
        self.assertEqual(len(links), 1)
        self.assertTrue(links[0]["url"].endswith("/999888"))

    def test_profile_count_parses_singular_and_plural_labels(self):
        self.assertEqual(intake.profile_count("49 Slideshow"), 49)
        self.assertEqual(intake.profile_count("49 Slideshows"), 49)
        self.assertIsNone(intake.profile_count("presentations are listed"))

    def test_profile_discovery_status_does_not_treat_missing_count_as_zero(self):
        self.assertEqual(
            intake.derive_profile_discovery_status(None, 0),
            "no-profile-links-or-count-extracted",
        )
        self.assertEqual(
            intake.derive_profile_discovery_status(49, 0),
            "profile-count-visible-but-links-not-extracted",
        )
        self.assertEqual(
            intake.derive_profile_discovery_status(49, 12),
            "profile-links-extracted",
        )
        self.assertEqual(
            intake.derive_profile_discovery_status(None, 12),
            "profile-links-extracted-count-not-observed",
        )


    def test_timestamp_to_iso_uses_utc(self):
        self.assertEqual(
            intake.timestamp_to_iso("20260312183717"),
            "2026-03-12T18:37:17Z",
        )
        self.assertIsNone(intake.timestamp_to_iso("20261312183717"))
        self.assertIsNone(intake.timestamp_to_iso("unknown"))

    def test_cdx_capture_record_preserves_archive_provenance(self):
        capture = intake.cdx_capture_record({
            "timestamp": "20260312183717",
            "original": "https://www.slideshare.net/slideshow/example/12345",
            "mimetype": "text/html",
            "statuscode": "200",
            "digest": "ABC123",
            "length": "2048",
        })
        self.assertEqual(capture["captured_at"], "2026-03-12T18:37:17Z")
        self.assertEqual(capture["status_code"], "200")
        self.assertEqual(capture["digest"], "ABC123")
        self.assertEqual(
            capture["replay_url"],
            "https://web.archive.org/web/20260312183717/"
            "https://www.slideshare.net/slideshow/example/12345",
        )

    def test_registry_items_are_limited_to_slide_share_platform(self):
        registry = {
            "artefacts": [
                {
                    "id": "slide-a",
                    "platform": "SlideShare",
                    "url": "https://www.slideshare.net/slideshow/a/111",
                },
                {
                    "id": "other",
                    "platform": "Google Gemini",
                    "url": "https://gemini.google.com/share/abc",
                },
                {
                    "id": "profile",
                    "platform": "SlideShare",
                    "url": "https://www.slideshare.net/danielberanek",
                },
            ]
        }
        records = intake.slideshare_registry_items(registry)
        self.assertEqual([item["id"] for item in records], ["slide-a"])


if __name__ == "__main__":
    unittest.main()

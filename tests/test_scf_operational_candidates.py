import unittest
from datetime import datetime, timedelta, timezone

from scripts.prepare_scf_operational_candidates import (
    existing_evidence_index,
    normalise_deployment_run,
    normalise_release,
    parse_timestamp,
)

NOW = datetime(2026, 11, 23, 3, 0, tzinfo=timezone.utc)
CUTOFF = NOW - timedelta(hours=48)
REPO = "dan-beranek/dio-odi-mcp"
WORKFLOWS = ("Deploy Cloudflare Worker",)


class ScfOperationalIntakeTests(unittest.TestCase):
    def deployment(self, **overrides):
        run = {
            "id": 123456,
            "name": "Deploy Cloudflare Worker",
            "status": "completed",
            "conclusion": "success",
            "head_branch": "main",
            "event": "push",
            "head_sha": "abc123",
            "created_at": "2026-11-22T20:00:00Z",
            "updated_at": "2026-11-22T20:04:00Z",
            "html_url": "https://github.com/dan-beranek/dio-odi-mcp/actions/runs/123456",
        }
        run.update(overrides)
        return run

    def release(self, **overrides):
        release = {
            "id": 987,
            "tag_name": "v0.2.0",
            "name": "MCP v0.2.0",
            "draft": False,
            "prerelease": False,
            "published_at": "2026-11-22T20:00:00Z",
            "target_commitish": "main",
            "html_url": "https://github.com/dan-beranek/dio-odi-mcp/releases/tag/v0.2.0",
        }
        release.update(overrides)
        return release

    def test_successful_allowlisted_deployment_becomes_candidate(self):
        candidate = normalise_deployment_run(
            REPO, WORKFLOWS, self.deployment(), CUTOFF, {}
        )
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["kind"], "deployment")
        self.assertEqual(candidate["date_candidate"], "2026-11-22")
        self.assertEqual(candidate["date_basis_candidate"], "deployment_date")
        self.assertEqual(candidate["reference_status"], "review-required")

    def test_failed_deployment_is_ignored(self):
        self.assertIsNone(normalise_deployment_run(
            REPO, WORKFLOWS, self.deployment(conclusion="failure"), CUTOFF, {}
        ))

    def test_validation_workflow_is_not_a_deployment_candidate(self):
        self.assertIsNone(normalise_deployment_run(
            REPO, WORKFLOWS, self.deployment(name="CI"), CUTOFF, {}
        ))

    def test_non_main_branch_is_ignored(self):
        self.assertIsNone(normalise_deployment_run(
            REPO, WORKFLOWS, self.deployment(head_branch="feature/test"), CUTOFF, {}
        ))

    def test_old_deployment_is_ignored(self):
        self.assertIsNone(normalise_deployment_run(
            REPO, WORKFLOWS,
            self.deployment(updated_at="2026-11-20T01:00:00Z"),
            CUTOFF, {}
        ))

    def test_existing_exact_evidence_url_is_linked_to_event(self):
        url = "https://github.com/dan-beranek/dio-odi-mcp/actions/runs/123456"
        feed = {"events": [{
            "id": "SCF-2026-049",
            "evidence": {"sources": [{"url": url}]},
        }]}
        candidate = normalise_deployment_run(
            REPO, WORKFLOWS, self.deployment(), CUTOFF,
            existing_evidence_index(feed)
        )
        self.assertEqual(candidate["reference_status"], "already-cited")
        self.assertEqual(candidate["existing_event_ids"], ["SCF-2026-049"])

    def test_published_stable_release_becomes_candidate(self):
        candidate = normalise_release(REPO, self.release(), CUTOFF, {})
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["kind"], "release")
        self.assertEqual(candidate["date_candidate"], "2026-11-22")
        self.assertEqual(candidate["date_basis_candidate"], "publication_date")

    def test_draft_prerelease_and_unpublished_release_are_ignored(self):
        for changes in (
            {"draft": True},
            {"prerelease": True},
            {"published_at": None},
        ):
            with self.subTest(changes=changes):
                self.assertIsNone(normalise_release(
                    REPO, self.release(**changes), CUTOFF, {}
                ))

    def test_old_release_is_ignored(self):
        self.assertIsNone(normalise_release(
            REPO, self.release(published_at="2026-11-20T01:00:00Z"),
            CUTOFF, {}
        ))

    def test_timestamp_parser_normalises_utc(self):
        parsed = parse_timestamp("2026-11-22T20:00:00Z")
        self.assertEqual(parsed.tzinfo, timezone.utc)
        self.assertEqual(parsed.isoformat(), "2026-11-22T20:00:00+00:00")


if __name__ == "__main__":
    unittest.main()

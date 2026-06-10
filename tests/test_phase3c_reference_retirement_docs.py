#!/usr/bin/env python3

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = (
    REPO_ROOT
    / "docs"
    / "phase3c-reference-retirement-decision.md"
)
README = REPO_ROOT / "README.md"
AUDIT = REPO_ROOT / "docs" / "phase3c-migration-parity-audit.md"


class Phase3C10DecisionDocumentationTests(unittest.TestCase):
    def test_document_records_selected_option_b(self):
        text = DOCUMENT.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "Status: complete; permanent public runtime in production.",
            "## Retirement options",
            "### Option A — immediate retirement",
            "### Option B — disabled reference fallback",
            "This option is selected.",
            "### Option C — continued parallel rehearsal",
            "## Selected production architecture",
            "## Controlled cutover sequence",
            "## Production cutover completion",
            "## Rollback triggers",
            "## Rollback procedure",
            "## Reference retention period",
            "## Release boundary",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_document_records_permanent_runtime_contract(self):
        text = DOCUMENT.read_text(encoding="utf-8")

        required = (
            "/opt/sanity-node",
            "/opt/sanity-node/app",
            "/opt/sanity-node/config/config.yaml",
            "/opt/sanity-node/html/index.html",
            "/opt/sanity-node/logs/generator.log",
            "/opt/sanity-node/run/generator.lock",
            "sanity-node-generate.service",
            "sanity-node-generate.timer",
            "sanity-node-web.service",
            "scripts/run-public-production.sh",
            "TCP port 8088",
            "starts independently from the generator",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)

    def test_document_records_fail_closed_generation(self):
        text = DOCUMENT.read_text(encoding="utf-8")

        required = (
            "requires `dashboard.runtime_mode: public`",
            "non-blocking execution lock",
            "runs startup preflight",
            "process-specific temporary file",
            "accepted public GUI markers",
            "rejects obsolete Config Preview wording",
            "atomically replaces the last successful production output",
            "A failed run does not replace the last successful",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)

    def test_document_records_reference_fallback_state(self):
        text = DOCUMENT.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "reference generator timer: inactive and disabled",
            "reference web service: inactive and disabled",
            "public rehearsal timer: inactive and disabled",
            "retained reference implementation",
            "without deleting the new workspace",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_document_records_retention_and_release_boundary(self):
        text = DOCUMENT.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "at least 30 days",
            "at least one release after `v0.3.0`",
            "The later of those two milestones",
            "requires a separate explicit decision",
            "close Phase 3C",
            "the `v0.3.0` release candidate",
            "The existing `v0.2.0` tag remains unchanged.",
            "does not create or move a release tag",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_document_records_completed_production_cutover(self):
        text = DOCUMENT.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "Status: complete; permanent public runtime in production.",
            "## Production cutover completion",
            "controlled production cutover was completed",
            "complete rollback to the retained reference runtime",
            "multiple consecutive scheduled permanent generations",
            "commit `bf0aa34` corrected the web-service startup contract",
            "did not start the generator",
            "remain installed but disabled",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

        self.assertNotIn(
            "controlled production cutover pending",
            text,
        )

    def test_readme_records_phase3c_complete(self):
        text = README.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "Phase 3C.10 selected Option B and completed the controlled "
            "production cutover",
            "permanent host-native public runtime now owns the served "
            "dashboard",
            "reference implementation and the public rehearsal runtime "
            "remain installed but disabled",
            "docs/phase3c-reference-retirement-decision.md",
            "Phase 3C.10 Reference retirement and production cutover "
            "Complete",
            "Phase 3C is complete",
            "the `v0.3.0` release candidate",
            "fresh-install",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

        forbidden = (
            "controlled production cutover pending",
            "production cutover and post-cutover observation remain pending",
            "Reference mode remains the served known-good path until",
        )

        for value in forbidden:
            with self.subTest(value=value):
                self.assertNotIn(value, normalized)

    def test_migration_audit_records_completed_boundary(self):
        text = AUDIT.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "## Phase 3C.10 completion — reference retirement and "
            "production cutover",
            "selected Option B and completed the controlled production "
            "cutover",
            "complete rollback rehearsal",
            "Commit `bf0aa34` corrected the permanent web-service startup "
            "ordering",
            "Phase 3C.10 Reference retirement and production cutover "
            "Complete",
            "Phase 3C is complete",
            "the `v0.3.0` release candidate",
            "clean public installation journey",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

        forbidden = (
            "Decision complete; controlled cutover pending",
            "The remaining Phase 3C execution work",
            "Reference mode remains the served known-good path until",
        )

        for value in forbidden:
            with self.subTest(value=value):
                self.assertNotIn(value, normalized)

    def test_document_does_not_publish_private_inventory(self):
        text = DOCUMENT.read_text(encoding="utf-8")

        forbidden_patterns = {
            "private IPv4 address": (
                r"\b192\.168\.\d{1,3}\.\d{1,3}\b"
            ),
            "personal home path": r"/home/[^/\s]+",
            "private dataset prefix": (
                r"\b(?:tank|backup|nvme)/"
            ),
            "private host model label": r"\bT(?:330|620)\b",
            "private deployment account": (
                r"(?:\bcontrols\b\s+(?:account|user|group)\b|"
                r"(?:User=|Group=|\baccount\s+|\buser\s+|"
                r"\bgroup\s+)controls\b)"
            ),
            "private deployment hostname": (
                r"homelabvonh23rz"
            ),
            "private SSH key filename": r"id_ed25519",
        }

        for label, pattern in forbidden_patterns.items():
            with self.subTest(label=label):
                self.assertIsNone(
                    re.search(pattern, text),
                    f"decision document contains {label}",
                )


if __name__ == "__main__":
    unittest.main()

import ast
import html
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPO_ROOT / "scripts" / "generate-dashboard.py"

FUNCTION_NAMES = {
    "h",
    "badge",
    "build_public_issue_card",
}


def load_functions():
    source = GENERATOR.read_text(encoding="utf-8")
    parsed = ast.parse(source, filename=str(GENERATOR))

    selected_nodes = [
        node
        for node in parsed.body
        if isinstance(node, ast.FunctionDef)
        and node.name in FUNCTION_NAMES
    ]

    namespace = {
        "html": html,
    }

    exec(
        compile(
            ast.Module(body=selected_nodes, type_ignores=[]),
            filename=str(GENERATOR),
            mode="exec",
        ),
        namespace,
    )

    return namespace


FUNCTIONS = load_functions()
BUILDER = FUNCTIONS.get("build_public_issue_card")


class PublicIssueCardContractTests(unittest.TestCase):
    def test_renderer_exists(self):
        self.assertIsNotNone(
            BUILDER,
            "build_public_issue_card is not implemented yet",
        )


@unittest.skipIf(
    BUILDER is None,
    "public issue-card renderer not implemented yet",
)
class PublicIssueCardRenderingTests(unittest.TestCase):
    def test_healthy_status_renders_no_card(self):
        rendered = BUILDER(
            {
                "label": "OK",
                "css": "ok",
                "note": "Data fresh",
                "issues": {
                    3: [],
                    2: [],
                    1: [],
                },
            }
        )

        self.assertEqual(rendered, "")

    def test_orders_critical_warning_and_info_items(self):
        rendered = BUILDER(
            {
                "label": "NOK",
                "css": "bad",
                "note": (
                    "Systems · T620 TrueNAS: UNREACHABLE"
                ),
                "issues": {
                    3: [
                        "Systems · T620 TrueNAS: UNREACHABLE",
                        "Services · Jellyfin: DOWN",
                    ],
                    2: [
                        "Protection · Utility Backup: OLD",
                    ],
                    1: [
                        "Services · Redis: UPDATE",
                    ],
                },
            }
        )

        self.assertIn(
            'data-public-issue-card="true"',
            rendered,
        )
        self.assertIn("Issues / Failures", rendered)
        self.assertIn("public-issues-card bad", rendered)
        self.assertIn("2 Critical · 1 Warning · 1 Info", rendered)

        markers = [
            "Systems · T620 TrueNAS: UNREACHABLE",
            "Services · Jellyfin: DOWN",
            "Protection · Utility Backup: OLD",
            "Services · Redis: UPDATE",
        ]

        positions = [
            rendered.index(marker)
            for marker in markers
        ]

        self.assertEqual(positions, sorted(positions))
        self.assertIn(">CRITICAL</span>", rendered)
        self.assertIn(">WARNING</span>", rendered)
        self.assertIn(">INFO</span>", rendered)

    def test_info_only_update_uses_information_style(self):
        rendered = BUILDER(
            {
                "label": "INFO",
                "css": "info",
                "note": "Services · Redis: UPDATE",
                "issues": {
                    3: [],
                    2: [],
                    1: [
                        "Services · Redis: UPDATE",
                    ],
                },
            }
        )

        self.assertIn("public-issues-card info", rendered)
        self.assertIn("0 Critical · 0 Warning · 1 Info", rendered)
        self.assertIn("Services · Redis: UPDATE", rendered)

    def test_duplicate_issue_text_is_rendered_once(self):
        rendered = BUILDER(
            {
                "label": "NOK",
                "css": "bad",
                "issues": {
                    3: [
                        "Systems · T330 TrueNAS: UNREACHABLE",
                        "Systems · T330 TrueNAS: UNREACHABLE",
                    ],
                    2: [],
                    1: [],
                },
            }
        )

        self.assertEqual(
            rendered.count(
                "Systems · T330 TrueNAS: UNREACHABLE"
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()

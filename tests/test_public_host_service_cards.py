import ast
import html
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPO_ROOT / "scripts" / "generate-dashboard.py"
FIXTURE = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "public_host_service_cards.json"
)

FUNCTION_NAMES = {
    "cfg_get",
    "enabled_items",
    "status_text_class",
    "h",
    "configured_host_display_name",
    "configured_host_sort_key",
    "build_service_summary",
    "build_public_host_service_cards",
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
        "CONFIG": {
            "collector": {
                "id": "collector",
            }
        },
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
BUILDER = FUNCTIONS.get("build_public_host_service_cards")


class PublicHostServiceCardContractTests(unittest.TestCase):
    def test_renderer_exists(self):
        self.assertIsNotNone(
            BUILDER,
            "build_public_host_service_cards is not implemented yet",
        )


@unittest.skipIf(
    BUILDER is None,
    "host service-card renderer not implemented yet",
)
class PublicHostServiceCardRenderingTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(
            FIXTURE.read_text(encoding="utf-8")
        )

    def render(self):
        return BUILDER(
            self.fixture["hosts"],
            self.fixture["services"],
            self.fixture["statuses"],
            reserved_blank_cards=(
                self.fixture["reserved_blank_cards"]
            ),
        )

    def test_renders_exactly_four_cards_in_required_order(self):
        rendered = self.render()

        markers = [
            'data-host-card="collector"',
            'data-host-card="t330"',
            'data-host-card="t620"',
            'data-host-card="reserved"',
        ]

        self.assertEqual(rendered.count("data-host-card="), 4)

        positions = [
            rendered.index(marker)
            for marker in markers
        ]

        self.assertEqual(positions, sorted(positions))

    def test_utility_node_card_contains_all_services(self):
        rendered = self.render()

        self.assertIn("Utility Node Services", rendered)
        self.assertIn(
            "5 Apps · 3 Helpers · 8 UP · 0 DOWN",
            rendered,
        )

        for service_name in (
            "Familienbudget",
            "Wiki.js Private",
            "Pi-hole",
            "Nginx Proxy Manager",
            "Dockge",
            "Cloudflare Tunnel",
            "Wiki.js Database",
            "Diun",
        ):
            self.assertIn(service_name, rendered)

    def test_t330_remains_a_real_zero_service_card(self):
        rendered = self.render()

        self.assertIn("T330 Services", rendered)
        self.assertIn("0 Services", rendered)
        self.assertIn("No services configured", rendered)

    def test_t620_card_shows_full_inventory_and_update(self):
        rendered = self.render()

        self.assertIn("T620 Services", rendered)
        self.assertIn(
            "10 Apps · 5 Helpers · 14 UP · "
            "0 DOWN · 1 UPDATE",
            rendered,
        )
        self.assertIn("qBittorrent VPN", rendered)
        self.assertIn(">UPDATE</span>", rendered)
        self.assertIn(
            "service-details two-column",
            rendered,
        )

    def test_fourth_card_is_an_intentionally_blank_placeholder(self):
        rendered = self.render()

        self.assertIn(
            '<div class="summary-card host-service-card '
            'placeholder" data-host-card="reserved" '
            'aria-hidden="true"></div>',
            rendered,
        )


if __name__ == "__main__":
    unittest.main()

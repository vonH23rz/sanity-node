from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate-dashboard.py"
FOUNDATION = ROOT / "web" / "vonh23rz-dashboard-typography.css"


def test_typography_foundation_file_exists() -> None:
    assert FOUNDATION.exists()

    css = FOUNDATION.read_text(encoding="utf-8")

    assert "vonH23rz dashboard typography foundation" in css
    assert "--vh-font-family" in css
    assert '--vh-text-color: #53585f;' in css
    assert "--vh-font-size-base: 12px;" in css
    assert "--vh-weight-body: 400;" in css
    assert "--vh-weight-soft: 300;" in css
    assert "text-transform: none !important;" in css
    assert "font-weight: var(--vh-weight-soft) !important;" in css
    assert "line-height: var(--vh-line-height-compact) !important;" in css


def test_generator_loads_typography_foundation() -> None:
    source = GENERATOR.read_text(encoding="utf-8")

    assert "TYPOGRAPHY_FOUNDATION_PATH" in source
    assert "vonh23rz-dashboard-typography.css" in source
    assert "DASHBOARD_TYPOGRAPHY_FOUNDATION_CSS = load_static_css" in source
    assert "{DASHBOARD_TYPOGRAPHY_FOUNDATION_CSS}" in source


def test_typography_foundation_is_final_css_layer() -> None:
    source = GENERATOR.read_text(encoding="utf-8")

    foundation_index = source.index("{DASHBOARD_TYPOGRAPHY_FOUNDATION_CSS}")
    style_end_index = source.index("</style>", foundation_index)

    assert foundation_index < style_end_index
    assert "Sanity Node final typography weight correction." not in source[foundation_index:style_end_index]


def test_typography_foundation_unifies_downstream_section_sizes() -> None:
    css = FOUNDATION.read_text(encoding="utf-8")

    assert "Uniform downstream section typography size." in css
    assert ".pool-card th," in css
    assert ".replication-card th," in css
    assert ".pool-card td," in css
    assert ".replication-card td," in css
    assert ".pool-card td:first-child," in css
    assert ".replication-card td:first-child," in css
    assert ".summary-details," in css
    assert ".service-line," in css
    assert "font-size: var(--vh-font-size-base) !important;" in css

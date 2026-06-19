from pathlib import Path


GENERATOR = Path("scripts/generate-dashboard.py")


def _source() -> str:
    return GENERATOR.read_text(encoding="utf-8")


def _weight_alignment_block() -> str:
    source = _source()
    marker = "Sanity Node Security Node typography weight alignment."
    assert marker in source

    start = source.index("/* " + marker)
    end = source.index("*/", start)
    block_end = source.index("\n}", source.index(".badge,", end)) + 2
    return source[start:block_end]


def _targeted_heading_weight_alignment_block() -> str:
    source = _source()
    marker = "Targeted Security Node-style heading weight alignment."
    assert marker in source

    start = source.index("/* " + marker)
    end = source.index("</style>", start)
    return source[start:end]


def test_security_node_typography_weight_alignment_override_exists() -> None:
    block = _weight_alignment_block()

    assert "Keep the accepted XS font family, size, color, spacing, and layout." in block
    assert "Only soften the older bold-heavy Sanity Node text treatment." in block

    assert ".info-label," in block
    assert ".pool-card th," in block
    assert ".replication-card th {" in block
    assert "font-weight: 600 !important;" in block
    assert "text-transform: none !important;" in block
    assert "letter-spacing: 0.01em !important;" in block

    assert ".info-value," in block
    assert ".pool-card td," in block
    assert ".replication-card td," in block
    assert ".dashboard-footer strong {" in block
    assert "font-weight: 500 !important;" in block

    assert ".badge," in block
    assert ".temp-badge," in block
    assert "font-weight: 600 !important;" in block


def test_security_node_typography_weight_alignment_does_not_change_xs_baseline() -> None:
    source = _source()

    assert "Sanity Node shared XS typography baseline." in source
    assert 'font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;' in source
    assert "color: #53585f !important;" in source
    assert "font-size: 12px !important;" in source
    assert "font-size: 22px !important;" in source


def test_security_node_typography_weight_alignment_is_final_css_override() -> None:
    source = _source()
    marker_index = source.index("Sanity Node Security Node typography weight alignment.")
    style_end_index = source.index("</style>", marker_index)

    original_softening_block = _weight_alignment_block()
    targeted_block = _targeted_heading_weight_alignment_block()

    assert marker_index < style_end_index
    assert "font-weight: 800 !important;" not in source[marker_index:style_end_index]

    # The original Security Node alignment block must stay a softening layer.
    assert "font-weight: 700 !important;" not in original_softening_block

    # A later, narrow override is allowed only for the explicit heading/value targets.
    assert "Matches Known Hosts-style heading emphasis" in targeted_block
    assert ".header-left h1 {{" in targeted_block
    assert ".host-service-card .value {{" in targeted_block
    assert ".system-card h3,\n.public-issues-header h2 {{" in targeted_block
    assert targeted_block.count("font-weight: 700 !important;") == 3
    assert ".public-issues-card th" not in targeted_block
    assert ".public-issues-card td" not in targeted_block

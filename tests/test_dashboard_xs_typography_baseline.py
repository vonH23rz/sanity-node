from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate-dashboard.py"


def test_xs_typography_baseline_is_defined_in_dashboard_generator():
    source = GENERATOR.read_text(encoding="utf-8")

    assert "Sanity Node shared XS typography baseline" in source
    assert 'font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;' in source
    assert "body {" in source
    assert "font-size: 12px !important;" in source
    assert "line-height: 1.29 !important;" in source
    assert "color: #53585f !important;" in source
    assert ".header-left h1 {" in source
    assert "font-size: 22px !important;" in source
    assert "line-height: 1.12 !important;" in source
    assert "h2," in source
    assert "font-size: 15.5px !important;" in source
    assert ".summary-card .value {" in source
    assert "font-size: 9.5px !important;" in source

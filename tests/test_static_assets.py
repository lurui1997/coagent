from pathlib import Path

from app.static_assets import static_asset_url, versioned_static_url


def test_static_asset_url_includes_version(tmp_path: Path):
    css = tmp_path / "style.css"
    css.write_text("body{}", encoding="utf-8")
    url = static_asset_url(tmp_path, "style.css")
    assert url.startswith("/static/style.css?v=")
    assert url.split("?v=")[1].isdigit()


def test_versioned_static_url_none_for_unknown(tmp_path: Path):
    assert versioned_static_url(tmp_path, "missing.css") is None

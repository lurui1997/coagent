"""静态资源 URL（带 mtime 版本号，避免 nginx/浏览器缓存旧 CSS）。"""

from __future__ import annotations

from pathlib import Path

VERSIONED_STATIC_FILES = frozenset({"style.css", "theme.js", "vendor/htmx.min.js"})


def file_mtime(static_dir: Path, filename: str) -> int:
    path = static_dir / filename
    return int(path.stat().st_mtime) if path.is_file() else 0


def static_asset_url(static_dir: Path, filename: str) -> str:
    return f"/static/{filename}?v={file_mtime(static_dir, filename)}"


def static_dir_version(static_dir: Path, *filenames: str) -> str:
    mtimes = [file_mtime(static_dir, name) for name in filenames]
    mtimes = [m for m in mtimes if m]
    return str(max(mtimes) if mtimes else 0)


def versioned_static_url(static_dir: Path, filename: str) -> str | None:
    if filename not in VERSIONED_STATIC_FILES:
        return None
    version = file_mtime(static_dir, filename)
    if not version:
        return None
    return f"/static/{filename}?v={version}"

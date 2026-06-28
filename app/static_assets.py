"""静态资源 URL（带 mtime 版本号，避免 nginx/浏览器缓存旧 CSS）。"""

from __future__ import annotations

from pathlib import Path


def static_asset_url(static_dir: Path, filename: str) -> str:
    path = static_dir / filename
    version = int(path.stat().st_mtime) if path.is_file() else 0
    return f"/static/{filename}?v={version}"


def static_dir_version(static_dir: Path, *filenames: str) -> str:
    mtimes = []
    for name in filenames:
        path = static_dir / name
        if path.is_file():
            mtimes.append(int(path.stat().st_mtime))
    return str(max(mtimes) if mtimes else 0)

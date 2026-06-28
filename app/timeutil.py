"""项目统一使用东八区（UTC+8）时间。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

TZ_CN = timezone(timedelta(hours=8))


def now_cn() -> datetime:
    return datetime.now(TZ_CN)


def now_iso() -> str:
    """东八区 ISO8601，例如 2026-06-28T15:30:00+08:00"""
    return now_cn().isoformat(timespec="seconds")


def today_cn_str() -> str:
    return now_cn().strftime("%Y-%m-%d")


def format_display(iso_str: str | None) -> str:
    """UI 展示：YYYY-MM-DD HH:MM:SS（东八区）"""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ_CN)
        else:
            dt = dt.astimezone(TZ_CN)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return iso_str[:19].replace("T", " ")


def utc_now_iso() -> str:
    """兼容旧名，实际返回东八区时间。"""
    return now_iso()

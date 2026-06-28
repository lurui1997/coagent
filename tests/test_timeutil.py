from app.timeutil import TZ_CN, format_display, now_iso, today_cn_str


def test_now_iso_uses_cn_offset():
    ts = now_iso()
    assert "+08:00" in ts


def test_today_cn_str_format():
    assert len(today_cn_str()) == 10
    assert today_cn_str()[4] == "-"


def test_format_display_cn():
    assert format_display("2026-06-28T15:30:00+08:00") == "2026-06-28 15:30:00"
    assert format_display("2026-06-28T07:30:00+00:00") == "2026-06-28 15:30:00"


def test_tz_cn_offset():
    assert TZ_CN.utcoffset(None).total_seconds() == 8 * 3600

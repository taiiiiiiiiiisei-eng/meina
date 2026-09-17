"""めいなの自然な日本語リマインダー命令を安全に解析する。"""
from __future__ import annotations

import re
from datetime import datetime, timedelta


_RELATIVE = re.compile(r"(?P<num>\d+)\s*(?P<unit>秒|分|時間|時|日)\s*後")
_CLOCK = re.compile(r"(?P<hour>\d{1,2})\s*時(?:\s*(?P<minute>\d{1,2})\s*分?)?")


def parse_reminder_command(text: str, now: datetime | None = None) -> dict | None:
    """「10分後に宿題」「18時に配信」などをリマインダー情報へ変換する。"""
    raw = str(text or "").strip()
    if not raw or "リマインド" not in raw and "リマインダー" not in raw:
        return None

    current = now or datetime.now().astimezone()
    match = _RELATIVE.search(raw)
    if match:
        amount = int(match.group("num"))
        unit = match.group("unit")
        delta = {
            "秒": timedelta(seconds=amount),
            "分": timedelta(minutes=amount),
            "時間": timedelta(hours=amount),
            "時": timedelta(hours=amount),
            "日": timedelta(days=amount),
        }[unit]
        due = current + delta
        text_part = _extract_text(raw, match.span(), "後")
        if text_part:
            return {"text": text_part, "due_at": due.isoformat(timespec="seconds")}
        return None

    match = _CLOCK.search(raw)
    if match:
        hour = int(match.group("hour"))
        minute = int(match.group("minute") or 0)
        if hour > 23 or minute > 59:
            return None
        due = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if due <= current:
            due += timedelta(days=1)
        text_part = _extract_text(raw, match.span(), "時")
        if text_part:
            return {"text": text_part, "due_at": due.isoformat(timespec="seconds")}
    return None


def _extract_text(raw: str, span: tuple[int, int], marker: str) -> str:
    before = raw[: span[0]]
    after = raw[span[1] :]
    parts = re.split(r"(?:に|へ|って|を)?(?:リマインド|リマインダー)(?:して|してね|お願い)?", before, maxsplit=1)
    text = parts[-1] if len(parts) > 1 else after
    if not text.strip():
        text = after
    text = re.sub(r"^[、。\s]+|[、。！？?\s]+$", "", text)
    text = re.sub(r"^(?:に|を|の)\s*", "", text)
    if not text and after:
        text = after
    return text.strip(" 、。！？?")

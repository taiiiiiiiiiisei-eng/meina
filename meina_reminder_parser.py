"""めいなの自然な日本語リマインダー・予定命令を安全に解析する。"""
from __future__ import annotations

import re
from datetime import datetime, timedelta


_RELATIVE = re.compile(r"(?:あと\s*)?(?P<num>\d+)\s*(?P<unit>秒|分|時間|時|日)\s*(?:後|で)")
_CLOCK = re.compile(r"(?:(?P<ampm>午前|午後)\s*)?(?P<hour>\d{1,2})\s*時(?:\s*(?P<minute>\d{1,2})\s*分?)?")
_COMMAND_WORDS = re.compile(
    r"(?:リマインド|リマインダー|予定|スケジュール|起こして|知らせて|思い出させて|教えて)"
    r"(?:を)?(?:追加|登録|設定|リマインド)?"
    r"(?:して|してね|してください|して下さい|お願い|お願いします)?"
)
_DAY_WORDS = re.compile(r"(?P<day>今日|明日|明後日)")
_TRAILING_COMMAND = re.compile(
    r"(?:を)?(?:追加|登録|設定|リマインド|リマインダー)?"
    r"(?:して|してね|してください|して下さい|お願い|お願いします)?$"
)


def parse_reminder_command(text: str, now: datetime | None = None) -> dict | None:
    """相対時間または今日/明日/明後日の時刻から予定・リマインダーを解析する。"""
    raw = str(text or "").strip()
    if not raw:
        return None
    direct_notice = bool(re.search(r"(?:起こして|知らせて|思い出させて|教えて)", raw))
    if not _COMMAND_WORDS.search(raw) and not direct_notice:
        return None

    current = now or datetime.now().astimezone()

    relative = _RELATIVE.search(raw)
    if relative:
        amount = int(relative.group("num"))
        unit = relative.group("unit")
        delta = {
            "秒": timedelta(seconds=amount),
            "分": timedelta(minutes=amount),
            "時間": timedelta(hours=amount),
            "時": timedelta(hours=amount),
            "日": timedelta(days=amount),
        }[unit]
        due = current + delta
        text_part = _extract_text(raw, relative.span())
        if text_part:
            return {"text": text_part, "due_at": due.isoformat(timespec="seconds")}
        direct_label = _default_direct_notice_text(raw)
        if direct_label:
            return {"text": direct_label, "due_at": due.isoformat(timespec="seconds")}
        return None

    clock = _CLOCK.search(raw)
    if not clock:
        return None

    hour = int(clock.group("hour"))
    minute = int(clock.group("minute") or 0)
    ampm = clock.group("ampm")
    if ampm == "午前" and hour == 12:
        hour = 0
    elif ampm == "午後" and hour < 12:
        hour += 12
    if hour > 23 or minute > 59:
        return None

    day_match = _DAY_WORDS.search(raw)
    day_name = day_match.group("day") if day_match else "今日"
    day_offset = {"今日": 0, "明日": 1, "明後日": 2}[day_name]

    due = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
    due += timedelta(days=day_offset)
    if day_offset == 0 and due <= current:
        due += timedelta(days=1)

    text_part = _extract_text(raw, clock.span())
    if text_part:
        return {"text": text_part, "due_at": due.isoformat(timespec="seconds")}
    direct_label = _default_direct_notice_text(raw)
    if direct_label:
        return {"text": direct_label, "due_at": due.isoformat(timespec="seconds")}
    return None


def _default_direct_notice_text(raw: str) -> str | None:
    compact = str(raw).replace(" ", "").replace("　", "")
    if "起こして" in compact:
        return "起床"
    if "知らせて" in compact:
        return "通知"
    if "思い出させて" in compact:
        return "リマインド"
    if "教えて" in compact:
        return "通知"
    return None


def _extract_text(raw: str, time_span: tuple[int, int]) -> str:
    before = raw[: time_span[0]]
    after = raw[time_span[1] :]
    text = after or before
    text = _DAY_WORDS.sub("", text)
    text = _COMMAND_WORDS.sub("", text)
    text = text.replace("予定", "")
    text = _TRAILING_COMMAND.sub("", text)
    text = re.sub(r"^[、。！？?\s]+", "", text)
    text = re.sub(r"^(?:に|へ|を|の|って)\s*", "", text)
    text = re.sub(r"[、。！？?\s]+$", "", text)
    return text.strip(" 、。！？?")

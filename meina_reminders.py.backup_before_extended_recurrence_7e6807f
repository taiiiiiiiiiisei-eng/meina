"""めいなのローカル・リマインダー管理。外部サービスを使わずJSONへ保存する。"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

REMINDER_PATH = Path(__file__).with_name("meina_reminders.json")


def _load() -> list[dict[str, Any]]:
    if not REMINDER_PATH.exists():
        return []
    try:
        data = json.loads(REMINDER_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _save(items: list[dict[str, Any]]) -> None:
    REMINDER_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def format_reminder_due(due_at: str, now: datetime | None = None) -> str:
    """予定日時を音声で読みやすい日本語へ整形する。"""
    raw = str(due_at or "").strip()
    try:
        due = datetime.fromisoformat(raw)
    except (TypeError, ValueError):
        return raw or "日時不明"

    current = now or datetime.now().astimezone()
    if due.tzinfo is None and current.tzinfo is not None:
        due = due.replace(tzinfo=current.tzinfo)
    elif due.tzinfo is not None and current.tzinfo is not None:
        due = due.astimezone(current.tzinfo)

    if due.date() == current.date():
        date_text = "今日"
    elif due.date() == (current + timedelta(days=1)).date():
        date_text = "明日"
    elif due.year == current.year:
        date_text = f"{due.month}月{due.day}日"
    else:
        date_text = f"{due.year}年{due.month}月{due.day}日"

    if due.minute:
        time_text = f"{due.hour}時{due.minute}分"
    else:
        time_text = f"{due.hour}時"
    return f"{date_text}{time_text}"


_WEEKDAYS_JA = ("月", "火", "水", "木", "金", "土", "日")
_VALID_REPEAT_RULES = {None, "daily", "weekly"}


def format_reminder_repeat(item: dict[str, Any]) -> str:
    """繰り返し設定を読み上げやすい日本語へ整形する。"""
    rule = item.get("repeat_rule")
    if rule == "daily":
        return "毎日"
    if rule == "weekly":
        try:
            due = datetime.fromisoformat(str(item.get("due_at", "")))
            return f"毎週{_WEEKDAYS_JA[due.weekday()]}曜"
        except (TypeError, ValueError):
            return "毎週"
    return ""


def _normalize_repeat_rule(value: Any) -> str | None:
    rule = str(value or "").strip().lower() or None
    if rule not in _VALID_REPEAT_RULES:
        raise ValueError(f"unsupported repeat_rule: {value}")
    return rule


def add_reminder(
    text: str,
    due_at: str,
    repeat_rule: str | None = None,
) -> dict[str, Any]:
    due = datetime.fromisoformat(due_at)
    repeat = _normalize_repeat_rule(repeat_rule)
    item = {
        "id": f"r-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "text": str(text).strip(),
        "due_at": due.isoformat(timespec="seconds"),
        "done": False,
    }
    if repeat:
        item["repeat_rule"] = repeat
    items = _load()
    items.append(item)
    _save(items)
    return item


def list_reminders(include_done: bool = False) -> list[dict[str, Any]]:
    items = _load()
    if include_done:
        return items
    return [item for item in items if not item.get("done")]


def _normalize_reminder_text(value: Any) -> str:
    """音声認識で混ざりやすい空白を無視して比較用文字列へ正規化する。"""
    return re.sub(r"[\s　]+", "", str(value or "")).casefold()


def find_reminders(query: str) -> list[dict[str, Any]]:
    """完全一致を優先し、なければ部分一致する未完了リマインダーを返す。"""
    needle = _normalize_reminder_text(query)
    if not needle:
        return []

    items = list_reminders()
    exact = [
        item
        for item in items
        if _normalize_reminder_text(item.get("text", "")) == needle
    ]
    if exact:
        return exact

    return [
        item
        for item in items
        if needle in _normalize_reminder_text(item.get("text", ""))
    ]


def filter_reminders_by_due(
    items: list[dict[str, Any]],
    *,
    date: str | None = None,
    hour: int | None = None,
    minute: int | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """候補を日付・時刻で安全に絞り込む。日時指定なしならそのまま返す。"""
    if date is None and hour is None and minute is None:
        return list(items)

    current = now or datetime.now().astimezone()
    result: list[dict[str, Any]] = []
    for item in items:
        try:
            due = datetime.fromisoformat(str(item["due_at"]))
            if due.tzinfo is None and current.tzinfo is not None:
                due = due.replace(tzinfo=current.tzinfo)
            elif due.tzinfo is not None and current.tzinfo is not None:
                due = due.astimezone(current.tzinfo)
        except (KeyError, TypeError, ValueError):
            continue

        if date is not None and due.date().isoformat() != str(date):
            continue
        if hour is not None and due.hour != int(hour):
            continue
        if minute is not None and due.minute != int(minute):
            continue
        result.append(item)

    return result


def _date_reminders(target_date, current: datetime) -> list[dict[str, Any]]:
    result = []
    for item in list_reminders():
        try:
            due = datetime.fromisoformat(str(item["due_at"])).astimezone(current.tzinfo)
            if due.date() == target_date:
                result.append(item)
        except (KeyError, TypeError, ValueError):
            continue
    result.sort(key=lambda item: str(item.get("due_at", "")))
    return result


def today_reminders(now: datetime | None = None) -> list[dict[str, Any]]:
    current = now or datetime.now().astimezone()
    return _date_reminders(current.date(), current)


def tomorrow_reminders(now: datetime | None = None) -> list[dict[str, Any]]:
    current = now or datetime.now().astimezone()
    return _date_reminders((current + timedelta(days=1)).date(), current)


def upcoming_reminders(days: int = 7, now: datetime | None = None) -> list[dict[str, Any]]:
    """現在から指定日数以内の未完了予定を時刻順で返す。"""
    current = now or datetime.now().astimezone()
    end = current + timedelta(days=max(1, int(days)))
    result = []
    for item in list_reminders():
        try:
            due = datetime.fromisoformat(str(item["due_at"])).astimezone(current.tzinfo)
            if current <= due <= end:
                result.append(item)
        except (KeyError, TypeError, ValueError):
            continue
    result.sort(key=lambda item: str(item.get("due_at", "")))
    return result


def due_reminders(now: datetime | None = None) -> list[dict[str, Any]]:
    current = now or datetime.now().astimezone()
    result = []
    for item in list_reminders():
        try:
            due = datetime.fromisoformat(str(item["due_at"]))
            if due <= current:
                result.append(item)
        except (KeyError, TypeError, ValueError):
            continue
    return result


def reschedule_reminder(reminder_id: str, due_at: str) -> dict[str, Any] | None:
    """IDが一致する未完了リマインダーの日時だけを更新する。"""
    try:
        due = datetime.fromisoformat(str(due_at))
    except (TypeError, ValueError):
        return None

    items = _load()
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue
        item["due_at"] = due.isoformat(timespec="seconds")
        _save(items)
        return item
    return None


def rename_reminder(reminder_id: str, new_text: str) -> dict[str, Any] | None:
    """IDが一致する未完了リマインダーの名前だけを更新する。"""
    name = str(new_text or "").strip()
    if not name or any(ord(char) < 32 for char in name):
        return None

    items = _load()
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue
        item["text"] = name
        _save(items)
        return item
    return None



def advance_recurring_reminder(
    reminder_id: str,
    now: datetime | None = None,
) -> dict[str, Any] | None:
    """繰り返し予定を次回へ進める。遅延時は現在時刻より後まで繰り越す。"""
    current = now or datetime.now().astimezone()
    items = _load()
    for item in items:
        if item.get("id") != reminder_id or item.get("done"):
            continue

        rule = item.get("repeat_rule")
        if rule not in ("daily", "weekly"):
            return None

        try:
            due = datetime.fromisoformat(str(item.get("due_at", "")))
        except (TypeError, ValueError):
            return None

        if due.tzinfo is None and current.tzinfo is not None:
            due = due.replace(tzinfo=current.tzinfo)
        elif due.tzinfo is not None and current.tzinfo is not None:
            due = due.astimezone(current.tzinfo)

        step = timedelta(days=1 if rule == "daily" else 7)
        due += step
        while due <= current:
            due += step

        item["due_at"] = due.isoformat(timespec="seconds")
        item["done"] = False
        _save(items)
        return item
    return None


def complete_reminder(
    reminder_id: str,
    now: datetime | None = None,
) -> bool:
    """通常予定は完了、繰り返し予定は次回へ進める。"""
    items = _load()
    for item in items:
        if item.get("id") != reminder_id:
            continue
        if item.get("repeat_rule") in ("daily", "weekly") and not item.get("done"):
            return (
                advance_recurring_reminder(reminder_id, now=now) is not None
            )
        item["done"] = True
        _save(items)
        return True
    return False


def delete_reminder(reminder_id: str) -> bool:
    items = _load()
    remaining = [item for item in items if item.get("id") != reminder_id]
    if len(remaining) == len(items):
        return False
    _save(remaining)
    return True

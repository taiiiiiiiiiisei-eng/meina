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


def add_reminder(text: str, due_at: str) -> dict[str, Any]:
    due = datetime.fromisoformat(due_at)
    item = {
        "id": f"r-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "text": str(text).strip(),
        "due_at": due.isoformat(timespec="seconds"),
        "done": False,
    }
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


def complete_reminder(reminder_id: str) -> bool:
    items = _load()
    changed = False
    for item in items:
        if item.get("id") == reminder_id:
            item["done"] = True
            changed = True
            break
    if changed:
        _save(items)
    return changed


def delete_reminder(reminder_id: str) -> bool:
    items = _load()
    remaining = [item for item in items if item.get("id") != reminder_id]
    if len(remaining) == len(items):
        return False
    _save(remaining)
    return True

"""めいなのローカル・リマインダー管理。外部サービスを使わずJSONへ保存する。"""
from __future__ import annotations

import json
from datetime import datetime
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


def find_reminders(query: str) -> list[dict[str, Any]]:
    """内容にqueryを含む未完了リマインダーだけ返す。"""
    needle = str(query or "").strip().lower()
    if not needle:
        return []
    return [
        item for item in list_reminders()
        if needle in str(item.get("text", "")).lower()
    ]


def today_reminders(now: datetime | None = None) -> list[dict[str, Any]]:
    current = now or datetime.now().astimezone()
    result = []
    for item in list_reminders():
        try:
            due = datetime.fromisoformat(str(item["due_at"])).astimezone(current.tzinfo)
            if due.date() == current.date():
                result.append(item)
        except (KeyError, TypeError, ValueError):
            continue
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

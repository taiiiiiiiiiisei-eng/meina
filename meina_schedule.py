"""めいなの予定管理。リマインダーを予定表として安全に扱う薄い層。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from meina_reminders import add_reminder, delete_reminder, find_reminders, list_reminders


def add_schedule(text: str, due_at: str) -> dict[str, Any]:
    return add_reminder(text, due_at)


def today_schedule(now: datetime | None = None) -> list[dict[str, Any]]:
    from meina_reminders import today_reminders
    return today_reminders(now)


def tomorrow_schedule(now: datetime | None = None) -> list[dict[str, Any]]:
    from meina_reminders import tomorrow_reminders
    return tomorrow_reminders(now)


def search_schedule(query: str) -> list[dict[str, Any]]:
    return find_reminders(query)


def remove_schedule(reminder_id: str) -> bool:
    return delete_reminder(reminder_id)


def pending_schedule(limit: int = 20) -> list[dict[str, Any]]:
    return list_reminders()[: max(1, int(limit))]

"""めいなリマインダーの依存関係なしセルフテスト。"""
from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

import meina_reminders


def main() -> int:
    original = meina_reminders.REMINDER_PATH
    with tempfile.TemporaryDirectory() as tmp:
        meina_reminders.REMINDER_PATH = Path(tmp) / "reminders.json"
        item = meina_reminders.add_reminder(
            "テストする",
            "2030-01-01T10:00:00+09:00",
        )
        assert item["done"] is False
        assert meina_reminders.list_reminders()[0]["text"] == "テストする"
        due = meina_reminders.due_reminders(
            datetime.fromisoformat("2030-01-01T11:00:00+09:00")
        )
        assert len(due) == 1
        assert meina_reminders.complete_reminder(item["id"])
        assert meina_reminders.list_reminders() == []
    meina_reminders.REMINDER_PATH = original
    print("Reminder self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

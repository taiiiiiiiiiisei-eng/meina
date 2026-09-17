"""めいなのリマインダー解析・保存の依存関係なしセルフテスト。"""
from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import meina_reminder_parser
import meina_reminders


def main() -> int:
    now = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)

    parsed = meina_reminder_parser.parse_reminder_command(
        "10分後に宿題をリマインドして",
        now,
    )
    assert parsed is not None
    assert parsed["text"] == "宿題を"
    assert parsed["due_at"].startswith("2026-09-12T10:10:00")

    parsed_clock = meina_reminder_parser.parse_reminder_command(
        "18時に配信をリマインドして",
        now,
    )
    assert parsed_clock is not None
    assert parsed_clock["text"] == "配信を"

    original = meina_reminders.REMINDER_PATH
    try:
        with tempfile.TemporaryDirectory() as tmp:
            meina_reminders.REMINDER_PATH = Path(tmp) / "reminders.json"
            item = meina_reminders.add_reminder("宿題", "2026-09-12T10:00:00+00:00")
            assert meina_reminders.due_reminders(now)
            assert meina_reminders.complete_reminder(item["id"])
            assert not meina_reminders.due_reminders(now)
    finally:
        meina_reminders.REMINDER_PATH = original

    print("Reminder self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

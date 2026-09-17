"""めいなリマインダーの依存関係なしセルフテスト。"""
from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import meina_reminder_parser
import meina_reminders
from command_router import route_command


def main() -> int:
    now = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)

    parsed = meina_reminder_parser.parse_reminder_command("10分後に宿題をリマインドして", now)
    assert parsed is not None
    assert parsed["text"] == "宿題を"
    assert parsed["due_at"].startswith("2026-09-12T10:10:00")

    parsed_clock = meina_reminder_parser.parse_reminder_command("18時に配信をリマインドして", now)
    assert parsed_clock is not None
    assert parsed_clock["text"] == "配信"

    parsed_tomorrow = meina_reminder_parser.parse_reminder_command("明日18時に配信予定を追加して", now)
    assert parsed_tomorrow is not None
    assert parsed_tomorrow["text"] == "配信"
    assert parsed_tomorrow["due_at"] == "2026-09-13T18:00:00+00:00"

    cases = {
        "10分後に宿題をリマインドして": ("reminder", "10分後に宿題をリマインドして"),
        "明日18時に配信予定を追加して": ("reminder", "明日18時に配信予定を追加して"),
        "リマインダー一覧を教えて": ("reminder_list", None),
        "今日の予定を教えて": ("reminder_today", None),
        "明日の予定を教えて": ("reminder_tomorrow", None),
        "リマインダーを完了して宿題": ("reminder_done", "リマインダーを完了して宿題"),
        "リマインダーを削除して宿題": ("reminder_delete", "リマインダーを削除して宿題"),
    }
    for text, (kind, expected_query) in cases.items():
        route = route_command(text, {"confidence": 0.10})
        assert route is not None
        assert route["kind"] == kind
        assert route["confidence"] == 1.0
        assert route["query"] == expected_query

    original = meina_reminders.REMINDER_PATH
    try:
        with tempfile.TemporaryDirectory() as tmp:
            meina_reminders.REMINDER_PATH = Path(tmp) / "reminders.json"
            item = meina_reminders.add_reminder("宿題をする", "2030-01-01T10:00:00+09:00")
            assert item["done"] is False
            assert meina_reminders.list_reminders()[0]["text"] == "宿題をする"
            assert meina_reminders.find_reminders("宿題")[0]["id"] == item["id"]
            assert len(meina_reminders.today_reminders(datetime.fromisoformat("2030-01-01T08:00:00+09:00"))) == 1
            assert len(meina_reminders.tomorrow_reminders(datetime.fromisoformat("2029-12-31T23:00:00+09:00"))) == 1
            due = meina_reminders.due_reminders(
                datetime.fromisoformat("2030-01-01T11:00:00+09:00")
            )
            assert len(due) == 1
            assert meina_reminders.complete_reminder(item["id"])
            assert meina_reminders.list_reminders() == []

            deleted = meina_reminders.add_reminder("削除テスト", "2030-01-02T10:00:00+09:00")
            assert meina_reminders.delete_reminder(deleted["id"])
            assert meina_reminders.list_reminders() == []
    finally:
        meina_reminders.REMINDER_PATH = original

    print("Reminder self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

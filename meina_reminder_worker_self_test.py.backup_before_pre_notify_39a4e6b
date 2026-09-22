"""リマインダー監視部品の依存関係なしセルフテスト。"""
from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

import meina_reminders
from meina_reminder_worker import (
    is_reminder_worker_running,
    process_due_reminders,
    start_reminder_worker,
    stop_reminder_worker,
)


def main() -> int:
    original = meina_reminders.REMINDER_PATH
    try:
        with tempfile.TemporaryDirectory() as tmp:
            meina_reminders.REMINDER_PATH = Path(tmp) / "reminders.json"
            now = datetime.fromisoformat("2030-01-05T12:00:00+09:00")

            one_shot = meina_reminders.add_reminder(
                "一回だけ",
                "2030-01-05T11:00:00+09:00",
            )
            daily = meina_reminders.add_reminder(
                "毎日の確認",
                "2030-01-05T10:00:00+09:00",
                repeat_rule="daily",
            )
            weekly = meina_reminders.add_reminder(
                "毎週の確認",
                "2030-01-05T09:00:00+09:00",
                repeat_rule="weekly",
            )
            weekdays = meina_reminders.add_reminder(
                "平日の確認",
                "2030-01-04T09:00:00+09:00",
                repeat_rule="weekdays",
            )
            monthly = meina_reminders.add_reminder(
                "月末の確認",
                "2029-12-31T09:00:00+09:00",
                repeat_rule="monthly",
                repeat_day=31,
            )
            paused = meina_reminders.add_reminder(
                "停止中の確認",
                "2030-01-05T08:00:00+09:00",
                repeat_rule="daily",
            )
            assert meina_reminders.pause_reminder(paused["id"]) is not None

            spoken: list[str] = []
            delivered = process_due_reminders(spoken.append, now=now)
            assert delivered == 5
            assert len(spoken) == 5
            assert any("一回だけ" in message for message in spoken)
            assert any("毎日の確認" in message for message in spoken)
            assert any("毎週の確認" in message for message in spoken)
            assert any("平日の確認" in message for message in spoken)
            assert any("月末の確認" in message for message in spoken)
            assert not any("停止中の確認" in message for message in spoken)

            all_items = meina_reminders.list_reminders(include_done=True)
            by_id = {item["id"]: item for item in all_items}
            assert by_id[one_shot["id"]]["done"] is True
            assert by_id[daily["id"]]["done"] is False
            assert by_id[daily["id"]]["due_at"] == "2030-01-06T10:00:00+09:00"
            assert by_id[weekly["id"]]["done"] is False
            assert by_id[weekly["id"]]["due_at"] == "2030-01-12T09:00:00+09:00"
            assert by_id[weekdays["id"]]["done"] is False
            assert by_id[weekdays["id"]]["due_at"] == "2030-01-07T09:00:00+09:00"
            assert by_id[monthly["id"]]["done"] is False
            assert by_id[monthly["id"]]["due_at"] == "2030-01-31T09:00:00+09:00"
            assert by_id[monthly["id"]]["repeat_day"] == 31

            # 同じ現在時刻でもう一度処理しても二重通知しない。
            assert process_due_reminders(spoken.append, now=now) == 0
            assert len(spoken) == 5

            resumed = meina_reminders.resume_reminder(
                paused["id"],
                now=now,
            )
            assert resumed is not None
            assert resumed["due_at"] == "2030-01-06T08:00:00+09:00"
            assert process_due_reminders(spoken.append, now=now) == 0

            assert is_reminder_worker_running() is False
            assert start_reminder_worker(spoken.append, interval_seconds=60.0) is True
            assert is_reminder_worker_running() is True
            assert start_reminder_worker(spoken.append, interval_seconds=60.0) is False
            assert stop_reminder_worker() is True
            assert is_reminder_worker_running() is False
    finally:
        meina_reminders.REMINDER_PATH = original

    print("Reminder worker self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

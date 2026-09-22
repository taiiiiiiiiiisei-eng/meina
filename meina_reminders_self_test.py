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

    parsed = meina_reminder_parser.parse_reminder_command(
        "10分後に宿題をリマインドして",
        now,
    )
    assert parsed is not None
    assert parsed["text"] == "宿題"
    assert parsed["due_at"] == "2026-09-12T10:10:00+00:00"

    parsed_clock = meina_reminder_parser.parse_reminder_command(
        "18時に配信をリマインドして",
        now,
    )
    assert parsed_clock is not None
    assert parsed_clock["text"] == "配信"
    assert parsed_clock["due_at"] == "2026-09-12T18:00:00+00:00"

    schedule_cases = (
        ("明日18時に配信予定を追加して", "配信", "2026-09-13T18:00:00+00:00"),
        ("明日18時に配信を追加して", "配信", "2026-09-13T18:00:00+00:00"),
        ("明後日20時に勉強予定を登録して", "勉強", "2026-09-14T20:00:00+00:00"),
        ("9月25日18時に配信予定を追加して", "配信", "2026-09-25T18:00:00+00:00"),
        ("2027年1月3日9時に初詣予定を追加して", "初詣", "2027-01-03T09:00:00+00:00"),
        ("午後6時に配信をリマインドして", "配信", "2026-09-12T18:00:00+00:00"),
    )
    for command, expected_text, expected_time in schedule_cases:
        parsed_schedule = meina_reminder_parser.parse_reminder_command(command, now)
        assert parsed_schedule is not None, command
        assert parsed_schedule["text"] == expected_text, command
        assert parsed_schedule["due_at"] == expected_time, command

    format_now = datetime.fromisoformat("2026-09-23T10:00:00+09:00")
    assert (
        meina_reminders.format_reminder_due(
            "2026-09-23T18:00:00+09:00",
            format_now,
        )
        == "今日18時"
    )
    assert (
        meina_reminders.format_reminder_due(
            "2026-09-24T20:30:00+09:00",
            format_now,
        )
        == "明日20時30分"
    )
    assert (
        meina_reminders.format_reminder_due(
            "2026-09-25T18:00:00+09:00",
            format_now,
        )
        == "9月25日18時"
    )
    assert (
        meina_reminders.format_reminder_due(
            "2027-01-03T09:05:00+09:00",
            format_now,
        )
        == "2027年1月3日9時5分"
    )
    assert (
        meina_reminders.format_reminder_due(
            "2026-09-23T09:00:00+00:00",
            format_now,
        )
        == "今日18時"
    )
    assert meina_reminders.format_reminder_due("not-a-date", format_now) == "not-a-date"
    assert meina_reminders.format_reminder_due("", format_now) == "日時不明"

    parsed_natural = meina_reminder_parser.parse_reminder_command("30分後に知らせて", now)
    assert parsed_natural is not None
    assert parsed_natural["text"] == "通知"

    parsed_wake = meina_reminder_parser.parse_reminder_command("18時に起こして", now)
    assert parsed_wake is not None
    assert parsed_wake["text"] == "起床"

    assert meina_reminder_parser.parse_reminder_command(
        "2月30日18時に配信予定を追加して",
        now,
    ) is None

    action_cases = (
        ("リマインダーを完了して宿題", "done", "宿題"),
        ("宿題のリマインダーを完了して", "done", "宿題"),
        ("リマインダーの宿題を済みにして", "done", "宿題"),
        ("宿題の予定終わった", "done", "宿題"),
        ("リマインダーを削除して宿題", "delete", "宿題"),
        ("宿題の予定を消して", "delete", "宿題"),
        ("リマインダーから宿題を削除して", "delete", "宿題"),
        ("宿題のスケジュールをキャンセルして", "delete", "宿題"),
        ("リマインダーを完了して", "done", ""),
        ("予定を消して", "delete", ""),
    )
    for command, action, expected_target in action_cases:
        assert (
            meina_reminder_parser.parse_reminder_action_target(command, action)
            == expected_target
        ), command

    # 質問文は変更命令として扱わず、誤って完了・削除しない。
    assert (
        meina_reminder_parser.parse_reminder_action_target(
            "宿題の予定終わった？",
            "done",
        )
        is None
    )
    assert (
        meina_reminder_parser.parse_reminder_action_target(
            "宿題の予定を消していい？",
            "delete",
        )
        is None
    )

    reschedule_cases = (
        (
            "宿題の予定を明日20時に変更して",
            "宿題",
            "2026-09-13T20:00:00+00:00",
        ),
        (
            "リマインダーの配信を午後6時に変えて",
            "配信",
            "2026-09-12T18:00:00+00:00",
        ),
        (
            "勉強の予定を30分後にずらして",
            "勉強",
            "2026-09-12T10:30:00+00:00",
        ),
        (
            "予定を明日20時に変更して",
            "",
            "2026-09-13T20:00:00+00:00",
        ),
    )
    for command, expected_target, expected_due in reschedule_cases:
        parsed_reschedule = meina_reminder_parser.parse_reminder_reschedule_command(
            command,
            now,
        )
        assert parsed_reschedule is not None, command
        assert parsed_reschedule["target"] == expected_target, command
        assert parsed_reschedule["due_at"] == expected_due, command

    assert (
        meina_reminder_parser.parse_reminder_reschedule_command(
            "宿題の予定を明日20時に変更していい？",
            now,
        )
        is None
    )
    assert (
        meina_reminder_parser.parse_reminder_reschedule_command(
            "宿題の予定を25時に変更して",
            now,
        )
        is None
    )

    rename_cases = (
        ("宿題の予定を数学の宿題に名前変更して", "宿題", "数学の宿題"),
        ("リマインダーの配信を夜配信に改名して", "配信", "夜配信"),
        ("勉強の予定名を資格勉強に変更して", "勉強", "資格勉強"),
        ("予定を数学の宿題に名前変更して", "", "数学の宿題"),
        ("宿題の予定を名前変更して", "宿題", ""),
    )
    for command, expected_target, expected_name in rename_cases:
        parsed_rename = meina_reminder_parser.parse_reminder_rename_command(
            command,
            now,
        )
        assert parsed_rename is not None, command
        assert parsed_rename["target"] == expected_target, command
        assert parsed_rename["new_name"] == expected_name, command

    assert (
        meina_reminder_parser.parse_reminder_rename_command(
            "宿題の予定を数学の宿題に名前変更していい？",
            now,
        )
        is None
    )

    cases = {
        "10分後に宿題をリマインドして": ("reminder", "10分後に宿題をリマインドして"),
        "明日18時に配信予定を追加して": ("reminder", "明日18時に配信予定を追加して"),
        "18時に起こして": ("reminder", "18時に起こして"),
        "30分後に知らせて": ("reminder", "30分後に知らせて"),
        "リマインダー一覧を教えて": ("reminder_list", None),
        "今日の予定を教えて": ("reminder_today", None),
        "明日の予定を教えて": ("reminder_tomorrow", None),
        "今後の予定を教えて": ("reminder_upcoming", None),
        "リマインダーを完了して宿題": ("reminder_done", "宿題"),
        "リマインダーを削除して宿題": ("reminder_delete", "宿題"),
        "宿題のリマインダーを完了して": ("reminder_done", "宿題"),
        "宿題の予定を消して": ("reminder_delete", "宿題"),
        "リマインダーから宿題を削除して": ("reminder_delete", "宿題"),
        "リマインダーを完了して": ("reminder_done", ""),
        "予定を消して": ("reminder_delete", ""),
    }
    for text, (kind, expected_query) in cases.items():
        route = route_command(text, {"confidence": 0.10})
        assert route is not None
        assert route["kind"] == kind
        assert route["confidence"] == 1.0
        assert route["query"] == expected_query

    reschedule_route = route_command(
        "宿題の予定を明日20時に変更して",
        {"confidence": 0.10},
    )
    assert reschedule_route is not None
    assert reschedule_route["kind"] == "reminder_reschedule"
    assert reschedule_route["confidence"] == 1.0
    assert reschedule_route["query"]["target"] == "宿題"
    assert "T20:00:00" in reschedule_route["query"]["due_at"]

    rename_route = route_command(
        "宿題の予定を数学の宿題に名前変更して",
        {"confidence": 0.10},
    )
    assert rename_route is not None
    assert rename_route["kind"] == "reminder_rename"
    assert rename_route["confidence"] == 1.0
    assert rename_route["query"] == {
        "target": "宿題",
        "new_name": "数学の宿題",
    }

    original = meina_reminders.REMINDER_PATH
    try:
        with tempfile.TemporaryDirectory() as tmp:
            meina_reminders.REMINDER_PATH = Path(tmp) / "reminders.json"

            item = meina_reminders.add_reminder(
                "宿題をする",
                "2030-01-01T10:00:00+09:00",
            )
            assert item["done"] is False
            assert meina_reminders.list_reminders()[0]["text"] == "宿題をする"
            assert meina_reminders.find_reminders("宿題")[0]["id"] == item["id"]
            assert len(
                meina_reminders.today_reminders(
                    datetime.fromisoformat("2030-01-01T08:00:00+09:00")
                )
            ) == 1
            assert len(
                meina_reminders.tomorrow_reminders(
                    datetime.fromisoformat("2029-12-31T23:00:00+09:00")
                )
            ) == 1
            assert len(
                meina_reminders.upcoming_reminders(
                    7,
                    datetime.fromisoformat("2029-12-30T08:00:00+09:00"),
                )
            ) == 1

            due = meina_reminders.due_reminders(
                datetime.fromisoformat("2030-01-01T11:00:00+09:00")
            )
            assert len(due) == 1
            assert meina_reminders.complete_reminder(item["id"])
            assert meina_reminders.list_reminders() == []

            deleted = meina_reminders.add_reminder(
                "削除テスト",
                "2030-01-02T10:00:00+09:00",
            )
            assert meina_reminders.delete_reminder(deleted["id"])
            assert meina_reminders.list_reminders() == []

            exact = meina_reminders.add_reminder(
                "宿題",
                "2030-01-03T10:00:00+09:00",
            )
            partial = meina_reminders.add_reminder(
                "数学の宿題",
                "2030-01-03T11:00:00+09:00",
            )

            exact_matches = meina_reminders.find_reminders("宿題")
            assert [item["id"] for item in exact_matches] == [exact["id"]]
            assert meina_reminders.find_reminders("宿 題")[0]["id"] == exact["id"]
            assert meina_reminders.find_reminders("数学")[0]["id"] == partial["id"]

            duplicate = meina_reminders.add_reminder(
                "宿題",
                "2030-01-03T12:00:00+09:00",
            )
            duplicate_matches = meina_reminders.find_reminders("宿題")
            duplicate_ids = {item["id"] for item in duplicate_matches}
            assert duplicate_ids == {exact["id"], duplicate["id"]}
            assert partial["id"] not in duplicate_ids

            rescheduled = meina_reminders.add_reminder(
                "配信準備",
                "2030-01-04T18:00:00+09:00",
            )
            updated = meina_reminders.reschedule_reminder(
                rescheduled["id"],
                "2030-01-04T20:30:00+09:00",
            )
            assert updated is not None
            assert updated["id"] == rescheduled["id"]
            assert updated["text"] == "配信準備"
            assert updated["due_at"] == "2030-01-04T20:30:00+09:00"

            assert (
                meina_reminders.reschedule_reminder(
                    "missing-id",
                    "2030-01-04T21:00:00+09:00",
                )
                is None
            )
            assert (
                meina_reminders.reschedule_reminder(
                    rescheduled["id"],
                    "not-a-date",
                )
                is None
            )

            renamed = meina_reminders.rename_reminder(
                rescheduled["id"],
                "夜の配信準備",
            )
            assert renamed is not None
            assert renamed["id"] == rescheduled["id"]
            assert renamed["text"] == "夜の配信準備"
            assert renamed["due_at"] == "2030-01-04T20:30:00+09:00"
            assert meina_reminders.rename_reminder(rescheduled["id"], "") is None
            assert (
                meina_reminders.rename_reminder(
                    "missing-id",
                    "見つからない予定",
                )
                is None
            )
    finally:
        meina_reminders.REMINDER_PATH = original

    print("Reminder self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

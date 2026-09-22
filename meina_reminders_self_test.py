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

    recurring_cases = (
        (
            "毎日18時に薬をリマインドして",
            "薬",
            "2026-09-12T18:00:00+00:00",
            "daily",
        ),
        (
            "平日18時に宿題をリマインドして",
            "宿題",
            "2026-09-14T18:00:00+00:00",
            "weekdays",
        ),
        (
            "毎週土曜18時に配信予定を追加して",
            "配信",
            "2026-09-12T18:00:00+00:00",
            "weekly",
        ),
        (
            "毎週月曜日9時に学校の予定を追加して",
            "学校",
            "2026-09-14T09:00:00+00:00",
            "weekly",
        ),
        (
            "毎月31日18時に月末処理予定を追加して",
            "月末処理",
            "2026-09-30T18:00:00+00:00",
            "monthly",
        ),
    )
    for command, expected_text, expected_due, expected_repeat in recurring_cases:
        parsed_repeat = meina_reminder_parser.parse_reminder_command(command, now)
        assert parsed_repeat is not None, command
        assert parsed_repeat["text"] == expected_text, command
        assert parsed_repeat["due_at"] == expected_due, command
        assert parsed_repeat["repeat_rule"] == expected_repeat, command
        if expected_repeat == "monthly":
            assert parsed_repeat["repeat_day"] == 31, command

    late_saturday = datetime(2026, 9, 12, 20, 0, tzinfo=timezone.utc)
    parsed_next_week = meina_reminder_parser.parse_reminder_command(
        "毎週土曜18時に配信予定を追加して",
        late_saturday,
    )
    assert parsed_next_week is not None
    assert parsed_next_week["due_at"] == "2026-09-19T18:00:00+00:00"
    assert parsed_next_week["repeat_rule"] == "weekly"

    assert (
        meina_reminder_parser.parse_reminder_command(
            "毎月32日18時に無効予定を追加して",
            now,
        )
        is None
    )

    friday = datetime(2030, 1, 4, 10, 0, tzinfo=timezone.utc)
    friday_weekday = meina_reminder_parser.parse_reminder_command(
        "平日18時に勉強をリマインドして",
        friday,
    )
    assert friday_weekday is not None
    assert friday_weekday["due_at"] == "2030-01-04T18:00:00+00:00"

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

    due_action_cases = (
        (
            "18時の宿題を完了して",
            "done",
            "宿題",
            None,
            18,
            0,
        ),
        (
            "明日の宿題を削除して",
            "delete",
            "宿題",
            "2026-09-13",
            None,
            None,
        ),
        (
            "明日18時の宿題の予定を完了して",
            "done",
            "宿題",
            "2026-09-13",
            18,
            0,
        ),
        (
            "9月25日の宿題を削除して",
            "delete",
            "宿題",
            "2026-09-25",
            None,
            None,
        ),
        (
            "午後6時の配信を完了して",
            "done",
            "配信",
            None,
            18,
            0,
        ),
    )
    for command, action, target, date_value, hour, minute in due_action_cases:
        request = meina_reminder_parser.parse_reminder_action_request(
            command,
            action,
            now,
        )
        assert request is not None, command
        assert request["target"] == target, command
        assert request["date"] == date_value, command
        assert request["hour"] == hour, command
        assert request["minute"] == minute, command

    assert (
        meina_reminder_parser.parse_reminder_action_request(
            "18時の宿題を完了していい？",
            "done",
            now,
        )
        is None
    )
    assert (
        meina_reminder_parser.parse_reminder_action_request(
            "宿題を完了して",
            "done",
            now,
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

    selected_reschedule = meina_reminder_parser.parse_reminder_reschedule_command(
        "18時の宿題の予定を明日20時に変更して",
        now,
    )
    assert selected_reschedule is not None
    assert selected_reschedule["target"] == "宿題"
    assert selected_reschedule["hour"] == 18
    assert selected_reschedule["minute"] == 0
    assert selected_reschedule["date"] is None
    assert selected_reschedule["due_at"] == "2026-09-13T20:00:00+00:00"

    dated_reschedule = meina_reminder_parser.parse_reminder_reschedule_command(
        "明日の宿題の予定を明後日21時に変更して",
        now,
    )
    assert dated_reschedule is not None
    assert dated_reschedule["target"] == "宿題"
    assert dated_reschedule["date"] == "2026-09-13"
    assert dated_reschedule["hour"] is None
    assert dated_reschedule["due_at"] == "2026-09-14T21:00:00+00:00"

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

    clear_repeat = meina_reminder_parser.parse_reminder_repeat_clear_command(
        "薬の繰り返しを停止して",
        now,
    )
    assert clear_repeat is not None
    assert clear_repeat["target"] == "薬"
    assert clear_repeat["date"] is None
    assert clear_repeat["hour"] is None

    clear_repeat_at_time = meina_reminder_parser.parse_reminder_repeat_clear_command(
        "18時の薬の予定の繰り返しを解除して",
        now,
    )
    assert clear_repeat_at_time is not None
    assert clear_repeat_at_time["target"] == "薬"
    assert clear_repeat_at_time["hour"] == 18
    assert clear_repeat_at_time["minute"] == 0

    assert (
        meina_reminder_parser.parse_reminder_repeat_clear_command(
            "薬の繰り返しを停止していい？",
            now,
        )
        is None
    )

    pause_command = meina_reminder_parser.parse_reminder_pause_command(
        "薬の予定を一時停止して",
        now,
    )
    assert pause_command is not None
    assert pause_command["target"] == "薬"
    assert pause_command["date"] is None
    assert pause_command["hour"] is None

    pause_at_time = meina_reminder_parser.parse_reminder_pause_command(
        "18時の薬の予定を一時停止して",
        now,
    )
    assert pause_at_time is not None
    assert pause_at_time["target"] == "薬"
    assert pause_at_time["hour"] == 18

    resume_command = meina_reminder_parser.parse_reminder_resume_command(
        "薬のリマインダーを再開して",
        now,
    )
    assert resume_command is not None
    assert resume_command["target"] == "薬"

    assert (
        meina_reminder_parser.parse_reminder_pause_command(
            "薬の予定を一時停止していい？",
            now,
        )
        is None
    )
    assert (
        meina_reminder_parser.parse_reminder_resume_command(
            "薬のリマインダーを再開していい？",
            now,
        )
        is None
    )

    repeat_change_cases = (
        (
            "薬の繰り返しを平日に変更して",
            "薬",
            "weekdays",
            None,
            None,
            None,
        ),
        (
            "18時の薬の予定の繰り返しを毎週土曜に変更して",
            "薬",
            "weekly",
            5,
            18,
            None,
        ),
        (
            "支払いの定期設定を毎月15日に変えて",
            "支払い",
            "monthly",
            None,
            None,
            15,
        ),
        (
            "宿題を毎日の繰り返しにして",
            "宿題",
            "daily",
            None,
            None,
            None,
        ),
    )
    for command, target, rule, weekday, hour, day in repeat_change_cases:
        changed_repeat = meina_reminder_parser.parse_reminder_repeat_change_command(
            command,
            now,
        )
        assert changed_repeat is not None, command
        assert changed_repeat["target"] == target, command
        assert changed_repeat["repeat_rule"] == rule, command
        assert changed_repeat["repeat_weekday"] == weekday, command
        assert changed_repeat["hour"] == hour, command
        assert changed_repeat["repeat_day"] == day, command

    assert (
        meina_reminder_parser.parse_reminder_repeat_change_command(
            "薬の繰り返しを平日に変更していい？",
            now,
        )
        is None
    )
    assert (
        meina_reminder_parser.parse_reminder_repeat_change_command(
            "薬の繰り返しを毎月32日に変更して",
            now,
        )
        is None
    )

    selected_rename = meina_reminder_parser.parse_reminder_rename_command(
        "18時の宿題の予定名を数学の宿題に変更して",
        now,
    )
    assert selected_rename is not None
    assert selected_rename["target"] == "宿題"
    assert selected_rename["new_name"] == "数学の宿題"
    assert selected_rename["hour"] == 18
    assert selected_rename["minute"] == 0
    assert selected_rename["date"] is None

    dated_rename = meina_reminder_parser.parse_reminder_rename_command(
        "明日の宿題の予定を英語の宿題に名前変更して",
        now,
    )
    assert dated_rename is not None
    assert dated_rename["target"] == "宿題"
    assert dated_rename["new_name"] == "英語の宿題"
    assert dated_rename["date"] == "2026-09-13"
    assert dated_rename["hour"] is None

    cases = {
        "10分後に宿題をリマインドして": ("reminder", "10分後に宿題をリマインドして"),
        "明日18時に配信予定を追加して": ("reminder", "明日18時に配信予定を追加して"),
        "18時に起こして": ("reminder", "18時に起こして"),
        "30分後に知らせて": ("reminder", "30分後に知らせて"),
        "毎日18時に薬をリマインドして": ("reminder", "毎日18時に薬をリマインドして"),
        "毎週土曜18時に配信予定を追加して": ("reminder", "毎週土曜18時に配信予定を追加して"),
        "平日18時に宿題をリマインドして": ("reminder", "平日18時に宿題をリマインドして"),
        "毎月15日18時に支払い予定を追加して": ("reminder", "毎月15日18時に支払い予定を追加して"),
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
    assert rename_route["query"]["target"] == "宿題"
    assert rename_route["query"]["new_name"] == "数学の宿題"
    assert rename_route["query"]["date"] is None
    assert rename_route["query"]["hour"] is None
    assert rename_route["query"]["minute"] is None

    pause_route = route_command(
        "薬の予定を一時停止して",
        {"confidence": 0.10},
    )
    assert pause_route is not None
    assert pause_route["kind"] == "reminder_pause"
    assert pause_route["confidence"] == 1.0
    assert pause_route["query"]["target"] == "薬"

    resume_route = route_command(
        "薬のリマインダーを再開して",
        {"confidence": 0.10},
    )
    assert resume_route is not None
    assert resume_route["kind"] == "reminder_resume"
    assert resume_route["confidence"] == 1.0
    assert resume_route["query"]["target"] == "薬"

    pause_at_time_route = route_command(
        "18時の薬の予定を一時停止して",
        {"confidence": 0.10},
    )
    assert pause_at_time_route is not None
    assert pause_at_time_route["kind"] == "reminder_pause"
    assert pause_at_time_route["query"]["hour"] == 18

    repeat_change_route = route_command(
        "薬の繰り返しを平日に変更して",
        {"confidence": 0.10},
    )
    assert repeat_change_route is not None
    assert repeat_change_route["kind"] == "reminder_repeat_set"
    assert repeat_change_route["confidence"] == 1.0
    assert repeat_change_route["query"]["target"] == "薬"
    assert repeat_change_route["query"]["repeat_rule"] == "weekdays"

    repeat_change_weekly_route = route_command(
        "18時の薬の予定の繰り返しを毎週土曜に変更して",
        {"confidence": 0.10},
    )
    assert repeat_change_weekly_route is not None
    assert repeat_change_weekly_route["kind"] == "reminder_repeat_set"
    assert repeat_change_weekly_route["query"]["target"] == "薬"
    assert repeat_change_weekly_route["query"]["hour"] == 18
    assert repeat_change_weekly_route["query"]["repeat_weekday"] == 5

    repeat_clear_route = route_command(
        "薬の繰り返しを停止して",
        {"confidence": 0.10},
    )
    assert repeat_clear_route is not None
    assert repeat_clear_route["kind"] == "reminder_repeat_clear"
    assert repeat_clear_route["confidence"] == 1.0
    assert repeat_clear_route["query"]["target"] == "薬"

    repeat_clear_at_time_route = route_command(
        "18時の薬の予定の繰り返しを解除して",
        {"confidence": 0.10},
    )
    assert repeat_clear_at_time_route is not None
    assert repeat_clear_at_time_route["kind"] == "reminder_repeat_clear"
    assert repeat_clear_at_time_route["query"]["target"] == "薬"
    assert repeat_clear_at_time_route["query"]["hour"] == 18

    selected_reschedule_route = route_command(
        "18時の宿題の予定を明日20時に変更して",
        {"confidence": 0.10},
    )
    assert selected_reschedule_route is not None
    assert selected_reschedule_route["kind"] == "reminder_reschedule"
    assert selected_reschedule_route["query"]["target"] == "宿題"
    assert selected_reschedule_route["query"]["hour"] == 18
    assert selected_reschedule_route["query"]["minute"] == 0
    assert "T20:00:00" in selected_reschedule_route["query"]["due_at"]

    selected_rename_route = route_command(
        "18時の宿題の予定名を数学の宿題に変更して",
        {"confidence": 0.10},
    )
    assert selected_rename_route is not None
    assert selected_rename_route["kind"] == "reminder_rename"
    assert selected_rename_route["query"]["target"] == "宿題"
    assert selected_rename_route["query"]["new_name"] == "数学の宿題"
    assert selected_rename_route["query"]["hour"] == 18
    assert selected_rename_route["query"]["minute"] == 0

    due_done_route = route_command(
        "18時の宿題を完了して",
        {"confidence": 0.10},
    )
    assert due_done_route is not None
    assert due_done_route["kind"] == "reminder_done"
    assert due_done_route["confidence"] == 1.0
    assert due_done_route["query"]["target"] == "宿題"
    assert due_done_route["query"]["hour"] == 18
    assert due_done_route["query"]["minute"] == 0

    due_delete_route = route_command(
        "明日の宿題を削除して",
        {"confidence": 0.10},
    )
    assert due_delete_route is not None
    assert due_delete_route["kind"] == "reminder_delete"
    assert due_delete_route["confidence"] == 1.0
    assert due_delete_route["query"]["target"] == "宿題"
    assert due_delete_route["query"]["date"] is not None

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

            first_same_name = meina_reminders.add_reminder(
                "英語",
                "2030-01-05T18:00:00+09:00",
            )
            second_same_name = meina_reminders.add_reminder(
                "英語",
                "2030-01-05T20:00:00+09:00",
            )
            english_matches = meina_reminders.find_reminders("英語")
            assert {item["id"] for item in english_matches} == {
                first_same_name["id"],
                second_same_name["id"],
            }

            at_18 = meina_reminders.filter_reminders_by_due(
                english_matches,
                hour=18,
                minute=0,
                now=datetime.fromisoformat("2030-01-05T12:00:00+09:00"),
            )
            assert [item["id"] for item in at_18] == [first_same_name["id"]]

            on_date = meina_reminders.filter_reminders_by_due(
                english_matches,
                date="2030-01-05",
                now=datetime.fromisoformat("2030-01-05T12:00:00+09:00"),
            )
            assert {item["id"] for item in on_date} == {
                first_same_name["id"],
                second_same_name["id"],
            }

            no_match = meina_reminders.filter_reminders_by_due(
                english_matches,
                hour=19,
                minute=0,
                now=datetime.fromisoformat("2030-01-05T12:00:00+09:00"),
            )
            assert no_match == []


            daily = meina_reminders.add_reminder(
                "薬",
                "2030-01-05T18:00:00+09:00",
                repeat_rule="daily",
            )
            assert daily["repeat_rule"] == "daily"
            assert meina_reminders.format_reminder_repeat(daily) == "毎日"
            assert meina_reminders.complete_reminder(
                daily["id"],
                now=datetime.fromisoformat("2030-01-05T18:01:00+09:00"),
            )
            daily_after = meina_reminders.find_reminders("薬")
            assert len(daily_after) == 1
            assert daily_after[0]["done"] is False
            assert daily_after[0]["due_at"] == "2030-01-06T18:00:00+09:00"

            weekly = meina_reminders.add_reminder(
                "週次配信",
                "2030-01-05T18:00:00+09:00",
                repeat_rule="weekly",
            )
            assert meina_reminders.format_reminder_repeat(weekly) == "毎週土曜"
            assert meina_reminders.complete_reminder(
                weekly["id"],
                now=datetime.fromisoformat("2030-01-20T12:00:00+09:00"),
            )
            weekly_after = meina_reminders.find_reminders("週次配信")
            assert len(weekly_after) == 1
            assert weekly_after[0]["done"] is False
            assert weekly_after[0]["due_at"] == "2030-01-26T18:00:00+09:00"

            weekdays = meina_reminders.add_reminder(
                "平日勉強",
                "2030-01-04T18:00:00+09:00",
                repeat_rule="weekdays",
            )
            assert meina_reminders.format_reminder_repeat(weekdays) == "平日"
            assert meina_reminders.complete_reminder(
                weekdays["id"],
                now=datetime.fromisoformat("2030-01-04T18:01:00+09:00"),
            )
            weekdays_after = meina_reminders.find_reminders("平日勉強")
            assert len(weekdays_after) == 1
            assert weekdays_after[0]["due_at"] == "2030-01-07T18:00:00+09:00"

            monthly = meina_reminders.add_reminder(
                "月末処理",
                "2030-01-31T18:00:00+09:00",
                repeat_rule="monthly",
                repeat_day=31,
            )
            assert monthly["repeat_day"] == 31
            assert meina_reminders.format_reminder_repeat(monthly) == "毎月31日"
            assert meina_reminders.complete_reminder(
                monthly["id"],
                now=datetime.fromisoformat("2030-01-31T18:01:00+09:00"),
            )
            monthly_after = meina_reminders.find_reminders("月末処理")
            assert len(monthly_after) == 1
            assert monthly_after[0]["due_at"] == "2030-02-28T18:00:00+09:00"
            assert monthly_after[0]["repeat_day"] == 31

            assert meina_reminders.complete_reminder(
                monthly["id"],
                now=datetime.fromisoformat("2030-02-28T18:01:00+09:00"),
            )
            monthly_after = meina_reminders.find_reminders("月末処理")
            assert monthly_after[0]["due_at"] == "2030-03-31T18:00:00+09:00"
            assert monthly_after[0]["repeat_day"] == 31

            rescheduled_monthly = meina_reminders.reschedule_reminder(
                monthly["id"],
                "2030-03-20T19:00:00+09:00",
            )
            assert rescheduled_monthly is not None
            assert rescheduled_monthly["repeat_day"] == 20
            assert meina_reminders.format_reminder_repeat(rescheduled_monthly) == "毎月20日"

            cleared = meina_reminders.clear_reminder_repeat(monthly["id"])
            assert cleared is not None
            assert "repeat_rule" not in cleared
            assert "repeat_day" not in cleared
            assert cleared["due_at"] == "2030-03-20T19:00:00+09:00"
            assert meina_reminders.format_reminder_repeat(cleared) == ""

            one_shot = meina_reminders.add_reminder(
                "単発予定",
                "2030-04-01T12:00:00+09:00",
            )
            cleared_one_shot = meina_reminders.clear_reminder_repeat(one_shot["id"])
            assert cleared_one_shot is not None
            assert cleared_one_shot["text"] == "単発予定"
            assert meina_reminders.clear_reminder_repeat("missing-id") is None

            repeat_change_target = meina_reminders.add_reminder(
                "繰り返し変更",
                "2030-01-05T18:00:00+09:00",
            )
            changed_weekdays = meina_reminders.set_reminder_repeat(
                repeat_change_target["id"],
                "weekdays",
                now=datetime.fromisoformat("2030-01-04T19:00:00+09:00"),
            )
            assert changed_weekdays is not None
            assert changed_weekdays["repeat_rule"] == "weekdays"
            assert changed_weekdays["due_at"] == "2030-01-07T18:00:00+09:00"
            assert meina_reminders.format_reminder_repeat(changed_weekdays) == "平日"

            changed_weekly = meina_reminders.set_reminder_repeat(
                repeat_change_target["id"],
                "weekly",
                repeat_weekday=5,
                now=datetime.fromisoformat("2030-01-07T19:00:00+09:00"),
            )
            assert changed_weekly is not None
            assert changed_weekly["repeat_rule"] == "weekly"
            assert changed_weekly["due_at"] == "2030-01-12T18:00:00+09:00"
            assert meina_reminders.format_reminder_repeat(changed_weekly) == "毎週土曜"

            changed_monthly = meina_reminders.set_reminder_repeat(
                repeat_change_target["id"],
                "monthly",
                repeat_day=31,
                now=datetime.fromisoformat("2030-01-15T12:00:00+09:00"),
            )
            assert changed_monthly is not None
            assert changed_monthly["repeat_rule"] == "monthly"
            assert changed_monthly["repeat_day"] == 31
            assert changed_monthly["due_at"] == "2030-01-31T18:00:00+09:00"
            assert meina_reminders.format_reminder_repeat(changed_monthly) == "毎月31日"

            changed_daily = meina_reminders.set_reminder_repeat(
                repeat_change_target["id"],
                "daily",
                now=datetime.fromisoformat("2030-01-31T19:00:00+09:00"),
            )
            assert changed_daily is not None
            assert changed_daily["repeat_rule"] == "daily"
            assert "repeat_day" not in changed_daily
            assert changed_daily["due_at"] == "2030-02-01T18:00:00+09:00"

            assert (
                meina_reminders.set_reminder_repeat(
                    repeat_change_target["id"],
                    "weekly",
                    repeat_weekday=7,
                )
                is None
            )
            assert (
                meina_reminders.set_reminder_repeat(
                    repeat_change_target["id"],
                    "yearly",
                )
                is None
            )

            paused_daily = meina_reminders.add_reminder(
                "停止テスト",
                "2030-02-01T18:00:00+09:00",
                repeat_rule="daily",
            )
            paused_item = meina_reminders.pause_reminder(paused_daily["id"])
            assert paused_item is not None
            assert paused_item["paused"] is True
            due_while_paused = meina_reminders.due_reminders(
                datetime.fromisoformat("2030-02-03T20:00:00+09:00")
            )
            assert paused_daily["id"] not in {
                item["id"] for item in due_while_paused
            }

            resumed_item = meina_reminders.resume_reminder(
                paused_daily["id"],
                now=datetime.fromisoformat("2030-02-03T20:00:00+09:00"),
            )
            assert resumed_item is not None
            assert "paused" not in resumed_item
            assert resumed_item["repeat_rule"] == "daily"
            assert resumed_item["due_at"] == "2030-02-04T18:00:00+09:00"

            one_shot_pause = meina_reminders.add_reminder(
                "単発停止",
                "2030-02-01T12:00:00+09:00",
            )
            assert meina_reminders.pause_reminder(one_shot_pause["id"]) is not None
            one_shot_resumed = meina_reminders.resume_reminder(
                one_shot_pause["id"],
                now=datetime.fromisoformat("2030-02-03T20:00:00+09:00"),
            )
            assert one_shot_resumed is not None
            assert one_shot_resumed["due_at"] == "2030-02-01T12:00:00+09:00"
            assert "paused" not in one_shot_resumed
            assert meina_reminders.pause_reminder("missing-id") is None
            assert meina_reminders.resume_reminder("missing-id") is None
    finally:
        meina_reminders.REMINDER_PATH = original

    print("Reminder self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

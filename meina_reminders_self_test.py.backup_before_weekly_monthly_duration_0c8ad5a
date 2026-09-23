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

    duration_cases = (
        (
            "18時から1時間勉強の予定を追加して",
            "勉強",
            "2026-09-12T18:00:00+00:00",
            60,
        ),
        (
            "明日20時から90分配信予定を追加して",
            "配信",
            "2026-09-13T20:00:00+00:00",
            90,
        ),
        (
            "毎日18時から2時間勉強をリマインドして",
            "勉強",
            "2026-09-12T18:00:00+00:00",
            120,
        ),
    )
    for command, expected_text, expected_due, expected_duration in duration_cases:
        parsed_duration = meina_reminder_parser.parse_reminder_command(command, now)
        assert parsed_duration is not None, command
        assert parsed_duration["text"] == expected_text, command
        assert parsed_duration["due_at"] == expected_due, command
        assert parsed_duration["duration_minutes"] == expected_duration, command

    assert (
        meina_reminder_parser.parse_reminder_command(
            "18時から1441分勉強の予定を追加して",
            now,
        )
        is None
    )

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

    duration_set = meina_reminder_parser.parse_reminder_duration_command(
        "宿題の予定の所要時間を2時間にして",
        now,
    )
    assert duration_set is not None
    assert duration_set["target"] == "宿題"
    assert duration_set["duration_minutes"] == 120

    duration_at_time = meina_reminder_parser.parse_reminder_duration_command(
        "18時の宿題の予定の長さを90分にして",
        now,
    )
    assert duration_at_time is not None
    assert duration_at_time["target"] == "宿題"
    assert duration_at_time["hour"] == 18
    assert duration_at_time["duration_minutes"] == 90

    duration_clear = meina_reminder_parser.parse_reminder_duration_command(
        "宿題の予定の所要時間を解除して",
        now,
    )
    assert duration_clear is not None
    assert duration_clear["target"] == "宿題"
    assert duration_clear["duration_minutes"] is None

    assert (
        meina_reminder_parser.parse_reminder_duration_command(
            "宿題の予定の所要時間を25時間にして",
            now,
        )
        is None
    )
    assert (
        meina_reminder_parser.parse_reminder_duration_command(
            "宿題の予定の所要時間を2時間にしていい？",
            now,
        )
        is None
    )

    auto_slot = meina_reminder_parser.parse_reminder_free_slot_add_command(
        "今日18時から22時の空いてる時間に1時間勉強の予定を入れて"
    )
    assert auto_slot is not None
    assert auto_slot["day"] == "今日"
    assert auto_slot["start_hour"] == 18
    assert auto_slot["end_hour"] == 22
    assert auto_slot["duration_minutes"] == 60
    assert auto_slot["text"] == "勉強"

    auto_slot_alt = meina_reminder_parser.parse_reminder_free_slot_add_command(
        "明日18時30分から21時の空き時間に配信を90分入れて"
    )
    assert auto_slot_alt is not None
    assert auto_slot_alt["day"] == "明日"
    assert auto_slot_alt["start_minute"] == 30
    assert auto_slot_alt["duration_minutes"] == 90
    assert auto_slot_alt["text"] == "配信"

    assert (
        meina_reminder_parser.parse_reminder_free_slot_add_command(
            "今日18時から22時の空いてる時間に1時間勉強の予定を入れていい？"
        )
        is None
    )

    move_free = meina_reminder_parser.parse_reminder_move_free_command(
        "宿題の予定を今日18時から22時の空いてる時間に移して",
        now,
    )
    assert move_free is not None
    assert move_free["target"] == "宿題"
    assert move_free["day"] == "今日"
    assert move_free["start_hour"] == 18
    assert move_free["end_hour"] == 22

    move_free_selected = meina_reminder_parser.parse_reminder_move_free_command(
        "18時の宿題の予定を明日19時から22時の空き時間に移動して",
        now,
    )
    assert move_free_selected is not None
    assert move_free_selected["target"] == "宿題"
    assert move_free_selected["hour"] == 18
    assert move_free_selected["day"] == "明日"

    assert (
        meina_reminder_parser.parse_reminder_move_free_command(
            "宿題の予定を今日18時から22時の空いてる時間に移していい？",
            now,
        )
        is None
    )

    restore_completed = (
        meina_reminder_parser.parse_reminder_restore_completed_command(
            "宿題の予定を未完了に戻して",
            now,
        )
    )
    assert restore_completed is not None
    assert restore_completed["target"] == "宿題"
    assert restore_completed["hour"] is None

    restore_completed_at_time = (
        meina_reminder_parser.parse_reminder_restore_completed_command(
            "18時の宿題の予定の完了を取り消して",
            now,
        )
    )
    assert restore_completed_at_time is not None
    assert restore_completed_at_time["target"] == "宿題"
    assert restore_completed_at_time["hour"] == 18

    assert (
        meina_reminder_parser.parse_reminder_restore_completed_command(
            "宿題の予定を未完了に戻していい？",
            now,
        )
        is None
    )

    restore_deleted = (
        meina_reminder_parser.parse_reminder_restore_deleted_command(
            "宿題の予定の削除を取り消して",
            now,
        )
    )
    assert restore_deleted is not None
    assert restore_deleted["target"] == "宿題"

    restore_deleted_at_time = (
        meina_reminder_parser.parse_reminder_restore_deleted_command(
            "18時の宿題の予定をゴミ箱から戻して",
            now,
        )
    )
    assert restore_deleted_at_time is not None
    assert restore_deleted_at_time["target"] == "宿題"
    assert restore_deleted_at_time["hour"] == 18

    assert (
        meina_reminder_parser.parse_reminder_restore_deleted_command(
            "宿題の予定の削除を取り消していい？",
            now,
        )
        is None
    )

    note_set = meina_reminder_parser.parse_reminder_note_command(
        "宿題の予定にメモを追加して「英語のワーク30ページ」",
        now,
    )
    assert note_set is not None
    assert note_set["target"] == "宿題"
    assert note_set["operation"] == "set"
    assert note_set["note"] == "英語のワーク30ページ"

    note_set_at_time = meina_reminder_parser.parse_reminder_note_command(
        "18時の宿題の予定のメモを数学プリントにして",
        now,
    )
    assert note_set_at_time is not None
    assert note_set_at_time["target"] == "宿題"
    assert note_set_at_time["hour"] == 18
    assert note_set_at_time["operation"] == "set"
    assert note_set_at_time["note"] == "数学プリント"

    note_get = meina_reminder_parser.parse_reminder_note_command(
        "宿題の予定のメモを教えて",
        now,
    )
    assert note_get is not None
    assert note_get["operation"] == "get"
    assert note_get["target"] == "宿題"

    note_clear = meina_reminder_parser.parse_reminder_note_command(
        "宿題の予定のメモを消して",
        now,
    )
    assert note_clear is not None
    assert note_clear["operation"] == "clear"
    assert note_clear["target"] == "宿題"

    assert (
        meina_reminder_parser.parse_reminder_note_command(
            "宿題の予定のメモを消していい？",
            now,
        )
        is None
    )
    assert (
        meina_reminder_parser.parse_reminder_note_command(
            "宿題の予定のメモを"
            + ("a" * 501)
            + "にして",
            now,
        )
        is None
    )

    location_set = meina_reminder_parser.parse_reminder_location_command(
        "宿題の予定の場所を図書館にして",
        now,
    )
    assert location_set is not None
    assert location_set["target"] == "宿題"
    assert location_set["operation"] == "set"
    assert location_set["location"] == "図書館"

    location_get = meina_reminder_parser.parse_reminder_location_command(
        "18時の宿題の予定の場所を教えて",
        now,
    )
    assert location_get is not None
    assert location_get["target"] == "宿題"
    assert location_get["hour"] == 18
    assert location_get["operation"] == "get"

    location_clear = meina_reminder_parser.parse_reminder_location_command(
        "宿題の予定の場所を解除して",
        now,
    )
    assert location_clear is not None
    assert location_clear["operation"] == "clear"
    assert (
        meina_reminder_parser.parse_reminder_location_command(
            "宿題の予定の場所を解除していい？",
            now,
        )
        is None
    )

    category_set = meina_reminder_parser.parse_reminder_category_command(
        "宿題の予定を学校カテゴリにして",
        now,
    )
    assert category_set is not None
    assert category_set["target"] == "宿題"
    assert category_set["category"] == "学校"

    category_at_time = meina_reminder_parser.parse_reminder_category_command(
        "18時の宿題の予定のカテゴリを勉強にして",
        now,
    )
    assert category_at_time is not None
    assert category_at_time["target"] == "宿題"
    assert category_at_time["hour"] == 18
    assert category_at_time["category"] == "勉強"

    category_clear = meina_reminder_parser.parse_reminder_category_command(
        "宿題の予定のカテゴリを解除して",
        now,
    )
    assert category_clear is not None
    assert category_clear["target"] == "宿題"
    assert category_clear["category"] is None

    assert (
        meina_reminder_parser.parse_reminder_category_command(
            "宿題の予定を学校カテゴリにしていい？",
            now,
        )
        is None
    )

    important_set = meina_reminder_parser.parse_reminder_importance_command(
        "宿題の予定を重要にして",
        now,
    )
    assert important_set is not None
    assert important_set["target"] == "宿題"
    assert important_set["important"] is True

    important_at_time = meina_reminder_parser.parse_reminder_importance_command(
        "18時の宿題の予定を重要にして",
        now,
    )
    assert important_at_time is not None
    assert important_at_time["target"] == "宿題"
    assert important_at_time["hour"] == 18

    important_clear = meina_reminder_parser.parse_reminder_importance_command(
        "宿題の予定の重要設定を解除して",
        now,
    )
    assert important_clear is not None
    assert important_clear["target"] == "宿題"
    assert important_clear["important"] is False

    assert (
        meina_reminder_parser.parse_reminder_importance_command(
            "宿題の予定を重要にしていい？",
            now,
        )
        is None
    )

    snooze_cases = (
        (
            "宿題を10分後に回して",
            "宿題",
            10,
            None,
        ),
        (
            "18時の宿題を15分延長して",
            "宿題",
            15,
            18,
        ),
        (
            "宿題の予定を30分延期して",
            "宿題",
            30,
            None,
        ),
    )
    for command, target, delay, hour in snooze_cases:
        parsed_snooze = meina_reminder_parser.parse_reminder_snooze_command(
            command,
            now,
        )
        assert parsed_snooze is not None, command
        assert parsed_snooze["target"] == target, command
        assert parsed_snooze["delay_minutes"] == delay, command
        assert parsed_snooze["hour"] == hour, command

    assert (
        meina_reminder_parser.parse_reminder_snooze_command(
            "宿題を0分後に回して",
            now,
        )
        is None
    )
    assert (
        meina_reminder_parser.parse_reminder_snooze_command(
            "宿題を1441分後に回して",
            now,
        )
        is None
    )
    assert (
        meina_reminder_parser.parse_reminder_snooze_command(
            "宿題を10分後に回していい？",
            now,
        )
        is None
    )

    pre_notify_cases = (
        (
            "薬を10分前にも知らせて",
            "薬",
            10,
            None,
        ),
        (
            "薬の事前通知を10分前に設定して",
            "薬",
            10,
            None,
        ),
        (
            "18時の薬の予定を15分前に通知して",
            "薬",
            15,
            18,
        ),
    )
    for command, target, minutes, hour in pre_notify_cases:
        parsed_pre = meina_reminder_parser.parse_reminder_pre_notify_set_command(
            command,
            now,
        )
        assert parsed_pre is not None, command
        assert parsed_pre["target"] == target, command
        assert parsed_pre["notify_before_minutes"] == minutes, command
        assert parsed_pre["hour"] == hour, command

    clear_pre = meina_reminder_parser.parse_reminder_pre_notify_clear_command(
        "薬の事前通知を解除して",
        now,
    )
    assert clear_pre is not None
    assert clear_pre["target"] == "薬"

    assert (
        meina_reminder_parser.parse_reminder_pre_notify_set_command(
            "薬を0分前にも知らせて",
            now,
        )
        is None
    )
    assert (
        meina_reminder_parser.parse_reminder_pre_notify_set_command(
            "薬を1441分前にも知らせて",
            now,
        )
        is None
    )
    assert (
        meina_reminder_parser.parse_reminder_pre_notify_set_command(
            "薬を10分前にも知らせていい？",
            now,
        )
        is None
    )
    assert (
        meina_reminder_parser.parse_reminder_pre_notify_clear_command(
            "薬の事前通知を解除していい？",
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

    duration_route = route_command(
        "宿題の予定の所要時間を2時間にして",
        {"confidence": 0.10},
    )
    assert duration_route is not None
    assert duration_route["kind"] == "reminder_duration"
    assert duration_route["query"]["target"] == "宿題"
    assert duration_route["query"]["duration_minutes"] == 120

    duration_clear_route = route_command(
        "宿題の予定の所要時間を解除して",
        {"confidence": 0.10},
    )
    assert duration_clear_route is not None
    assert duration_clear_route["kind"] == "reminder_duration"
    assert duration_clear_route["query"]["duration_minutes"] is None

    auto_slot_route = route_command(
        "今日18時から22時の空いてる時間に1時間勉強の予定を入れて",
        {"confidence": 0.10},
    )
    assert auto_slot_route is not None
    assert auto_slot_route["kind"] == "reminder_schedule_free"
    assert auto_slot_route["query"]["text"] == "勉強"
    assert auto_slot_route["query"]["duration_minutes"] == 60

    move_free_route = route_command(
        "宿題の予定を今日18時から22時の空いてる時間に移して",
        {"confidence": 0.10},
    )
    assert move_free_route is not None
    assert move_free_route["kind"] == "reminder_move_free"
    assert move_free_route["query"]["target"] == "宿題"
    assert move_free_route["query"]["start_hour"] == 18
    assert move_free_route["query"]["end_hour"] == 22

    move_free_selected_route = route_command(
        "18時の宿題の予定を明日19時から22時の空き時間に移動して",
        {"confidence": 0.10},
    )
    assert move_free_selected_route is not None
    assert move_free_selected_route["kind"] == "reminder_move_free"
    assert move_free_selected_route["query"]["hour"] == 18
    assert move_free_selected_route["query"]["day"] == "明日"

    note_set_route = route_command(
        "宿題の予定にメモを追加して「英語のワーク30ページ」",
        {"confidence": 0.10},
    )
    assert note_set_route is not None
    assert note_set_route["kind"] == "reminder_note"
    assert note_set_route["query"]["operation"] == "set"
    assert note_set_route["query"]["note"] == "英語のワーク30ページ"

    note_get_route = route_command(
        "宿題の予定のメモを教えて",
        {"confidence": 0.10},
    )
    assert note_get_route is not None
    assert note_get_route["kind"] == "reminder_note"
    assert note_get_route["query"]["operation"] == "get"

    note_get_at_time_route = route_command(
        "18時の宿題の予定のメモを教えて",
        {"confidence": 0.10},
    )
    assert note_get_at_time_route is not None
    assert note_get_at_time_route["kind"] == "reminder_note"
    assert note_get_at_time_route["query"]["operation"] == "get"
    assert note_get_at_time_route["query"]["hour"] == 18

    note_clear_route = route_command(
        "18時の宿題の予定のメモを消して",
        {"confidence": 0.10},
    )
    assert note_clear_route is not None
    assert note_clear_route["kind"] == "reminder_note"
    assert note_clear_route["query"]["operation"] == "clear"
    assert note_clear_route["query"]["hour"] == 18

    location_set_route = route_command(
        "宿題の予定の場所を図書館にして",
        {"confidence": 0.10},
    )
    assert location_set_route is not None
    assert location_set_route["kind"] == "reminder_location"
    assert location_set_route["query"]["operation"] == "set"
    assert location_set_route["query"]["location"] == "図書館"

    location_get_route = route_command(
        "18時の宿題の予定の場所を教えて",
        {"confidence": 0.10},
    )
    assert location_get_route is not None
    assert location_get_route["kind"] == "reminder_location"
    assert location_get_route["query"]["operation"] == "get"
    assert location_get_route["query"]["hour"] == 18

    location_clear_route = route_command(
        "宿題の予定の場所を解除して",
        {"confidence": 0.10},
    )
    assert location_clear_route is not None
    assert location_clear_route["kind"] == "reminder_location"
    assert location_clear_route["query"]["operation"] == "clear"

    location_list_route = route_command(
        "図書館での予定を教えて",
        {"confidence": 0.10},
    )
    assert location_list_route is not None
    assert location_list_route["kind"] == "reminder_location_list"
    assert location_list_route["query"] == "図書館"

    location_list_explicit_route = route_command(
        "場所が図書館の予定を教えて",
        {"confidence": 0.10},
    )
    assert location_list_explicit_route is not None
    assert location_list_explicit_route["kind"] == "reminder_location_list"
    assert location_list_explicit_route["query"] == "図書館"

    missing_location_route = route_command(
        "場所未設定の予定を教えて",
        {"confidence": 0.10},
    )
    assert missing_location_route is not None
    assert missing_location_route["kind"] == "reminder_missing_location"

    location_summary_route = route_command(
        "今日の場所別件数",
        {"confidence": 0.10},
    )
    assert location_summary_route is not None
    assert location_summary_route["kind"] == "reminder_location_summary"
    assert location_summary_route["query"] == "today"

    tomorrow_location_summary_route = route_command(
        "明日の場所別件数",
        {"confidence": 0.10},
    )
    assert tomorrow_location_summary_route is not None
    assert tomorrow_location_summary_route["kind"] == "reminder_location_summary"
    assert tomorrow_location_summary_route["query"] == "tomorrow"

    category_list_route = route_command(
        "学校カテゴリの予定を教えて",
        {"confidence": 0.10},
    )
    assert category_list_route is not None
    assert category_list_route["kind"] == "reminder_category_list"
    assert category_list_route["query"] == "学校"

    category_summary_route = route_command(
        "今日のカテゴリ別件数",
        {"confidence": 0.10},
    )
    assert category_summary_route is not None
    assert category_summary_route["kind"] == "reminder_category_summary"
    assert category_summary_route["query"] == "today"

    tomorrow_category_summary_route = route_command(
        "明日のカテゴリ別件数",
        {"confidence": 0.10},
    )
    assert tomorrow_category_summary_route is not None
    assert tomorrow_category_summary_route["kind"] == "reminder_category_summary"
    assert tomorrow_category_summary_route["query"] == "tomorrow"

    weekly_category_summary_route = route_command(
        "今週のカテゴリ別件数",
        {"confidence": 0.10},
    )
    assert weekly_category_summary_route is not None
    assert weekly_category_summary_route["kind"] == "reminder_category_summary"
    assert weekly_category_summary_route["query"] == "week"

    weekly_location_summary_route = route_command(
        "今週の場所別件数",
        {"confidence": 0.10},
    )
    assert weekly_location_summary_route is not None
    assert weekly_location_summary_route["kind"] == "reminder_location_summary"
    assert weekly_location_summary_route["query"] == "week"

    monthly_category_summary_route = route_command(
        "今月のカテゴリ別件数",
        {"confidence": 0.10},
    )
    assert monthly_category_summary_route is not None
    assert monthly_category_summary_route["kind"] == "reminder_category_summary"
    assert monthly_category_summary_route["query"] == "month"

    monthly_location_summary_route = route_command(
        "今月の場所別件数",
        {"confidence": 0.10},
    )
    assert monthly_location_summary_route is not None
    assert monthly_location_summary_route["kind"] == "reminder_location_summary"
    assert monthly_location_summary_route["query"] == "month"

    deleted_list_route = route_command(
        "最近削除した予定を教えて",
        {"confidence": 0.10},
    )
    assert deleted_list_route is not None
    assert deleted_list_route["kind"] == "reminder_deleted_list"

    restore_deleted_route = route_command(
        "18時の宿題の予定をゴミ箱から戻して",
        {"confidence": 0.10},
    )
    assert restore_deleted_route is not None
    assert restore_deleted_route["kind"] == "reminder_restore_deleted"
    assert restore_deleted_route["query"]["target"] == "宿題"
    assert restore_deleted_route["query"]["hour"] == 18

    completed_week_route = route_command(
        "今週終わった予定を教えて",
        {"confidence": 0.10},
    )
    assert completed_week_route is not None
    assert completed_week_route["kind"] == "reminder_completed_period"
    assert completed_week_route["query"] == {
        "scope": "week",
        "category": None,
    }

    completed_month_route = route_command(
        "今月終わった予定を教えて",
        {"confidence": 0.10},
    )
    assert completed_month_route is not None
    assert completed_month_route["kind"] == "reminder_completed_period"
    assert completed_month_route["query"] == {
        "scope": "month",
        "category": None,
    }

    category_completed_week_route = route_command(
        "学校カテゴリで今週終わった予定を教えて",
        {"confidence": 0.10},
    )
    assert category_completed_week_route is not None
    assert category_completed_week_route["kind"] == "reminder_completed_period"
    assert category_completed_week_route["query"] == {
        "scope": "week",
        "category": "学校",
    }

    category_completed_month_route = route_command(
        "学校カテゴリで今月終わった予定を教えて",
        {"confidence": 0.10},
    )
    assert category_completed_month_route is not None
    assert category_completed_month_route["kind"] == "reminder_completed_period"
    assert category_completed_month_route["query"] == {
        "scope": "month",
        "category": "学校",
    }

    location_completed_week_route = route_command(
        "図書館で今週終わった予定を教えて",
        {"confidence": 0.10},
    )
    assert location_completed_week_route is not None
    assert location_completed_week_route["kind"] == "reminder_completed_period"
    assert location_completed_week_route["query"] == {
        "scope": "week",
        "location": "図書館",
    }

    location_completed_month_route = route_command(
        "自習室で今月終わった予定を教えて",
        {"confidence": 0.10},
    )
    assert location_completed_month_route is not None
    assert location_completed_month_route["kind"] == "reminder_completed_period"
    assert location_completed_month_route["query"] == {
        "scope": "month",
        "location": "自習室",
    }

    location_completed_today_route = route_command(
        "場所が図書館で今日完了した予定を教えて",
        {"confidence": 0.10},
    )
    assert location_completed_today_route is not None
    assert location_completed_today_route["kind"] == "reminder_completed_period"
    assert location_completed_today_route["query"] == {
        "scope": "today",
        "location": "図書館",
    }

    location_progress_route = route_command(
        "今日の場所別進捗",
        {"confidence": 0.10},
    )
    assert location_progress_route is not None
    assert location_progress_route["kind"] == "reminder_location_progress"
    assert location_progress_route["query"] == "today"

    tomorrow_location_progress_route = route_command(
        "明日の場所別進捗",
        {"confidence": 0.10},
    )
    assert tomorrow_location_progress_route is not None
    assert tomorrow_location_progress_route["kind"] == "reminder_location_progress"
    assert tomorrow_location_progress_route["query"] == "tomorrow"

    weekly_location_progress_route = route_command(
        "今週の場所別進捗",
        {"confidence": 0.10},
    )
    assert weekly_location_progress_route is not None
    assert weekly_location_progress_route["kind"] == "reminder_location_progress"
    assert weekly_location_progress_route["query"] == "week"

    restore_completed_route = route_command(
        "18時の宿題の予定の完了を取り消して",
        {"confidence": 0.10},
    )
    assert restore_completed_route is not None
    assert restore_completed_route["kind"] == "reminder_restore_completed"
    assert restore_completed_route["query"]["target"] == "宿題"
    assert restore_completed_route["query"]["hour"] == 18

    completed_today_route = route_command(
        "今日終わった予定を教えて",
        {"confidence": 0.10},
    )
    assert completed_today_route is not None
    assert completed_today_route["kind"] == "reminder_completed_today"

    completion_today_route = route_command(
        "今日何個終わった？",
        {"confidence": 0.10},
    )
    assert completion_today_route is not None
    assert completion_today_route["kind"] == "reminder_completion_summary"
    assert completion_today_route["query"] == "today"

    completion_week_route = route_command(
        "今週何個終わった？",
        {"confidence": 0.10},
    )
    assert completion_week_route is not None
    assert completion_week_route["kind"] == "reminder_completion_summary"
    assert completion_week_route["query"] == "week"

    completion_month_route = route_command(
        "今月何個終わった？",
        {"confidence": 0.10},
    )
    assert completion_month_route is not None
    assert completion_month_route["kind"] == "reminder_completion_summary"
    assert completion_month_route["query"] == "month"

    category_progress_route = route_command(
        "今日のカテゴリ別進捗",
        {"confidence": 0.10},
    )
    assert category_progress_route is not None
    assert category_progress_route["kind"] == "reminder_category_progress"
    assert category_progress_route["query"] == "today"

    tomorrow_category_progress_route = route_command(
        "明日のカテゴリ別進捗",
        {"confidence": 0.10},
    )
    assert tomorrow_category_progress_route is not None
    assert tomorrow_category_progress_route["kind"] == "reminder_category_progress"
    assert tomorrow_category_progress_route["query"] == "tomorrow"

    weekly_category_progress_route = route_command(
        "今週のカテゴリ別進捗",
        {"confidence": 0.10},
    )
    assert weekly_category_progress_route is not None
    assert weekly_category_progress_route["kind"] == "reminder_category_progress"
    assert weekly_category_progress_route["query"] == "week"

    monthly_category_progress_route = route_command(
        "今月のカテゴリ別進捗",
        {"confidence": 0.10},
    )
    assert monthly_category_progress_route is not None
    assert monthly_category_progress_route["kind"] == "reminder_category_progress"
    assert monthly_category_progress_route["query"] == "month"

    monthly_location_progress_route = route_command(
        "今月の場所別進捗",
        {"confidence": 0.10},
    )
    assert monthly_location_progress_route is not None
    assert monthly_location_progress_route["kind"] == "reminder_location_progress"
    assert monthly_location_progress_route["query"] == "month"

    category_set_route = route_command(
        "宿題の予定を学校カテゴリにして",
        {"confidence": 0.10},
    )
    assert category_set_route is not None
    assert category_set_route["kind"] == "reminder_category"
    assert category_set_route["query"]["target"] == "宿題"
    assert category_set_route["query"]["category"] == "学校"

    category_clear_route = route_command(
        "宿題の予定のカテゴリを解除して",
        {"confidence": 0.10},
    )
    assert category_clear_route is not None
    assert category_clear_route["kind"] == "reminder_category"
    assert category_clear_route["query"]["category"] is None

    important_list_route = route_command(
        "重要な予定を教えて",
        {"confidence": 0.10},
    )
    assert important_list_route is not None
    assert important_list_route["kind"] == "reminder_important"

    important_set_route = route_command(
        "宿題の予定を重要にして",
        {"confidence": 0.10},
    )
    assert important_set_route is not None
    assert important_set_route["kind"] == "reminder_importance"
    assert important_set_route["query"]["target"] == "宿題"
    assert important_set_route["query"]["important"] is True

    important_clear_route = route_command(
        "宿題の予定の重要設定を解除して",
        {"confidence": 0.10},
    )
    assert important_clear_route is not None
    assert important_clear_route["kind"] == "reminder_importance"
    assert important_clear_route["query"]["important"] is False

    conflict_route = route_command(
        "予定かぶってる？",
        {"confidence": 0.10},
    )
    assert conflict_route is not None
    assert conflict_route["kind"] == "reminder_conflicts"
    assert conflict_route["query"] == 7

    free_route = route_command(
        "今日18時から22時の空き時間を教えて",
        {"confidence": 0.10},
    )
    assert free_route is not None
    assert free_route["kind"] == "reminder_free_time"
    assert free_route["query"] == {
        "day": "今日",
        "start_hour": 18,
        "start_minute": 0,
        "end_hour": 22,
        "end_minute": 0,
        "minimum_minutes": 15,
    }

    free_total_route = route_command(
        "今日18時から22時の空き時間合計",
        {"confidence": 0.10},
    )
    assert free_total_route is not None
    assert free_total_route["kind"] == "reminder_free_total"
    assert free_total_route["query"]["start_hour"] == 18
    assert free_total_route["query"]["end_hour"] == 22

    free_total_natural_route = route_command(
        "今日18時から22時でどれくらい空いてる",
        {"confidence": 0.10},
    )
    assert free_total_natural_route is not None
    assert free_total_natural_route["kind"] == "reminder_free_total"

    free_hour_route = route_command(
        "今日18時から22時で1時間空いてる時間",
        {"confidence": 0.10},
    )
    assert free_hour_route is not None
    assert free_hour_route["kind"] == "reminder_free_time"
    assert free_hour_route["query"]["minimum_minutes"] == 60

    free_tomorrow_route = route_command(
        "明日18時30分から21時の空いてる時間",
        {"confidence": 0.10},
    )
    assert free_tomorrow_route is not None
    assert free_tomorrow_route["kind"] == "reminder_free_time"
    assert free_tomorrow_route["query"]["day"] == "明日"
    assert free_tomorrow_route["query"]["start_minute"] == 30

    remaining_today_route = route_command(
        "今日あとどれくらい空いてる？",
        {"confidence": 0.10},
    )
    assert remaining_today_route is not None
    assert remaining_today_route["kind"] == "reminder_remaining_today"

    day_load_today_route = route_command(
        "今日どれくらい予定詰まってる？",
        {"confidence": 0.10},
    )
    assert day_load_today_route is not None
    assert day_load_today_route["kind"] == "reminder_day_load"
    assert day_load_today_route["query"] == "today"

    day_load_tomorrow_route = route_command(
        "明日の予定どれくらい詰まってる？",
        {"confidence": 0.10},
    )
    assert day_load_tomorrow_route is not None
    assert day_load_tomorrow_route["kind"] == "reminder_day_load"
    assert day_load_tomorrow_route["query"] == "tomorrow"

    week_peak_count_route = route_command(
        "今週いちばん予定が多い日は？",
        {"confidence": 0.10},
    )
    assert week_peak_count_route is not None
    assert week_peak_count_route["kind"] == "reminder_week_peak"
    assert week_peak_count_route["query"] == "count"

    week_peak_duration_route = route_command(
        "今週いちばん忙しい日は？",
        {"confidence": 0.10},
    )
    assert week_peak_duration_route is not None
    assert week_peak_duration_route["kind"] == "reminder_week_peak"
    assert week_peak_duration_route["query"] == "duration"

    duration_total_today_route = route_command(
        "今日の予定時間合計",
        {"confidence": 0.10},
    )
    assert duration_total_today_route is not None
    assert duration_total_today_route["kind"] == "reminder_duration_total"
    assert duration_total_today_route["query"] == "today"

    duration_total_tomorrow_route = route_command(
        "明日何時間予定入ってる？",
        {"confidence": 0.10},
    )
    assert duration_total_tomorrow_route is not None
    assert duration_total_tomorrow_route["kind"] == "reminder_duration_total"
    assert duration_total_tomorrow_route["query"] == "tomorrow"

    missing_duration_route = route_command(
        "所要時間未設定の予定を教えて",
        {"confidence": 0.10},
    )
    assert missing_duration_route is not None
    assert missing_duration_route["kind"] == "reminder_missing_duration"

    next_action_route = route_command(
        "次に何やればいい？",
        {"confidence": 0.10},
    )
    assert next_action_route is not None
    assert next_action_route["kind"] == "reminder_next_action"

    priority_today_route = route_command(
        "今日の優先予定を教えて",
        {"confidence": 0.10},
    )
    assert priority_today_route is not None
    assert priority_today_route["kind"] == "reminder_priority_today"

    focus_slot_route = route_command(
        "今日1時間集中できる時間ある？",
        {"confidence": 0.10},
    )
    assert focus_slot_route is not None
    assert focus_slot_route["kind"] == "reminder_focus_slot"
    assert focus_slot_route["query"] == {
        "day": "今日",
        "duration_minutes": 60,
    }

    focus_slot_tomorrow_route = route_command(
        "明日90分まとまって空いてる時間ある？",
        {"confidence": 0.10},
    )
    assert focus_slot_tomorrow_route is not None
    assert focus_slot_tomorrow_route["kind"] == "reminder_focus_slot"
    assert focus_slot_tomorrow_route["query"] == {
        "day": "明日",
        "duration_minutes": 90,
    }

    brief_route = route_command(
        "今日の予定まとめ",
        {"confidence": 0.10},
    )
    assert brief_route is not None
    assert brief_route["kind"] == "reminder_brief"
    assert brief_route["confidence"] == 1.0
    assert brief_route["query"] is None

    next_route = route_command(
        "次の予定は？",
        {"confidence": 0.10},
    )
    assert next_route is not None
    assert next_route["kind"] == "reminder_next"
    assert next_route["confidence"] == 1.0
    assert next_route["query"] is None

    soon_route = route_command(
        "30分以内の予定ある？",
        {"confidence": 0.10},
    )
    assert soon_route is not None
    assert soon_route["kind"] == "reminder_soon"
    assert soon_route["confidence"] == 1.0
    assert soon_route["query"] == 30

    soon_default_route = route_command(
        "もうすぐの予定は？",
        {"confidence": 0.10},
    )
    assert soon_default_route is not None
    assert soon_default_route["kind"] == "reminder_soon"
    assert soon_default_route["query"] == 30

    week_route = route_command(
        "今週の予定を教えて",
        {"confidence": 0.10},
    )
    assert week_route is not None
    assert week_route["kind"] == "reminder_week"

    month_route = route_command(
        "今月の予定",
        {"confidence": 0.10},
    )
    assert month_route is not None
    assert month_route["kind"] == "reminder_month"

    overdue_route = route_command(
        "期限切れの予定ある？",
        {"confidence": 0.10},
    )
    assert overdue_route is not None
    assert overdue_route["kind"] == "reminder_overdue"

    snooze_route = route_command(
        "宿題を10分後に回して",
        {"confidence": 0.10},
    )
    assert snooze_route is not None
    assert snooze_route["kind"] == "reminder_snooze"
    assert snooze_route["query"]["target"] == "宿題"
    assert snooze_route["query"]["delay_minutes"] == 10

    snooze_at_time_route = route_command(
        "18時の宿題を15分延長して",
        {"confidence": 0.10},
    )
    assert snooze_at_time_route is not None
    assert snooze_at_time_route["kind"] == "reminder_snooze"
    assert snooze_at_time_route["query"]["target"] == "宿題"
    assert snooze_at_time_route["query"]["hour"] == 18

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

    pre_notify_route = route_command(
        "薬を10分前にも知らせて",
        {"confidence": 0.10},
    )
    assert pre_notify_route is not None
    assert pre_notify_route["kind"] == "reminder_pre_notify_set"
    assert pre_notify_route["confidence"] == 1.0
    assert pre_notify_route["query"]["target"] == "薬"
    assert pre_notify_route["query"]["notify_before_minutes"] == 10

    pre_notify_clear_route = route_command(
        "薬の事前通知を解除して",
        {"confidence": 0.10},
    )
    assert pre_notify_clear_route is not None
    assert pre_notify_clear_route["kind"] == "reminder_pre_notify_clear"
    assert pre_notify_clear_route["confidence"] == 1.0
    assert pre_notify_clear_route["query"]["target"] == "薬"

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
                duration_minutes=45,
            )
            assert meina_reminders.set_reminder_category(
                deleted["id"],
                "学校",
            )
            assert meina_reminders.set_reminder_importance(
                deleted["id"],
                True,
            )
            assert meina_reminders.set_reminder_location(
                deleted["id"],
                "図書館",
            )
            assert meina_reminders.delete_reminder(
                deleted["id"],
                now=datetime.fromisoformat("2030-01-02T09:00:00+09:00"),
            )
            assert meina_reminders.list_reminders() == []

            deleted_items = meina_reminders.list_deleted_reminders()
            assert [item["id"] for item in deleted_items] == [deleted["id"]]
            assert deleted_items[0]["deleted_at"] == "2030-01-02T09:00:00+09:00"
            assert deleted_items[0]["category"] == "学校"
            assert deleted_items[0]["important"] is True
            assert deleted_items[0]["duration_minutes"] == 45
            assert deleted_items[0]["location"] == "図書館"
            assert meina_reminders.find_deleted_reminders("削 除 テスト")[0]["id"] == deleted["id"]

            restored_deleted = meina_reminders.restore_deleted_reminder(
                deleted["id"]
            )
            assert restored_deleted is not None
            assert restored_deleted["id"] == deleted["id"]
            assert restored_deleted["category"] == "学校"
            assert restored_deleted["important"] is True
            assert restored_deleted["duration_minutes"] == 45
            assert restored_deleted["location"] == "図書館"
            assert "deleted_at" not in restored_deleted
            assert meina_reminders.list_deleted_reminders() == []
            assert meina_reminders.find_reminders("削除テスト")[0]["id"] == deleted["id"]
            assert meina_reminders.restore_deleted_reminder(deleted["id"]) is None

            assert meina_reminders.delete_reminder(
                deleted["id"],
                now=datetime.fromisoformat("2030-01-02T09:05:00+09:00"),
            )
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

            duplicate_source = meina_reminders.add_reminder(
                "重複確認",
                "2040-01-01T10:00:00+09:00",
            )
            duplicate_match = meina_reminders.find_duplicate_reminder(
                "重 複確認",
                "2040-01-01T10:00:00+09:00",
            )
            assert duplicate_match is not None
            assert duplicate_match["id"] == duplicate_source["id"]
            assert (
                meina_reminders.find_duplicate_reminder(
                    "重複確認",
                    "2040-01-01T11:00:00+09:00",
                )
                is None
            )

            recurring_duplicate = meina_reminders.add_reminder(
                "月次重複",
                "2040-01-31T18:00:00+09:00",
                repeat_rule="monthly",
                repeat_day=31,
            )
            recurring_match = meina_reminders.find_duplicate_reminder(
                "月次重複",
                "2040-01-31T18:00:00+09:00",
                repeat_rule="monthly",
                repeat_day=31,
            )
            assert recurring_match is not None
            assert recurring_match["id"] == recurring_duplicate["id"]
            assert (
                meina_reminders.find_duplicate_reminder(
                    "月次重複",
                    "2040-01-31T18:00:00+09:00",
                    repeat_rule="monthly",
                    repeat_day=30,
                )
                is None
            )

            paused_next = meina_reminders.add_reminder(
                "停止中の次予定",
                "2040-01-02T10:00:00+09:00",
            )
            assert meina_reminders.pause_reminder(paused_next["id"]) is not None
            active_next = meina_reminders.add_reminder(
                "有効な次予定",
                "2040-01-02T11:00:00+09:00",
            )
            next_item = meina_reminders.next_reminder(
                datetime.fromisoformat("2040-01-02T09:00:00+09:00")
            )
            assert next_item is not None
            assert next_item["id"] == active_next["id"]

            next_including_paused = meina_reminders.next_reminder(
                datetime.fromisoformat("2040-01-02T09:00:00+09:00"),
                include_paused=True,
            )
            assert next_including_paused is not None
            assert next_including_paused["id"] == paused_next["id"]

            soon_15 = meina_reminders.add_reminder(
                "15分後",
                "2040-01-03T09:15:00+09:00",
            )
            soon_45 = meina_reminders.add_reminder(
                "45分後",
                "2040-01-03T09:45:00+09:00",
            )
            paused_10 = meina_reminders.add_reminder(
                "停止中10分後",
                "2040-01-03T09:10:00+09:00",
            )
            assert meina_reminders.pause_reminder(paused_10["id"]) is not None

            within_30 = meina_reminders.reminders_within(
                30,
                datetime.fromisoformat("2040-01-03T09:00:00+09:00"),
            )
            assert [item["id"] for item in within_30] == [soon_15["id"]]

            within_60 = meina_reminders.reminders_within(
                60,
                datetime.fromisoformat("2040-01-03T09:00:00+09:00"),
            )
            assert [item["id"] for item in within_60] == [
                soon_15["id"],
                soon_45["id"],
            ]

            calendar_now = datetime.fromisoformat(
                "2030-01-02T12:00:00+09:00"
            )
            week_monday = meina_reminders.add_reminder(
                "週の月曜",
                "2029-12-31T09:00:00+09:00",
            )
            week_sunday = meina_reminders.add_reminder(
                "週の日曜",
                "2030-01-06T20:00:00+09:00",
            )
            next_monday = meina_reminders.add_reminder(
                "次週の月曜",
                "2030-01-07T09:00:00+09:00",
            )
            week_items = meina_reminders.week_reminders(calendar_now)
            week_ids = {item["id"] for item in week_items}
            assert week_monday["id"] in week_ids
            assert week_sunday["id"] in week_ids
            assert next_monday["id"] not in week_ids

            january_item = meina_reminders.add_reminder(
                "1月末",
                "2030-01-31T23:00:00+09:00",
            )
            february_item = meina_reminders.add_reminder(
                "2月初",
                "2030-02-01T00:00:00+09:00",
            )
            month_items = meina_reminders.month_reminders(calendar_now)
            month_ids = {item["id"] for item in month_items}
            assert january_item["id"] in month_ids
            assert february_item["id"] not in month_ids

            overdue_active = meina_reminders.add_reminder(
                "期限切れ有効",
                "2029-12-30T10:00:00+09:00",
            )
            overdue_paused = meina_reminders.add_reminder(
                "期限切れ停止",
                "2029-12-30T11:00:00+09:00",
            )
            assert meina_reminders.pause_reminder(overdue_paused["id"])
            overdue_items = meina_reminders.overdue_reminders(calendar_now)
            overdue_ids = {item["id"] for item in overdue_items}
            assert overdue_active["id"] in overdue_ids
            assert overdue_paused["id"] not in overdue_ids
            overdue_with_paused = meina_reminders.overdue_reminders(
                calendar_now,
                include_paused=True,
            )
            assert overdue_paused["id"] in {
                item["id"] for item in overdue_with_paused
            }

            one_snooze = meina_reminders.add_reminder(
                "単発スヌーズ",
                "2041-01-01T10:00:00+09:00",
            )
            assert meina_reminders.set_reminder_pre_notify(one_snooze["id"], 10)
            snoozed_one = meina_reminders.snooze_reminder(
                one_snooze["id"],
                15,
                now=datetime.fromisoformat("2041-01-01T10:05:00+09:00"),
            )
            assert snoozed_one is not None
            assert snoozed_one["due_at"] == "2041-01-01T10:20:00+09:00"
            assert "pre_notified_due_at" not in snoozed_one

            daily_snooze = meina_reminders.add_reminder(
                "定期スヌーズ",
                "2041-01-01T18:00:00+09:00",
                repeat_rule="daily",
            )
            snoozed_daily = meina_reminders.snooze_reminder(
                daily_snooze["id"],
                20,
                now=datetime.fromisoformat("2041-01-01T17:55:00+09:00"),
            )
            assert snoozed_daily is not None
            assert snoozed_daily["due_at"] == "2041-01-01T18:15:00+09:00"
            assert snoozed_daily["snooze_original_due_at"] == (
                "2041-01-01T18:00:00+09:00"
            )
            assert meina_reminders.complete_reminder(
                daily_snooze["id"],
                now=datetime.fromisoformat("2041-01-01T18:16:00+09:00"),
            )
            daily_after_snooze = meina_reminders.find_reminders("定期スヌーズ")
            assert len(daily_after_snooze) == 1
            assert daily_after_snooze[0]["due_at"] == (
                "2041-01-02T18:00:00+09:00"
            )
            assert "snooze_original_due_at" not in daily_after_snooze[0]
            assert meina_reminders.snooze_reminder(
                daily_snooze["id"],
                0,
            ) is None
            assert meina_reminders.snooze_reminder(
                daily_snooze["id"],
                1441,
            ) is None

            duration_item = meina_reminders.add_reminder(
                "所要時間テスト",
                "2050-01-01T18:00:00+09:00",
                duration_minutes=90,
            )
            assert duration_item["duration_minutes"] == 90
            assert meina_reminders.format_reminder_duration(duration_item) == "1時間30分"

            duration_summary = meina_reminders.reminder_duration_summary(
                [
                    {"duration_minutes": 30},
                    {"duration_minutes": 90},
                    {"text": "未設定"},
                    {"duration_minutes": 60, "paused": True},
                ]
            )
            assert duration_summary == {
                "total_minutes": 120,
                "timed_count": 2,
                "missing_count": 1,
            }
            duration_summary_with_paused = (
                meina_reminders.reminder_duration_summary(
                    [
                        {"duration_minutes": 30},
                        {"duration_minutes": 60, "paused": True},
                    ],
                    include_paused=True,
                )
            )
            assert duration_summary_with_paused["total_minutes"] == 90

            changed_duration = meina_reminders.set_reminder_duration(
                duration_item["id"],
                120,
            )
            assert changed_duration is not None
            assert changed_duration["duration_minutes"] == 120
            assert meina_reminders.format_reminder_duration(changed_duration) == "2時間"

            cleared_duration = meina_reminders.set_reminder_duration(
                duration_item["id"],
                None,
            )
            assert cleared_duration is not None
            assert "duration_minutes" not in cleared_duration
            assert meina_reminders.set_reminder_duration(
                duration_item["id"],
                0,
            ) is None
            assert meina_reminders.set_reminder_duration(
                "missing-id",
                60,
            ) is None

            restored_duration = meina_reminders.set_reminder_duration(
                duration_item["id"],
                90,
            )
            assert restored_duration is not None

            same_without_duration = meina_reminders.find_duplicate_reminder(
                "所要時間テスト",
                "2050-01-01T18:00:00+09:00",
            )
            assert same_without_duration is None
            same_with_duration = meina_reminders.find_duplicate_reminder(
                "所要時間テスト",
                "2050-01-01T18:00:00+09:00",
                duration_minutes=90,
            )
            assert same_with_duration is not None
            assert same_with_duration["id"] == duration_item["id"]

            note_item = meina_reminders.add_reminder(
                "メモテスト",
                "2050-01-02T14:00:00+09:00",
            )
            noted = meina_reminders.set_reminder_note(
                note_item["id"],
                "英語のワーク30ページ",
            )
            assert noted is not None
            assert noted["note"] == "英語のワーク30ページ"
            assert (
                meina_reminders.format_reminder_note(noted)
                == "英語のワーク30ページ"
            )
            assert meina_reminders.set_reminder_note(
                note_item["id"],
                "a" * 501,
            ) is None
            assert meina_reminders.set_reminder_note(
                note_item["id"],
                "改行\n入り",
            ) is None
            unchanged_note = meina_reminders.find_reminders("メモテスト")
            assert unchanged_note[0]["note"] == "英語のワーク30ページ"
            cleared_note = meina_reminders.set_reminder_note(
                note_item["id"],
                None,
            )
            assert cleared_note is not None
            assert "note" not in cleared_note
            assert meina_reminders.set_reminder_note(
                "missing-id",
                "メモ",
            ) is None

            location_item = meina_reminders.add_reminder(
                "場所テスト",
                "2050-01-02T14:30:00+09:00",
            )
            located = meina_reminders.set_reminder_location(
                location_item["id"],
                "彦根市立図書館",
            )
            assert located is not None
            assert located["location"] == "彦根市立図書館"
            assert (
                meina_reminders.format_reminder_location(located)
                == "彦根市立図書館"
            )
            location_matches = meina_reminders.reminders_by_location(
                "彦 根 市 立 図 書 館"
            )
            assert [item["id"] for item in location_matches] == [
                location_item["id"]
            ]
            assert location_item["id"] not in {
                item["id"]
                for item in meina_reminders.reminders_missing_location()
            }
            location_counts = meina_reminders.reminder_location_counts(
                [
                    {"location": "図書館"},
                    {"location": "図書館"},
                    {"location": "学校"},
                    {},
                ]
            )
            assert location_counts == {
                "図書館": 2,
                "場所未設定": 1,
                "学校": 1,
            }
            assert meina_reminders.set_reminder_location(
                location_item["id"],
                "a" * 101,
            ) is None
            assert meina_reminders.set_reminder_location(
                location_item["id"],
                "改行\n入り",
            ) is None
            cleared_location = meina_reminders.set_reminder_location(
                location_item["id"],
                None,
            )
            assert cleared_location is not None
            assert "location" not in cleared_location
            assert location_item["id"] in {
                item["id"]
                for item in meina_reminders.reminders_missing_location()
            }
            assert meina_reminders.set_reminder_location(
                "missing-id",
                "図書館",
            ) is None

            category_item = meina_reminders.add_reminder(
                "カテゴリテスト",
                "2050-01-02T15:00:00+09:00",
            )
            categorized = meina_reminders.set_reminder_category(
                category_item["id"],
                "学校",
            )
            assert categorized is not None
            assert categorized["category"] == "学校"
            assert meina_reminders.format_reminder_category(categorized) == "学校"
            assert category_item["id"] in {
                item["id"]
                for item in meina_reminders.reminders_by_category("学 校")
            }

            category_counts = meina_reminders.reminder_category_counts(
                [
                    {"category": "学校"},
                    {"category": "学校"},
                    {"category": "配信"},
                    {},
                ]
            )
            assert category_counts == {
                "学校": 2,
                "未分類": 1,
                "配信": 1,
            }

            assert meina_reminders.set_reminder_category(
                category_item["id"],
                "a" * 33,
            ) is None
            unchanged_category = meina_reminders.find_reminders("カテゴリテスト")
            assert unchanged_category[0]["category"] == "学校"

            cleared_category = meina_reminders.set_reminder_category(
                category_item["id"],
                None,
            )
            assert cleared_category is not None
            assert "category" not in cleared_category
            assert meina_reminders.set_reminder_category(
                "missing-id",
                "学校",
            ) is None

            important_item = meina_reminders.add_reminder(
                "重要テスト",
                "2050-01-02T16:00:00+09:00",
            )
            marked_important = meina_reminders.set_reminder_importance(
                important_item["id"],
                True,
            )
            assert marked_important is not None
            assert marked_important["important"] is True
            assert meina_reminders.format_reminder_importance(marked_important) == "重要"
            assert important_item["id"] in {
                item["id"] for item in meina_reminders.important_reminders()
            }

            unmarked = meina_reminders.set_reminder_importance(
                important_item["id"],
                False,
            )
            assert unmarked is not None
            assert "important" not in unmarked
            assert important_item["id"] not in {
                item["id"] for item in meina_reminders.important_reminders()
            }
            assert meina_reminders.set_reminder_importance("missing-id", True) is None

            conflict_a = meina_reminders.add_reminder(
                "重なりA",
                "2050-01-02T18:00:00+09:00",
                duration_minutes=60,
            )
            conflict_b = meina_reminders.add_reminder(
                "重なりB",
                "2050-01-02T18:30:00+09:00",
                duration_minutes=60,
            )
            no_conflict = meina_reminders.add_reminder(
                "重ならない",
                "2050-01-02T20:00:00+09:00",
                duration_minutes=30,
            )
            conflicts = meina_reminders.find_schedule_conflicts(
                now=datetime.fromisoformat("2050-01-02T17:00:00+09:00"),
                days=1,
            )
            conflict_ids = {
                frozenset((first["id"], second["id"]))
                for first, second in conflicts
            }
            assert frozenset((conflict_a["id"], conflict_b["id"])) in conflict_ids
            assert all(no_conflict["id"] not in pair for pair in conflict_ids)

            direct_conflicts = meina_reminders.find_conflicting_reminders(
                conflict_a["id"],
                now=datetime.fromisoformat("2050-01-02T17:00:00+09:00"),
            )
            assert conflict_b["id"] in {item["id"] for item in direct_conflicts}
            assert no_conflict["id"] not in {item["id"] for item in direct_conflicts}

            paused_conflict = meina_reminders.add_reminder(
                "停止中重なり",
                "2050-01-02T18:15:00+09:00",
                duration_minutes=60,
            )
            assert meina_reminders.pause_reminder(paused_conflict["id"])
            conflicts_after_pause = meina_reminders.find_schedule_conflicts(
                now=datetime.fromisoformat("2050-01-02T17:00:00+09:00"),
                days=1,
            )
            assert all(
                paused_conflict["id"] not in {first["id"], second["id"]}
                for first, second in conflicts_after_pause
            )
            direct_after_pause = meina_reminders.find_conflicting_reminders(
                conflict_a["id"],
                now=datetime.fromisoformat("2050-01-02T17:00:00+09:00"),
            )
            assert paused_conflict["id"] not in {
                item["id"] for item in direct_after_pause
            }

            free_slots = meina_reminders.find_free_time_slots(
                datetime.fromisoformat("2050-01-02T18:00:00+09:00"),
                datetime.fromisoformat("2050-01-02T22:00:00+09:00"),
                minimum_minutes=15,
            )
            assert free_slots == [
                (
                    datetime.fromisoformat("2050-01-02T19:30:00+09:00"),
                    datetime.fromisoformat("2050-01-02T20:00:00+09:00"),
                ),
                (
                    datetime.fromisoformat("2050-01-02T20:30:00+09:00"),
                    datetime.fromisoformat("2050-01-02T22:00:00+09:00"),
                ),
            ]

            window_stats = meina_reminders.schedule_window_stats(
                datetime.fromisoformat("2050-01-02T18:00:00+09:00"),
                datetime.fromisoformat("2050-01-02T22:00:00+09:00"),
            )
            assert window_stats == {
                "window_minutes": 240,
                "free_minutes": 120,
                "busy_minutes": 120,
                "longest_free_minutes": 90,
            }

            first_hour_slot = meina_reminders.find_first_free_slot(
                datetime.fromisoformat("2050-01-02T18:00:00+09:00"),
                datetime.fromisoformat("2050-01-02T22:00:00+09:00"),
                required_minutes=60,
            )
            assert first_hour_slot == (
                datetime.fromisoformat("2050-01-02T20:30:00+09:00"),
                datetime.fromisoformat("2050-01-02T21:30:00+09:00"),
            )
            assert (
                meina_reminders.find_first_free_slot(
                    datetime.fromisoformat("2050-01-02T18:00:00+09:00"),
                    datetime.fromisoformat("2050-01-02T20:00:00+09:00"),
                    required_minutes=60,
                )
                is None
            )

            movable = meina_reminders.add_reminder(
                "移動対象",
                "2050-01-03T18:00:00+09:00",
                duration_minutes=60,
            )
            blocker = meina_reminders.add_reminder(
                "移動先ブロック",
                "2050-01-03T19:00:00+09:00",
                duration_minutes=60,
            )
            slot_excluding_self = meina_reminders.find_first_free_slot(
                datetime.fromisoformat("2050-01-03T18:00:00+09:00"),
                datetime.fromisoformat("2050-01-03T22:00:00+09:00"),
                required_minutes=60,
                exclude_reminder_id=movable["id"],
            )
            assert slot_excluding_self == (
                datetime.fromisoformat("2050-01-03T18:00:00+09:00"),
                datetime.fromisoformat("2050-01-03T19:00:00+09:00"),
            )
            slot_without_exclusion = meina_reminders.find_first_free_slot(
                datetime.fromisoformat("2050-01-03T18:00:00+09:00"),
                datetime.fromisoformat("2050-01-03T22:00:00+09:00"),
                required_minutes=60,
            )
            assert slot_without_exclusion == (
                datetime.fromisoformat("2050-01-03T20:00:00+09:00"),
                datetime.fromisoformat("2050-01-03T21:00:00+09:00"),
            )

            moved_one = meina_reminders.move_reminder_occurrence(
                movable["id"],
                "2050-01-03T20:00:00+09:00",
            )
            assert moved_one is not None
            assert moved_one["due_at"] == "2050-01-03T20:00:00+09:00"
            assert "snooze_original_due_at" not in moved_one

            recurring_move = meina_reminders.add_reminder(
                "定期移動",
                "2050-01-04T18:00:00+09:00",
                repeat_rule="daily",
                duration_minutes=60,
            )
            moved_recurring = meina_reminders.move_reminder_occurrence(
                recurring_move["id"],
                "2050-01-04T20:00:00+09:00",
            )
            assert moved_recurring is not None
            assert moved_recurring["due_at"] == "2050-01-04T20:00:00+09:00"
            assert moved_recurring["snooze_original_due_at"] == (
                "2050-01-04T18:00:00+09:00"
            )
            assert meina_reminders.complete_reminder(
                recurring_move["id"],
                now=datetime.fromisoformat("2050-01-04T20:01:00+09:00"),
            )
            recurring_after_move = meina_reminders.find_reminders("定期移動")
            assert len(recurring_after_move) == 1
            assert recurring_after_move[0]["due_at"] == (
                "2050-01-05T18:00:00+09:00"
            )
            assert "snooze_original_due_at" not in recurring_after_move[0]
            assert blocker["id"] in {
                item["id"] for item in meina_reminders.list_reminders()
            }

            priority_original_path = meina_reminders.REMINDER_PATH
            meina_reminders.REMINDER_PATH = Path(tmp) / "priority_reminders.json"
            try:
                priority_now = datetime.fromisoformat(
                    "2070-01-01T12:00:00+09:00"
                )
                overdue_normal = meina_reminders.add_reminder(
                    "期限切れ通常",
                    "2070-01-01T10:00:00+09:00",
                )
                overdue_important = meina_reminders.add_reminder(
                    "期限切れ重要",
                    "2070-01-01T11:00:00+09:00",
                )
                assert meina_reminders.set_reminder_importance(
                    overdue_important["id"],
                    True,
                )
                future_normal = meina_reminders.add_reminder(
                    "未来通常",
                    "2070-01-01T13:00:00+09:00",
                )
                future_important = meina_reminders.add_reminder(
                    "未来重要",
                    "2070-01-01T18:00:00+09:00",
                )
                assert meina_reminders.set_reminder_importance(
                    future_important["id"],
                    True,
                )
                paused_overdue = meina_reminders.add_reminder(
                    "停止中期限切れ重要",
                    "2070-01-01T09:00:00+09:00",
                )
                assert meina_reminders.set_reminder_importance(
                    paused_overdue["id"],
                    True,
                )
                assert meina_reminders.pause_reminder(paused_overdue["id"])

                ranked = meina_reminders.prioritized_reminders(priority_now)
                assert [item["id"] for item in ranked] == [
                    overdue_important["id"],
                    overdue_normal["id"],
                    future_important["id"],
                    future_normal["id"],
                ]

                next_priority = meina_reminders.next_priority_reminder(priority_now)
                assert next_priority is not None
                assert next_priority["id"] == overdue_important["id"]

                today_ranked = meina_reminders.prioritized_reminders(
                    priority_now,
                    target_date=priority_now.date(),
                )
                assert [item["id"] for item in today_ranked] == [
                    overdue_important["id"],
                    overdue_normal["id"],
                    future_important["id"],
                    future_normal["id"],
                ]

                tomorrow_ranked = meina_reminders.prioritized_reminders(
                    priority_now,
                    target_date=datetime.fromisoformat(
                        "2070-01-02T12:00:00+09:00"
                    ).date(),
                )
                assert tomorrow_ranked == []
            finally:
                meina_reminders.REMINDER_PATH = priority_original_path

            projection_daily = meina_reminders.add_reminder(
                "投影毎日",
                "2060-01-01T18:00:00+09:00",
                repeat_rule="daily",
                duration_minutes=60,
            )
            projection_weekly = meina_reminders.add_reminder(
                "投影毎週",
                "2060-01-01T20:00:00+09:00",
                repeat_rule="weekly",
                duration_minutes=30,
            )
            projection_monthly = meina_reminders.add_reminder(
                "投影毎月",
                "2060-01-31T21:00:00+09:00",
                repeat_rule="monthly",
                duration_minutes=45,
            )

            projected_short = meina_reminders.project_reminder_occurrences(
                datetime.fromisoformat("2060-01-01T00:00:00+09:00").date(),
                datetime.fromisoformat("2060-01-03T00:00:00+09:00").date(),
                now=datetime.fromisoformat("2060-01-01T12:00:00+09:00"),
            )
            daily_due = [
                item["due_at"]
                for item in projected_short
                if item["id"] == projection_daily["id"]
            ]
            assert daily_due == [
                "2060-01-01T18:00:00+09:00",
                "2060-01-02T18:00:00+09:00",
                "2060-01-03T18:00:00+09:00",
            ]
            weekly_due = [
                item["due_at"]
                for item in meina_reminders.project_reminder_occurrences(
                    datetime.fromisoformat("2060-01-01T00:00:00+09:00").date(),
                    datetime.fromisoformat("2060-01-15T00:00:00+09:00").date(),
                    now=datetime.fromisoformat("2060-01-01T12:00:00+09:00"),
                )
                if item["id"] == projection_weekly["id"]
            ]
            assert weekly_due == [
                "2060-01-01T20:00:00+09:00",
                "2060-01-08T20:00:00+09:00",
                "2060-01-15T20:00:00+09:00",
            ]
            monthly_due = [
                item["due_at"]
                for item in meina_reminders.project_reminder_occurrences(
                    datetime.fromisoformat("2060-01-31T00:00:00+09:00").date(),
                    datetime.fromisoformat("2060-03-31T00:00:00+09:00").date(),
                    now=datetime.fromisoformat("2060-01-31T12:00:00+09:00"),
                )
                if item["id"] == projection_monthly["id"]
            ]
            assert monthly_due == [
                "2060-01-31T21:00:00+09:00",
                "2060-02-29T21:00:00+09:00",
                "2060-03-31T21:00:00+09:00",
            ]

            day_summary = meina_reminders.day_schedule_summary(
                datetime.fromisoformat("2060-01-01T00:00:00+09:00").date(),
                now=datetime.fromisoformat("2060-01-01T12:00:00+09:00"),
            )
            assert day_summary["count"] >= 2
            assert day_summary["total_minutes"] >= 90

            projection_moved = meina_reminders.add_reminder(
                "投影移動毎日",
                "2060-02-01T18:00:00+09:00",
                repeat_rule="daily",
                duration_minutes=60,
            )
            moved_projection = meina_reminders.move_reminder_occurrence(
                projection_moved["id"],
                "2060-02-02T20:00:00+09:00",
            )
            assert moved_projection is not None
            moved_due = [
                item["due_at"]
                for item in meina_reminders.project_reminder_occurrences(
                    datetime.fromisoformat("2060-02-01T00:00:00+09:00").date(),
                    datetime.fromisoformat("2060-02-04T00:00:00+09:00").date(),
                    now=datetime.fromisoformat("2060-02-01T12:00:00+09:00"),
                )
                if item["id"] == projection_moved["id"]
            ]
            assert moved_due == [
                "2060-02-02T20:00:00+09:00",
                "2060-02-03T18:00:00+09:00",
                "2060-02-04T18:00:00+09:00",
            ]

            week_projection = meina_reminders.remaining_week_schedule_summary(
                now=datetime.fromisoformat("2060-01-01T12:00:00+09:00")
            )
            assert week_projection
            assert week_projection[0]["date"] == "2060-01-01"

            missing_duration_item = meina_reminders.add_reminder(
                "時間未設定確認",
                "2050-01-03T10:00:00+09:00",
            )
            missing_ids = {
                item["id"]
                for item in meina_reminders.reminders_missing_duration()
            }
            assert missing_duration_item["id"] in missing_ids
            assert meina_reminders.set_reminder_duration(
                missing_duration_item["id"],
                45,
            )
            missing_ids_after = {
                item["id"]
                for item in meina_reminders.reminders_missing_duration()
            }
            assert missing_duration_item["id"] not in missing_ids_after

            try:
                meina_reminders.add_reminder(
                    "無効時間",
                    "2050-01-03T12:00:00+09:00",
                    duration_minutes=1441,
                )
                raise AssertionError("invalid duration should fail")
            except ValueError:
                pass

            main_test_path = meina_reminders.REMINDER_PATH
            meina_reminders.REMINDER_PATH = Path(tmp) / "completion_history.json"
            try:
                history_now = datetime.fromisoformat(
                    "2030-01-07T12:00:00+09:00"
                )

                school_done = meina_reminders.add_reminder(
                    "学校宿題完了",
                    "2030-01-07T10:00:00+09:00",
                    duration_minutes=60,
                )
                assert meina_reminders.set_reminder_category(
                    school_done["id"],
                    "学校",
                )
                assert meina_reminders.set_reminder_note(
                    school_done["id"],
                    "提出前に見直す",
                )
                assert meina_reminders.set_reminder_location(
                    school_done["id"],
                    "自習室",
                )
                stream_done = meina_reminders.add_reminder(
                    "配信準備完了",
                    "2030-01-07T11:00:00+09:00",
                    duration_minutes=30,
                )
                assert meina_reminders.set_reminder_category(
                    stream_done["id"],
                    "配信",
                )
                school_remaining = meina_reminders.add_reminder(
                    "学校の残り",
                    "2030-01-07T16:00:00+09:00",
                    duration_minutes=45,
                )
                assert meina_reminders.set_reminder_category(
                    school_remaining["id"],
                    "学校",
                )
                assert meina_reminders.set_reminder_location(
                    school_remaining["id"],
                    "自習室",
                )
                meina_reminders.add_reminder(
                    "明日の予定",
                    "2030-01-08T17:00:00+09:00",
                    duration_minutes=30,
                )

                assert meina_reminders.complete_reminder(
                    school_done["id"],
                    now=datetime.fromisoformat("2030-01-07T10:30:00+09:00"),
                )
                assert meina_reminders.complete_reminder(
                    stream_done["id"],
                    now=datetime.fromisoformat("2030-01-07T11:10:00+09:00"),
                )
                assert (
                    meina_reminders.complete_reminder(
                        school_done["id"],
                        now=datetime.fromisoformat("2030-01-07T11:30:00+09:00"),
                    )
                    is False
                )

                restore_candidate = meina_reminders.add_reminder(
                    "戻すテスト",
                    "2030-01-07T11:30:00+09:00",
                    duration_minutes=20,
                )
                assert meina_reminders.complete_reminder(
                    restore_candidate["id"],
                    now=datetime.fromisoformat("2030-01-07T11:40:00+09:00"),
                )
                completed_matches = meina_reminders.find_completed_reminders(
                    "戻すテスト"
                )
                assert [item["id"] for item in completed_matches] == [
                    restore_candidate["id"]
                ]
                restored = meina_reminders.restore_completed_reminder(
                    restore_candidate["id"]
                )
                assert restored is not None
                assert restored["done"] is False
                assert "completed_at" not in restored
                assert meina_reminders.find_completed_reminders("戻すテスト") == []
                assert (
                    meina_reminders.restore_completed_reminder(
                        restore_candidate["id"]
                    )
                    is None
                )

                stored_all = meina_reminders.list_reminders(include_done=True)
                stored_school = next(
                    item for item in stored_all
                    if item["id"] == school_done["id"]
                )
                assert stored_school["done"] is True
                assert stored_school["completed_at"] == (
                    "2030-01-07T10:30:00+09:00"
                )
                assert stored_school["note"] == "提出前に見直す"
                assert stored_school["location"] == "自習室"

                daily_history = meina_reminders.add_reminder(
                    "毎日の学校確認",
                    "2030-01-07T09:00:00+09:00",
                    repeat_rule="daily",
                    duration_minutes=15,
                )
                assert meina_reminders.set_reminder_category(
                    daily_history["id"],
                    "学校",
                )
                assert meina_reminders.set_reminder_note(
                    daily_history["id"],
                    "毎回の確認メモ",
                )
                assert meina_reminders.set_reminder_location(
                    daily_history["id"],
                    "教室",
                )
                assert meina_reminders.complete_reminder(
                    daily_history["id"],
                    now=datetime.fromisoformat("2030-01-07T09:05:00+09:00"),
                )
                daily_after_history = meina_reminders.find_reminders(
                    "毎日の学校確認"
                )[0]
                assert daily_after_history["due_at"] == (
                    "2030-01-08T09:00:00+09:00"
                )
                assert len(daily_after_history["completion_history"]) == 1
                recurring_event = daily_after_history["completion_history"][0]
                assert recurring_event["due_at"] == (
                    "2030-01-07T09:00:00+09:00"
                )
                assert recurring_event["completed_at"] == (
                    "2030-01-07T09:05:00+09:00"
                )
                assert recurring_event["category"] == "学校"
                assert recurring_event["note"] == "毎回の確認メモ"
                assert recurring_event["location"] == "教室"
                assert (
                    meina_reminders.restore_completed_reminder(
                        daily_history["id"]
                    )
                    is None
                )

                resumed_without_completion = meina_reminders.add_reminder(
                    "再開だけの定期",
                    "2030-01-06T08:00:00+09:00",
                    repeat_rule="daily",
                )
                assert meina_reminders.pause_reminder(
                    resumed_without_completion["id"]
                )
                resumed_item = meina_reminders.resume_reminder(
                    resumed_without_completion["id"],
                    now=history_now,
                )
                assert resumed_item is not None
                assert "completion_history" not in resumed_item

                today_events = meina_reminders.completion_events_for_date(
                    history_now.date(),
                    history_now,
                )
                assert len(today_events) == 3
                assert {event["text"] for event in today_events} == {
                    "学校宿題完了",
                    "配信準備完了",
                    "毎日の学校確認",
                }

                school_events = meina_reminders.completion_events_for_date(
                    history_now.date(),
                    history_now,
                    category="学 校",
                )
                assert {event["text"] for event in school_events} == {
                    "学校宿題完了",
                    "毎日の学校確認",
                }
                stream_events = meina_reminders.completion_events(
                    history_now.date(),
                    history_now.date(),
                    history_now,
                    category="配信",
                )
                assert [event["text"] for event in stream_events] == [
                    "配信準備完了"
                ]
                missing_category_events = meina_reminders.completion_events(
                    history_now.date(),
                    history_now.date(),
                    history_now,
                    category="存在しない",
                )
                assert missing_category_events == []

                study_room_events = meina_reminders.completion_events_for_date(
                    history_now.date(),
                    history_now,
                    location="自 習 室",
                )
                assert [event["text"] for event in study_room_events] == [
                    "学校宿題完了"
                ]
                classroom_events = meina_reminders.completion_events(
                    history_now.date(),
                    history_now.date(),
                    history_now,
                    location="教室",
                )
                assert [event["text"] for event in classroom_events] == [
                    "毎日の学校確認"
                ]
                missing_location_events = meina_reminders.completion_events(
                    history_now.date(),
                    history_now.date(),
                    history_now,
                    location="存在しない場所",
                )
                assert missing_location_events == []

                month_start = history_now.date().replace(day=1)
                monthly_school_events = meina_reminders.completion_events(
                    month_start,
                    history_now.date(),
                    history_now,
                    category="学校",
                )
                assert {event["text"] for event in monthly_school_events} == {
                    "学校宿題完了",
                    "毎日の学校確認",
                }
                monthly_study_room_events = meina_reminders.completion_events(
                    month_start,
                    history_now.date(),
                    history_now,
                    location="自習室",
                )
                assert [event["text"] for event in monthly_study_room_events] == [
                    "学校宿題完了"
                ]

                location_progress = meina_reminders.completion_location_progress(
                    history_now.date(),
                    history_now,
                )
                assert location_progress["自習室"] == {
                    "completed": 1,
                    "remaining": 1,
                }
                assert location_progress["教室"] == {
                    "completed": 1,
                    "remaining": 0,
                }
                assert location_progress["場所未設定"]["completed"] == 1
                assert location_progress["場所未設定"]["remaining"] >= 1

                today_progress = meina_reminders.completion_progress_summary(
                    history_now,
                    scope="today",
                )
                assert today_progress == {
                    "completed_count": 3,
                    "remaining_count": 2,
                }

                category_progress = meina_reminders.completion_category_progress(
                    history_now.date(),
                    history_now,
                )
                assert category_progress["学校"] == {
                    "completed": 2,
                    "remaining": 1,
                }
                assert category_progress["配信"] == {
                    "completed": 1,
                    "remaining": 0,
                }
                assert category_progress["未分類"] == {
                    "completed": 0,
                    "remaining": 1,
                }

                tomorrow_remaining = meina_reminders.remaining_scope_reminders(
                    history_now,
                    scope="tomorrow",
                )
                tomorrow_category_counts = meina_reminders.reminder_category_counts(
                    tomorrow_remaining
                )
                assert tomorrow_category_counts == {
                    "未分類": 2,
                    "学校": 1,
                }
                tomorrow_location_counts = meina_reminders.reminder_location_counts(
                    tomorrow_remaining
                )
                assert tomorrow_location_counts == {
                    "場所未設定": 2,
                    "教室": 1,
                }

                tomorrow_category_progress = (
                    meina_reminders.completion_category_progress(
                        history_now.date(),
                        history_now,
                        scope="tomorrow",
                    )
                )
                assert tomorrow_category_progress == {
                    "未分類": {"completed": 0, "remaining": 2},
                    "学校": {"completed": 0, "remaining": 1},
                }

                tomorrow_location_progress = (
                    meina_reminders.completion_location_progress(
                        history_now.date(),
                        history_now,
                        scope="tomorrow",
                    )
                )
                assert tomorrow_location_progress == {
                    "場所未設定": {"completed": 0, "remaining": 2},
                    "教室": {"completed": 0, "remaining": 1},
                }

                month_progress = meina_reminders.completion_progress_summary(
                    history_now,
                    scope="month",
                )
                assert month_progress == {
                    "completed_count": 3,
                    "remaining_count": 51,
                }

                monthly_remaining = meina_reminders.remaining_scope_reminders(
                    history_now,
                    scope="month",
                )
                monthly_category_counts = meina_reminders.reminder_category_counts(
                    monthly_remaining
                )
                assert monthly_category_counts == {
                    "未分類": 26,
                    "学校": 25,
                }
                monthly_location_counts = meina_reminders.reminder_location_counts(
                    monthly_remaining
                )
                assert monthly_location_counts == {
                    "場所未設定": 26,
                    "教室": 24,
                    "自習室": 1,
                }

                monthly_category_progress = (
                    meina_reminders.completion_category_progress(
                        history_now.date(),
                        history_now,
                        scope="month",
                    )
                )
                assert monthly_category_progress == {
                    "未分類": {"completed": 0, "remaining": 26},
                    "学校": {"completed": 2, "remaining": 25},
                    "配信": {"completed": 1, "remaining": 0},
                }

                monthly_location_progress = (
                    meina_reminders.completion_location_progress(
                        history_now.date(),
                        history_now,
                        scope="month",
                    )
                )
                assert monthly_location_progress == {
                    "場所未設定": {"completed": 1, "remaining": 26},
                    "教室": {"completed": 1, "remaining": 24},
                    "自習室": {"completed": 1, "remaining": 1},
                }

                week_progress = meina_reminders.completion_progress_summary(
                    history_now,
                    scope="week",
                )
                assert week_progress["completed_count"] == 3
                assert week_progress["remaining_count"] >= 1

                weekly_category_progress = (
                    meina_reminders.completion_category_progress(
                        history_now.date(),
                        history_now,
                        scope="week",
                    )
                )
                assert weekly_category_progress["学校"] == {
                    "completed": 2,
                    "remaining": 7,
                }
                assert weekly_category_progress["配信"] == {
                    "completed": 1,
                    "remaining": 0,
                }
                assert weekly_category_progress["未分類"]["completed"] == 0
                assert weekly_category_progress["未分類"]["remaining"] >= 1

                weekly_remaining = meina_reminders.remaining_scope_reminders(
                    history_now,
                    scope="week",
                )
                weekly_category_counts = meina_reminders.reminder_category_counts(
                    weekly_remaining
                )
                assert weekly_category_counts["学校"] == 7
                assert weekly_category_counts["未分類"] >= 1

                weekly_location_counts = meina_reminders.reminder_location_counts(
                    weekly_remaining
                )
                assert weekly_location_counts["自習室"] == 1
                assert weekly_location_counts["教室"] == 6
                assert weekly_location_counts["場所未設定"] >= 1

                weekly_location_progress = (
                    meina_reminders.completion_location_progress(
                        history_now.date(),
                        history_now,
                        scope="week",
                    )
                )
                assert weekly_location_progress["自習室"] == {
                    "completed": 1,
                    "remaining": 1,
                }
                assert weekly_location_progress["教室"] == {
                    "completed": 1,
                    "remaining": 6,
                }
                assert weekly_location_progress["場所未設定"]["completed"] == 1
                assert weekly_location_progress["場所未設定"]["remaining"] >= 1

                no_old_events = meina_reminders.completion_events(
                    datetime.fromisoformat("2029-12-01T00:00:00+09:00").date(),
                    datetime.fromisoformat("2029-12-31T00:00:00+09:00").date(),
                    history_now,
                )
                assert no_old_events == []
            finally:
                meina_reminders.REMINDER_PATH = main_test_path

            pre_item = meina_reminders.add_reminder(
                "事前通知テスト",
                "2040-01-04T10:00:00+09:00",
            )
            configured_pre = meina_reminders.set_reminder_pre_notify(
                pre_item["id"],
                10,
            )
            assert configured_pre is not None
            assert configured_pre["notify_before_minutes"] == 10

            before_window = meina_reminders.pre_due_reminders(
                datetime.fromisoformat("2040-01-04T09:49:00+09:00")
            )
            assert pre_item["id"] not in {item["id"] for item in before_window}

            in_window = meina_reminders.pre_due_reminders(
                datetime.fromisoformat("2040-01-04T09:50:00+09:00")
            )
            assert [item["id"] for item in in_window] == [pre_item["id"]]

            assert meina_reminders.mark_reminder_pre_notified(
                pre_item["id"],
                pre_item["due_at"],
            )
            assert (
                meina_reminders.pre_due_reminders(
                    datetime.fromisoformat("2040-01-04T09:55:00+09:00")
                )
                == []
            )

            cleared_pre = meina_reminders.clear_reminder_pre_notify(pre_item["id"])
            assert cleared_pre is not None
            assert "notify_before_minutes" not in cleared_pre
            assert "pre_notified_due_at" not in cleared_pre
            assert meina_reminders.set_reminder_pre_notify(pre_item["id"], 0) is None
            assert meina_reminders.set_reminder_pre_notify(pre_item["id"], 1441) is None

            paused_pre = meina_reminders.add_reminder(
                "停止中事前通知",
                "2040-01-04T11:00:00+09:00",
            )
            assert meina_reminders.set_reminder_pre_notify(paused_pre["id"], 15)
            assert meina_reminders.pause_reminder(paused_pre["id"])
            paused_window = meina_reminders.pre_due_reminders(
                datetime.fromisoformat("2040-01-04T10:50:00+09:00")
            )
            assert paused_pre["id"] not in {item["id"] for item in paused_window}

            recurring_pre = meina_reminders.add_reminder(
                "毎回事前通知",
                "2040-01-05T18:00:00+09:00",
                repeat_rule="daily",
            )
            assert meina_reminders.set_reminder_pre_notify(recurring_pre["id"], 10)
            first_pre = meina_reminders.pre_due_reminders(
                datetime.fromisoformat("2040-01-05T17:50:00+09:00")
            )
            assert recurring_pre["id"] in {item["id"] for item in first_pre}
            assert meina_reminders.mark_reminder_pre_notified(
                recurring_pre["id"],
                recurring_pre["due_at"],
            )
            assert meina_reminders.complete_reminder(
                recurring_pre["id"],
                now=datetime.fromisoformat("2040-01-05T18:01:00+09:00"),
            )
            next_pre = meina_reminders.pre_due_reminders(
                datetime.fromisoformat("2040-01-06T17:50:00+09:00")
            )
            assert recurring_pre["id"] in {item["id"] for item in next_pre}
    finally:
        meina_reminders.REMINDER_PATH = original

    print("Reminder self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

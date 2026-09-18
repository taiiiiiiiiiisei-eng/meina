"""予定・リマインダー統合セルフテスト。"""
from datetime import datetime

from command_router import route_command
from meina_reminder_parser import parse_reminder_command


def main() -> int:
    now = datetime.fromisoformat("2026-09-18T17:00:00+09:00")

    cases = [
        ("明日18時に配信の予定を追加して", "配信の予定", "2026-09-19T18:00:00+09:00"),
        ("明後日9時に学校をリマインドして", "学校を", "2026-09-20T09:00:00+09:00"),
        ("30分後に宿題を知らせて", "宿題を", "2026-09-18T17:30:00+09:00"),
    ]

    for text, expected_text, expected_due in cases:
        parsed = parse_reminder_command(text, now)
        assert parsed is not None
        assert parsed["text"] == expected_text
        assert parsed["due_at"] == expected_due

        route = route_command(text, {"confidence": 0.1})
        assert route is not None
        assert route["kind"] == "reminder"
        assert route["confidence"] == 1.0

    for text, kind in [
        ("今日の予定を教えて", "reminder_today"),
        ("明日の予定を教えて", "reminder_tomorrow"),
        ("今後の予定を教えて", "reminder_upcoming"),
        ("リマインダー一覧を教えて", "reminder_list"),
    ]:
        route = route_command(text, {"confidence": 0.1})
        assert route is not None and route["kind"] == kind

    print("Schedule self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

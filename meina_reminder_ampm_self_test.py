"""日本語の午前・午後を含む予定時刻のセルフテスト。"""
from datetime import datetime, timezone
from meina_reminder_parser import parse_reminder_command

def main() -> int:
    now = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)
    pm = parse_reminder_command("明日午後6時に配信予定を追加して", now)
    assert pm is not None
    assert pm["text"] == "配信"
    assert pm["due_at"] == "2026-09-13T18:00:00+00:00"
    am = parse_reminder_command("明日午前9時に学校予定を追加して", now)
    assert am is not None
    assert am["text"] == "学校"
    assert am["due_at"] == "2026-09-13T09:00:00+00:00"
    print("Reminder AM/PM self-test: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

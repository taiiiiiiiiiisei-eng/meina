"""リマインダーの一覧・今日・完了・削除を既存エージェントへ安全に接続する起動アップグレード。"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
MARKER = "# MEINA_REMINDER_COMMANDS_V4"
BACKUP = ROOT / "meina_agent.py.backup_before_reminder_v4"

IMPORT_LINE = "from meina_reminders import add_reminder, complete_reminder, delete_reminder, due_reminders, list_reminders, today_reminders\n"

HELPERS = '''\n\ndef _format_reminder_due(value):\n    try:\n        from datetime import datetime\n        due = datetime.fromisoformat(str(value))\n        return f"{due.month}月{due.day}日{due.hour}時{due.minute}分"\n    except (TypeError, ValueError):\n        return str(value)\n\n\ndef _execute_reminder_list():\n    items = list_reminders()\n    if not items:\n        speak("現在、登録されているリマインダーはありません")\n        return True\n    speak(f"登録されているリマインダーは{len(items)}件です")\n    for item in items[:5]:\n        speak(f"{item.get('text', '')}。{_format_reminder_due(item.get('due_at', ''))}です")\n    if len(items) > 5:\n        speak(f"残り{len(items) - 5}件あります")\n    return True\n\n\ndef _execute_reminder_today():\n    items = today_reminders()\n    if not items:\n        speak("今日のリマインダーはありません")\n        return True\n    speak(f"今日のリマインダーは{len(items)}件です")\n    for item in items[:5]:\n        speak(f"{_format_reminder_due(item.get('due_at', ''))}、{item.get('text', '')}")\n    if len(items) > 5:\n        speak(f"残り{len(items) - 5}件あります")\n    return True\n\n\ndef _execute_reminder_done():\n    items = list_reminders()\n    if not items:\n        speak("完了できるリマインダーはありません")\n        return True\n    item = items[0]\n    if complete_reminder(str(item.get('id', ''))):\n        speak(f"リマインダーを完了にしました。{item.get('text', '')}")\n    return True\n\n\ndef _execute_reminder_delete():\n    items = list_reminders()\n    if not items:\n        speak("削除できるリマインダーはありません")\n        return True\n    item = items[0]\n    if delete_reminder(str(item.get('id', ''))):\n        speak(f"リマインダーを削除しました。{item.get('text', '')}")\n    return True\n'''


def main() -> int:
    if not AGENT.exists():
        print("meina_agent.py not found")
        return 1
    text = AGENT.read_text(encoding="utf-8")
    if MARKER in text:
        print("Reminder commands V4 already applied")
        return 0

    if not BACKUP.exists():
        shutil.copy2(AGENT, BACKUP)
        print(f"Backup created: {BACKUP}")

    if "from meina_reminders import add_reminder" in text:
        text = re.sub(r"from meina_reminders import .*\n", IMPORT_LINE, text, count=1)
    else:
        anchor = "import command_router\n"
        if anchor not in text:
            raise RuntimeError("import anchor not found")
        text = text.replace(anchor, anchor + "\n" + IMPORT_LINE, 1)

    if "def _execute_reminder_today():" not in text:
        anchor = "\n\ndef execute_routed_command(route):"
        if anchor not in text:
            raise RuntimeError("execute_routed_command anchor not found")
        text = text.replace(anchor, HELPERS + anchor, 1)

    dispatch_anchor = "def execute_routed_command(route):\n"
    if dispatch_anchor not in text:
        raise RuntimeError("execute_routed_command definition not found")

    dispatch = (
        dispatch_anchor
        + '    if route.get("kind") == "reminder_today":\n'
        + '        return _execute_reminder_today()\n'
        + '    if route.get("kind") == "reminder_list":\n'
        + '        return _execute_reminder_list()\n'
        + '    if route.get("kind") == "reminder_done":\n'
        + '        return _execute_reminder_done()\n'
        + '    if route.get("kind") == "reminder_delete":\n'
        + '        return _execute_reminder_delete()\n'
    )
    pattern = re.compile(
        r"def execute_routed_command\(route\):\n(?!\s+if route\.get\(\"kind\"\) == \"reminder_today\"\):"
    )
    text = pattern.sub(dispatch, text, count=1)

    text = text.rstrip() + f"\n\n{MARKER}\n"
    AGENT.write_text(text, encoding="utf-8")
    print("Reminder commands V4 applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""今後の予定表表示を既存リマインダー音声機能へ接続する起動アップグレード。"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
MARKER = "# MEINA_REMINDER_COMMANDS_V7"
BACKUP = ROOT / "meina_agent.py.backup_before_reminder_v7"
IMPORT_LINE = "from meina_reminders import add_reminder, complete_reminder, delete_reminder, due_reminders, find_reminders, list_reminders, today_reminders, tomorrow_reminders, upcoming_reminders\n"

HELPER = '''\n\ndef _execute_reminder_upcoming():\n    items = upcoming_reminders(7)\n    if not items:\n        speak("今後7日間の予定はありません")\n        return True\n    speak(f"今後7日間の予定は{len(items)}件です")\n    for item in items[:10]:\n        speak(f"{_format_reminder_due(item.get('due_at', ''))}、{item.get('text', '')}")\n    if len(items) > 10:\n        speak(f"残り{len(items) - 10}件あります")\n    return True\n'''


def main() -> int:
    if not AGENT.exists():
        print("meina_agent.py not found")
        return 1
    text = AGENT.read_text(encoding="utf-8")
    if MARKER in text:
        print("Reminder commands V7 already applied")
        return 0

    if not BACKUP.exists():
        shutil.copy2(AGENT, BACKUP)
        print(f"Backup created: {BACKUP}")

    import_match = re.search(r"^from meina_reminders import .*\n", text, re.MULTILINE)
    if import_match:
        text = text[:import_match.start()] + IMPORT_LINE + text[import_match.end():]
    else:
        anchor = "import command_router\n"
        if anchor not in text:
            raise RuntimeError("import anchor not found")
        text = text.replace(anchor, anchor + "\n" + IMPORT_LINE, 1)

    if "def _execute_reminder_upcoming():" not in text:
        anchor = "\n\ndef execute_routed_command(route):"
        if anchor not in text:
            raise RuntimeError("execute_routed_command anchor not found")
        text = text.replace(anchor, HELPER + anchor, 1)

    if 'route.get("kind") == "reminder_upcoming"' not in text:
        anchor = "def execute_routed_command(route):\n"
        if anchor not in text:
            raise RuntimeError("execute_routed_command definition not found")
        dispatch = (
            anchor
            + '    if route.get("kind") == "reminder_upcoming":\n'
            + "        return _execute_reminder_upcoming()\n"
        )
        text = text.replace(anchor, dispatch, 1)

    text = text.rstrip() + f"\n\n{MARKER}\n"
    AGENT.write_text(text, encoding="utf-8")
    print("Reminder commands V7 applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""リマインダーの一覧・削除・完了を既存エージェントへ安全に追加する起動アップグレード。"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
MARKER = "# MEINA_REMINDER_COMMANDS_V3"
BACKUP = ROOT / "meina_agent.py.backup_before_reminder_v3"

IMPORT_BLOCK = "from meina_reminders import add_reminder, complete_reminder, due_reminders, list_reminders\nfrom meina_reminder_parser import parse_reminder_command\n"

HELPERS = r'''

def _execute_reminder_list():
    items = list_reminders()
    if not items:
        speak("現在、登録されているリマインダーはありません")
        return True
    speak(f"登録されているリマインダーは{len(items)}件です")
    for item in items[:5]:
        speak(f"{item.get('text', '')}。時刻は{item.get('due_at', '')}")
    if len(items) > 5:
        speak(f"残り{len(items) - 5}件あります")
    return True


def _execute_reminder_done():
    items = list_reminders()
    if not items:
        speak("完了できるリマインダーはありません")
        return True
    item = items[0]
    if complete_reminder(str(item.get("id", ""))):
        speak(f"リマインダーを完了にしました。{item.get('text', '')}")
    return True


def _execute_reminder_delete():
    items = list_reminders()
    if not items:
        speak("削除できるリマインダーはありません")
        return True
    item = items[0]
    if complete_reminder(str(item.get("id", ""))):
        speak(f"リマインダーを削除しました。{item.get('text', '')}")
    return True
'''


def main() -> int:
    if not AGENT.exists():
        print("meina_agent.py not found")
        return 1
    text = AGENT.read_text(encoding="utf-8")
    if MARKER in text:
        print("Reminder commands V3 already applied")
        return 0
    if not BACKUP.exists():
        shutil.copy2(AGENT, BACKUP)
    if "from meina_reminder_parser import parse_reminder_command" not in text:
        anchor = "import command_router\n"
        if anchor not in text:
            raise RuntimeError("import anchor not found")
        text = text.replace(anchor, anchor + "\n" + IMPORT_BLOCK, 1)
    if "def _execute_reminder_list():" not in text:
        anchor = "\n\ndef execute_routed_command(route):"
        if anchor not in text:
            raise RuntimeError("execute_routed_command anchor not found")
        text = text.replace(anchor, HELPERS + anchor, 1)
    dispatch = '''def execute_routed_command(route):
    if route.get("kind") == "reminder_list":
        return _execute_reminder_list()
    if route.get("kind") == "reminder_done":
        return _execute_reminder_done()
    if route.get("kind") == "reminder_delete":
        return _execute_reminder_delete()
'''
    text = re.sub(r"def execute_routed_command\(route\):\n", dispatch, text, count=1)
    text = text.replace(MARKER, MARKER, 1) if MARKER in text else text
    text = text + f"\n\n{MARKER}\n"
    AGENT.write_text(text, encoding="utf-8")
    print("Reminder commands V3 applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

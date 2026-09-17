"""リマインダーの一覧・今日・明日・完了・削除を既存エージェントへ安全に接続する起動アップグレード。"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
MARKER = "# MEINA_REMINDER_COMMANDS_V6"
BACKUP = ROOT / "meina_agent.py.backup_before_reminder_v6"
IMPORT_LINE = "from meina_reminders import add_reminder, complete_reminder, delete_reminder, due_reminders, find_reminders, list_reminders, today_reminders, tomorrow_reminders\n"

HELPERS = r'''

def _format_reminder_due(value):
    try:
        from datetime import datetime
        due = datetime.fromisoformat(str(value))
        return f"{due.month}月{due.day}日{due.hour}時{due.minute}分"
    except (TypeError, ValueError):
        return str(value)


def _extract_reminder_target(query):
    text = str(query or "").strip()
    text = re.sub(r"^(?:メイナ[、,]?)", "", text)
    text = re.sub(r"リマインダー(?:を)?(?:完了|削除)(?:して|してください|お願い)?", "", text)
    text = re.sub(r"リマインド(?:を)?(?:完了|削除)(?:して|してください|お願い)?", "", text)
    text = re.sub(r"^(?:の|を|に|して|ください|お願いします)[、,\s]*", "", text)
    return text.strip(" 、。！？? ")


def _pick_reminder(query):
    target = _extract_reminder_target(query)
    if not target:
        return list_reminders()[:1], ""
    return find_reminders(target), target


def _speak_date_group(label, items):
    if not items:
        speak(f"{label}のリマインダーはありません")
        return True
    speak(f"{label}のリマインダーは{len(items)}件です")
    for item in items[:5]:
        speak(f"{_format_reminder_due(item.get('due_at', ''))}、{item.get('text', '')}")
    if len(items) > 5:
        speak(f"残り{len(items) - 5}件あります")
    return True


def _execute_reminder_list():
    return _speak_date_group("登録されている", list_reminders())


def _execute_reminder_today():
    return _speak_date_group("今日", today_reminders())


def _execute_reminder_tomorrow():
    return _speak_date_group("明日", tomorrow_reminders())


def _execute_reminder_done(query=None):
    items, target = _pick_reminder(query)
    if not items:
        speak(f"「{target}」に一致するリマインダーが見つかりません")
        return True
    if len(items) > 1:
        speak(f"「{target}」に一致するリマインダーが{len(items)}件あります。もう少し具体的に指定してください")
        return True
    item = items[0]
    if complete_reminder(str(item.get('id', ''))):
        speak(f"リマインダーを完了にしました。{item.get('text', '')}")
    return True


def _execute_reminder_delete(query=None):
    items, target = _pick_reminder(query)
    if not items:
        speak(f"「{target}」に一致するリマインダーが見つかりません")
        return True
    if len(items) > 1:
        speak(f"「{target}」に一致するリマインダーが{len(items)}件あります。もう少し具体的に指定してください")
        return True
    item = items[0]
    if delete_reminder(str(item.get('id', ''))):
        speak(f"リマインダーを削除しました。{item.get('text', '')}")
    return True
'''


def main() -> int:
    if not AGENT.exists():
        print("meina_agent.py not found")
        return 1
    text = AGENT.read_text(encoding="utf-8")
    if MARKER in text:
        print("Reminder commands V6 already applied")
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

    start = text.find("\ndef _format_reminder_due(value):")
    anchor = "\n\ndef execute_routed_command(route):"
    if start != -1:
        end = text.find(anchor, start)
        if end == -1:
            raise RuntimeError("execute_routed_command anchor not found")
        text = text[:start] + HELPERS + text[end:]
    else:
        if anchor not in text:
            raise RuntimeError("execute_routed_command anchor not found")
        text = text.replace(anchor, HELPERS + anchor, 1)

    dispatch = (
        "def execute_routed_command(route):\n"
        '    if route.get("kind") == "reminder_tomorrow":\n'
        "        return _execute_reminder_tomorrow()\n"
        '    if route.get("kind") == "reminder_today":\n'
        "        return _execute_reminder_today()\n"
        '    if route.get("kind") == "reminder_list":\n'
        "        return _execute_reminder_list()\n"
        '    if route.get("kind") == "reminder_done":\n'
        "        return _execute_reminder_done(route.get(\"query\"))\n"
        '    if route.get("kind") == "reminder_delete":\n'
        "        return _execute_reminder_delete(route.get(\"query\"))\n"
    )
    text = re.sub(r"def execute_routed_command\(route\):\n(?!\s+if route\.get\(\"kind\"\) == \"reminder_tomorrow\"\):", dispatch, text, count=1)

    text = text.rstrip() + f"\n\n{MARKER}\n"
    AGENT.write_text(text, encoding="utf-8")
    print("Reminder commands V6 applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

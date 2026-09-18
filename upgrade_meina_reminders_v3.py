"""リマインダー秘書機能V3を既存エージェントへ安全に追加する。"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
MARKER = "# MEINA_REMINDER_COMMANDS_V3"
BACKUP = ROOT / "meina_agent.py.backup_before_reminder_v3"

HELPERS = r'''
def _execute_reminder_list():
    items = list_reminders()
    if not items:
        speak("現在、登録されているリマインダーはありません")
        return True
    speak(f"登録されているリマインダーは{len(items)}件です")
    for item in items[:5]:
        speak(f"{item.get('text', '')}。時刻は{item.get('due_at', '').replace('T', ' ')}")
    if len(items) > 5:
        speak(f"残り{len(items) - 5}件あります")
    return True


def _execute_reminder_today():
    from meina_reminders import today_reminders
    items = today_reminders()
    if not items:
        speak("今日の予定はありません")
        return True
    speak("今日の予定です")
    for item in items[:5]:
        speak(f"{item.get('text', '')}。時刻は{item.get('due_at', '').replace('T', ' ')}")
    return True


def _execute_reminder_tomorrow():
    from meina_reminders import tomorrow_reminders
    items = tomorrow_reminders()
    if not items:
        speak("明日の予定はありません")
        return True
    speak("明日の予定です")
    for item in items[:5]:
        speak(f"{item.get('text', '')}。時刻は{item.get('due_at', '').replace('T', ' ')}")
    return True


def _execute_reminder_upcoming():
    from meina_reminders import upcoming_reminders
    items = upcoming_reminders()
    if not items:
        speak("今後の予定はありません")
        return True
    speak("今後の予定です")
    for item in items[:7]:
        speak(f"{item.get('text', '')}。時刻は{item.get('due_at', '').replace('T', ' ')}")
    return True


def _execute_reminder_mutation(route):
    from meina_reminders import complete_reminder, delete_reminder, find_reminders
    raw = str(route.get("query") or "")
    query = re.sub(r"(リマインダー|リマインド)(を)?(完了|削除)", "", raw).strip(" 、。！？?")
    if not query:
        speak("対象のリマインダー名を指定してください")
        return True

    matches = find_reminders(query)
    if not matches:
        speak("その名前のリマインダーは見つかりませんでした")
        return True
    if len(matches) > 1:
        speak("同じ名前のリマインダーが複数あります。もう少し具体的に指定してください")
        return True

    item = matches[0]
    if route.get("kind") == "reminder_done":
        ok = complete_reminder(item["id"])
        action = "完了"
    else:
        ok = delete_reminder(item["id"])
        action = "削除"
    speak(f"「{item.get('text', '')}」を{action}{'しました' if ok else 'できませんでした'}")
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

    shutil.copy2(AGENT, BACKUP)
    print(f"Backup created: {BACKUP}")

    if "from meina_reminders import add_reminder, complete_reminder, due_reminders, list_reminders" not in text:
        anchor = "import command_router
"
        if anchor not in text:
            raise RuntimeError("import anchor not found")
        imports = "from meina_reminders import add_reminder, complete_reminder, due_reminders, list_reminders, delete_reminder, find_reminders
from meina_reminder_parser import parse_reminder_command
"
        text = text.replace(anchor, anchor + imports, 1)

    if "def _execute_reminder_today():" not in text:
        anchor = "

MEINA_UPGRADE_TASK_PLAN_LOCAL_V1_EXEC"
        if anchor not in text:
            anchor = "

def execute_task_plan(route):"
        if anchor not in text:
            raise RuntimeError("task plan anchor not found")
        text = text.replace(anchor, "
" + HELPERS + anchor, 1)

    marker = "def execute_routed_command(route):"
    if marker not in text:
        raise RuntimeError("execute_routed_command not found")

    dispatch = '''def execute_routed_command(route):
    if route.get("kind") == "reminder_list":
        return _execute_reminder_list()
    if route.get("kind") == "reminder_today":
        return _execute_reminder_today()
    if route.get("kind") == "reminder_tomorrow":
        return _execute_reminder_tomorrow()
    if route.get("kind") == "reminder_upcoming":
        return _execute_reminder_upcoming()
    if route.get("kind") in ("reminder_done", "reminder_delete"):
        return _execute_reminder_mutation(route)
'''
    text = text.replace(marker, dispatch, 1)
    text += f"

{MARKER}
"
    AGENT.write_text(text, encoding="utf-8")
    print("Reminder commands V3 applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

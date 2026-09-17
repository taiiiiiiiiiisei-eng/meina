"""起動時にめいなのリマインダー音声機能を安全に追加する。"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
MARKER = "# MEINA_REMINDER_INTEGRATION_V2"
BACKUP = ROOT / "meina_agent.py.backup_before_reminder_v2"

IMPORT_BLOCK = "from meina_reminders import add_reminder, complete_reminder, due_reminders, list_reminders\nfrom meina_reminder_parser import parse_reminder_command\n"

HANDLER = '''\n\ndef _execute_reminder(route):\n    parsed = parse_reminder_command(route.get("query", ""))\n    if not parsed:\n        speak("リマインダーの時間と内容を理解できませんでした")\n        return True\n    item = add_reminder(parsed["text"], parsed["due_at"])\n    speak(f"リマインダーを設定しました。{parsed['text']}")\n    print("⏰ リマインダー:", item)\n    return True\n\n\ndef _execute_reminder_list():\n    items = list_reminders()\n    if not items:\n        speak("現在、登録されているリマインダーはありません")\n        return True\n    items = items[:5]\n    for item in items:\n        speak(f"{item.get('text', '')}。予定時刻は{item.get('due_at', '')}")\n    return True\n\n\ndef _reminder_worker():\n    import time\n    while True:\n        try:\n            for item in due_reminders():\n                speak(f"リマインダーです。{item.get('text', '')}")\n                complete_reminder(str(item.get("id", "")))\n        except Exception as e:\n            print("❌ リマインダー監視エラー:", e)\n        time.sleep(1.0)\n\n\ndef _start_reminder_worker():\n    import threading\n    thread = threading.Thread(target=_reminder_worker, daemon=True, name="meina-reminder-worker")\n    thread.start()\n\n'''


def _add_dispatch(text: str) -> str:
    """既存のタスクプランwrapperを壊さず、reminderだけを最優先で追加する。"""
    if 'route.get("kind") == "reminder"' in text:
        return text
    marker = 'def execute_routed_command(route):'
    if marker not in text:
        raise RuntimeError("execute_routed_command wrapper not found")
    replacement = '''def execute_routed_command(route):\n    if route.get("kind") == "reminder":\n        return _execute_reminder(route)\n    if route.get("kind") == "reminder_list":\n        return _execute_reminder_list()\n'''
    return text.replace(marker, replacement, 1)


def main() -> int:
    if not AGENT.exists():
        print("meina_agent.py not found")
        return 1
    text = AGENT.read_text(encoding="utf-8")
    if MARKER in text:
        print("Reminder integration already applied")
        return 0

    if not BACKUP.exists():
        shutil.copy2(AGENT, BACKUP)
        print(f"Backup created: {BACKUP}")

    if "from meina_reminders import add_reminder" not in text:
        anchor = "import command_router\n"
        if anchor not in text:
            raise RuntimeError("import anchor not found")
        text = text.replace(anchor, anchor + "\n" + IMPORT_BLOCK, 1)

    if "def _execute_reminder(route):" not in text:
        insert_before = "\n\ndef execute_action(frame):"
        if insert_before not in text:
            raise RuntimeError("execute_action anchor not found")
        text = text.replace(insert_before, HANDLER + insert_before, 1)

    text = _add_dispatch(text)

    speak_anchor = "# =========================================================\n# 音声録音\n# =========================================================\n"
    if speak_anchor not in text:
        raise RuntimeError("speak section anchor not found")
    worker_block = f"\n{MARKER}\n_start_reminder_worker()\n"
    text = text.replace(speak_anchor, worker_block + "\n" + speak_anchor, 1)

    AGENT.write_text(text, encoding="utf-8")
    print("Reminder voice integration V2 applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

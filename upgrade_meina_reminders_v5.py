"""明日の予定読み上げを既存のリマインダー音声機能へ安全に追加する。"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
MARKER = "# MEINA_REMINDER_COMMANDS_V5"
BACKUP = ROOT / "meina_agent.py.backup_before_reminder_v5"

HELPER = '''\n\ndef _execute_reminder_tomorrow():\n    items = tomorrow_reminders()\n    if not items:\n        speak("明日のリマインダーはありません")\n        return True\n    speak(f"明日のリマインダーは{len(items)}件です")\n    for item in items[:5]:\n        speak(f"{_format_reminder_due(item.get('due_at', ''))}、{item.get('text', '')}")\n    if len(items) > 5:\n        speak(f"残り{len(items) - 5}件あります")\n    return True\n'''


def main() -> int:
    if not AGENT.exists():
        print("meina_agent.py not found")
        return 1

    text = AGENT.read_text(encoding="utf-8")
    if MARKER in text:
        print("Reminder commands V5 already applied")
        return 0

    if not BACKUP.exists():
        shutil.copy2(AGENT, BACKUP)
        print(f"Backup created: {BACKUP}")

    if "tomorrow_reminders" not in text:
        import_line = re.search(r"^from meina_reminders import .*\n", text, re.MULTILINE)
        if import_line:
            line = import_line.group(0).rstrip("\n")
            if "tomorrow_reminders" not in line:
                replacement = line.rstrip() + ", tomorrow_reminders\n"
                text = text[: import_line.start()] + replacement + text[import_line.end() :]
        else:
            raise RuntimeError("meina_reminders import not found")

    if "def _execute_reminder_tomorrow():" not in text:
        anchor = "\n\ndef execute_routed_command(route):"
        if anchor not in text:
            raise RuntimeError("execute_routed_command anchor not found")
        text = text.replace(anchor, HELPER + anchor, 1)

    if 'route.get("kind") == "reminder_tomorrow"' not in text:
        anchor = 'def execute_routed_command(route):\n'
        if anchor not in text:
            raise RuntimeError("execute_routed_command definition not found")
        dispatch = (
            anchor
            + '    if route.get("kind") == "reminder_tomorrow":\n'
            + '        return _execute_reminder_tomorrow()\n'
        )
        text = text.replace(anchor, dispatch, 1)

    text = text.rstrip() + f"\n\n{MARKER}\n"
    AGENT.write_text(text, encoding="utf-8")
    print("Reminder commands V5 applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""リマインダー秘書最終配線の静的セルフテスト。"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main() -> int:
    final = ROOT / "upgrade_meina_reminder_secretary_final.py"
    ast.parse(final.read_text(encoding="utf-8"))
    text = final.read_text(encoding="utf-8")
    for name in (
        "upgrade_meina_reminder_worker.py",
        "upgrade_meina_reminders_v3.py",
        "upgrade_meina_reminders_v4.py",
        "upgrade_meina_reminders_v5.py",
        "upgrade_meina_reminders_v7.py",
    ):
        assert name in text, name

    for name in (
        "upgrade_meina_reminders_v4.py",
        "upgrade_meina_reminders_v5.py",
        "upgrade_meina_reminders_v7.py",
    ):
        assert (ROOT / name).exists(), name

    print("Reminder secretary final self-test: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

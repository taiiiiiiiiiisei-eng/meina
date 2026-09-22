"""リマインダー監視部品の依存関係なしセルフテスト。"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main() -> int:
    upgrader = (ROOT / "upgrade_meina_reminder_worker.py").read_text(encoding="utf-8")
    assert "# MEINA_REMINDER_WORKER_V1" in upgrader
    assert "due_reminders()" in upgrader
    assert "complete_reminder" in upgrader

    agent = (ROOT / "meina_agent.py").read_text(encoding="utf-8")
    ast.parse(agent)
    print("Reminder worker self-test: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

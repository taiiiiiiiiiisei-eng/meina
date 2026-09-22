"""旧リマインダー監視アップグレーダーの安全な互換チェック。

現在は meina_agent.py から meina_reminder_worker.py を直接起動する。
このスクリプトは互換性のため残すが、ファイル書き換えは行わない。
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
WORKER = ROOT / "meina_reminder_worker.py"


def main() -> int:
    for path in (AGENT, WORKER):
        if not path.exists():
            print(f"FAILED: {path.name} が見つかりません")
            return 1
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            print(f"FAILED: {path.name} Python構文エラー: {exc}")
            return 1

    agent_text = AGENT.read_text(encoding="utf-8")
    if "start_reminder_worker" not in agent_text:
        print("FAILED: meina_agent.py に直接監視配線がありません")
        return 1

    print("Reminder worker direct integration: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""リマインダー秘書の安全な最終配線チェック。
既存の meina_agent.py の通常ルーティングを置き換える旧アップグレーダーは
ここから自動実行しない。まず静的セルフテストで現在の実装を検証する。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SELF_TEST = ROOT / "meina_reminder_secretary_v8_self_test.py"

def main() -> int:
    if not SELF_TEST.exists():
        print("FAILED: meina_reminder_secretary_v8_self_test.py が見つかりません")
        return 1
    result = subprocess.run([sys.executable, str(SELF_TEST)], check=False)
    if result.returncode != 0:
        print(f"FAILED: reminder secretary safe self-test (exit={result.returncode})")
        return result.returncode
    print("Reminder secretary final wiring: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

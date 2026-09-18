"""リマインダー秘書機能の最終配線を一度だけ適用する。
既存のV3/V4/V5/V7アップグレーダーを順番に実行するだけで、
既存コードを直接書き換えるロジックは各アップグレーダーに任せる。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

SCRIPTS = (
    "upgrade_meina_reminder_worker.py",
    "upgrade_meina_reminders_v3.py",
    "upgrade_meina_reminders_v4.py",
    "upgrade_meina_reminders_v5.py",
    "upgrade_meina_reminders_v7.py",
)

def main() -> int:
    for name in SCRIPTS:
        path = ROOT / name
        if not path.exists():
            print(f"SKIP: {name} が見つかりません")
            continue
        print(f"\n>>> {name}")
        result = subprocess.run([sys.executable, str(path)], check=False)
        if result.returncode != 0:
            print(f"FAILED: {name} (exit={result.returncode})")
            return result.returncode
    print("\nReminder secretary final wiring: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

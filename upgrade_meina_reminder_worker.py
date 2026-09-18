"""起動時にローカルリマインダー監視を追加する安全なアップグレーダー。"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
MARKER = "# MEINA_REMINDER_WORKER_V1"
BACKUP = ROOT / "meina_agent.py.backup_before_reminder_worker_v1"

BLOCK = r'''
# MEINA_REMINDER_WORKER_V1
def _meina_reminder_worker():
    import threading
    import time
    from meina_reminders import complete_reminder, due_reminders

    def worker():
        while True:
            try:
                for item in due_reminders():
                    message = f"リマインダーです。{item.get('text', '')}"
                    speak(message)
                    complete_reminder(str(item.get("id", "")))
            except Exception as e:
                print("❌ リマインダー監視エラー:", e)
            time.sleep(1.0)

    threading.Thread(
        target=worker,
        daemon=True,
        name="meina-reminder-worker",
    ).start()


_meina_reminder_worker()
'''

def main() -> int:
    if not AGENT.exists():
        print("meina_agent.py not found")
        return 1
    text = AGENT.read_text(encoding="utf-8")
    if MARKER in text:
        print("Reminder worker already applied")
        return 0
    if not BACKUP.exists():
        shutil.copy2(AGENT, BACKUP)
        print(f"Backup created: {BACKUP}")
    anchor = "
# =========================================================
# メイン
# =========================================================
"
    if anchor not in text:
        raise RuntimeError("main anchor not found")
    text = text.replace(anchor, "
" + BLOCK + anchor, 1)
    AGENT.write_text(text, encoding="utf-8")
    print("Reminder worker integration applied")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

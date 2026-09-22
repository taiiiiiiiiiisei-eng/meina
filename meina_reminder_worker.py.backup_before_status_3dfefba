"""めいなのローカル・リマインダー監視。起動中に期限到来を音声通知する。"""
from __future__ import annotations

import threading
from typing import Callable

from meina_reminders import complete_reminder, due_reminders

_worker_thread: threading.Thread | None = None
_worker_stop: threading.Event | None = None


def process_due_reminders(
    speak_func: Callable[[str], None],
    now=None,
) -> int:
    """現在期限を迎えている予定を通知し、通常完了または次回へ繰り越す。"""
    delivered = 0
    for item in due_reminders(now):
        reminder_id = str(item.get("id") or "")
        if not reminder_id:
            continue

        message = f"リマインダーです。{item.get('text', '')}"
        speak_func(message)

        if complete_reminder(reminder_id, now=now):
            delivered += 1
    return delivered


def start_reminder_worker(
    speak_func: Callable[[str], None],
    interval_seconds: float = 1.0,
) -> bool:
    """監視スレッドを一度だけ起動する。すでに動作中ならFalse。"""
    global _worker_thread, _worker_stop

    if _worker_thread is not None and _worker_thread.is_alive():
        return False

    stop_event = threading.Event()
    interval = max(0.2, float(interval_seconds))

    def worker() -> None:
        while not stop_event.is_set():
            try:
                process_due_reminders(speak_func)
            except Exception as exc:
                print("❌ リマインダー監視エラー:", exc)
            stop_event.wait(interval)

    thread = threading.Thread(
        target=worker,
        daemon=True,
        name="meina-reminder-worker",
    )
    _worker_stop = stop_event
    _worker_thread = thread
    thread.start()
    return True


def stop_reminder_worker() -> bool:
    """テストや終了処理用に監視スレッドへ停止要求を送る。"""
    global _worker_thread, _worker_stop

    if _worker_stop is None:
        return False

    _worker_stop.set()
    thread = _worker_thread
    if thread is not None and thread.is_alive():
        thread.join(timeout=2.0)

    _worker_thread = None
    _worker_stop = None
    return True

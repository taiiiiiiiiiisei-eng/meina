"""リマインダー秘書の安全な最終検証。
既存ルーティングを壊さず、関連Pythonの構文と依存関係なしセルフテストを確認する。
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
ROUTER = ROOT / "command_router.py"
PARSER = ROOT / "meina_reminder_parser.py"
REMINDERS = ROOT / "meina_reminders.py"
WORKER = ROOT / "meina_reminder_worker.py"
LEGACY_WORKER_UPGRADER = ROOT / "upgrade_meina_reminder_worker.py"
REMINDER_TEST = ROOT / "meina_reminders_self_test.py"

REQUIRED_KINDS = (
    "reminder",
    "reminder_today",
    "reminder_tomorrow",
    "reminder_week",
    "reminder_month",
    "reminder_overdue",
    "reminder_upcoming",
    "reminder_brief",
    "reminder_next",
    "reminder_soon",
    "reminder_list",
    "reminder_pre_notify_set",
    "reminder_pre_notify_clear",
    "reminder_pause",
    "reminder_resume",
    "reminder_repeat_set",
    "reminder_repeat_clear",
    "reminder_snooze",
    "reminder_reschedule",
    "reminder_rename",
    "reminder_done",
    "reminder_delete",
)


def _functions(tree):
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _parse_file(path: Path) -> ast.AST | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        print(f"FAILED: {path.name} Python構文エラー: {exc}")
        return None


def main() -> int:
    required_files = (
        AGENT,
        ROUTER,
        PARSER,
        REMINDERS,
        WORKER,
        LEGACY_WORKER_UPGRADER,
        REMINDER_TEST,
    )
    for path in required_files:
        if not path.exists():
            print(f"FAILED: {path.name} が見つかりません")
            return 1

    trees = {}
    for path in required_files:
        tree = _parse_file(path)
        if tree is None:
            return 1
        trees[path] = tree

    agent_text = AGENT.read_text(encoding="utf-8")
    router_text = ROUTER.read_text(encoding="utf-8")
    agent_funcs = _functions(trees[AGENT])

    if "execute_routed_command" not in agent_funcs or "_execute_routed_command_base" not in agent_funcs:
        print("FAILED: 通常のルーティング関数が見つかりません")
        return 1

    worker_funcs = _functions(trees[WORKER])
    required_worker_funcs = {
        "process_due_reminders",
        "process_pre_due_reminders",
        "start_reminder_worker",
        "stop_reminder_worker",
        "is_reminder_worker_running",
    }
    if not required_worker_funcs.issubset(worker_funcs):
        print("FAILED: リマインダー監視関数が不足しています")
        return 1
    if "start_reminder_worker" not in agent_text:
        print("FAILED: meina_agent からリマインダー監視が起動されません")
        return 1
    if "stop_reminder_worker" not in agent_text:
        print("FAILED: meina_agent の終了時に監視停止処理がありません")
        return 1
    if "_SPEAK_LOCK" not in agent_text or "with _SPEAK_LOCK:" not in agent_text:
        print("FAILED: TTSのスレッド競合防止ロックがありません")
        return 1
    if "find_duplicate_reminder" not in agent_text:
        print("FAILED: 音声経由の重複予定防止がありません")
        return 1
    if "next_reminder" not in agent_text:
        print("FAILED: 次の予定案内がありません")
        return 1
    if "notify_before_minutes" not in agent_text:
        print("FAILED: 事前通知設定の表示・実行配線がありません")
        return 1
    if "snooze_reminder" not in agent_text:
        print("FAILED: スヌーズ実行配線がありません")
        return 1
    if "week_reminders" not in agent_text or "month_reminders" not in agent_text:
        print("FAILED: 暦週・暦月の予定表示配線がありません")
        return 1

    legacy_worker_text = LEGACY_WORKER_UPGRADER.read_text(encoding="utf-8")
    forbidden_worker_mutations = ("copy2(", "AGENT.write_text(", "write_text(text")
    if any(token in legacy_worker_text for token in forbidden_worker_mutations):
        print("FAILED: 旧リマインダー監視アップグレーダーが本体を書き換えます")
        return 1

    missing_router = [
        kind for kind in REQUIRED_KINDS
        if f'"kind": "{kind}"' not in router_text
    ]
    missing_agent = [
        kind for kind in REQUIRED_KINDS
        if (
            f'kind == "{kind}"' not in agent_text
            and f'kind in ("reminder_done", "reminder_delete")' not in agent_text
        )
    ]
    if missing_router:
        print("FAILED: command_router に不足:", ", ".join(missing_router))
        return 1
    if missing_agent:
        print("FAILED: meina_agent に不足:", ", ".join(missing_agent))
        return 1

    final = ROOT / "upgrade_meina_reminder_secretary_final.py"
    if final.exists():
        final_text = final.read_text(encoding="utf-8")
        forbidden = (
            "upgrade_meina_reminders_v3.py",
            "upgrade_meina_reminders_v4.py",
            "upgrade_meina_reminders_v5.py",
            "upgrade_meina_reminders_v7.py",
        )
        bad = [name for name in forbidden if name in final_text]
        if bad:
            print(
                "FAILED: 旧アップグレーダーを最終配線から実行しています:",
                ", ".join(bad),
            )
            return 1

    result = subprocess.run(
        [sys.executable, str(REMINDER_TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if result.returncode != 0:
        print(f"FAILED: reminder self-test (exit={result.returncode})")
        return result.returncode

    print("Reminder secretary safe wiring self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

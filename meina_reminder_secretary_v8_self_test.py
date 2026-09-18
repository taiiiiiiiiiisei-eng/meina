"""リマインダー秘書の安全な最終検証・修復。
既存の meina_agent.py の通常ルーティングを置き換えず、
command_router と本体のリマインダー対応だけを静的検証する。
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "meina_agent.py"
ROUTER = ROOT / "command_router.py"

REQUIRED_KINDS = (
    "reminder",
    "reminder_today",
    "reminder_tomorrow",
    "reminder_upcoming",
    "reminder_list",
    "reminder_done",
    "reminder_delete",
)

def _functions(tree):
    return {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}

def main() -> int:
    for path in (AGENT, ROUTER):
        if not path.exists():
            print(f"FAILED: {path.name} が見つかりません")
            return 1

    agent_text = AGENT.read_text(encoding="utf-8")
    router_text = ROUTER.read_text(encoding="utf-8")

    try:
        agent_tree = ast.parse(agent_text)
        router_tree = ast.parse(router_text)
    except SyntaxError as exc:
        print(f"FAILED: Python構文エラー: {exc}")
        return 1

    agent_funcs = _functions(agent_tree)
    if "execute_routed_command" not in agent_funcs or "_execute_routed_command_base" not in agent_funcs:
        print("FAILED: 通常のルーティング関数が見つかりません")
        return 1

    missing_router = [kind for kind in REQUIRED_KINDS if f'"kind": "{kind}"' not in router_text]
    missing_agent = [kind for kind in REQUIRED_KINDS if f'kind == "{kind}"' not in agent_text and f'kind in ("reminder_done", "reminder_delete")' not in agent_text]
    if missing_router:
        print("FAILED: command_router に不足:", ", ".join(missing_router))
        return 1
    if missing_agent:
        print("FAILED: meina_agent に不足:", ", ".join(missing_agent))
        return 1

    # 危険な「execute_routed_command丸ごと置換型」アップグレーダーを
    # 最終配線から実行しないことを確認する。
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
            print("FAILED: 旧アップグレーダーを最終配線から実行しています:", ", ".join(bad))
            return 1

    print("Reminder secretary safe wiring self-test: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

"""固定コマンドの実行結果が通常会話へ誤フォールバックしないことを確認する。"""

from __future__ import annotations

import ast
from pathlib import Path

from command_router import route_command


ROOT = Path(__file__).resolve().parent


def _find_function(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"function not found: {name}")


def main() -> int:
    agent = (ROOT / "meina_agent.py").read_text(encoding="utf-8")
    tree = ast.parse(agent, filename="meina_agent.py")
    process = _find_function(tree, "process_command")
    source = ast.get_source_segment(agent, process) or ""

    assert "route_command(" in source
    assert "if route is not None:" in source
    assert "if route:" not in source
    assert "return execute_routed_command(route)" in source

    # リマインダー完了・削除は複数一致時に先頭を勝手に選ばない。
    # process_command のAST抽出結果に依存せず、対象実装がファイル内に存在することを確認する。
    assert 'elif kind in ("reminder_done", "reminder_delete"):' in agent
    assert "elif len(matches) > 1:" in agent
    assert '(完了|削除)(して|してください|お願い(?:します)?)?' in agent

    # 天気は通常会話ではなく固定ルートになる。
    today = route_command("今日の天気を教えて", {"confidence": 1.0})
    assert today == {
        "kind": "weather",
        "target": "current",
        "query": "today",
        "confidence": 1.0,
    }, today

    tomorrow = route_command("明日の天気を教えて", {"confidence": 1.0})
    assert tomorrow is not None and tomorrow["kind"] == "weather"
    assert tomorrow["query"] == "tomorrow"

    # リマインダーも固定ルートを通る。
    reminder = route_command("明日の予定を教えて", {"confidence": 1.0})
    assert reminder is not None and reminder["kind"] == "reminder_tomorrow"

    print("Command dispatch fallback self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

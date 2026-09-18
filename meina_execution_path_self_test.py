"""安全なコマンド実行経路を守る静的テスト。"""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _function_node(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"function not found: {name}")


def _called_names(node: ast.AST) -> list[str]:
    names: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            target = child.func
            if isinstance(target, ast.Name):
                names.append(target.id)
            elif isinstance(target, ast.Attribute):
                names.append(target.attr)
    return names


def main() -> int:
    agent_source = (ROOT / "meina_agent.py").read_text(encoding="utf-8")
    app_source = (ROOT / "meina_app.py").read_text(encoding="utf-8")

    agent_tree = ast.parse(agent_source, filename="meina_agent.py")
    app_tree = ast.parse(app_source, filename="meina_app.py")

    process_command = _function_node(agent_tree, "process_command")
    calls = _called_names(process_command)

    # すべてのコマンド処理は安全なルーター経由で実行する。
    assert "route_command" in calls
    assert "execute_routed_command" in calls
    assert "execute_action" not in calls
    assert "launch_app" not in calls
    assert "open_notepad" not in calls
    assert "open_google" not in calls
    assert "google_search" not in calls

    # GUIも直接PC操作をせず、meina_agent.process_commandだけを入口にする。
    gui_calls = []
    for node in ast.walk(app_tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "process_command":
                gui_calls.append(node)
    assert gui_calls, "GUI must call meina_agent.process_command"

    # GUI側に直接PC操作の実行呼び出しを入れない。
    gui_direct_calls = _called_names(app_tree)
    assert "launch_app" not in gui_direct_calls
    assert "open_notepad" not in gui_direct_calls
    assert "open_google" not in gui_direct_calls
    assert "google_search" not in gui_direct_calls

    print("Execution path guard self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
